"""Assets for the v5a viewer (v5_viewer/meshes.js).

- part_straight / part_scallop: the shade WITHOUT side relief, in the WALL frame (x along the wall,
  y up, z out of the wall, origin at the switch-box centre)
- device / plate: in the DOORBELL frame (the viewer places them with the doorbell->wall matrix)
- PATTERNS[edge][pattern]['1' | '-1']: relief polygons (z, y) of each side wall, in the doorbell frame
- _dims: the doorbell->wall matrix, nut-pocket and wall-bolt positions
"""
import base64, io, json, os, sys
import numpy as np, trimesh
from build123d import import_brep, export_stl

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sunshade as v1
import sunshade_v3 as v3
import sunshade_v4 as v4
import sunshade_v5a as a5
import shade_patterns as sp
from shapely.geometry import Polygon

ROOT = os.path.join(HERE, "..")
V = os.path.join(ROOT, "v5a")
OUT = os.path.join(ROOT, "v5_viewer"); os.makedirs(OUT, exist_ok=True)

G = json.load(open(os.path.join(V, "geom.json"))) if os.path.exists(os.path.join(V, "geom.json")) else None
U = np.array([float(a5.U.X), float(a5.U.Y), float(a5.U.Z)]); N = np.array([float(a5.N.X), float(a5.N.Y), float(a5.N.Z)])
Ob = a5.WALL_PL.from_local_coords((a5.C_U, v1.MID_Y, 0)); O = np.array([Ob.X, Ob.Y, Ob.Z])
R = np.vstack([U, [0, 1, 0], N]); T = np.eye(4); T[:3, :3] = R; T[:3, 3] = -R @ O


def mesh(shape, tol, M=None):
    p = os.path.join(OUT, "_t.brep.stl")
    export_stl(shape, p, tolerance=tol, angular_tolerance=0.2)
    m = trimesh.load(p); os.remove(p)
    if M is not None:
        m.apply_transform(M)
    buf = io.BytesIO(); m.export(buf, file_type="stl")
    return base64.b64encode(buf.getvalue()).decode(), m


data, base_g = {}, {}
for edge in ("straight", "scallop"):
    data[f"part_{edge}"], m = mesh(import_brep(os.path.join(V, f"base_{edge}.brep")), 0.06, T)
    base_g[edge] = float(m.volume) / 1000 * 1.17
    print(edge, len(m.faces), np.round(m.bounds, 1).tolist(), round(base_g[edge], 1), "g")
data["device"], _ = mesh(v1.device_solid(), 0.06)
data["plate"], _ = mesh(v1.plate_solid(), 0.08)

pats, mass = {}, {}
for edge in ("straight", "scallop"):
    mass[edge] = {}
    P, Nn, Rr, _ = a5.lip(edge == "scallop")
    pats[edge] = {}
    for name in sp.PATTERNS:
        pats[edge][name] = {}
        for s in (+1, -1):
            polys = a5.relief_polys(name, s, P, Rr)
            pats[edge][name][str(s)] = [dict(o=[[round(x, 2), round(y, 2)] for x, y in g.exterior.coords],
                                             h=[[[round(x, 2), round(y, 2)] for x, y in r.coords] for r in g.interiors]) for g in polys]
        area = sum(sum(Polygon(o["o"], o["h"]).area for o in pats[edge][name][str(s)]) for s in (1, -1))
        mass[edge][name] = round(base_g[edge] + area * v4.LAT_H * 1.17 / 1000, 1)
        print(edge, name, len(pats[edge][name]["1"]), "polys/side", mass[edge][name], "g")

data["_dims"] = dict(XO=v4.XO, LAT_H=v4.LAT_H, M=T.flatten().tolist(), MID_Y=v1.MID_Y, SEAT=v3.SEAT, FRONT=v1.Z_FRONT,
                     LENS_Y=-v1.LENS_DROP, DEV_W=v1.DEV_W, DEV_H=v1.DEV_H,
                     pockets=a5.pocket_centres(), bolts_y=[v1.MID_Y + 60.0, v1.MID_Y - 60.0],
                     bolt_wall=[list(map(float, ax.origin)) for ax in a5.wall_screw_axes()], normal=list(map(float, N)))
data["_labels"] = sp.LABELS
data["_mass"] = mass
open(os.path.join(OUT, "meshes.js"), "w").write("window.MESHES = " + json.dumps(data) + ";\nwindow.PATTERNS = " + json.dumps(pats, separators=(",", ":")) + ";\n")
print(os.path.getsize(os.path.join(OUT, "meshes.js")) // 1000, "kB")

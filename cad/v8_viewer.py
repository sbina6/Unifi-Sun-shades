"""Assets for the v8 (simple, thin flap) shade viewer (v8_viewer/meshes.js).

- part: the shade WITHOUT side relief, in the WALL frame (x along the wall, y up, z out of the wall,
  origin at the switch-box centre)
- device / plate / bracket: in the DOORBELL frame (the viewer places them with the doorbell->wall matrix)
- PATTERNS[pattern]: engraved motif polygons (n, y) of the side walls (wall frame, the same on both walls)
- _dims: the doorbell->wall matrix, box-screw and bracket-bolt positions (wall frame), masses
"""
import base64, io, json, os, sys
import numpy as np, trimesh
from build123d import import_brep, export_stl

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sunshade as v1
import sunshade_v8 as a8
import shade_patterns as sp

ROOT = os.path.join(HERE, "..")
V = os.path.join(ROOT, "v8")
OUT = os.path.join(ROOT, "v8_viewer"); os.makedirs(OUT, exist_ok=True)

U, N, O = a8.vec(a8.U), a8.vec(a8.N), a8.vec(a8.BOXPL.origin)
R = np.vstack([U, [0, 1, 0], N]); T = np.eye(4); T[:3, :3] = R; T[:3, 3] = -R @ O


def mesh(shape, tol, M=None):
    p = os.path.join(OUT, "_t.brep.stl")
    export_stl(shape, p, tolerance=tol, angular_tolerance=0.2)
    m = trimesh.load(p); os.remove(p)
    if M is not None:
        m.apply_transform(M)
    buf = io.BytesIO(); m.export(buf, file_type="stl")
    return base64.b64encode(buf.getvalue()).decode(), m


data = {}
data["part"], m = mesh(import_brep(os.path.join(V, "base.brep")), 0.03, T)
base_g = float(m.volume) / 1000 * 1.17
print("base", len(m.faces), np.round(m.bounds, 1).tolist(), round(base_g, 1), "g")
data["device"], _ = mesh(v1.device_solid(), 0.06)
data["plate"], _ = mesh(v1.plate_solid(), 0.08)

P, Nn, Rr, _ = a8.lip()
pats, mass = {}, {}
for name in sp.PATTERNS:
    polys = a8.window_polys(name, P, Rr)
    pats[name] = [dict(o=[[round(x, 2), round(y, 2)] for x, y in g.exterior.coords],
                       h=[[[round(x, 2), round(y, 2)] for x, y in r.coords] for r in g.interiors]) for g in polys]
    mass[name] = round(base_g - 2 * sum(g.area for g in polys) * a8.ENGRAVE * 1.17 / 1000, 1)
    print(name, len(polys), "polys", mass[name], "g")

lw = lambda u, y, n=0.0: [float(u), float(y), float(n)]
data["_dims"] = dict(HW=a8.HW, LAT_H=0.06, ENGRAVE=a8.ENGRAVE, M=T.flatten().tolist(), BP=a8.BP, LUG_TOP=a8.LUG_TOP, FRONT=v1.Z_FRONT, LENS_Y=-v1.LENS_DROP,
                     lugs=[lw(u, y) for u, y in a8.lug_pos()], pockets=[lw(u, y) for u, y in a8.pocket_pos()],
                     travel=a8.TRAVEL, region=[0, float(a8.Y_BOT), 44, 92])
data["_labels"] = sp.LABELS
data["_mass"] = mass
open(os.path.join(OUT, "meshes.js"), "w").write("window.MESHES = " + json.dumps(data) + ";\nwindow.PATTERNS = " + json.dumps(pats, separators=(",", ":")) + ";\n")
print(os.path.getsize(os.path.join(OUT, "meshes.js")) // 1000, "kB")

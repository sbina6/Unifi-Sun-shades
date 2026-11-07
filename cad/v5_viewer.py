"""Meshes for the v5 viewer (v5_viewer/meshes.js): both variants in the WALL frame (x along the
wall, y up, z out of the wall, origin at the switch-box centre), plus the doorbell and plate."""
import base64, io, json, os, sys
import numpy as np, trimesh
from build123d import import_brep, export_stl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "v5_viewer"); os.makedirs(OUT, exist_ok=True)


def mesh(path, tol, T):
    p = os.path.join(OUT, "_t.brep.stl")
    export_stl(import_brep(path), p, tolerance=tol, angular_tolerance=0.2)
    m = trimesh.load(p); os.remove(p); m.apply_transform(T)
    buf = io.BytesIO(); m.export(buf, file_type="stl")
    return base64.b64encode(buf.getvalue()).decode(), m


data, info = {}, {}
for ver in ("v5a", "v5b"):
    V = os.path.join(ROOT, ver)
    G = json.load(open(os.path.join(V, "geom.json")))
    U, N, O = (np.array(G[k], float) for k in ("u_axis", "wall_normal", "box_centre"))
    R = np.vstack([U, [0, 1, 0], N]); T = np.eye(4); T[:3, :3] = R; T[:3, 3] = -R @ O
    data[f"{ver}_part"], m = mesh(os.path.join(V, "hood.brep"), 0.06, T)
    data[f"{ver}_device"], _ = mesh(os.path.join(V, "device.brep"), 0.08, T)
    data[f"{ver}_plate"], _ = mesh(os.path.join(V, "plate.brep"), 0.08, T)
    info[ver] = np.round(m.bounds, 1).tolist()
    print(ver, len(m.faces), info[ver])
data["_dims"] = dict(BOX=75.0, bounds=info)
open(os.path.join(OUT, "meshes.js"), "w").write("window.MESHES = " + json.dumps(data) + ";\n")

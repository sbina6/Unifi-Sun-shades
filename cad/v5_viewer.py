"""Meshes for the v5 viewer (v5/viewer/meshes.js) in the WALL frame: x along the wall, y up,
z out of the wall, origin at the switch-box centre. Part, doorbell and plate."""
import base64, io, json, os, sys
import numpy as np, trimesh
from build123d import import_brep, export_stl

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.join(HERE, "..", "v5")
OUT = os.path.join(V, "viewer"); os.makedirs(OUT, exist_ok=True)
G = json.load(open(os.path.join(V, "v5_geom.json")))
U, N, O = (np.array(G[k]) for k in ("u_axis", "wall_normal", "wall_origin"))
R = np.vstack([U, [0, 1, 0], N])
T = np.eye(4); T[:3, :3] = R; T[:3, 3] = -R @ O - np.array([G["C_U"], -68.5, 0])

data = {}
for name, f, tol in (("part", "hood.brep", 0.06), ("device", "device.brep", 0.08), ("plate", "plate.brep", 0.08)):
    p = os.path.join(OUT, "_t.brep.stl")
    export_stl(import_brep(os.path.join(V, f)), p, tolerance=tol, angular_tolerance=0.2)
    m = trimesh.load(p); os.remove(p); m.apply_transform(T)
    buf = io.BytesIO(); m.export(buf, file_type="stl"); data[name] = base64.b64encode(buf.getvalue()).decode()
    print(name, len(m.faces), np.round(m.bounds, 1).tolist())
lug = {k: (((np.array(v[0]) - O) @ U) - G["C_U"]) for k, v in G["lug_wall_points"].items()}
data["_dims"] = dict(BOX=G["box"], LUGS=lug)
open(os.path.join(OUT, "meshes.js"), "w").write("window.MESHES = " + json.dumps(data) + ";\n")

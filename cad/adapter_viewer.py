"""Meshes for the adapter viewer (adapter/viewer/meshes.js), all in the adapter frame:
x right, y up, z out of the wall, origin at the box centre, adapter front at z = T.
Flat mount: Doorbell Lite plate + body straight on the adapter. v4 mount: the v4 hood with the
doorbell, moved from its wall frame onto the adapter front."""
import base64, io, json, os, sys
import numpy as np, trimesh
from build123d import import_brep, import_step, export_stl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import wall_adapter as A
import sunshade as v1

OUT = os.path.join(ROOT, "adapter", "viewer")
os.makedirs(OUT, exist_ok=True)


def mesh(shape, tol):
    p = os.path.join(OUT, "_tmp.brep.stl")
    export_stl(shape, p, tolerance=tol, angular_tolerance=0.2)
    m = trimesh.load(p); os.remove(p)
    return m


def b64(m):
    buf = io.BytesIO(); m.export(buf, file_type="stl")
    return base64.b64encode(buf.getvalue()).decode()


meshes = {}
meshes["adapter"] = mesh(import_brep(os.path.join(ROOT, "adapter", "adapter.brep")), 0.03)

dev, plate = mesh(v1.device_solid(), 0.08), mesh(v1.plate_solid(), 0.08)
# flat: plate back (v1 z = T_FL) onto the adapter front, doorbell middle at the screw midpoint
Tf = np.eye(4); Tf[1, 3] = -v1.MID_Y + A.DY; Tf[2, 3] = A.T - v1.T_FL
meshes["flat_device"] = dev.copy().apply_transform(Tf)
meshes["flat_plate"] = plate.copy().apply_transform(Tf)

# v4: doorbell frame -> v3/v4 wall frame (origin at the top wall screw) -> adapter front
g = json.load(open(os.path.join(ROOT, "v3", "v3_geom.json")))
P = np.array(g["wall_point"]); N = np.array(g["wall_normal"]); U = np.array([N[2], 0, -N[0]])
q = np.array(g["wall_screw_seat_points"]["top"]); W0 = q - N * ((q - P) @ N)
R = np.vstack([U, [0, 1, 0], N])
T1 = np.eye(4); T1[:3, :3] = R; T1[:3, 3] = -R @ W0
T2 = np.eye(4); T2[1, 3] = A.DY + A.SCREW_DY; T2[2, 3] = A.T
Tv = T2 @ T1
meshes["v4_hood"] = mesh(import_step(os.path.join(ROOT, "v4", "sunshade_hood_v4.step")), 0.12).apply_transform(Tv)
meshes["v4_device"] = dev.copy().apply_transform(Tv)
meshes["v4_plate"] = plate.copy().apply_transform(Tv)

data = {k: b64(m) for k, m in meshes.items()}
data["_dims"] = dict(T=A.T, W=A.W, Y_BOT=A.Y_BOT, Y_TOP=A.Y_TOP, BOX=A.BOX, BOX_LUG=A.BOX_LUG, DY=A.DY, SCREW_DY=A.SCREW_DY)
open(os.path.join(OUT, "meshes.js"), "w").write("window.MESHES = " + json.dumps(data) + ";\n")
print({k: (len(m.faces), round(len(data[k]) / 1e6, 2)) for k, m in meshes.items()})

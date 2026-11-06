import sys, os, numpy as np, trimesh
from build123d import import_brep, export_stl
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
V = os.path.join(os.path.dirname(__file__), "..", "v1")
out = sys.argv[1]
meshes = []
for name, col in [("hood", (0.85, 0.55, 0.2, 1)), ("device", (0.2, 0.2, 0.25, 0.35))]:
    export_stl(import_brep(f"{V}/{name}.brep"), f"/tmp/_{name}.stl", tolerance=0.05)
    meshes.append((trimesh.load(f"/tmp/_{name}.stl"), col))
fig = plt.figure(figsize=(14, 7))
for k, (el, az) in enumerate([(20, -50), (15, 40), (75, -90)]):
    ax = fig.add_subplot(1, 3, k + 1, projection="3d")
    for m, col in meshes:
        tri = m.vertices[m.faces][:, :, [0, 2, 1]]       # plot (x, z, y): y up
        n = m.face_normals[:, [0, 2, 1]]
        light = np.clip(n @ np.array([0.3, -0.5, 0.8]), 0.15, 1)
        fc = np.array(col)[None].repeat(len(tri), 0); fc[:, :3] *= light[:, None]
        ax.add_collection3d(Poly3DCollection(tri, facecolors=fc, edgecolors="none"))
    ax.set_xlim(-40, 40); ax.set_ylim(-20, 60); ax.set_zlim(-140, 20)
    ax.set_box_aspect((80, 80, 160)); ax.view_init(el, az); ax.set_axis_off()
plt.tight_layout(); plt.savefig(out, dpi=90)

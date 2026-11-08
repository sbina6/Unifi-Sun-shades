"""Build every side-wall pattern of v5a and export it oriented for printing (45 deg, wall side down)
as v5a/print_kit/designs/shade_<pattern>_<edge>_TR300.stl, with mesh checks.
usage: python cad/export_v5_designs.py [scallop|straight]"""
import json, os, sys
import numpy as np, trimesh
from build123d import export_stl, Rot, Pos
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sunshade_v5a as a5
import shade_patterns as sp

edge = sys.argv[1] if len(sys.argv) > 1 else "scallop"
OUT = os.path.join(HERE, "..", "v5a", "print_kit", "designs"); os.makedirs(OUT, exist_ok=True)
rep = {}
for name in sp.PATTERNS:
    part, dropped, _ = a5.build(name, edge == "scallop", True)
    s = Rot(45, 0, 0) * part
    bb = s.bounding_box()
    s = Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * s
    f = os.path.join(OUT, f"shade_{name}_{edge}_TR300.stl")
    export_stl(s, f, tolerance=0.02, angular_tolerance=0.1)
    m = trimesh.load(f)
    nz = m.face_normals[:, 2]; ang = np.degrees(np.arcsin(np.clip(-nz, 0, 1))); bad = (nz < -0.01) & (ang > 45.5)
    rep[name] = dict(file=os.path.basename(f), mass_g=round(float(m.volume) / 1000 * 1.17, 1), watertight=bool(m.is_watertight),
                     bodies=len(m.split(only_watertight=False)), min_z=round(float(m.bounds[0][2]), 3),
                     bbox_mm=[round(float(x), 1) for x in m.bounds[1] - m.bounds[0]],
                     flat_down_area_mm2=round(float(m.area_faces[bad].sum())), largest_flat_facet_mm2=round(float(m.area_faces[bad].max()), 2) if bad.any() else 0)
    print(name, rep[name], flush=True)
json.dump(rep, open(os.path.join(OUT, f"designs_{edge}.json"), "w"), indent=1)

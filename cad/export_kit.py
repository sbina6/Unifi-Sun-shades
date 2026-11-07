"""Orient, export and check the STLs, then build the print kit zip. Run after sunshade.py + verify.py."""
import json, os, shutil, zipfile, datetime
import numpy as np, trimesh
from build123d import import_brep, export_stl, Rot, Pos

HERE = os.path.dirname(os.path.abspath(__file__))
VER = os.environ.get("CAD_VER", "v1")
V = os.path.join(HERE, "..", VER)
KIT = os.path.join(V, "print_kit")
os.makedirs(KIT, exist_ok=True)

TILT = 45.0   # device +y tilted 45 deg from print +z, wall side facing the build plate


def orient(shape, tilt):
    s = Rot(tilt, 0, 0) * shape
    bb = s.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * s


def check(path):
    m = trimesh.load(path)
    bodies = m.split(only_watertight=False)
    return dict(watertight=bool(m.is_watertight), bodies=len(bodies), winding_ok=bool(m.is_winding_consistent),
                volume_mm3=round(float(m.volume), 1), mass_g_TR300=round(float(m.volume) / 1000 * 1.17, 1),
                min_z=round(float(m.bounds[0][2]), 4),
                bbox_mm=[round(float(x), 1) for x in (m.bounds[1] - m.bounds[0])])


parts = {}
hood = import_brep(os.path.join(V, "hood.brep"))
_g = os.path.join(V, "geom.json")
if os.path.exists(_g) and json.load(open(_g)).get("orient_in_wall_frame"):
    # hood square to the WALL (v5b): tilt it in the wall frame, not the turned doorbell frame
    from build123d import Plane, Vector
    _G = json.load(open(_g))
    hood = Plane(origin=Vector(*_G["box_centre"]), x_dir=Vector(*_G["u_axis"]), z_dir=Vector(*_G["wall_normal"])).to_local_coords(hood)
hood = orient(hood, TILT)
export_stl(hood, os.path.join(KIT, f"sunshade_hood_{VER}_TR300.stl"), tolerance=0.02, angular_tolerance=0.1)
cp = import_brep(os.path.join(V, "coupon.brep"))
export_stl(cp, os.path.join(KIT, f"fit_test_coupon_{VER}_TR300.stl"), tolerance=0.01, angular_tolerance=0.1)
for f in sorted(os.listdir(KIT)):
    if f.endswith(".stl"):
        parts[f] = check(os.path.join(KIT, f))

# sealed internal voids: a single shell per body means no trapped void
for f, r in parts.items():
    m = trimesh.load(os.path.join(KIT, f))
    shells = m.split(only_watertight=False)
    r["sealed_internal_voids"] = int(sum(1 for s in shells if s.volume < 0))
# overhang check of the hood as oriented: down-facing area by angle from horizontal
m = trimesh.load(os.path.join(KIT, f"sunshade_hood_{VER}_TR300.stl"))
nz = m.face_normals[:, 2]
down = nz < -0.01
ang = np.degrees(np.arcsin(np.clip(-nz[down], 0, 1)))       # 90 = flat ceiling
area = m.area_faces[down]
parts[f"sunshade_hood_{VER}_TR300.stl"]["down_facing_area_mm2"] = {
    "steeper_than_45deg_from_horizontal_(self-supporting)": round(float(area[ang <= 45.5].sum()), 0),
    "flatter_than_45deg_(needs_support)": round(float(area[ang > 45.5].sum()), 0)}

from build123d import export_step
for nm, src in (("sunshade_hood", "hood.brep"), ("fit_test_coupon", "coupon.brep")):
    f = f"{nm}_{VER}.step"
    if not os.path.exists(os.path.join(V, f)):
        export_step(import_brep(os.path.join(V, src)), os.path.join(V, f))
    shutil.copy(os.path.join(V, f), os.path.join(KIT, f))
shutil.copy(os.path.join(V, "verify_report.json"), os.path.join(KIT, "verify_report.json"))

manifest = dict(
    kit="UniFi Doorbell Lite static sunshade", version=VER, date=str(datetime.date.today()),
    device="Ubiquiti UniFi Protect Doorbell Lite (UVC-Doorbell-Lite), 137 x 40 x 26.4 mm",
    parts=[
        dict(file=f"sunshade_hood_{VER}_TR300.stl", qty=1, material="Phrozen TR300",
             orientation=f"pre-oriented: long axis {TILT:.0f} deg from vertical, wall face toward the plate, roof up",
             supports="wall-side (back) face of the flange only + light supports under the roof underside; none on the flange front face (doorbell seat), none on the brim edge",
             **parts[f"sunshade_hood_{VER}_TR300.stl"]),
        dict(file=f"fit_test_coupon_{VER}_TR300.stl", qty=1, material="Phrozen TR300",
             orientation="axis-aligned, flat (do not tilt); measure 62.00 X / 62.00 Y / 56.60 Z",
             supports="raft/light supports under the frame", **parts[f"fit_test_coupon_{VER}_TR300.stl"]),
    ],
    hardware="none extra for the flat mount (doorbell's own 2x M3 wall screws pass through the flange); wedge mount: 2x M3 plate screws ~2.5 mm longer than the kit's",
)
json.dump(manifest, open(os.path.join(KIT, "manifest.json"), "w"), indent=1)
print(json.dumps(parts, indent=1))

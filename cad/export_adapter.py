"""Orient, export and check the wall-adapter STLs, render views, build adapter/print_kit + zip.
Run after wall_adapter.py and verify_adapter.py."""
import json, os, shutil, zipfile, datetime
import numpy as np, trimesh
from build123d import import_brep, export_stl, Rot, Pos

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.join(HERE, "..", "adapter")
KIT = os.path.join(V, "print_kit")
os.makedirs(KIT, exist_ok=True)
TILT = 45.0   # long axis 45 deg from vertical, wall (back) side toward the build plate


def orient(shape, tilt):
    s = Rot(tilt, 0, 0) * shape
    bb = s.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * s


def check(path):
    m = trimesh.load(path)
    shells = m.split(only_watertight=False)
    return dict(watertight=bool(m.is_watertight), bodies=len(shells), winding_ok=bool(m.is_winding_consistent),
                volume_mm3=round(float(m.volume), 1), mass_g_TR300=round(float(m.volume) / 1000 * 1.17, 1),
                min_z=round(float(m.bounds[0][2]), 4),
                bbox_mm=[round(float(x), 1) for x in (m.bounds[1] - m.bounds[0])],
                sealed_internal_voids=int(sum(1 for s in shells if s.volume < 0)))


AD = "wall_adapter_TR300.stl"
CP = "fit_test_coupon_adapter_TR300.stl"
export_stl(orient(import_brep(os.path.join(V, "adapter.brep")), TILT), os.path.join(KIT, AD), tolerance=0.02, angular_tolerance=0.1)
export_stl(import_brep(os.path.join(V, "coupon.brep")), os.path.join(KIT, CP), tolerance=0.01, angular_tolerance=0.1)
parts = {f: check(os.path.join(KIT, f)) for f in (AD, CP)}

m = trimesh.load(os.path.join(KIT, AD))
nz = m.face_normals[:, 2]
down = nz < -0.01
ang = np.degrees(np.arcsin(np.clip(-nz[down], 0, 1)))
area = m.area_faces[down]
parts[AD]["down_facing_area_mm2"] = {
    "steeper_than_45deg_from_horizontal_(self-supporting)": round(float(area[ang <= 45.5].sum()), 0),
    "flatter_than_45deg_(needs_support)": round(float(area[ang > 45.5].sum()), 0)}

for f in ("wall_adapter.step", "fit_test_coupon_adapter.step", "verify_report.json"):
    shutil.copy(os.path.join(V, f), os.path.join(KIT, f))

# renders come from the three.js viewer (cad/adapter_shots.js, Playwright): adapter/adapter_views.png
shots = [os.path.join(V, "viewer", f"s_{n}.png") for n in ("front_v4", "front_flat", "back_none", "side_v4")]
if all(os.path.exists(f) for f in shots):
    from PIL import Image
    ims = [Image.open(f).convert("RGB") for f in shots]
    w, h = ims[0].size
    grid = Image.new("RGB", (2 * w, 2 * h), "white")
    for i, im in enumerate(ims):
        grid.paste(im, ((i % 2) * w, (i // 2) * h))
    grid.resize((w, h)).save(os.path.join(V, "adapter_views.png"), optimize=True)
    for f in shots:
        os.remove(f)
if os.path.exists(os.path.join(V, "adapter_views.png")):
    shutil.copy(os.path.join(V, "adapter_views.png"), os.path.join(KIT, "adapter_views.png"))

manifest = dict(
    kit="UniFi Doorbell Lite wall adapter for a Qatar / UK (BS 4662) square switch box",
    version="adapter-1", date=str(datetime.date.today()),
    device="Ubiquiti UniFi Protect Doorbell Lite (UVC-Doorbell-Lite), 137 x 40 x 26.4 mm",
    parts=[
        dict(file=AD, qty=1, material="Phrozen TR300",
             orientation=f"pre-oriented: long axis {TILT:.0f} deg from vertical, wall (back) side toward the build plate",
             supports="back rim and rib edges only (they sit against the wall); none on the front face, countersinks, nut channels or cable window edge",
             **parts[AD]),
        dict(file=CP, qty=1, material="Phrozen TR300",
             orientation="axis-aligned, flat (do not tilt); measure 62.00 X / 62.00 Y / 56.60 Z; nut channels 5.6/5.7/5.8; M3 holes 3.3/3.4/3.5; M3.5 box-screw hole 3.9 + 7.4 countersink",
             supports="raft/light supports under the frame", **parts[CP]),
    ],
    hardware=[
        "2 x M3.5 countersunk box screws: the ones from the switch plate you removed (25 mm is standard)",
        "2 x M3 x 12 stainless flat-head (countersunk) Phillips, Voltaat 5-pc pack",
        "2 x M3 hex nut, Voltaat 5-pc pack",
    ],
)
json.dump(manifest, open(os.path.join(KIT, "manifest.json"), "w"), indent=1)

zp = os.path.join(V, "doorbell_lite_wall_adapter_print_kit.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(KIT)):
        z.write(os.path.join(KIT, f), f"print_kit/{f}")
print(json.dumps(parts, indent=1))
print("zip", zp, os.path.getsize(zp))

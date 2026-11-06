"""Verification for sunshade v1. Run after sunshade.py:
    /tmp/cadenv/bin/python cad/verify.py
Writes v1/verify_report.json and v1/fov_overlay.png.
Heavy booleans run in a 'spawn' pool; each worker loads BREPs (fork deadlocks OCC).
"""
import json, math, os, multiprocessing as mp
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.join(HERE, "..", "v1")
P = json.load(open(os.path.join(V, "params.json")))
T_FL, MID_Y, ZF = P["T_FL"], P["MID_Y"], P["Z_FRONT"]

# hook pivot: device's top-back catch on the plate's top tab (plate top at MID_Y + 62.5)
PIVOT = (0.0, T_FL)    # (y, z): body rocks on its top-back edge while the catch is on the plate tab


def _load(name):
    from build123d import import_brep
    return import_brep(os.path.join(V, f"{name}.brep"))


def pose_overlap(args):
    """Device pose: lift (mm, +y), tilt (deg, bottom swings out about PIVOT), approach (mm, +z)."""
    lift, tilt, appr = args
    from build123d import Pos, Rot, Location
    hood, dev = _load("hood"), _load("device")
    py, pz = PIVOT
    d = Pos(0, py, pz) * Rot(-tilt, 0, 0) * Pos(0, -py, -pz) * dev   # -tilt: bottom (+y below) goes +z
    d = Pos(0, lift, appr) * d
    v = (hood & d).volume if (hood & d) is not None else 0.0
    return (lift, tilt, appr, round(v, 3))


def solid_checks(_):
    from build123d import Pos, Cylinder, Box, Rot
    hood, dev, plate = _load("hood"), _load("device"), _load("plate")
    out = {}
    inter = hood & dev
    out["device_vs_hood_overlap_mm3"] = round(inter.volume if inter else 0.0, 4)
    inter = hood & plate
    out["plate_vs_hood_overlap_mm3"] = round(inter.volume if inter else 0.0, 4)
    shell = hood & (Pos(0, -60, T_FL + 0.05 + 100) * Box(200, 400, 200))   # hood without flange
    out["device_to_walls_roof_min_gap_mm"] = round(dev.distance_to(shell), 3)
    # screw paths (shank d3 through flange to wall; head d6 x 2.5 on the plate)
    paths = {}
    for label, dy in [("flat wall screw (74 c/c)", 37.0), ("wedge plate screw (92 c/c)", 46.0),
                      ("tolerance -4 (66 c/c)", 33.0), ("tolerance +4 (100 c/c)", 50.0)]:
        vol = 0.0
        for s in (+1, -1):
            y = MID_Y + s * dy
            shank = Pos(0, y, (T_FL + 1.6 - 30) / 2) * Cylinder(1.5, 30 + T_FL + 1.6)
            i = hood & shank
            vol += i.volume if i else 0.0
        paths[label] = round(vol, 4)
    # wedge-mount wall-screw HEADS (countersunk in the wedge, but check if proud by 2 mm, d6)
    vol = 0.0
    for s in (+1, -1):
        head = Pos(0, MID_Y + s * 39.0, -1.0) * Cylinder(3.0, 2.0)
        i = hood & (Pos(0, 0, 2.0) * head)   # head standing 2 mm proud of the wedge = inside flange
        vol += i.volume if i else 0.0
    paths["wedge wall-screw head, 2 mm proud, d6 (78 c/c)"] = round(vol, 4)
    # bottom lock screw + screwdriver from below (vertical, x=0, a few mm in front of plate)
    for zc in (T_FL + 3.0, T_FL + 6.0, T_FL + 10.0):
        drv = Pos(0, -137 - 60, zc) * Rot(90, 0, 0) * Cylinder(3.0, 120)
        i = hood & (Pos(0, 0, 0) * drv)
        paths[f"lock screw + driver d6 from below at z={zc:.1f}"] = round(i.volume if i else 0.0, 4)
    # PoE cable through the flange: flat (d18 hole, centre 88 below top) and wedge window
    cab = Pos(0, -88, -10) * Cylinder(4.0, 40)
    i = hood & cab
    paths["PoE cable d8 at flat-mount hole"] = round(i.volume if i else 0.0, 4)
    out["paths_overlap_mm3"] = paths
    return out


# ---------------- camera field-of-view intrusion ----------------
FISH = np.array([1.91883021e+01, 5.26733149e-02, -7.27681727e-04])   # r(px) = a t + b t^2 + c t^3, t in deg


def fov_check(stl_path, out_png):
    import trimesh
    from PIL import Image, ImageDraw
    m = trimesh.load(stl_path)
    L = np.array(P["LENS"])
    S = 4                                  # image downscale: 1920x2560 -> 480x640
    W, H = 1920 // S, 2560 // S
    # splat dense surface samples (robust near 90 deg off-axis, no polygon wrap-around)
    pts, _ = trimesh.sample.sample_surface(m, 3_000_000, seed=1)
    v = pts - L
    v = v[v[:, 2] > 0]
    th = np.degrees(np.arccos(np.clip(v[:, 2] / np.linalg.norm(v, axis=1), -1, 1)))
    r = FISH[0] * th + FISH[1] * th ** 2 + FISH[2] * th ** 3
    ph = np.arctan2(v[:, 1], v[:, 0])
    u = ((960 + r * np.cos(ph)) / S).astype(int)
    w = ((1280 - r * np.sin(ph)) / S).astype(int)
    ok = (u >= 0) & (u < W) & (w >= 0) & (w < H)
    arr = np.zeros((H, W), np.uint8)
    arr[w[ok], u[ok]] = 255
    mask = Image.fromarray(arr)
    a = np.array(mask) > 0
    frac = a.mean()
    # where in the image: corners vs edges
    yy, xx = np.mgrid[0:H, 0:W]
    edge_band = (xx < W * 0.1) | (xx > W * 0.9) | (yy < H * 0.1) | (yy > H * 0.9)
    corner = ((xx < W * 0.2) | (xx > W * 0.8)) & ((yy < H * 0.2) | (yy > H * 0.8))
    mid_cols = (xx > W * 0.2) & (xx < W * 0.8)
    res = dict(occluded_fraction=round(float(frac), 5),
               occluded_outside_corners=round(float((a & ~corner).mean()), 5),
               top_edge_centre_strip_occluded=round(float(a[: int(H * 0.05)][:, int(W * 0.2):int(W * 0.8)].mean()), 5),
               side_edge_centre_strip_occluded=round(float(a[int(H * 0.2):int(H * 0.8)][:, list(range(int(W * 0.05))) + list(range(int(W * 0.95), W))].mean()), 5))
    # overlay: synthetic grid view with the shade in orange
    img = Image.new("RGB", (W, H), (235, 238, 242))
    g = ImageDraw.Draw(img)
    for k in range(0, 91, 10):   # off-axis rings every 10 deg
        rr = (FISH[0] * k + FISH[1] * k * k + FISH[2] * k ** 3) / S
        g.ellipse([W / 2 - rr, H / 2 - rr, W / 2 + rr, H / 2 + rr], outline=(170, 175, 185))
    g.line([W / 2, 0, W / 2, H], fill=(170, 175, 185)); g.line([0, H / 2, W, H / 2], fill=(170, 175, 185))
    ov = Image.new("RGB", (W, H), (230, 120, 30))
    img = Image.composite(ov, img, mask)
    g = ImageDraw.Draw(img)
    g.text((8, 8), f"camera view (1920x2560, fisheye fit)\nshade occupies {frac*100:.2f}% of pixels", fill=(20, 20, 20))
    img.save(out_png)
    return res


if __name__ == "__main__":
    ctx = mp.get_context("spawn")
    report = {}
    poses = []
    for tilt0 in (10.0, 15.0, 20.0):
        for appr in (30, 20, 10, 5, 0):          # approach under the roof, lifted 4 mm, tilted
            poses.append((4.0, tilt0, appr))
        for lift in (3, 2, 1, 0):                # drop onto the hook
            poses.append((float(lift), tilt0, 0))
        for t in np.linspace(tilt0, 0, 6):       # swing the bottom in
            poses.append((0.0, float(t), 0))
    with ctx.Pool(min(8, os.cpu_count() or 2)) as pool:
        res = pool.map(pose_overlap, poses)
        report["static"] = pool.apply(solid_checks, (None,))
    by_tilt = {}
    for i, tilt0 in enumerate((10.0, 15.0, 20.0)):
        chunk = res[i * 15:(i + 1) * 15]
        by_tilt[f"hook-on at {tilt0:.0f} deg tilt, 4 mm lift"] = dict(
            max_overlap_mm3=max(c[3] for c in chunk),
            clashes=[c for c in chunk if c[3] > 0.01])
    report["install_sweep"] = by_tilt

    # STL for FOV (hood as installed)
    from build123d import import_brep, export_stl
    export_stl(import_brep(os.path.join(V, "hood.brep")), "/tmp/_hood_fov.stl", tolerance=0.05)
    report["camera_fov"] = fov_check("/tmp/_hood_fov.stl", os.path.join(V, "fov_overlay.png"))
    json.dump(report, open(os.path.join(V, "verify_report.json"), "w"), indent=1)
    print(json.dumps(report, indent=1))

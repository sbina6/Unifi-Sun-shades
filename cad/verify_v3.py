"""Checks for v3 (integrated 20 deg wedge). Run after sunshade_v3.py:
    /tmp/cadenv/bin/python cad/verify_v3.py
Reuses verify.py's install sweep and camera check (same doorbell frame); adds the v3 screw,
nut, cable and wall-flush checks. Heavy booleans run in a 'spawn' pool from BREPs."""
import json, math, os, sys, multiprocessing as mp
import numpy as np
os.environ.setdefault("CAD_VER", "v3")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import verify as V0

V = os.path.join(HERE, "..", os.environ.get("CAD_VER", "v3"))
G = json.load(open(os.path.join(V, "v3_geom.json")))


def v3_checks(_):
    from build123d import import_brep, Pos, Plane, Cylinder, Box, Vector, Align, Rot
    import sunshade as v1
    part = import_brep(os.path.join(V, "hood.brep"))
    dev = import_brep(os.path.join(V, "device.brep"))
    plate = import_brep(os.path.join(V, "plate.brep"))
    nW, pW = Vector(*G["wall_normal"]), Vector(*G["wall_point"])
    seat = G["seat_z"]
    out = {}
    vol = lambda a: (a.volume if a is not None else 0.0)
    out["device_vs_part_overlap_mm3"] = round(vol(part & dev), 4)
    out["plate_vs_part_overlap_mm3"] = round(vol(part & plate), 4)
    shell = part & (Pos(0, -60, seat + 0.05 + 100) * Box(200, 400, 200))
    out["device_to_shell_min_gap_mm"] = round(dev.distance_to(shell), 3)
    # wall flush: nothing behind the wall plane; back edge touches it
    behind = Plane(origin=pW, z_dir=-nW) * Pos(0, 0, 100) * Box(600, 600, 200)
    out["part_behind_wall_mm3"] = round(vol(part & behind), 4)
    near = Plane(origin=pW, z_dir=nW) * Pos(0, 0, 0.25) * Box(600, 600, 0.5)
    out["part_area_in_contact_band_mm3"] = round(vol(part & near), 1)
    paths = {}
    for nm, q in G["wall_screw_seat_points"].items():
        q = Vector(*q); t = (q - pW).dot(nW); o = q - nW * t        # point on the wall
        ax = Plane(origin=o, z_dir=nW)
        shank = ax * Pos(0, 0, -25) * Cylinder(1.5, 25 + 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        head = ax * Pos(0, 0, 3.05) * Cylinder(2.9, 2.4, align=(Align.CENTER, Align.CENTER, Align.MIN))
        driver = ax * Pos(0, 0, 5.5) * Cylinder(3.0, 150, align=(Align.CENTER, Align.CENTER, Align.MIN))
        paths[f"wall screw ({nm}) shank d3 through floor into anchor"] = round(vol(part & shank), 4)
        paths[f"wall screw ({nm}) head d5.8 in counterbore"] = round(vol(part & head), 4)
        paths[f"wall screw ({nm}) screwdriver d6 x 150 along axis"] = round(vol(part & driver), 4)
        paths[f"wall screw ({nm}) floor under head (mm)"] = 3.0
    for sgn, nm in ((+1, "top"), (-1, "bottom")):
        for dy in (-1.0, 0.0, 2.5, 5.0):
            y = v1.MID_Y + sgn * (G["plate_screw_dy"] + dy)   # dy > 0 = outward
            tip = seat + 1.6 + 1.4 - 12.0                  # M3x12 countersunk sitting on the plate hole
            shank = Pos(0, y, tip) * Cylinder(1.5, seat + 1.6 - tip, align=(Align.CENTER, Align.CENTER, Align.MIN))
            nut = Pos(0, y, seat - 2.2 - 2.4) * Box(5.5, 6.35, 2.4, align=(Align.CENTER, Align.CENTER, Align.MIN))
            paths[f"plate screw ({nm}, {dy:+.0f}) M3x12 shank"] = round(vol(part & shank), 4)
            paths[f"plate screw ({nm}, {dy:+.0f}) nut 5.5 AF x 2.4"] = round(vol(part & nut), 4)
            wall_z_at0 = pW.Z - (0 - pW.X) * nW.X / nW.Z
            paths[f"plate screw ({nm}) tip clear of wall (mm)"] = round(tip - wall_z_at0, 2)
    # lock screw + driver from below
    for zc in (seat + 3.0, seat + 6.0, seat + 10.0):
        drv = Pos(0, -137 - 60, zc) * Rot(90, 0, 0) * Cylinder(3.0, 120)
        paths[f"lock screw + driver d6 from below at z={zc:.1f}"] = round(vol(part & drv), 4)
    # PoE cable from the wall hole (under the doorbell's lower half) out through the body
    for y in (-80.0, -88.0, -95.0):
        q = Vector(0, y, seat); t = (q - pW).dot(nW); o = q - nW * t
        cab = Plane(origin=o, z_dir=nW) * Pos(0, 0, -5) * Cylinder(4.0, 40, align=(Align.CENTER, Align.CENTER, Align.MIN))
        paths[f"PoE cable d8 from the wall at y={y:.0f}"] = round(vol(part & cab), 4)
    out["paths"] = paths
    return out


if __name__ == "__main__":
    ctx = mp.get_context("spawn")
    poses = []
    for tilt0 in (10.0, 15.0, 20.0):
        for appr in (30, 20, 10, 5, 0):
            poses.append((4.0, tilt0, appr))
        for lift in (3, 2, 1, 0):
            poses.append((float(lift), tilt0, 0))
        for t in np.linspace(tilt0, 0, 6):
            poses.append((0.0, float(t), 0))
    with ctx.Pool(min(4, os.cpu_count() or 2)) as pool:
        res = pool.map(V0.pose_overlap, poses)
        rep = {"static": pool.apply(v3_checks, (None,))}
    rep["install_sweep"] = {f"hook-on at {t:.0f} deg tilt, 4 mm lift":
                            dict(max_overlap_mm3=max(c[3] for c in res[i * 15:(i + 1) * 15]),
                                 clashes=[c for c in res[i * 15:(i + 1) * 15] if c[3] > 0.01])
                            for i, t in enumerate((10.0, 15.0, 20.0))}
    from build123d import import_brep, export_stl
    export_stl(import_brep(os.path.join(V, "hood.brep")), "/tmp/_hood_fov_v3.stl", tolerance=0.05)
    rep["camera_fov"] = V0.fov_check("/tmp/_hood_fov_v3.stl", os.path.join(V, "fov_overlay.png"))
    json.dump(rep, open(os.path.join(V, "verify_report.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))

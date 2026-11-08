"""Checks for v5a / v5b (one piece: shade + wedge + switch-box cover). Run after sunshade_v5a/b.py:
    /tmp/cadenv/bin/python cad/verify_v5.py v5a      (or v5b)
Reuses verify.py's hook-on sweep and camera check; adds the box-screw, driver, plate-screw, cable,
lock-screw, wall-flush and box-coverage checks. Heavy booleans run in a 'spawn' pool."""
import json, os, sys, multiprocessing as mp
import numpy as np
VER = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].startswith("v5") else os.environ.get("CAD_VER", "v5a")
os.environ["CAD_VER"] = VER
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import verify as V0

V = os.path.join(HERE, "..", VER)
G3 = json.load(open(os.path.join(V, "v3_geom.json")))
G5 = json.load(open(os.path.join(V, "geom.json")))


def static_checks(_):
    from build123d import import_brep, Pos, Plane, Cylinder, Cone, Box, Vector, Align, Rot
    import sunshade as v1
    part = import_brep(os.path.join(V, "hood.brep"))
    dev = import_brep(os.path.join(V, "device.brep"))
    plate = import_brep(os.path.join(V, "plate.brep"))
    nW, pW = Vector(*G3["wall_normal"]), Vector(*G3["wall_point"])
    seat = G3["seat_z"]
    vol = lambda a: (a.volume if a is not None else 0.0)
    out = {"device_vs_part_overlap_mm3": round(vol(part & dev), 4),
           "plate_vs_part_overlap_mm3": round(vol(part & plate), 4)}
    shell = part & (Pos(0, -60, seat + 0.05 + 100) * Box(200, 400, 200))
    out["device_to_shell_min_gap_mm"] = round(dev.distance_to(shell), 3)
    behind = Plane(origin=pW, z_dir=-nW) * Pos(0, 0, 100) * Box(600, 600, 200)
    out["part_behind_wall_mm3"] = round(vol(part & behind), 4)
    paths = {}
    if G5["box_lugs_used"]:
        # box screws: M3.5 shank, d7.0 countersunk head flush on its boss, d6 driver along the axis
        # (driven before the doorbell goes on; the installed doorbell must not touch the head)
        bt = G5["boss_t"]
        for i, p in enumerate(G5["lug_points"]):
            nm = ("left", "right")[i]
            ax = Plane(origin=Vector(*p), z_dir=nW)
            shank = ax * Pos(0, 0, -5) * Cylinder(1.75, bt + 5, align=(Align.CENTER, Align.CENTER, Align.MIN))
            head = ax * Pos(0, 0, bt - 1.75) * Cone(1.75, 3.5, 1.75, align=(Align.CENTER, Align.CENTER, Align.MIN))
            driver = ax * Pos(0, 0, bt + 0.3) * Cylinder(3.0, 150, align=(Align.CENTER, Align.CENTER, Align.MIN))
            paths[f"box screw ({nm}) M3.5 shank into the lug"] = round(vol(part & shank), 4)
            paths[f"box screw ({nm}) d7 countersunk head, flush"] = round(vol(part & head), 4)
            paths[f"box screw ({nm}) screwdriver d6 x 150 along the axis"] = round(vol(part & driver), 4)
            paths[f"box screw ({nm}) head vs installed doorbell + plate"] = round(vol(head & (plate + dev)), 4)
    else:
        # wall screws (kit M3 + anchors) in counterbores square to the wall, as v3
        fl = G5["wall_screw_floor"]
        for i, p in enumerate(G5["wall_screws"]):
            nm = ("top", "bottom")[i]
            ax = Plane(origin=Vector(*p), z_dir=nW)
            # the kit screw is drawn at its biggest: d4.0 shank, d8.0 head (counterbore d8.5, hole d4.2)
            shank = ax * Pos(0, 0, -25) * Cylinder(2.0, 25 + fl, align=(Align.CENTER, Align.CENTER, Align.MIN))
            head = ax * Pos(0, 0, fl + 0.05) * Cylinder(4.0, 2.4, align=(Align.CENTER, Align.CENTER, Align.MIN))
            driver = ax * Pos(0, 0, fl + 2.5) * Cylinder(3.0, 150, align=(Align.CENTER, Align.CENTER, Align.MIN))
            paths[f"wall screw ({nm}) d3 shank through the floor"] = round(vol(part & shank), 4)
            paths[f"wall screw ({nm}) head d5.8 in counterbore"] = round(vol(part & head), 4)
            paths[f"wall screw ({nm}) screwdriver d6 x 150 along the axis"] = round(vol(part & driver), 4)
    # plate screws on sliding nuts (as v3)
    for sgn, nm in ((+1, "top"), (-1, "bottom")):
        for dy in (-1.0, 0.0, 2.5, 5.0):
            y = v1.MID_Y + sgn * (G3["plate_screw_dy"] + dy)
            tip = seat + 1.6 + 1.4 - 12.0
            shank = Pos(0, y, tip) * Cylinder(1.5, seat + 1.6 - tip, align=(Align.CENTER, Align.CENTER, Align.MIN))
            nut = Pos(0, y, seat - 2.2 - 2.4) * Box(5.5, 6.35, 2.4, align=(Align.CENTER, Align.CENTER, Align.MIN))
            paths[f"plate screw ({nm}, {dy:+.0f}) M3x12 shank"] = round(vol(part & shank), 4)
            paths[f"plate screw ({nm}, {dy:+.0f}) nut 5.5 AF x 2.4"] = round(vol(part & nut), 4)
            # nut dropped into its pocket from the wall side (pocket runs along the doorbell z axis)
            ins = Pos(0, y, -45) * Box(5.5, 6.35, 45 + seat - 2.2 - 0.05, align=(Align.CENTER, Align.CENTER, Align.MIN))
            paths[f"M3 nut pocket ({nm}, {dy:+.0f}) nut inserted from the wall side"] = round(vol(part & ins), 4)
            wz = pW.Z - (0 - pW.X) * nW.X / nW.Z
            paths[f"plate screw ({nm}, {dy:+.0f}) tip clearance to the wall (mm)"] = round(tip - wz, 2)
    for zc in (seat + 3.0, seat + 6.0, seat + 10.0):
        drv = Pos(0, -137 - 60, zc) * Rot(90, 0, 0) * Cylinder(3.0, 120)
        paths[f"lock screw + driver d6 from below at z={zc:.1f}"] = round(vol(part & drv), 4)
    for y in (-80.0, -88.0, -95.0):
        q = Vector(0.5, y, seat); t = (q - pW).dot(nW); o = q - nW * t
        cab = Plane(origin=o, z_dir=nW) * Pos(0, 0, -5) * Cylinder(4.0, 40, align=(Align.CENTER, Align.CENTER, Align.MIN))
        paths[f"PoE cable d8 from the box at y={y:.0f}"] = round(vol(part & cab), 4)
    out["paths"] = paths
    return out


def coverage(_):
    """Box opening as seen from the front along the wall normal: covered by the part, the plate or
    the doorbell. Triangles of all three projected onto the wall plane and unioned. Screw holes
    that a screw head fills are not counted."""
    import trimesh
    from build123d import import_brep, export_stl
    from shapely.geometry import Polygon, Point, box as sbox
    from shapely.ops import unary_union
    U = np.array(G5["u_axis"]); O = np.array(G5["box_centre"])
    polys = []
    for f in ("hood", "device", "plate"):
        p = os.path.join(V, f"_{f}_cov.brep.stl")
        export_stl(import_brep(os.path.join(V, f"{f}.brep")), p, tolerance=0.1, angular_tolerance=0.3)
        m = trimesh.load(p)
        uv = np.stack([(m.vertices - O) @ U, m.vertices[:, 1] - O[1]], 1)
        for tri in uv[m.faces]:
            pg = Polygon(tri)
            if pg.area > 1e-4:
                polys.append(pg.buffer(0.02))
    cov = unary_union(polys)
    h = G5["box"] / 2
    gap = sbox(-h, -h, h, h).difference(cov)
    heads = [Point((np.array(p) - O) @ U, p[1] - O[1]).buffer(3.6) for p in G5.get("lug_points", [])]
    rest = gap.difference(unary_union(heads)) if heads else gap
    return dict(box_opening_mm2=round(4 * h * h, 1), uncovered_mm2=round(gap.area, 2),
                uncovered_except_screw_holes_mm2=round(rest.area, 3))


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
        st = pool.apply_async(static_checks, (None,))
        cv = pool.apply_async(coverage, (None,))
        res = pool.map(V0.pose_overlap, poses)
        rep = {"static": st.get(), "box_coverage_from_front": cv.get()}
    rep["install_sweep"] = {f"hook-on at {t:.0f} deg tilt, 4 mm lift":
                            dict(max_overlap_mm3=max(c[3] for c in res[i * 15:(i + 1) * 15]),
                                 clashes=[c for c in res[i * 15:(i + 1) * 15] if c[3] > 0.01])
                            for i, t in enumerate((10.0, 15.0, 20.0))}
    from build123d import import_brep, export_stl
    export_stl(import_brep(os.path.join(V, "hood.brep")), f"/tmp/_hood_fov_{VER}.stl", tolerance=0.05)
    rep["camera_fov"] = V0.fov_check(f"/tmp/_hood_fov_{VER}.stl", os.path.join(V, "fov_overlay.png"))
    json.dump(rep, open(os.path.join(V, "verify_report.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))

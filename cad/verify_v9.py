"""Checks for v9 (simple, thin flap, nut holders: small shade + backplate; the doorbell's own plate bolts onto it, no angle).
    /tmp/cadenv/bin/python cad/verify_v9.py
Reuses verify.py's hook-on sweep and camera check (same doorbell frame). Writes v6/verify_report.json.
Heavy booleans run in a 'spawn' pool from BREPs."""
import json, os, sys, multiprocessing as mp
import numpy as np
os.environ["CAD_VER"] = "v9"
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import verify as V0

V = os.path.join(HERE, "..", "v9")
G = json.load(open(os.path.join(V, "geom.json")))


def plane():
    from build123d import Plane, Vector
    return Plane(origin=Vector(*G["box_centre"]), x_dir=Vector(*G["u_axis"]), z_dir=Vector(*G["wall_normal"]))


def static_checks(_):
    from build123d import import_brep, Pos, Cylinder, Cone, Box, Align, Rot, Vector
    import sunshade as v1
    part = import_brep(os.path.join(V, "hood.brep"))
    dev = import_brep(os.path.join(V, "device.brep"))
    plate = import_brep(os.path.join(V, "plate.brep"))
    BP = G["plate_back_n"]          # the doorbell plate's back (top of the nut holders)
    LT = G["lug_top"]               # top of the bosses round the box screws
    SK = G["skin"]
    P = plane()
    vol = lambda a: (a.volume if a is not None else 0.0)
    out = {}
    out["device_vs_part_overlap_mm3"] = round(vol(part & dev), 4)
    out["plate_vs_part_overlap_mm3"] = round(vol(part & plate), 4)
    out["device_to_part_min_gap_mm"] = round(dev.distance_to(part), 3)
    out["plate_to_part_min_gap_mm"] = round(plate.distance_to(part), 3)
    out["part_behind_wall_mm3"] = round(vol(part & (P * Pos(0, 0, -100) * Box(600, 600, 200))), 4)
    paths = {}
    # the switch box's own 2 screws, left and right: M3.5 shank, d7.4 countersunk head flush, d6 driver
    h = 1.75
    for nm, (u, y, n) in zip(("left", "right"), [(0,)*3, (0,)*3]):
        pass
    for nm, pt in zip(("left", "right"), G["lug_points"]):
        ax = type(P)(origin=Vector(*pt), x_dir=P.x_dir, z_dir=P.z_dir)
        shank = ax * Pos(0, 0, -5) * Cylinder(1.75, LT + 5, align=(Align.CENTER, Align.CENTER, Align.MIN))
        head = ax * Pos(0, 0, LT - h) * Cone(1.75, 3.6, h, align=(Align.CENTER, Align.CENTER, Align.MIN))   # d7.2 head in the d7.4 countersink
        driver = ax * Pos(0, 0, LT + 0.3) * Cylinder(3.0, 150, align=(Align.CENTER, Align.CENTER, Align.MIN))
        paths[f"box screw ({nm}) M3.5 shank into the lug"] = round(vol(part & shank), 4)
        paths[f"box screw ({nm}) d7.4 countersunk head, flush"] = round(vol(part & head), 4)
        paths[f"box screw ({nm}) screwdriver d6 x 150 along the axis"] = round(vol(part & driver), 4)
        paths[f"box screw ({nm}) head vs the doorbell plate"] = round(vol(head & plate), 4)
    # the doorbell plate's two M3 x 8 bolts into the nut pockets, across the whole slide. The head is
    # flush on the plate (n = BP + 1.6); the tip stops at n = 0.4, above the wall.
    for nm, pt in zip(("top", "bottom"), G["pocket_points"]):
        for dy in (-G["nut_travel"] / 2, 0.0, G["nut_travel"] / 2):
            ax = type(P)(origin=Vector(*pt), x_dir=P.x_dir, z_dir=P.z_dir) * Pos(0, dy, 0)
            shank = ax * Pos(0, 0, 0.4) * Cylinder(1.5, BP + 1.6 - 0.4, align=(Align.CENTER, Align.CENTER, Align.MIN))
            nut = ax * Pos(0, 0, BP - SK - 2.4) * Box(5.5, 6.35, 2.4, align=(Align.CENTER, Align.CENTER, Align.MIN))
            ins = ax * Pos(0, 0, -45) * Box(5.5, 6.35, 45.0 + BP - SK - 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN))
            drv = ax * Pos(0, 0, BP + 1.6) * Cylinder(3.0, 150, align=(Align.CENTER, Align.CENTER, Align.MIN))
            paths[f"M3 bolt ({nm}, {dy:+.0f}) shank through the slot"] = round(vol(part & shank), 4)
            paths[f"M3 nut ({nm}, {dy:+.0f}) seated against the skin"] = round(vol(part & nut), 4)
            paths[f"M3 nut ({nm}, {dy:+.0f}) dropped in from the wall side"] = round(vol(part & ins), 4)
            paths[f"M3 bolt ({nm}, {dy:+.0f}) screwdriver d6 from the front"] = round(vol(part & drv), 4)
    seat = 2.2
    for zc in (seat + 3.0, seat + 6.0, seat + 10.0):
        drv = Pos(0, -137 - 60, zc) * Rot(90, 0, 0) * Cylinder(3.0, 120)
        paths[f"lock screw + driver d6 from below at z={zc:.1f}"] = round(vol(part & drv), 4)
    cab = P * Pos(G["bracket_u_local"], -19.5, -10) * Cylinder(4.0, 70, align=(Align.CENTER, Align.CENTER, Align.MIN))
    paths["PoE cable d8 from the box through the window"] = round(vol(part & cab), 4)
    out["paths"] = paths
    # the doorbell plate's d18 cable hole must fall inside the cable window
    u0, u1, y0, y1 = G["cable_window"]
    cu, cy = G["bracket_u_local"], -19.5
    out["cable_hole_d18_inside_window"] = bool(cu + u0 <= cu - 9 and cu + u1 >= cu + 9 and y0 <= cy - 9 and y1 >= cy + 9)
    return out


def coverage(_):
    """Box opening seen from the front along the wall normal: covered by part, bracket, plate or doorbell."""
    import trimesh
    from build123d import import_brep, export_stl
    from shapely.geometry import Polygon, Point, box as sbox
    from shapely.ops import unary_union
    U = np.array(G["u_axis"]); O = np.array(G["box_centre"])
    polys = []
    for f in ("hood", "device", "plate"):
        p = os.path.join(V, f"_{f}_cov.brep.stl")
        export_stl(import_brep(os.path.join(V, f"{f}.brep")), p, tolerance=0.1, angular_tolerance=0.3)
        m = trimesh.load(p); os.remove(p)
        uv = np.stack([(m.vertices - O) @ U, m.vertices[:, 1] - O[1]], 1)
        for tri in uv[m.faces]:
            pg = Polygon(tri)
            if pg.area > 1e-4:
                polys.append(pg.buffer(0.02))
    cov = unary_union(polys)
    h = G["box"] / 2
    gap = sbox(-h, -h, h, h).difference(cov)
    heads = [Point((np.array(p) - O) @ U, p[1] - O[1]).buffer(3.8) for p in G["lug_points"]]
    rest = gap.difference(unary_union(heads))
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
    export_stl(import_brep(os.path.join(V, "hood.brep")), "/tmp/_hood_fov_v9.stl", tolerance=0.05)
    rep["camera_fov"] = V0.fov_check("/tmp/_hood_fov_v9.stl", os.path.join(V, "fov_overlay.png"))
    json.dump(rep, open(os.path.join(V, "verify_report.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))

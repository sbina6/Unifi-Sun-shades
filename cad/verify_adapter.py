"""Checks for the wall adapter (run after wall_adapter.py). Writes adapter/verify_report.json.

- screw, nut and nut-insertion paths clear of plastic
- box covered with margin; box-screw heads flush
- flat mount: metal plate fully on solid skin, d18 cable hole inside the cable window
- v3 / v4 hoods (and mirrored): their wall contact band fully on solid skin, their wall-screw
  holes on the adapter's screws, their plate-nut channels closed by solid skin, cable path open
- screw-length budget for M3 x 12 flat-head in every mount
"""
import json, os, sys
import numpy as np, trimesh
from build123d import *
from shapely.geometry import LineString, Polygon, Point, box as sbox
from shapely.ops import linemerge, unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import wall_adapter as A

OUT = os.path.join(ROOT, "adapter")
a = import_brep(os.path.join(OUT, "adapter.brep"))
rep = {}


def vol(s):
    try:
        return round(float(s.volume), 4)
    except Exception:
        return 0.0


def section(mesh, z):
    """Even-odd polygon of a mesh cut at height z (CLAUDE.md recipe)."""
    segs = trimesh.intersections.mesh_plane(mesh, [0, 0, 1], [0, 0, z])
    ls = linemerge(unary_union([LineString(np.round(s[:, :2], 3)) for s in segs]))
    rings = [Polygon(l.coords) for l in getattr(ls, "geoms", [ls]) if l.is_ring]
    out = Polygon()
    for r in rings:
        out = out.symmetric_difference(r.buffer(0))
    return out


# ---- paths clear of plastic ----
paths = {}
for s, nm in ((1, "top"), (-1, "bottom")):
    y = A.DY + s * A.SCREW_DY
    paths[f"M3 shank {nm} (d3.0 through)"] = vol(a & Pos(0, y, -1) * Cylinder(1.5, A.T + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    nut = Pos(0, y, A.T - A.SKIN - 2.4) * extrude(RegularPolygon(5.5 / np.sqrt(3), 6, rotation=0), 2.4)
    paths[f"M3 nut seated {nm} (5.5 AF x 2.4)"] = vol(a & nut)
    sweep = Pos(-A.NUT_BOSS[0] / 2 - 2, y, A.T - A.SKIN - 2.4) * Box(A.NUT_BOSS[0] + 4, 5.5, 2.4, align=(Align.CENTER, Align.CENTER, Align.MIN))
    paths[f"M3 nut insertion slide {nm} (from the back cavity)"] = vol(a & sweep)
    tool = Pos(-A.NUT_BOSS[0] / 2 - 8, y, 0) * Box(8, 5.4, A.T - A.SKIN - 0.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    paths[f"fingers/tweezers reach channel mouth {nm}"] = vol(a & tool)
for s in (-1, 1):
    p = Pos(s * A.BOX_LUG, 0, 0)
    shank = p * Pos(0, 0, -1) * Cylinder(1.75, A.T + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    head = p * Pos(0, 0, A.T - 1.75) * Cone(1.75, 3.5, 1.75, align=(Align.CENTER, Align.CENTER, Align.MIN))
    paths[f"M3.5 box screw {'right' if s > 0 else 'left'} (shank + d7.0 csk head flush)"] = vol(a & (shank + head))
rep["paths_overlap_mm3"] = paths

# ---- mesh of the adapter, as modelled (unoriented) ----
tmp = os.path.join(OUT, "_adapter_model.brep.stl")
export_stl(a, tmp, tolerance=0.01, angular_tolerance=0.1)
am = trimesh.load(tmp)
front = section(am, A.T - 0.2)               # solid front skin, holes removed
outline = section(am, A.T - 0.2).buffer(0)
outer = Polygon(outline.exterior) if hasattr(outline, "exterior") else unary_union([Polygon(g.exterior) for g in outline.geoms])
rep["front_skin_area_mm2"] = round(front.area, 1)

# box coverage
box_open = sbox(-A.BOX / 2, -A.BOX / 2, A.BOX / 2, A.BOX / 2)
rep["box_opening_cover_margin_mm"] = dict(
    sides=round(A.W / 2 - A.BOX / 2, 2), bottom=round(-A.BOX / 2 - A.Y_BOT, 2), top=round(A.Y_TOP - A.BOX / 2, 2),
    uncovered_mm2=round(box_open.difference(outer).area, 3))

# flat mount
plate = sbox(-15.5, A.DY - 62.5, 15.5, A.DY + 62.5)
dev = sbox(-20, A.DY - 68.5, 20, A.DY + 68.5)
win = A.cable_sk()
d18 = Point(0, A.DY - 19.5).buffer(9.0)
screw_holes = unary_union([Point(0, A.DY + s * A.SCREW_DY).buffer(1.8) for s in (-1, 1)])
# flush M3.5 countersunk heads fill their countersinks, so they count as support
box_heads = unary_union([Point(s * A.BOX_LUG, 0).buffer(A.BOX_CSK / 2) for s in (-1, 1)])
x0, x1, y0, y1, r = A.CABLE
win_poly = sbox(x0, A.DY + y0, x1, A.DY + y1).buffer(-r).buffer(r)
rep["flat_mount"] = dict(
    plate_area_off_solid_skin_mm2=round(plate.difference(front).difference(win_poly).difference(screw_holes).area, 2),
    doorbell_body_inside_outline=bool(outer.contains(dev)),
    d18_cable_hole_inside_window=bool(win_poly.buffer(0.01).contains(d18)),
    d18_cable_hole_inside_box=bool(box_open.contains(d18)))

# v3 / v4 placed on the adapter front (their wall frame: origin at the top wall screw)
g = json.load(open(os.path.join(ROOT, "v3", "v3_geom.json")))
P = np.array(g["wall_point"]); N = np.array(g["wall_normal"]); U = np.array([N[2], 0, -N[0]])
q = np.array(g["wall_screw_seat_points"]["top"]); W0 = q - N * ((q - P) @ N)
Rm = np.vstack([U, [0, 1, 0], N])
hoods = {}
for ver, f in (("v3", "v3/sunshade_v3.step"), ("v4", "v4/sunshade_hood_v4.step")):
    stl = os.path.join(OUT, f"_{ver}.brep.stl")
    export_stl(import_step(os.path.join(ROOT, f)), stl, tolerance=0.05)
    for mir in (1, -1):
        m = trimesh.load(stl)
        Tm = np.eye(4); Tm[:3, :3] = Rm; Tm[:3, 3] = -Rm @ W0
        m.apply_transform(Tm)
        S = np.eye(4); S[0, 0] = mir; S[1, 3] = A.DY + A.SCREW_DY; S[2, 3] = A.T
        m.apply_transform(S)
        if mir < 0:
            m.invert()
        contact = section(m, A.T + 0.3)
        holes = [g for g in (contact.interiors if hasattr(contact, "interiors") else [])]
        # its plate-nut channels (open toward the wall) must be closed by solid skin
        chan = unary_union([Polygon(h) for h in holes if 50 < Polygon(h).area < 120])
        # its cable path: the big hollow behind its seat
        hollow = max((Polygon(h) for h in holes), key=lambda p: p.area) if holes else Polygon()
        k = f"{ver}{'' if mir > 0 else ' mirrored'}"
        hoods[k] = dict(
            min_z=round(float(m.bounds[0][2]), 3),
            contact_area_mm2=round(contact.area, 1),
            contact_off_solid_skin_mm2=round(contact.difference(front).difference(screw_holes).difference(box_heads).area, 2),
            contact_band_min_margin_to_outline_mm=round(float(outer.exterior.distance(Polygon(contact.exterior))) if hasattr(contact, "exterior") else -1, 2),
            nut_channels_found=len(getattr(chan, "geoms", [chan])) if not chan.is_empty else 0,
            nut_channel_area_not_closed_by_skin_mm2=round(chan.difference(front).area, 3),
            adapter_cable_window_inside_its_hollow=bool(hollow.buffer(0.01).contains(win_poly)))
rep["hoods"] = hoods

# screw budget, M3 x 12 flat-head: head top sits ~1.3 above the face it bears on (90 deg cone on a d3.4 edge)
nut_back = A.T - A.SKIN - 2.4
budget = {}
for nm, stack in (("flat plate (1.6 sheet)", 1.6), ("v3 / v4 counterbore floor (3.0)", 3.0)):
    tip = A.T + stack + 1.3 - 12.0
    budget[nm] = dict(tip_z_above_wall=round(tip, 2), past_nut_mm=round(nut_back - tip, 2),
                      full_nut_engaged=bool(tip <= nut_back), tip_clear_of_wall=bool(tip >= 0.5))
budget["rule for anything else"] = f"stack under the head + 1.3 + {A.T - nut_back:.1f} <= L <= stack + 1.3 + {A.T - 0.5:.1f}"
rep["m3x12_budget"] = budget

# pass/fail
ok = all(v == 0 for v in paths.values())
ok &= rep["box_opening_cover_margin_mm"]["uncovered_mm2"] == 0
ok &= rep["flat_mount"]["plate_area_off_solid_skin_mm2"] < 0.5 and rep["flat_mount"]["d18_cable_hole_inside_window"]
for h in hoods.values():
    ok &= h["contact_off_solid_skin_mm2"] < 0.5 and h["nut_channel_area_not_closed_by_skin_mm2"] < 0.05
    ok &= h["nut_channels_found"] == 2 and h["adapter_cable_window_inside_its_hollow"] and h["min_z"] >= A.T - 0.05
for b in list(budget.values())[:2]:
    ok &= b["full_nut_engaged"] and b["tip_clear_of_wall"]
rep["ALL_PASS"] = bool(ok)
json.dump(rep, open(os.path.join(OUT, "verify_report.json"), "w"), indent=1)
print(json.dumps(rep, indent=1))

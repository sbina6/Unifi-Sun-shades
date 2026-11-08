"""Sunshade v5a: ONE printed part centred on a Qatar / UK BS 4662 switch box. Sunshade + 20 deg
wedge + 86 x 86 mm backplate that hides the box, with Islamic geometric relief on the side walls.

Mounting (the two joints that matter):
- PART TO WALL: the doorbell kit's own 2 screws and plugs, in 2 new holes 120 mm apart (60 mm above and
  below the box centre), square to the wall. Counterbore d8.5 x 3.0 floor, d4.2 clearance hole: takes
  any kit screw up to M4 / #8 with a head up to 8 mm. The counterbores open on the seat face under the
  doorbell; the part is its own drilling template.
- PART TO DOORBELL PLATE: 2 x M3 x 12 flat-head screws into 2 M3 NUT POCKETS (5.7 AF x 2.6 deep, open to
  the wall side, 2.2 mm skin in front). Each pocket is a 12.6 mm long slide, so the nut finds the screw
  wherever the plate's holes really are (plate holes 90-102 mm apart).

Shade: v4's barrel vault and lip (just outside the camera picture), walls 1.8, no car-shade ribs.
Optional scalloped lip (pitch 12, bite 3: only ever SHORTER than the camera limit).
Side walls: raised 0.6 mm relief, patterns in cad/shade_patterns.py (khatam, hexstar, rosette,
octstar, smooth).

Frame: the doorbell frame (see sunshade_v3.py).
usage: python cad/sunshade_v5a.py [--out DIR] [--pattern khatam] [--edge scallop|straight] [--base]
"""
import argparse, json, math, os, shutil, sys
import numpy as np
from build123d import *

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sunshade as v1
import sunshade_v3 as v3
import sunshade_v4 as v4
import shade_patterns as sp

# ---- lighter walls (v4/v3 functions read these module globals) ----
v4.WALL = 1.8
v3.PERIM = 1.8
v3.SKIN = 2.0
v4.LAT_H = 0.6              # side relief height
LAT_RIB, LAT_FRAME = 1.4, 2.6
NUT_BLOCK = (9.2, 16.0)     # x, y: 1.75 mm round the 5.7 x 12.6 nut pocket

# ---- box, backplate and wall screws (wall frame: u along the wall, y up, n out of the wall) ----
BOX = 75.0
C_U = -3.0                  # box centre along u from the doorbell's screw line: centre of the shade's
                            # front view (outer shell u -36.2..30.2), so the shade looks centred
COVER_MARGIN = 5.5          # 86 mm square, like a switch plate
COVER_T = 2.0
COVER_R = 8.0
WALL_SCREW_DY = 60.0        # new wall holes, 120 mm apart, above and below the box
CB_D, CB_FLOOR, BOSS_R = 8.5, 3.0, 7.0
WALL_HOLE = 4.2
CABLE_X = (-12.0, 12.0)
SC_PITCH, SC_DEPTH = 12.0, 3.0

G3 = json.load(open(os.path.join(HERE, "..", "v3", "v3_geom.json")))
N = Vector(*G3["wall_normal"])
U = Vector(N.Z, 0, -N.X)
_q = Vector(*G3["wall_screw_seat_points"]["top"])
_P = Vector(*G3["wall_point"])
W0 = _q - N * ((_q - _P).dot(N))            # wall point under the top wall-screw position (u = 0)
WALL_PL = Plane(origin=(W0.X, 0, W0.Z), x_dir=U, z_dir=N)   # (u, y, n) -> doorbell frame


def pocket_centres():
    """y of the two nut pockets (centre of each slide)."""
    return [v1.MID_Y + s * (v3.PLATE_SCREW_DY + (v3.TRAVEL_OUT - v3.TRAVEL_IN) / 2) for s in (+1, -1)]


def wall_screw_axes():
    out = []
    for sgn in (+1, -1):
        q = Vector(0, v1.MID_Y + sgn * WALL_SCREW_DY, v3.SEAT)
        t = (q - v3.P_WALL).dot(N)
        out.append(Plane(origin=q - N * t, z_dir=N))
    return out


# ---------------- lip (optionally scalloped) ----------------
def lip(scallop):
    P, Nn, R, lim = v4.lip_reach()
    if scallop:
        d = np.r_[0.0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
        u = ((d - d[-1] / 2.0) / SC_PITCH + 0.5) % 1.0              # an arch is centred on the crown
        bite = SC_DEPTH * np.sqrt(np.clip(1.0 - (2.0 * u - 1.0) ** 2, 0.0, 1.0))
        bite = np.minimum(bite, np.maximum(R - 1.0, 0.0))           # none in the tucked S-curve
        R = R - bite
    return P, Nn, R, lim


def lip_cutter(P, Nn, R, step):
    idx = list(range(0, len(P), step))
    if idx[-1] != len(P) - 1:
        idx.append(len(P) - 1)
    rows = [[Vector(P[i][0] + Nn[i][0] * w, P[i][1] + Nn[i][1] * w, v1.Z_FRONT + R[i]) for i in idx]
            for w in (-2.5, 0.0, 2.5)]
    f = Face.make_surface_from_array_of_points(rows, tol=0.05)
    return extrude(f, 120, dir=(0, 0, 1))


# ---------------- side relief ----------------
def side_region(s, P, R):
    """Raised-relief area on the outer face of side s (+1 / -1), as a shapely polygon in (z, y)."""
    from shapely.geometry import Polygon as SPoly, box as sbox
    g = v4.geom(0.0)
    side = P[:, 0] < -v4.XO + 2.0
    ys, rs = P[side, 1], R[side]
    o = np.argsort(ys); ys, rs = ys[o], rs[o]
    y_top = g["yf"] - 1.0
    zw_hi = max(v3.wall_z(s * v4.XO), v3.wall_z(s * (v4.XO + v4.LAT_H)))
    lipl = [(v1.Z_FRONT + float(np.interp(y, ys, rs)) - 0.4, y) for y in np.linspace(v4.Y_BOT, y_top, 480)]
    return SPoly([(zw_hi - 3.0, v4.Y_BOT)] + lipl + [(zw_hi - 3.0, y_top)]).buffer(0) & sbox(-60, v4.Y_BOT, 80, y_top)


def relief_polys(pattern, s, P, R):
    """Relief polygons (z, y) for side s, or [] for 'smooth'."""
    from shapely.ops import unary_union
    region = side_region(s, P, R)
    fn = sp.PATTERNS[pattern]
    wins = fn(region.buffer(-LAT_FRAME, join_style=2), LAT_RIB)
    if not wins:
        return []
    lat = region.difference(unary_union(wins))
    return [g.simplify(0.02) for g in getattr(lat, "geoms", [lat]) if g.area > 0.5]


def _face(poly):
    f = make_face(Polyline(*[tuple(c) for c in poly.exterior.coords], close=True))
    for ring in poly.interiors:
        f -= make_face(Polyline(*[tuple(c) for c in ring.coords], close=True))
    return f


def relief_solid(pattern, P, R):
    parts = []
    for s in (+1, -1):
        pl = Plane(origin=(s * v4.XO, 0, 0), x_dir=(0, 0, 1), z_dir=(-1, 0, 0))
        for poly in relief_polys(pattern, s, P, R):
            parts.append(extrude(pl * _face(poly), v4.LAT_H if s < 0 else -v4.LAT_H))
    if not parts:
        return None
    out = parts[0]
    for p in parts[1:]:
        out += p
    return out


# ---------------- wedge, backplate, mounting ----------------
def hollow_prism():
    """The wedge's hollow (open toward the wall). Its sides reach the shade's inner face, so the
    shade's 1.8 mm side walls are also the wedge's side walls."""
    z0 = -40.0
    w = 2 * (v4.XO - v4.WALL)
    return Pos(0, -v1.DEV_H / 2, z0) * extrude(Rectangle(w, v1.DEV_H - 2 * v3.PERIM), v3.SEAT - v3.SKIN - z0)


def wedge_body():
    z0 = -40.0
    foot = Pos(0, -v1.DEV_H / 2) * Rectangle(2 * v3.X_IN + 0.02, v1.DEV_H)
    body = Pos(0, 0, z0) * extrude(foot, v3.SEAT - z0)
    body = body - hollow_prism()
    for yc in pocket_centres():
        body += Pos(0, yc, (v3.SEAT + z0) / 2) * Box(*NUT_BLOCK, v3.SEAT - z0)
    for b in wall_screw_bosses():
        body += b
    return body & Pos(0, -v1.DEV_H / 2, v3.SEAT - 100) * Box(200, v1.DEV_H, 200)   # nothing proud of the seat


def cover():
    half = BOX / 2 + COVER_MARGIN
    plate = WALL_PL * Pos(C_U, v1.MID_Y, 0) * extrude(RectangleRounded(2 * half, 2 * half, COVER_R), COVER_T)
    return plate - hollow_prism()


def wall_screw_bosses():
    return [ax * Pos(0, 0, -2) * Cylinder(BOSS_R, 60, align=(Align.CENTER, Align.CENTER, Align.MIN)) for ax in wall_screw_axes()]


def wall_screw_cuts():
    cuts = []
    for ax in wall_screw_axes():
        cuts.append(ax * Pos(0, 0, CB_FLOOR) * Cylinder(CB_D / 2, 80, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        cuts.append(ax * Pos(0, 0, -5) * Cylinder(WALL_HOLE / 2, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return cuts


def body_cuts():
    """M3 nut pockets (open toward the wall) with their screw slots, and the cable window."""
    cuts = []
    span = v3.TRAVEL_OUT + v3.TRAVEL_IN
    for yc in pocket_centres():
        cuts.append(Pos(0, yc, v3.SEAT - 10) * extrude(SlotCenterToCenter(span, 3.4, rotation=90), 20))          # M3 shank slot
        cuts.append(Pos(0, yc, -40) * extrude(Rectangle(v3.NUT_AF, span + 6.6), (v3.SEAT - 2.2) - (-40)))        # nut pocket
    cy0, cy1, _ = v1.CABLE_WIN
    x0, x1 = CABLE_X
    cuts.append(Pos((x0 + x1) / 2, (cy0 + cy1) / 2, -45) * extrude(RectangleRounded(x1 - x0, cy1 - cy0, 3), 60))
    return cuts


def seat_windows():
    """Windows in the seat skin under the doorbell body, clear of the nut blocks, cable window and bosses."""
    from shapely.geometry import box as sbox, Point as SPoint
    from shapely.ops import unary_union
    P = v3.PERIM
    xi = v1.DEV_W / 2 - 1.5
    foot = sbox(-xi, -v1.DEV_H + P, xi, -P)
    keep = [sbox(-NUT_BLOCK[0] / 2, yc - NUT_BLOCK[1] / 2, NUT_BLOCK[0] / 2, yc + NUT_BLOCK[1] / 2) for yc in pocket_centres()]
    cy0, cy1, _ = v1.CABLE_WIN
    keep.append(sbox(CABLE_X[0], cy0, CABLE_X[1], cy1))
    for sgn in (+1, -1):
        keep.append(SPoint(0, v1.MID_Y + sgn * WALL_SCREW_DY).buffer(BOSS_R / v3.c_ + 1.0))
    region = foot.difference(unary_union(keep))
    wins = v1.window_pattern(region, a=3.6, b=6.0, rib=1.6, margin=1.0)
    return [Pos(0, 0, v3.SEAT - v3.SKIN - 1) * extrude(v1.poly_face(w), v3.SKIN + 2) for w in wins], len(wins)


def build(pattern="khatam", scallop=True, lattice=True):
    P, Nn, R, _ = lip(scallop)
    sh = v4.shell() - lip_cutter(P, Nn, R, 1 if scallop else 3)
    assert sh.bounding_box().max.Z < v1.Z_FRONT + 20, "lip cut failed"
    if lattice:
        rel = relief_solid(pattern, P, R)
        if rel is not None:
            sh = sh + rel
    part = (sh + wedge_body() + cover()) & v3.front_of_wall()
    for c in body_cuts() + wall_screw_cuts():
        part -= c
    wins, nwin = seat_windows()
    for w in wins:
        part -= w
    sols = sorted(part.solids(), key=lambda s: s.volume, reverse=True)
    return sols[0], [round(s.volume, 2) for s in sols[1:]], nwin


def write_geom(out, pattern, scallop):
    O = WALL_PL.from_local_coords((C_U, v1.MID_Y, 0))
    json.dump(dict(variant="v5a", pattern=pattern, edge="scallop" if scallop else "straight",
                   box_centre=list(O), u_axis=list(U), wall_normal=list(N), box=BOX, box_lugs_used=False,
                   wall_screws=[list(ax.origin) for ax in wall_screw_axes()], wall_screw_floor=CB_FLOOR,
                   wall_counterbore_d=CB_D, wall_hole_d=WALL_HOLE,
                   wall_holes_from_box_centre_mm=[[round((ax.origin - O).dot(U), 1), round(ax.origin.Y - O.Y, 1)] for ax in wall_screw_axes()],
                   nut_pockets_y=pocket_centres(), nut_pocket_travel=[-v3.TRAVEL_IN, v3.TRAVEL_OUT]),
              open(os.path.join(out, "geom.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "..", "v5a"))
    ap.add_argument("--pattern", default="khatam", choices=list(sp.PATTERNS))
    ap.add_argument("--edge", default="scallop", choices=["scallop", "straight"])
    ap.add_argument("--base", action="store_true", help="no relief: writes base_<edge>.brep for the viewer")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    scallop = a.edge == "scallop"
    part, dropped, nwin = build(a.pattern, scallop, lattice=not a.base)
    print("valid", part.is_valid, "vol", round(part.volume, 1), "mass g", round(part.volume / 1000 * 1.17, 1),
          "seat windows", nwin, "dropped", dropped)
    bb = part.bounding_box()
    print("bbox", [round(v, 1) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    if a.base:
        export_brep(part, os.path.join(a.out, f"base_{a.edge}.brep"))
    else:
        export_brep(part, os.path.join(a.out, "hood.brep"))
        export_step(part, os.path.join(a.out, "sunshade_hood_v5a.step"))
        export_brep(v1.device_solid(), os.path.join(a.out, "device.brep"))
        export_brep(v1.plate_solid(), os.path.join(a.out, "plate.brep"))
        shutil.copy(os.path.join(HERE, "..", "v3", "v3_geom.json"), os.path.join(a.out, "v3_geom.json"))
        shutil.copy(os.path.join(HERE, "..", "v4", "params.json"), os.path.join(a.out, "params.json"))
        write_geom(a.out, a.pattern, scallop)

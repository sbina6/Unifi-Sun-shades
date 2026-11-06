"""Sunshade v3: one printed part that replaces the 20 deg wedge and shades the doorbell.

Site: Doha, wall faces 150 deg. The doorbell is turned 20 deg to the LEFT (as seen standing in
front of the wall), so the camera looks along ~170 deg.

Frame: the DOORBELL frame used by v1/v2 (x right as you face the doorbell, y up, z out of the
doorbell's back). The doorbell's back sits on the seat face z = T_FL (2.2) exactly as in v1/v2,
so device.brep, plate.brep and the lens position are reused unchanged. The wall is a plane
tilted 20 deg about y: thin side at -x, thick side at +x.

Parts of the one body:
- wedge body behind the seat: 2.4 mm seat skin, 2.2 mm perimeter, bosses; S-diamond windows
- wall screws (doorbell kit M3 + anchors, existing holes 74 mm c/c) square to the WALL, heads in
  counterbores that open on the seat face
- plate screws: M3 countersunk 12 mm into M3 nuts that slide in printed channels (plate holes
  ~92 mm c/c, +-4 mm)
- shell: 2.2 mm, outer top corners R10, back edge flush to the wall, front lip cut to smooth
  curves that stay outside the camera picture (cad/v3_profiles.py)

usage: python cad/sunshade_v3.py [outdir]
"""
import json, math, os, sys
import numpy as np
from build123d import *

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sunshade as v1
from v3_profiles import side_reach, roof_reach, Y_SWITCH

WEDGE_DEG = 20.0
T_THIN = 3.0                     # body thickness at the thin (-x) inner edge, along z
SEAT = v1.T_FL                   # seat plane z (doorbell back)
SKIN = 2.4                       # seat skin
PERIM = 2.2
R_OUT, R_IN = 10.0, 10.0 - v1.WALL
X_IN = v1.DEV_W / 2 + v1.GAP_SIDE            # 22.0 inner face of the side walls
X_OUT = X_IN + v1.WALL                       # 24.2
Z_F = v1.Z_FRONT
WALL_SCREW_DY = 37.0             # 74 mm c/c (doorbell template)
PLATE_SCREW_DY = 46.0            # ~92 mm c/c, channel +-4
NUT_AF, NUT_H = 5.7, 2.6
TRAVEL_IN, TRAVEL_OUT = 1.0, 5.0     # nut/screw travel from the nominal 46 mm (inward / outward)
CB_D, CB_FLOOR = 7.5, 3.0        # wall-screw counterbore and floor under the head

s_, c_ = math.sin(math.radians(WEDGE_DEG)), math.cos(math.radians(WEDGE_DEG))
N_WALL = Vector(s_, 0, c_)       # wall normal in the doorbell frame (thick side at +x)
P_WALL = Vector(-X_IN, 0, SEAT - T_THIN)


def wall_z(x):
    """z of the wall plane at x."""
    return P_WALL.Z - (x - P_WALL.X) * s_ / c_


def front_of_wall(big=600):
    pl = Plane(origin=P_WALL, x_dir=(c_, 0, -s_), z_dir=N_WALL)
    return pl * Pos(0, 0, big / 2) * Box(big, big, big)


def u_profile(width, y_bot, y_top, r):
    """Rectangle with true-arc rounded corners; built tall so the bottom corners fall below y_bot
    and are trimmed off by the caller."""
    h = y_top - (y_bot - 60)
    return Pos(0, y_top - h / 2) * RectangleRounded(width, h, r)


def shell():
    z0, z1 = -40.0, Z_F + 40.0
    outer = Pos(0, 0, z0) * extrude(u_profile(2 * X_OUT, -v1.DEV_H, v1.Y_TOP, R_OUT), z1 - z0)
    inner = Pos(0, 0, z0) * extrude(u_profile(2 * X_IN, -v1.DEV_H - 20, v1.Y_TOP_IN, R_IN), z1 - z0)
    above_bottom = Pos(0, -v1.DEV_H + 150, 0) * Box(200, 300, 400)
    return (outer - inner) & above_bottom


def _spline_face(curve_pts, closing_pts, plane_map):
    """Face bounded by a smooth spline (curve_pts) and straight segments through closing_pts."""
    P = [Vector(*plane_map(*p)) for p in curve_pts]
    Q = [Vector(*plane_map(*p)) for p in closing_pts]
    edges = [Spline(*P)]
    chain = [P[-1]] + Q + [P[0]]
    for i in range(len(chain) - 1):
        edges.append(Line(chain[i], chain[i + 1]))
    return make_face(Wire(edges))


def trim_keep():
    """Region the shell may occupy: under the side curve AND (under the roof curve OR below Y_SWITCH)."""
    ys = np.linspace(-v1.DEV_H - 1, Y_SWITCH, 40)
    curve = [(Z_F + side_reach(y), y) for y in ys]
    close = [(Z_F + 120, Y_SWITCH), (Z_F + 120, 60.0), (-60.0, 60.0), (-60.0, -v1.DEV_H - 30),
             (Z_F + side_reach(-v1.DEV_H), -v1.DEV_H - 30)]
    f = _spline_face(curve, close, lambda z, y: (-100, y, z))
    A = extrude(f, 200, dir=(1, 0, 0))
    xs = np.linspace(-X_OUT - 1, X_OUT + 1, 41)
    curve = [(Z_F + roof_reach(x), x) for x in xs]
    close = [(-60.0, X_OUT + 30), (-60.0, -X_OUT - 30)]
    f = _spline_face(curve, close, lambda z, x: (x, -300, z))
    B = extrude(f, 400, dir=(0, 1, 0))
    H = Pos(0, Y_SWITCH - 150, 0) * Box(400, 300, 400)
    return A & (B + H)


def wedge_body():
    """Body between the wall and the seat face."""
    z0 = -40.0
    foot = Pos(0, -v1.DEV_H / 2) * Rectangle(2 * X_IN + 0.02, v1.DEV_H)
    body = Pos(0, 0, z0) * extrude(foot, SEAT - z0)
    hollow = Pos(0, -v1.DEV_H / 2, z0) * extrude(Rectangle(2 * X_IN - 2 * PERIM, v1.DEV_H - 2 * PERIM), SEAT - SKIN - z0)
    body = body - hollow
    # bosses: wall-screw counterbores (along the wall normal) and plate-screw nut blocks
    for sgn in (+1, -1):
        y = v1.MID_Y + sgn * WALL_SCREW_DY
        ax = Plane(origin=(0, y, SEAT), z_dir=-N_WALL)
        body += ax * Pos(0, 0, -5) * Cylinder(6.0, 60, align=(Align.CENTER, Align.CENTER, Align.MIN))
        yp = v1.MID_Y + sgn * (PLATE_SCREW_DY + 2.0)
        body += Pos(0, yp, (SEAT + z0) / 2) * Box(11.0, 20.0, SEAT - z0)
    # stiffening ribs between the bosses (centre spine)
    body += Pos(0, -v1.DEV_H / 2, (SEAT + z0) / 2) * Box(2.2, v1.DEV_H, SEAT - z0)
    # nothing may stand proud of the seat face
    return body & Pos(0, -v1.DEV_H / 2, SEAT - 100) * Box(200, v1.DEV_H, 200)


def body_cuts():
    """All holes in the body (applied after the wall cut)."""
    cuts = []
    for sgn in (+1, -1):
        y = v1.MID_Y + sgn * WALL_SCREW_DY
        # counterbore from the seat face down to CB_FLOOR above the wall, screw hole through
        q = Vector(0, y, SEAT)
        t = ((q - P_WALL).dot(N_WALL))                 # distance from the wall along the normal
        ax = Plane(origin=q - N_WALL * t, z_dir=N_WALL)  # origin on the wall plane
        cuts.append(ax * Pos(0, 0, CB_FLOOR) * Cylinder(CB_D / 2, 80, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        cuts.append(ax * Pos(0, 0, -5) * Cylinder(3.4 / 2, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        # plate screw: shank slot through the skin, nut channel open toward the wall
        # travel -1 / +5 mm along y (outward): plate holes measured ~92 c/c, possibly up to ~97
        yc = v1.MID_Y + sgn * (PLATE_SCREW_DY + (TRAVEL_OUT - TRAVEL_IN) / 2)
        span = TRAVEL_OUT + TRAVEL_IN
        slot = Pos(0, yc, SEAT - 10) * extrude(SlotCenterToCenter(span, 3.4, rotation=90), 20)
        cuts.append(slot)
        cuts.append(Pos(0, yc, -40) * extrude(Rectangle(NUT_AF, span + 6.6), (SEAT - 2.2) - (-40)))
    # cable window (flat-mount d18 hole and the wedge window both fall inside)
    cy0, cy1, cw = v1.CABLE_WIN
    cuts.append(Pos(0, (cy0 + cy1) / 2, -45) * extrude(RectangleRounded(cw, cy1 - cy0, 3), 60))
    return cuts


def seat_windows():
    """S-diamond windows through the seat skin, clear of bosses, channels and the rim."""
    from shapely.geometry import box as sbox, Point as SPoint
    from shapely.ops import unary_union
    foot = sbox(-X_IN + PERIM, -v1.DEV_H + PERIM, X_IN - PERIM, -PERIM)
    keep = [sbox(-1.1 - 1.0, -v1.DEV_H, 1.1 + 1.0, 0)]                     # spine
    for sgn in (+1, -1):
        keep.append(SPoint(0, v1.MID_Y + sgn * WALL_SCREW_DY).buffer(6.0 / c_ + 1.5))
        yp = v1.MID_Y + sgn * (PLATE_SCREW_DY + 2.0)
        keep.append(sbox(-5.5, yp - 10, 5.5, yp + 10))
    cy0, cy1, cw = v1.CABLE_WIN
    keep.append(sbox(-cw / 2, cy0, cw / 2, cy1))
    region = foot.difference(unary_union(keep))
    wins = v1.window_pattern(region, a=3.6, b=6.0, rib=1.8, margin=1.8)
    return [Pos(0, 0, SEAT - SKIN - 1) * extrude(v1.poly_face(w), SKIN + 2) for w in wins], len(wins)


def build():
    keep_wall = front_of_wall()
    import v3_lip
    sh = shell() - v3_lip.cutter(Z_F)
    assert sh.bounding_box().max.Z < Z_F + 20, "lip cut failed"
    body = wedge_body()
    part = (sh + body) & keep_wall
    for c in body_cuts():
        part -= c
    wins, nwin = seat_windows()
    for w in wins:
        part -= w
    sols = sorted(part.solids(), key=lambda s: s.volume, reverse=True)
    part = sols[0]
    return part, [s.volume for s in sols[1:]], nwin


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "v3")
    os.makedirs(out, exist_ok=True)
    part, dropped, nwin = build()
    print("valid", part.is_valid, "vol", round(part.volume, 1), "mass g", round(part.volume / 1000 * 1.17, 1),
          "windows", nwin, "dropped", [round(d, 2) for d in dropped])
    bb = part.bounding_box()
    print("bbox", [round(v, 1) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    export_brep(part, os.path.join(out, "hood.brep"))
    export_step(part, os.path.join(out, "sunshade_v3.step"))
    import shutil
    for f in ("device.brep", "plate.brep", "params.json"):   # coupon: cad/coupon_v3.py
        shutil.copy(os.path.join(HERE, "..", "v1", f), os.path.join(out, f))
    # wall plane + screw axes for the checks and viewer
    q = {}
    for sgn, nm in ((+1, "top"), (-1, "bottom")):
        p = Vector(0, v1.MID_Y + sgn * WALL_SCREW_DY, SEAT)
        q[nm] = [p.X, p.Y, p.Z]
    json.dump(dict(wedge_deg=WEDGE_DEG, wall_point=list(P_WALL), wall_normal=list(N_WALL),
                   wall_screw_seat_points=q, plate_screw_dy=PLATE_SCREW_DY, seat_z=SEAT),
              open(os.path.join(out, "v3_geom.json"), "w"), indent=1)

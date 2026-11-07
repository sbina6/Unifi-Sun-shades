"""Sunshade v5a (centred): v4 (car-shade style, integrated 20 deg wedge) and a switch-box cover in
ONE lighter part, centred on a Qatar / UK BS 4662 square switch box.

- Centred: the shade's front view is centred on the box (C_U), on a symmetric 86 x 86 mm, 2.0 mm
  backplate that hides the box.
- The shade sits over both box lugs (60.3 c/c), so it is fixed like v4: the doorbell kit's 2 x M3
  screws and anchors, square to the wall, heads in counterbores that open on the seat face under the
  metal plate. New holes 120 mm apart (WALL_SCREW_DY = 60), above and below the box; the part is
  the drilling template.
- Lighter than v4: shell 1.8 (2.2) and it is also the wedge's side wall, seat skin 2.0 (2.4) with
  S-diamond windows under the doorbell, no centre spine, nut blocks 9.2 x 16, lattice relief 0.6.
- Unchanged: outer surfaces, the lip (just outside the camera picture), vault ribs, side lattice,
  plate screws on sliding nuts. Shades like v4.

Frame: the doorbell frame (see sunshade_v3.py).   usage: python cad/sunshade_v5a.py [outdir]
"""
import json, math, os, shutil, sys
import numpy as np
from build123d import *

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sunshade as v1
import sunshade_v3 as v3
import sunshade_v4 as v4

# ---- lighter walls (v4/v3 functions read these module globals) ----
v4.WALL = 1.8
v3.PERIM = 1.8
v3.SKIN = 2.0
v4.LAT_H = 0.6              # side lattice relief (was 0.9)
NUT_BLOCK = (9.2, 16.0)     # x, y: 1.75 mm round the 5.7 x 12.6 nut channel (was 11 x 20)

# ---- box, backplate and wall screws (wall frame: u along the wall, y up, n out of the wall) ----
BOX = 75.0
BOX_LUG = 60.3 / 2
C_U = -3.0                  # box centre along u from the doorbell's screw line: centre of the shade's
                            # front view (outer shell u -36.2..30.2), so the shade looks centred
COVER_MARGIN = 5.5          # 86 mm square, like a switch plate
COVER_T = 2.0
COVER_R = 8.0
WALL_SCREW_DY = 60.0        # new wall holes, 120 mm apart, above and below the box
CB_D, CB_FLOOR, BOSS_R = 7.5, 3.0, 6.0
CABLE_X = (-12.0, 12.0)

G3 = json.load(open(os.path.join(HERE, "..", "v3", "v3_geom.json")))
N = Vector(*G3["wall_normal"])
U = Vector(N.Z, 0, -N.X)
_q = Vector(*G3["wall_screw_seat_points"]["top"])
_P = Vector(*G3["wall_point"])
W0 = _q - N * ((_q - _P).dot(N))            # wall point under the top wall-screw position (u = 0)
WALL_PL = Plane(origin=(W0.X, 0, W0.Z), x_dir=U, z_dir=N)   # (u, y, n) -> doorbell frame


def wall_screw_axes():
    """Plane per wall screw: origin on the wall, z along the wall normal (as v3)."""
    out = []
    for sgn in (+1, -1):
        q = Vector(0, v1.MID_Y + sgn * WALL_SCREW_DY, v3.SEAT)
        t = (q - v3.P_WALL).dot(N)
        out.append(Plane(origin=q - N * t, z_dir=N))
    return out


def hollow_prism():
    """The wedge's hollow (open toward the wall). Its sides reach the shade's inner face, so the
    shade's 1.8 mm side walls are also the wedge's side walls (no double wall)."""
    z0 = -40.0
    w = 2 * (v4.XO - v4.WALL)
    return Pos(0, -v1.DEV_H / 2, z0) * extrude(Rectangle(w, v1.DEV_H - 2 * v3.PERIM), v3.SEAT - v3.SKIN - z0)


def wedge_body():
    """v3 wedge body without the wall-screw bosses or the centre spine; nut blocks trimmed."""
    z0 = -40.0
    foot = Pos(0, -v1.DEV_H / 2) * Rectangle(2 * v3.X_IN + 0.02, v1.DEV_H)
    body = Pos(0, 0, z0) * extrude(foot, v3.SEAT - z0)
    body = body - hollow_prism()
    for sgn in (+1, -1):
        yp = v1.MID_Y + sgn * (v3.PLATE_SCREW_DY + (v3.TRAVEL_OUT - v3.TRAVEL_IN) / 2)
        body += Pos(0, yp, (v3.SEAT + z0) / 2) * Box(*NUT_BLOCK, v3.SEAT - z0)
    return body & Pos(0, -v1.DEV_H / 2, v3.SEAT - 100) * Box(200, v1.DEV_H, 200)


def cover():
    half = BOX / 2 + COVER_MARGIN
    plate = WALL_PL * Pos(C_U, v1.MID_Y, 0) * extrude(RectangleRounded(2 * half, 2 * half, COVER_R), COVER_T)
    return plate - hollow_prism()                # inside the wedge the box opens into the hollow


def wall_screw_bosses():
    return [ax * Pos(0, 0, -2) * Cylinder(BOSS_R, 60, align=(Align.CENTER, Align.CENTER, Align.MIN)) for ax in wall_screw_axes()]


def wall_screw_cuts():
    cuts = []
    for ax in wall_screw_axes():
        cuts.append(ax * Pos(0, 0, CB_FLOOR) * Cylinder(CB_D / 2, 80, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        cuts.append(ax * Pos(0, 0, -5) * Cylinder(3.4 / 2, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return cuts


def body_cuts():
    """v3 body cuts without the wall-screw counterbores; cable window trimmed."""
    cuts = []
    for sgn in (+1, -1):
        yc = v1.MID_Y + sgn * (v3.PLATE_SCREW_DY + (v3.TRAVEL_OUT - v3.TRAVEL_IN) / 2)
        span = v3.TRAVEL_OUT + v3.TRAVEL_IN
        cuts.append(Pos(0, yc, v3.SEAT - 10) * extrude(SlotCenterToCenter(span, 3.4, rotation=90), 20))
        cuts.append(Pos(0, yc, -40) * extrude(Rectangle(v3.NUT_AF, span + 6.6), (v3.SEAT - 2.2) - (-40)))
    cy0, cy1, _ = v1.CABLE_WIN
    x0, x1 = CABLE_X
    cuts.append(Pos((x0 + x1) / 2, (cy0 + cy1) / 2, -45) * extrude(RectangleRounded(x1 - x0, cy1 - cy0, 3), 60))
    return cuts


def seat_windows():
    """S-diamond windows in the seat skin under the doorbell, clear of the nut blocks, cable window
    and wall-screw bosses."""
    from shapely.geometry import box as sbox, Point as SPoint
    from shapely.ops import unary_union
    P = v3.PERIM
    xi = v1.DEV_W / 2 - 1.5        # only under the doorbell body: the 2.4 mm side gap must not show the box
    foot = sbox(-xi, -v1.DEV_H + P, xi, -P)
    keep = []
    for sgn in (+1, -1):
        yp = v1.MID_Y + sgn * (v3.PLATE_SCREW_DY + (v3.TRAVEL_OUT - v3.TRAVEL_IN) / 2)
        keep.append(sbox(-NUT_BLOCK[0] / 2, yp - NUT_BLOCK[1] / 2, NUT_BLOCK[0] / 2, yp + NUT_BLOCK[1] / 2))
    cy0, cy1, _ = v1.CABLE_WIN
    keep.append(sbox(CABLE_X[0], cy0, CABLE_X[1], cy1))
    for sgn in (+1, -1):
        keep.append(SPoint(0, v1.MID_Y + sgn * WALL_SCREW_DY).buffer(BOSS_R / v3.c_ + 1.0))
    region = foot.difference(unary_union(keep))
    wins = v1.window_pattern(region, a=3.6, b=6.0, rib=1.6, margin=1.0)
    return [Pos(0, 0, v3.SEAT - v3.SKIN - 1) * extrude(v1.poly_face(w), v3.SKIN + 2) for w in wins], len(wins)


def build():
    keep_wall = v3.front_of_wall()
    sh = (v4.shell() + v4.vault_ribs()) - v4.lip_cutter()
    assert sh.bounding_box().max.Z < v1.Z_FRONT + 20, "lip cut failed"
    lat, nlat = v4.side_lattice()
    body = wedge_body()
    for b in wall_screw_bosses():
        body += b
    body = body & Pos(0, -v1.DEV_H / 2, v3.SEAT - 100) * Box(200, v1.DEV_H, 200)   # nothing proud of the seat
    part = (sh + lat + body + cover()) & keep_wall
    for c in body_cuts() + wall_screw_cuts():
        part -= c
    wins, nwin = seat_windows()
    for w in wins:
        part -= w
    sols = sorted(part.solids(), key=lambda s: s.volume, reverse=True)
    return sols[0], [round(s.volume, 2) for s in sols[1:]], nwin, nlat


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "v5a")
    os.makedirs(out, exist_ok=True)
    part, dropped, nwin, nlat = build()
    print("valid", part.is_valid, "vol", round(part.volume, 1), "mass g", round(part.volume / 1000 * 1.17, 1),
          "seat windows", nwin, "lattice/side", nlat, "dropped", dropped)
    bb = part.bounding_box()
    print("bbox", [round(v, 1) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    export_brep(part, os.path.join(out, "hood.brep"))
    export_step(part, os.path.join(out, "sunshade_hood_v5a.step"))
    export_brep(v1.device_solid(), os.path.join(out, "device.brep"))
    export_brep(v1.plate_solid(), os.path.join(out, "plate.brep"))
    shutil.copy(os.path.join(HERE, "..", "v3", "v3_geom.json"), os.path.join(out, "v3_geom.json"))
    shutil.copy(os.path.join(HERE, "..", "v4", "params.json"), os.path.join(out, "params.json"))
    O = WALL_PL.from_local_coords((C_U, v1.MID_Y, 0))
    json.dump(dict(variant="v5a", box_centre=list(O), u_axis=list(U), wall_normal=list(N), box=BOX,
                   box_lugs_used=False,
                   wall_screws=[list(ax.origin) for ax in wall_screw_axes()], wall_screw_floor=CB_FLOOR,
                   wall_holes_from_box_centre_mm=[[round((ax.origin - O).dot(U), 1), round(ax.origin.Y - O.Y, 1)] for ax in wall_screw_axes()]),
              open(os.path.join(out, "geom.json"), "w"), indent=1)

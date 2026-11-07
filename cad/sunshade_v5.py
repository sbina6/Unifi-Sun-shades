"""Sunshade v5: v4 (car-shade style, integrated 20 deg wedge) and the switch-box adapter in ONE
lighter part. Fixes to a Qatar / UK BS 4662 square switch box with the box's own two screws.

Changes from v4 + adapter:
- No separate adapter and no wall screws / anchors: a 2.5 mm cover plate on the wall closes the
  box, merged with the wedge. The wedge's own back still sits flush on the wall.
- Box screws (lugs 60.3 c/c, left/right of the box centre). In one piece the shade's side walls
  would sit over both lugs, so the doorbell sits C_U = 17.15 mm to one side of the box centre:
  - the "hidden" lug lands inside the wedge hollow; its screw goes in through a d7.5 access hole
    in the seat, which the doorbell's metal plate then covers;
  - the "visible" lug is clear of the shade on the cover plate, countersunk flush.
- Lighter: shell 1.8 (was 2.2), wedge perimeter 1.8 (2.2), seat skin 2.0 (2.4) windowed all over,
  no wall-screw bosses or centre spine, the shade's side walls double as the wedge's, nut blocks trimmed to 9.2 x 16, lattice relief 0.6 (0.9),
  cover 2.0, cable window trimmed to 22 mm (clears the hidden lug's boss).
- Unchanged: the outer surfaces, the lip (cut just outside the camera picture), vault ribs, side
  lattice, plate screws on sliding nuts. The shading is the same as v4.

Frame: the doorbell frame (see sunshade_v3.py).   usage: python cad/sunshade_v5.py [outdir]
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

# ---- box and cover plate (wall frame: u along the wall, y up, n out of the wall) ----
BOX = 75.0
BOX_LUG = 60.3 / 2
C_U = 17.15                 # box centre along u, from the doorbell's screw line (box centre y = MID_Y)
COVER_MARGIN = 5.5          # past the box opening, like a switch plate (86 mm square)
COVER_T = 2.0
COVER_R = 8.0
BOSS_T = 3.5                # lug bosses: head seat
BOSS_D_VIS, BOSS_D_HID = 13.0, 10.0
BOX_HOLE, BOX_CSK = 3.9, 7.4
ACCESS_D = 7.5              # driver access to the hidden lug, through the seat
CABLE_X = (-10.0, 12.0)     # cable window x range at the seat (doorbell plate's d18 hole: +-9)

G3 = json.load(open(os.path.join(HERE, "..", "v3", "v3_geom.json")))
N = Vector(*G3["wall_normal"])
U = Vector(N.Z, 0, -N.X)
_q = Vector(*G3["wall_screw_seat_points"]["top"])
_P = Vector(*G3["wall_point"])
W0 = _q - N * ((_q - _P).dot(N))            # wall point under the top wall-screw position (u = 0)
WALL_PL = Plane(origin=(W0.X, 0, W0.Z), x_dir=U, z_dir=N)   # (u, y, n) -> doorbell frame


def lugs():
    """(u, y) of the two box lugs on the wall: hidden (inside the wedge), visible."""
    return (C_U - BOX_LUG, v1.MID_Y), (C_U + BOX_LUG, v1.MID_Y)


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
    (uh, yh), (uv, yv) = lugs()
    half = BOX / 2 + COVER_MARGIN
    plate = WALL_PL * Pos(C_U, v1.MID_Y, 0) * extrude(RectangleRounded(2 * half, 2 * half, COVER_R), COVER_T)
    plate -= hollow_prism()                      # inside the wedge the box opens into the hollow
    plate += WALL_PL * Pos(uv, yv, 0) * Cylinder(BOSS_D_VIS / 2, BOSS_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    plate += WALL_PL * Pos(uh, yh, 0) * Cylinder(BOSS_D_HID / 2, BOSS_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return plate


def lug_cuts():
    cuts = []
    h = (BOX_CSK - BOX_HOLE) / 2
    for i, (u, y) in enumerate(lugs()):
        ax = WALL_PL * Pos(u, y, 0)
        cuts.append(ax * Pos(0, 0, -1) * Cylinder(BOX_HOLE / 2, BOSS_T + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        cuts.append(ax * Pos(0, 0, BOSS_T - h) * Cone(BOX_HOLE / 2, BOX_CSK / 2, h + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        if i == 0:   # hidden: driver access from the head up through the seat
            cuts.append(ax * Pos(0, 0, BOSS_T) * Cylinder(ACCESS_D / 2, 60, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        else:        # visible: nothing above the flush head
            cuts.append(ax * Pos(0, 0, BOSS_T) * Cylinder(BOX_CSK / 2, 60, align=(Align.CENTER, Align.CENTER, Align.MIN)))
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
    """S-diamond windows over the whole seat skin, clear of the nut blocks, cable window and the
    hidden lug's access hole."""
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
    (uh, yh), _ = lugs()
    o = WALL_PL.from_local_coords((uh, yh, 0))
    t = (v3.SEAT - o.Z) / N.Z
    keep.append(SPoint(o.X + N.X * t, yh).buffer(ACCESS_D / 2 / v3.c_ + 1.8))
    region = foot.difference(unary_union(keep))
    wins = v1.window_pattern(region, a=3.6, b=6.0, rib=1.6, margin=1.0)
    return [Pos(0, 0, v3.SEAT - v3.SKIN - 1) * extrude(v1.poly_face(w), v3.SKIN + 2) for w in wins], len(wins)


def build():
    keep_wall = v3.front_of_wall()
    sh = (v4.shell() + v4.vault_ribs()) - v4.lip_cutter()
    assert sh.bounding_box().max.Z < v1.Z_FRONT + 20, "lip cut failed"
    lat, nlat = v4.side_lattice()
    part = (sh + lat + wedge_body() + cover()) & keep_wall
    for c in body_cuts() + lug_cuts():
        part -= c
    wins, nwin = seat_windows()
    for w in wins:
        part -= w
    sols = sorted(part.solids(), key=lambda s: s.volume, reverse=True)
    return sols[0], [round(s.volume, 2) for s in sols[1:]], nwin, nlat


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "v5")
    os.makedirs(out, exist_ok=True)
    part, dropped, nwin, nlat = build()
    print("valid", part.is_valid, "vol", round(part.volume, 1), "mass g", round(part.volume / 1000 * 1.17, 1),
          "seat windows", nwin, "lattice/side", nlat, "dropped", dropped)
    bb = part.bounding_box()
    print("bbox", [round(v, 1) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    export_brep(part, os.path.join(out, "hood.brep"))
    export_step(part, os.path.join(out, "sunshade_v5.step"))
    for f in ("device.brep", "plate.brep", "params.json", "v3_geom.json"):
        src = os.path.join(HERE, "..", "v4", f)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(out, f))
    (uh, yh), (uv, yv) = lugs()
    pts = {nm: [list(WALL_PL.from_local_coords((u, y, 0)))] for nm, (u, y) in (("hidden", (uh, yh)), ("visible", (uv, yv)))}
    json.dump(dict(C_U=C_U, box=BOX, lug_wall_points=pts, wall_normal=list(N), u_axis=list(U),
                   wall_origin=[W0.X, 0, W0.Z], cover_t=COVER_T, boss_t=BOSS_T),
              open(os.path.join(out, "v5_geom.json"), "w"), indent=1)

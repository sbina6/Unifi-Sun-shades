"""Wall adapter: covers a Qatar / UK (BS 4662) square switch box and gives the
UniFi Protect Doorbell Lite's mount a flat, solid wall to screw into.

    wall + switch box  ->  THIS ADAPTER  ->  metal plate (flat)  or  20 deg wedge / v3 / v4 hood

Frame (mm): x right, y up, z out of the wall. Wall at z = 0, adapter front at z = T.
Origin = centre of the switch box opening.

- Fixed to the box with the box's own 2 x M3.5 countersunk screws (lugs 60.3 c/c, left/right).
  Countersunk flush, so anything can sit over the heads.
- Two M3 nuts captured in side-entry channels, on the centreline 74 mm apart: the Doorbell Lite's
  wall-screw spacing, used by the flat plate, the 20 deg wedge and the v3/v4 hoods alike.
  Screws for every mount: M3 x 12 flat-head.
- Cable window 24 x 57 (v1 CABLE_WIN), inside the box opening and inside the v3/v4 hollow.
- Solid 2.4 mm front skin (it has to keep rain out of the box), 2.2 mm rim and 2.0 mm ribs on the
  back, cavities open toward the wall.
- Outline 86 wide (a Qatar switch-plate width) and tall enough to carry the whole v4 back face
  (wall footprint x -23.3..30.1, y -68.5..88.7 about the screw midpoint, measured from v4's STEP).

Run:  /tmp/cadenv/bin/python cad/wall_adapter.py   (writes ../adapter/)
"""
import os, sys
from build123d import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "adapter")

# ---------------- parameters ----------------
W = 86.0                    # outline width
Y_BOT, Y_TOP = -73.0, 93.0  # outline, about the box centre (doorbell screw midpoint at DY)
R_CORNER = 8.0
T = 10.0                    # overall thickness
SKIN = 2.4                  # front skin
RIM = 2.2                   # back perimeter rim
RIB = 2.0
FRONT_FILLET = 1.5

DY = 0.0                    # doorbell screw midpoint above the box centre
SCREW_DY = 37.0             # 74 mm c/c (Doorbell Lite template)
M3_HOLE = 3.4
NUT_AF, NUT_T = 5.7, 2.6    # channel; nut is 5.5 AF x 2.4
NUT_BOSS = (13.0, 10.5)     # x, y

BOX = 75.0                  # BS 4662 box opening
BOX_LUG = 60.3 / 2
BOX_HOLE, BOX_CSK = 3.9, 7.4    # M3.5 countersunk, 90 deg
BOX_BOSS = 11.0

CABLE = (-12.0, 12.0, -30.5, 26.5, 3.0)   # x0, x1, y0, y1 (about the screw midpoint), corner r
CABLE_FRAME = 2.2

RIB_Y = (-55.0, 52.0, 74.0) # horizontal ribs (about the box centre); none on the nut lines, so the
                            # nut channels open into a cavity
RIB_X = (-25.0, 25.0)       # vertical ribs


def rrect_at(x0, x1, y0, y1, r):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2) * RectangleRounded(x1 - x0, y1 - y0, r)


def outline():
    return rrect_at(-W / 2, W / 2, Y_BOT, Y_TOP, R_CORNER)


def cable_sk(grow=0.0):
    x0, x1, y0, y1, r = CABLE
    return rrect_at(x0 - grow, x1 + grow, DY + y0 - grow, DY + y1 + grow, r + grow)


def adapter():
    body = extrude(outline(), T)
    body = fillet(body.edges().group_by(Axis.Z)[-1], FRONT_FILLET)

    # hollow the back: keep skin, rim, ribs, bosses, cable frame
    inner = offset(outline(), -RIM, kind=Kind.INTERSECTION)
    keep = [cable_sk(CABLE_FRAME)]
    for s in (-1, 1):
        keep.append(Pos(s * BOX_LUG, 0) * Circle(BOX_BOSS / 2))
        keep.append(Pos(-1.0, DY + s * SCREW_DY) * Rectangle(*NUT_BOSS))
    hw = W                           # ribs run long and are clipped by the outline
    keep.append(Rectangle(hw, RIB))                                          # y = 0 (box lugs)
    for y in RIB_Y:
        keep.append(Pos(0, y) * Rectangle(hw, RIB))
    keep.append(Pos(0, (Y_BOT + DY - SCREW_DY) / 2) * Rectangle(RIB, DY - SCREW_DY - Y_BOT))
    keep.append(Pos(0, (Y_TOP + DY + SCREW_DY) / 2) * Rectangle(RIB, Y_TOP - DY - SCREW_DY))
    for x in RIB_X:
        keep.append(Pos(x, (Y_BOT + Y_TOP) / 2) * Rectangle(RIB, Y_TOP - Y_BOT))
    keep_sk = Sketch() + keep
    pocket = Sketch() + [inner]
    pocket = pocket - keep_sk
    body -= extrude(pocket, T - SKIN)

    # cable window, through
    body -= extrude(cable_sk(), T)

    # box screws: through hole + 90 deg countersink, flush with the front
    for s in (-1, 1):
        p = Pos(s * BOX_LUG, 0)
        body -= p * extrude(Circle(BOX_HOLE / 2), T)
        h = (BOX_CSK - BOX_HOLE) / 2
        body -= p * Pos(0, 0, T - h) * Cone(BOX_HOLE / 2, BOX_CSK / 2, h + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
        body -= p * Pos(0, 0, T) * Cylinder(BOX_CSK / 2, 2, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # doorbell screws: M3 hole through, nut channel entering from -x (back cavity side),
    # nut pulled up against the skin by the screw
    for s in (-1, 1):
        y = DY + s * SCREW_DY
        body -= Pos(0, y) * extrude(Circle(M3_HOLE / 2), T)
        z0 = T - SKIN - NUT_T
        L = 3.4 + NUT_BOSS[0]                              # from x = +3.4 out past the boss edge
        body -= Pos(3.4 - L / 2, y, z0) * Box(L, NUT_AF, NUT_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return body


def coupon():
    """Scale frame 62.00 X/Y + 56.60 Z tower, nut channels 5.6/5.7/5.8, M3 holes 3.3/3.4/3.5,
    and the M3.5 box-screw hole + countersink (3.9 / 7.4). Axis-aligned."""
    frame = extrude(Rectangle(62, 62), 2.5) - extrude(Rectangle(54, 54), 2.5)
    tower = Pos(-28, -28, 0) * extrude(Rectangle(6, 6), 56.6)
    block = Pos(8, -27, 0) * extrude(Rectangle(40, 8), 6.0)
    pad = Pos(27, 0, 0) * extrude(Rectangle(8, 14), 4.0)
    c = frame + tower + block + pad
    for i, af in enumerate((5.6, 5.7, 5.8)):
        x = -4 + i * 12
        c -= Pos(x, -27, 6.0 - 2.6) * extrude(Rectangle(af, 8.2), 2.6)
        c -= Pos(x, -27, 0) * extrude(Circle((3.3 + 0.1 * i) / 2), 6.0)
    c -= Pos(27, 0, 0) * extrude(Circle(BOX_HOLE / 2), 4.0)
    h = (BOX_CSK - BOX_HOLE) / 2
    c -= Pos(27, 0, 4.0 - h) * Cone(BOX_HOLE / 2, BOX_CSK / 2, h + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return c


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    a = adapter()
    print("adapter valid", a.is_valid, "solids", len(a.solids()), "vol", round(a.volume, 1),
          "mass g", round(a.volume / 1000 * 1.17, 1))
    bb = a.bounding_box()
    print("bbox", [round(v, 2) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    export_brep(a, os.path.join(OUT, "adapter.brep"))
    export_step(a, os.path.join(OUT, "wall_adapter.step"))
    c = coupon()
    export_brep(c, os.path.join(OUT, "coupon.brep"))
    export_step(c, os.path.join(OUT, "fit_test_coupon_adapter.step"))
    print("coupon vol", round(c.volume, 1))

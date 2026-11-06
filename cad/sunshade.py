"""Static sunshade (hood) for the UniFi Protect Doorbell Lite (UVC-Doorbell-Lite), v1.

Frame (mm): x right, y up, z out of the wall. Wall at z = 0.
The hood's back flange is clamped between the wall (or the 20 deg wedge) and the
doorbell's sheet-metal plate, so the doorbell sits exactly as before, 2.2 mm further out.

Device data (techspecs.ui.com + to-scale QIG drawing, cross-checked on the 18 mm cable hole):
  body 40 x 137 x 26.4, lens centre 14.6 below the top,
  wall screws on the centreline 74 apart (+-37 from the middle),
  wedge->plate screws ~92 apart, cable hole d18 centred 88 below the top.

Run:  /tmp/cadenv/bin/python cad/sunshade.py   (writes ../v1/)
"""
import json, math, os
import numpy as np
from build123d import *
from shapely.geometry import Polygon as SPoly, box as sbox, Point as SPoint
from shapely.ops import unary_union
from shapely import affinity

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v1")

# ---------------- parameters ----------------
DEV_W, DEV_H, DEV_D = 40.0, 137.0, 26.4
DEV_R = 5.0                 # plan corner radius of the body
LENS_DROP = 14.6            # lens centre below device top
T_FL = 2.2                  # flange thickness (behind plate)
GAP_SIDE = 2.0              # air gap device side -> wall (convection + install)
WALL = 2.2                  # side-wall thickness
GAP_TOP = 14.0              # air gap device top -> roof (hook-on install needs ~11)
ROOF = 2.4                  # roof thickness
BRIM = 10.0                 # roof projection ahead of device front
CHEEK_TAPER_TO = -40.0      # side walls go from BRIM ahead (at roof) to flush at this y
BRIM_R = 9.0                # plan radius of the brim front corners
SLOT_W = 6.0                # flange slots: pass screw shanks AND clear wedge screw heads
SLOT_Y = (33.0, 51.0)       # slot extent from device middle (covers 74 and ~92 spacings)
CABLE_WIN = (-99.0, -42.0, 24.0)   # y from, y to (below top), width: d18 hole and wedge window

X_OUT = DEV_W / 2 + GAP_SIDE + WALL          # 24.2
Y_TOP_IN = GAP_TOP
Y_TOP = GAP_TOP + ROOF
Z_FRONT = T_FL + DEV_D                       # device front plane
LENS = np.array([0.0, -LENS_DROP, Z_FRONT + 0.5])
MID_Y = -DEV_H / 2


def rrect(w, h, r):
    return RectangleRounded(w, h, r)


def device_solid():
    """Envelope of the doorbell (rounded box), back on the flange."""
    d = extrude(Pos(0, MID_Y) * rrect(DEV_W, DEV_H, DEV_R), DEV_D)
    d = fillet(d.edges().group_by(Axis.Z)[-1], 3.0)          # rounded front edges
    return Pos(0, 0, T_FL) * d


def plate_solid():
    """Metal plate envelope (31 x 125 x 1.6) with top hook tabs."""
    p = Pos(0, MID_Y, T_FL) * extrude(Rectangle(31, 125), 1.6)
    return p


# ---------- S-curved diamond window pattern ----------
def s_diamond(cx, cy, w, h, amp=0.13, n=10):
    v = [(cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy), (cx, cy - h / 2)]
    pts = []
    for i in range(4):
        p0, p1 = np.array(v[i]), np.array(v[(i + 1) % 4])
        d = p1 - p0
        L = np.linalg.norm(d)
        nrm = np.array([d[1], -d[0]]) / L
        for t in np.linspace(0, 1, n, endpoint=False):
            pts.append(p0 + d * t + nrm * amp * L * math.sin(2 * math.pi * t))
    return SPoly(pts)


def window_pattern(region, a=3.6, b=6.0, rib=1.8, margin=2.0):
    """S-diamond lattice: tiles with half-diagonals (a, b) share their S-edges, each tile is
    inset by rib/2 so every rib is the same width. Keep windows >= margin inside region."""
    out = []
    inner = region.buffer(-margin)
    minx, miny, maxx, maxy = region.bounds
    for j in range(int((miny - b) // b) - 1, int(maxy // b) + 2):
        cy = j * b
        off = a if j % 2 else 0.0
        for i in range(int(minx // (2 * a)) - 2, int(maxx // (2 * a)) + 3):
            cx = i * 2 * a + off
            win = s_diamond(cx, cy, 2 * a, 2 * b).buffer(-rib / 2, join_style=2)
            if not win.is_empty and inner.contains(win):
                out.append(win)
    return out


def poly_face(p):
    return make_face(Polyline(*[tuple(c) for c in p.exterior.coords], close=True))


def flange_cutouts():
    """2D cut-outs in the flange: slots, cable window, S-diamond windows."""
    cuts = []
    for s in (+1, -1):
        y0, y1 = MID_Y + s * SLOT_Y[0], MID_Y + s * SLOT_Y[1]
        cuts.append(SPoint(0, min(y0, y1)).buffer(SLOT_W / 2).union(
            SPoint(0, max(y0, y1)).buffer(SLOT_W / 2)).convex_hull)
    cy0, cy1, cw = CABLE_WIN
    cable = sbox(-cw / 2, cy0, cw / 2, cy1).buffer(3).buffer(-3)
    cuts.append(cable)
    # windows: inside the device footprint, 4 mm solid rim for the body's back edge,
    # 4 mm solid around slots and cable window, plate-screw pads stay solid
    foot = sbox(-DEV_W / 2, -DEV_H, DEV_W / 2, 0).buffer(-4.0 + 2.0, join_style=2)  # 4 mm rim band
    above = sbox(-DEV_W / 2 - GAP_SIDE + 2.0, 0.0, DEV_W / 2 + GAP_SIDE - 2.0, GAP_TOP)  # wall side, above body
    keep = unary_union(cuts)   # window_pattern keeps a 2 mm margin
    region = unary_union([foot, above]).difference(keep)
    wins = window_pattern(region)
    return cuts, wins


def hood_solid():
    # flange: full back plate from below device bottom to roof top
    fl = Pos(0, (-DEV_H + Y_TOP) / 2) * Rectangle(2 * X_OUT, DEV_H + Y_TOP)
    flange = extrude(fl, T_FL)
    cuts, wins = flange_cutouts()
    for c in cuts + wins:
        flange -= extrude(poly_face(c), T_FL)

    # side walls: profile in the y-z plane, extruded along x
    prof = [(0, -DEV_H), (Z_FRONT, -DEV_H), (Z_FRONT, CHEEK_TAPER_TO),
            (Z_FRONT + BRIM, Y_TOP_IN - 2), (Z_FRONT + BRIM, Y_TOP), (0, Y_TOP)]
    x0 = DEV_W / 2 + GAP_SIDE
    f = make_face(Polyline(*[(x0, y, z) for z, y in prof], close=True))
    w = extrude(f, WALL, dir=(1, 0, 0))
    walls = [w, mirror(w, Plane.YZ)]

    # roof with rounded brim corners (plan in x-z)
    depth = Z_FRONT + BRIM
    roof_sk = Pos(0, depth / 2) * RectangleRounded(2 * X_OUT, depth, BRIM_R)
    roof_sk = Plane.XZ * roof_sk  # sketch plane x-z (normal -y)
    roof = extrude(roof_sk, -ROOF)          # thickness upward (+y)
    roof = Pos(0, Y_TOP_IN, 0) * roof
    # square the back corners (against the wall)
    roof += Pos(0, Y_TOP_IN + ROOF / 2, BRIM_R / 2) * Box(2 * X_OUT, ROOF, BRIM_R)
    h = flange + walls[0] + walls[1] + roof
    # trim anything that ended up behind the wall plane
    h = h & Pos(0, -60, 200) * Box(200, 400, 400)
    return h


def fit_coupon():
    """Shrinkage coupon: 62.00 x 62.00 square frame (X/Y faces) + 56.60 tall corner tower (Z).
    Printed axis-aligned (NOT tilted) so the faces map onto the printer axes."""
    frame = extrude(Rectangle(62, 62), 2.5) - extrude(Rectangle(54, 54), 2.5)
    tower = Pos(-31 + 3, -31 + 3, 0) * extrude(Rectangle(6, 6), 56.6)
    return frame + tower


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    hood = hood_solid()
    dev = device_solid()
    plate = plate_solid()
    print("hood valid", hood.is_valid, "volume mm3", round(hood.volume, 1),
          "mass g", round(hood.volume / 1000 * 1.17, 1))
    bb = hood.bounding_box()
    print("hood bbox", [round(v, 1) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    export_step(hood, os.path.join(OUT, "sunshade_hood_v1.step"))
    export_brep(hood, os.path.join(OUT, "hood.brep"))
    export_brep(dev, os.path.join(OUT, "device.brep"))
    export_brep(plate, os.path.join(OUT, "plate.brep"))
    export_step(dev, os.path.join(OUT, "doorbell_lite_envelope_ref.step"))
    cp = fit_coupon()
    export_step(cp, os.path.join(OUT, "fit_test_coupon_v1.step"))
    export_brep(cp, os.path.join(OUT, "coupon.brep"))
    json.dump(dict(LENS=LENS.tolist(), Z_FRONT=Z_FRONT, T_FL=T_FL, MID_Y=MID_Y, DEV_H=DEV_H,
                   X_OUT=X_OUT, Y_TOP=Y_TOP, GAP_TOP=GAP_TOP),
              open(os.path.join(OUT, "params.json"), "w"), indent=1)

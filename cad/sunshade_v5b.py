"""Sunshade v5b (box-sized): the shade redesigned to the size of the switch box. One part.

An 86 mm wide hood (a Qatar switch-plate width) centred on the BS 4662 box, with its side walls
SQUARE TO THE WALL (v4's were square to the turned doorbell). The doorbell still sits on the
integrated 20 deg wedge inside it, turned toward the entrance. Because the side walls are square
to the wall and 86 mm apart, both box screws (lugs 60.3 c/c) sit inside the hood beside the wedge
and go straight in, before the doorbell is hooked on. No drilling.

- Hood: U profile in the wall plane, 86 wide, straight sides, R6 fillets into a barrel vault
  (outer R70, inner crown 20 mm above the doorbell), three raised vault ribs, S-diamond lattice in
  0.6 mm relief on both sides. Shell 1.8 mm.
- Lip: for every point round the U, the hood reaches out along the wall normal until just before
  the camera would see it (fisheye fit + 3 deg margin, conservative lens; cad/fov_limits.py), then
  smoothed. So the camera picture stays clear, as on v1-v4.
- Wedge: v3/v4 seat (doorbell pose unchanged), 1.8 perimeter, 2.0 seat skin with S-diamond windows
  under the doorbell, plate screws on sliding nuts.
- Box cover: 2.0 mm, 86 x 86 inside the hood, hides the box; lug bosses with flush countersinks.

Frame: the doorbell frame (sunshade_v3.py). BOX = plane on the wall at the box centre
(u along the wall, y up, n out of the wall).        usage: python cad/sunshade_v5b.py [outdir]
"""
import json, math, os, shutil, sys
import numpy as np
from build123d import *
from scipy.ndimage import gaussian_filter1d, minimum_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sunshade as v1
import sunshade_v3 as v3
import fov_limits as F

v3.PERIM = 1.8
v3.SKIN = 2.0

WALL = 1.8
HW = 43.0                   # outer half width (86 = switch plate)
CROWN_IN = 20.0             # inner crown above the doorbell top
R_ARCH_O, R_FIL_O = 70.0, 6.0
RIB_H, RIB_W, RIB_N = 0.9, 1.6, (6.0, 16.0, 26.0)
LAT_H = 0.6
LAT_A, LAT_B, LAT_RIB, LAT_FRAME = 3.8, 5.8, 1.3, 2.6
LIP_MARGIN = 0.6
N_CAP = 56.0                # cap: ~14 mm ahead of the doorbell's front corner (more adds no shade, v2 sweep)

BOX = 75.0
BOX_LUG = 60.3 / 2
C_U = 1.0                   # box centre along u from the doorbell's screw line (u=0 under seat x=0)
COVER = 86.0
COVER_T = 2.0
BOSS_T, BOSS_D = 3.5, 13.0
BOX_HOLE, BOX_CSK = 3.9, 7.4
NUT_BLOCK = (9.2, 16.0)

G3 = json.load(open(os.path.join(HERE, "..", "v3", "v3_geom.json")))
N = Vector(*G3["wall_normal"])
U = Vector(N.Z, 0, -N.X)
_q = Vector(*G3["wall_screw_seat_points"]["top"])
W0 = _q - N * ((_q - v3.P_WALL).dot(N))
BOXPL = Plane(origin=Vector(W0.X, v1.MID_Y, W0.Z) + U * C_U, x_dir=U, z_dir=N)
Y_BOT = -v1.DEV_H / 2                         # local y of the doorbell bottom (box centre = doorbell middle)
Y_DEVTOP = v1.DEV_H / 2


# ---------- hood profile (local u, y) ----------
def geom(d):
    X, R, r = HW - d, R_ARCH_O - d, R_FIL_O - d
    yc = Y_DEVTOP + CROWN_IN + WALL - R_ARCH_O
    yf = yc + math.sqrt((R - r) ** 2 - (X - r) ** 2)
    fc = (X - r, yf)
    phi = math.degrees(math.atan2(fc[1] - yc, fc[0]))
    return dict(X=X, R=R, r=r, fc=fc, yf=yf, phi=phi, yc=yc)


def profile_face(d, y_bot):
    g = geom(d)
    X, R, r, fc, yf, phi, yc = (g[k] for k in ("X", "R", "r", "fc", "yf", "phi", "yc"))
    edges = [Line((X, y_bot), (X, yf)), CenterArc(fc, r, 0, phi), CenterArc((0, yc), R, phi, 180 - 2 * phi),
             CenterArc((-fc[0], fc[1]), r, 180 - phi, phi), Line((-X, yf), (-X, y_bot)), Line((-X, y_bot), (X, y_bot))]
    return make_face(Wire(edges))


def outline_mid(step=1.0):
    g = geom(WALL / 2)
    X, R, r, fc, yf, phi, yc = (g[k] for k in ("X", "R", "r", "fc", "yf", "phi", "yc"))
    P, Nn = [], []
    ys = np.arange(Y_BOT - 3, yf, step)
    for y in ys:
        P.append((-X, y)); Nn.append((-1, 0))
    for a in np.linspace(180, 180 - phi, max(3, int(math.radians(phi) * r / step)), endpoint=False):
        t = math.radians(a); P.append((-fc[0] + r * math.cos(t), fc[1] + r * math.sin(t))); Nn.append((math.cos(t), math.sin(t)))
    for a in np.linspace(180 - phi, phi, int(math.radians(180 - 2 * phi) * R / step), endpoint=False):
        t = math.radians(a); P.append((R * math.cos(t), yc + R * math.sin(t))); Nn.append((math.cos(t), math.sin(t)))
    for a in np.linspace(phi, 0, max(3, int(math.radians(phi) * r / step)), endpoint=False):
        t = math.radians(a); P.append((fc[0] + r * math.cos(t), fc[1] + r * math.sin(t))); Nn.append((math.cos(t), math.sin(t)))
    for y in ys[::-1]:
        P.append((X, y)); Nn.append((1, 0))
    return np.array(P), np.array(Nn, float)


# ---------- camera limit along the wall normal ----------
_PHI = np.linspace(-math.pi, math.pi, 721)
_TH = np.array([F.theta_edge(p) for p in _PHI]) + F.MARGIN


def visible(p):
    """p: (k,3) doorbell-frame points. True where the camera (conservative lens) would see them."""
    d = p - F.L
    th = np.degrees(np.arccos(np.clip(d[:, 2] / np.linalg.norm(d, axis=1), -1, 1)))
    lim = np.interp(np.arctan2(d[:, 1], d[:, 0]), _PHI, _TH)
    return th < lim


def to_global(u, y, n):
    vec = lambda v: np.array([v.X, v.Y, v.Z], float)
    o, uu, nn = vec(BOXPL.origin), vec(U), vec(N)
    return o + np.outer(u, uu) + np.outer(y, [0, 1, 0]) + np.outer(n, nn)


def lip_reach():
    P, Nn = outline_mid()
    ns = np.arange(0, N_CAP + 0.25, 0.25)
    lim = np.empty(len(P))
    for i, (p, nv) in enumerate(zip(P, Nn)):
        vis = np.zeros(len(ns), bool)
        for w in (-WALL / 2, WALL / 2 + LAT_H):
            q = p + nv * w
            vis |= visible(to_global(np.full(len(ns), q[0]), np.full(len(ns), q[1]), ns))
        lim[i] = ns[np.argmax(vis)] if vis.any() else N_CAP
    R = lim - LIP_MARGIN
    R = minimum_filter1d(R, size=3, mode="nearest")
    for _ in range(4):
        R = gaussian_filter1d(R, sigma=1.5, mode="nearest")
        R = np.minimum(R, lim - LIP_MARGIN)
    return P, Nn, R, lim


def lip_cutter(P, Nn, R):
    idx = list(range(0, len(P), 3))
    if idx[-1] != len(P) - 1:
        idx.append(len(P) - 1)
    rows = [[BOXPL.from_local_coords((P[i][0] + Nn[i][0] * w, P[i][1] + Nn[i][1] * w, R[i])) for i in idx]
            for w in (-2.5, 0.0, 2.5)]
    f = Face.make_surface_from_array_of_points(rows, tol=0.05)
    return extrude(f, 150, dir=tuple(N))


def shell():
    outer = BOXPL * extrude(profile_face(0.0, Y_BOT), 150)
    inner = BOXPL * Pos(0, 0, -1) * extrude(profile_face(WALL, Y_BOT - 20), 152)
    return outer - inner


def vault_ribs():
    g = geom(0.0)
    band = profile_face(-RIB_H, Y_BOT) - profile_face(0.0, Y_BOT - 10)
    band = band & (Pos(0, g["yf"] + 60, 0) * Rectangle(300, 120))
    ribs = None
    for n in RIB_N:
        r = BOXPL * Pos(0, 0, n - RIB_W / 2) * extrude(band, RIB_W)
        ribs = r if ribs is None else ribs + r
    return ribs


def side_lattice(P, R):
    from shapely.geometry import Polygon as SPoly, box as sbox
    from shapely.ops import unary_union
    g = geom(0.0)
    side = P[:, 0] < -HW + 2.5
    ys, rs = P[side, 1], R[side]
    o = np.argsort(ys); ys, rs = ys[o], rs[o]
    y_top = g["yf"] - 1.0
    parts, nwin = [], 0
    for s in (-1, +1):
        sel = (P[:, 0] > HW - 2.5) if s > 0 else side
        yy, rr = P[sel, 1], R[sel]; o = np.argsort(yy); yy, rr = yy[o], rr[o]
        lip = [(float(np.interp(y, yy, rr)) - 0.4, y) for y in np.linspace(Y_BOT, y_top, 120)]
        region = SPoly([(3.0, Y_BOT)] + lip + [(3.0, y_top)]).buffer(0) & sbox(0, Y_BOT, 200, y_top)
        inner = region.buffer(-LAT_FRAME, join_style=2)
        wins = v1.window_pattern(inner, a=LAT_A, b=LAT_B, rib=LAT_RIB, margin=0.0)
        nwin = len(wins)
        lat = region.difference(unary_union(wins))
        org = BOXPL.from_local_coords((s * HW, 0, 0))
        pl = Plane(origin=org, x_dir=(N if s < 0 else -N), z_dir=U * s)
        for gp in getattr(lat, "geoms", [lat]):
            gp = gp.simplify(0.02)
            mx = (lambda c: (c[0], c[1])) if s < 0 else (lambda c: (-c[0], c[1]))
            outer = Polyline(*[mx(c) for c in gp.exterior.coords], close=True)
            f = make_face(outer)
            for ring in gp.interiors:
                f -= make_face(Polyline(*[mx(c) for c in ring.coords], close=True))
            parts.append(extrude(pl * f, LAT_H))
    out = parts[0]
    for p in parts[1:]:
        out += p
    return out, nwin


# ---------- wedge, cover, cuts ----------
def hollow_prism():
    z0 = -60.0
    return Pos(0, -v1.DEV_H / 2, z0) * extrude(Rectangle(2 * v3.X_IN - 2 * v3.PERIM, v1.DEV_H - 2 * v3.PERIM), v3.SEAT - v3.SKIN - z0)


def wedge_body():
    z0 = -60.0
    body = Pos(0, 0, z0) * extrude(Pos(0, -v1.DEV_H / 2) * Rectangle(2 * v3.X_IN, v1.DEV_H), v3.SEAT - z0)
    body -= hollow_prism()
    for sgn in (+1, -1):
        yp = v1.MID_Y + sgn * (v3.PLATE_SCREW_DY + (v3.TRAVEL_OUT - v3.TRAVEL_IN) / 2)
        body += Pos(0, yp, (v3.SEAT + z0) / 2) * Box(*NUT_BLOCK, v3.SEAT - z0)
    return body & Pos(0, -v1.DEV_H / 2, v3.SEAT - 100) * Box(300, v1.DEV_H, 200)


def cover():
    c = BOXPL * extrude(Rectangle(COVER, COVER), COVER_T)
    c -= hollow_prism()
    for s in (-1, 1):
        c += BOXPL * Pos(s * BOX_LUG, 0, 0) * Cylinder(BOSS_D / 2, BOSS_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return c


def cuts():
    out = []
    for sgn in (+1, -1):
        yc = v1.MID_Y + sgn * (v3.PLATE_SCREW_DY + (v3.TRAVEL_OUT - v3.TRAVEL_IN) / 2)
        span = v3.TRAVEL_OUT + v3.TRAVEL_IN
        out.append(Pos(0, yc, v3.SEAT - 10) * extrude(SlotCenterToCenter(span, 3.4, rotation=90), 20))
        out.append(Pos(0, yc, -60) * extrude(Rectangle(v3.NUT_AF, span + 6.6), (v3.SEAT - 2.2) + 60))
    cy0, cy1, cw = v1.CABLE_WIN
    out.append(Pos(0, (cy0 + cy1) / 2, -65) * extrude(RectangleRounded(cw, cy1 - cy0, 3), 80))
    h = (BOX_CSK - BOX_HOLE) / 2
    for s in (-1, 1):
        ax = BOXPL * Pos(s * BOX_LUG, 0, 0)
        out.append(ax * Pos(0, 0, -1) * Cylinder(BOX_HOLE / 2, BOSS_T + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        out.append(ax * Pos(0, 0, BOSS_T - h) * Cone(BOX_HOLE / 2, BOX_CSK / 2, h + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return out


def seat_windows():
    from shapely.geometry import box as sbox
    from shapely.ops import unary_union
    xi = v1.DEV_W / 2 - 1.5
    foot = sbox(-xi, -v1.DEV_H + v3.PERIM, xi, -v3.PERIM)
    keep = []
    for sgn in (+1, -1):
        yp = v1.MID_Y + sgn * (v3.PLATE_SCREW_DY + (v3.TRAVEL_OUT - v3.TRAVEL_IN) / 2)
        keep.append(sbox(-NUT_BLOCK[0] / 2, yp - NUT_BLOCK[1] / 2, NUT_BLOCK[0] / 2, yp + NUT_BLOCK[1] / 2))
    cy0, cy1, cw = v1.CABLE_WIN
    keep.append(sbox(-cw / 2, cy0, cw / 2, cy1))
    region = foot.difference(unary_union(keep))
    wins = v1.window_pattern(region, a=3.6, b=6.0, rib=1.6, margin=1.0)
    return [Pos(0, 0, v3.SEAT - v3.SKIN - 1) * extrude(v1.poly_face(w), v3.SKIN + 2) for w in wins], len(wins)


def build():
    P, Nn, R, lim = lip_reach()
    print("lip reach along n: min", round(float(R.min()), 1), "max", round(float(R.max()), 1),
          "min margin", round(float((lim - R).min()), 2))
    keep_wall = v3.front_of_wall()
    sh = (shell() + vault_ribs()) - lip_cutter(P, Nn, R)
    lat, nlat = side_lattice(P, R)
    part = (sh + lat + wedge_body() + cover()) & keep_wall
    for c in cuts():
        part -= c
    wins, nwin = seat_windows()
    for w in wins:
        part -= w
    sols = sorted(part.solids(), key=lambda s: s.volume, reverse=True)
    return sols[0], [round(s.volume, 2) for s in sols[1:]], nwin, nlat


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "v5b")
    os.makedirs(out, exist_ok=True)
    part, dropped, nwin, nlat = build()
    print("valid", part.is_valid, "vol", round(part.volume, 1), "mass g", round(part.volume / 1000 * 1.17, 1),
          "seat windows", nwin, "lattice/side", nlat, "dropped", dropped)
    bb = part.bounding_box()
    print("bbox", [round(v, 1) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    export_brep(part, os.path.join(out, "hood.brep"))
    export_step(part, os.path.join(out, "sunshade_hood_v5b.step"))
    export_brep(v1.device_solid(), os.path.join(out, "device.brep"))
    export_brep(v1.plate_solid(), os.path.join(out, "plate.brep"))
    shutil.copy(os.path.join(HERE, "..", "v3", "v3_geom.json"), os.path.join(out, "v3_geom.json"))
    shutil.copy(os.path.join(HERE, "..", "v4", "params.json"), os.path.join(out, "params.json"))
    json.dump(dict(variant="v5b", box_centre=list(BOXPL.origin), u_axis=list(U), wall_normal=list(N), box=BOX,
                   box_lugs_used=True, orient_in_wall_frame=True, lug_points=[list(BOXPL.from_local_coords((s * BOX_LUG, 0, 0))) for s in (-1, 1)],
                   boss_t=BOSS_T),
              open(os.path.join(out, "geom.json"), "w"), indent=1)

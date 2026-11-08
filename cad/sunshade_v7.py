"""Sunshade v7 (simple): a SMALL shade and a box backplate, no angle. One printed part.

The doorbell sits flat on the wall (no wedge, no bracket): its own metal plate bolts straight onto
the backplate. The shade hugs the doorbell (2.4 mm gap each side), so its walls stand only 48 mm
apart, between the switch box's two screws.

Two separate joints
- PART TO WALL: the switch box's own 2 screws (M3.5, lugs 60.3 apart, left and right of the box),
  countersunk flush in the 86 x 86 mm backplate, OUTSIDE the shade's walls (a driver reaches them
  along the wall normal). No drilling.
- DOORBELL PLATE TO PART: 2 x M3 x 8 flat-head bolts through the plate's two holes (74 mm apart) into
  2 M3 NUT POCKETS (5.7 AF x 4.8 deep, open to the wall side, 2.0 mm skin in front, 4 mm slide).

Parts of the one body
- shade: U profile in the wall plane, 48 wide, straight sides, R5 fillets into a barrel vault, shell
  1.6, edge cut along the wall normal to just outside the camera picture (fisheye fit + 3 deg margin);
  Islamic relief on both side walls (shade_patterns.py)
- backplate: 86 x 86 mm (hides the box) + a 34 mm spine the doorbell's full height under the plate,
  6.8 mm thick, hollow behind (2.0 skin, 2.0 rim, ribs)

Frame: the DOORBELL frame (sunshade.py) for device / plate; the part is built in the WALL frame
BOXPL (u along the wall, y up, n out of the wall, origin at the box centre). Flat: the wall frame is
the doorbell frame moved back by the backplate thickness.

usage: python cad/sunshade_v7.py [--out DIR] [--pattern khatam] [--base]
"""
import argparse, json, math, os, shutil, sys
import numpy as np
from build123d import *
from scipy.ndimage import gaussian_filter1d, minimum_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sunshade as v1
import fov_limits as F
import shade_patterns as sp

LENS_EXTRA_Z = 1.0          # the plate is a known 1.6 mm: a little slack only
F.L = F.L + np.array([0.0, 0.0, LENS_EXTRA_Z])

# ---------------- parameters ----------------
WALL = 1.6
GAP_SIDE = 2.4              # doorbell body to the shade's inner face
HW = v1.DEV_W / 2 + GAP_SIDE + WALL    # 24.0: outer half width, 48 wide, inside both box screws
CROWN_IN = 19.0             # inner crown above the doorbell top (the 20 deg hook-on needs more than 16)
R_ARCH_O, R_FIL_O = 30.0, 5.0
LAT_H, LAT_RIB, LAT_FRAME = 0.6, 1.4, 2.6
LIP_MARGIN = 1.6            # camera-limit margin (the extreme image corners need more than 0.6)
N_CAP = 44.0                # longest reach from the wall

BOX = 75.0
BOX_LUG = 60.3 / 2
BP = 6.8                    # backplate: 2.0 skin + 4.8 pocket, so M3 x 8 bolts reach the nut and stop above the wall
SKIN, RIM = 2.0, 2.0
COVER = 86.0
SPINE_W = 34.0
BOX_HOLE, BOX_CSK = 3.9, 7.4
HOLE_DY = 37.0              # the doorbell plate's two holes: 74 mm apart, centred on the doorbell
NUT_AF, NUT_T = 5.7, 2.4
TRAVEL = 4.0                # nut slide along the line, total
BLOCK = (9.2, 14.4)         # pad round each pocket (u, y)
CABLE = (-11.0, 11.0, -29.0, 26.0)   # window, relative to the centre line: u0, u1, y0, y1

# ---------------- frames (flat: the wall frame is the doorbell frame moved back by BP) ----------------
N = Vector(0, 0, 1)
U = Vector(1, 0, 0)
C_U = 0.0                                             # box centre = the doorbell's centre line
U0 = 0.0
Y_BOT, Y_DEVTOP = -v1.DEV_H / 2, v1.DEV_H / 2
BOXPL = Plane(origin=Vector(0, v1.MID_Y, v1.T_FL - BP), x_dir=U, z_dir=N)   # the plate's back sits on the backplate face


def front_of_wall():
    return Plane(origin=Vector(0, 0, v1.T_FL - BP), z_dir=N) * Pos(0, 0, 300) * Box(600, 600, 600)


def vec(v):
    return np.array([float(v.X), float(v.Y), float(v.Z)])


# ---------------- hood profile (local u, y) ----------------
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


# ---------------- camera limit along the wall normal ----------------
_PHI = np.linspace(-math.pi, math.pi, 721)
_TH = np.array([F.theta_edge(p) for p in _PHI]) + F.MARGIN


def visible(p):
    """p: (k,3) doorbell-frame points. True where the camera (conservative lens) would see them."""
    d = p - F.L
    th = np.degrees(np.arccos(np.clip(d[:, 2] / np.linalg.norm(d, axis=1), -1, 1)))
    lim = np.interp(np.arctan2(d[:, 1], d[:, 0]), _PHI, _TH)
    return th < lim


def to_global(u, y, n):
    o, uu, nn = vec(BOXPL.origin), vec(U), vec(N)
    return o + np.outer(u, uu) + np.outer(y, [0, 1, 0]) + np.outer(n, nn)


def lip():
    """(P, normals, R, limit): the reach R along the wall normal at every outline point: the longest
    reach that keeps the hood out of the camera picture (fisheye fit + 3 deg margin, conservative lens)."""
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


def lip_cutter(P, Nn, R, step):
    idx = list(range(0, len(P), step))
    if idx[-1] != len(P) - 1:
        idx.append(len(P) - 1)
    rows = [[BOXPL.from_local_coords((P[i][0] + Nn[i][0] * w, P[i][1] + Nn[i][1] * w, R[i])) for i in idx]
            for w in (-2.5, 0.0, 2.5)]
    f = Face.make_surface_from_array_of_points(rows, tol=0.05)
    return extrude(f, 150, dir=tuple(N))


def mesh_ok(shape, tag=""):
    """Tessellate and check the shape is watertight and no longer than the reach cap."""
    import tempfile, trimesh
    f = os.path.join(tempfile.gettempdir(), f"_v7_{os.getpid()}.stl")
    export_stl(shape, f, tolerance=0.03, angular_tolerance=0.1)       # print resolution: coarser tessellation gives false cracks
    t = trimesh.load(f); os.remove(f)
    nmax = float(((t.vertices - vec(BOXPL.origin)) @ vec(N)).max())
    return bool(t.is_watertight) and nmax <= N_CAP + 1.0


def cut_lip(shape, P, Nn, R):
    """shape minus the region beyond the lip. The curved cutter surface is fragile, so try a few
    samplings and keep the first result that tessellates watertight and short."""
    for step in (2, 1, 5):
        r = shape - lip_cutter(P, Nn, R, step)
        if mesh_ok(r):
            return r
    raise RuntimeError("lip cut failed")


def shell():
    outer = BOXPL * extrude(profile_face(0.0, Y_BOT), 150)
    inner = BOXPL * Pos(0, 0, -1) * extrude(profile_face(WALL, Y_BOT - 20), 152)
    return outer - inner


# ---------------- side relief (region in (n, y) on the straight side walls) ----------------
def side_region(P, R):
    from shapely.geometry import Polygon as SPoly, box as sbox
    g = geom(0.0)
    side = P[:, 0] < -HW + 2.5
    ys, rs = P[side, 1], R[side]
    o = np.argsort(ys); ys, rs = ys[o], rs[o]
    y_top = g["yf"] - 1.0
    lp = [(float(np.interp(y, ys, rs)) - 0.4, y) for y in np.linspace(Y_BOT, y_top, 560)]
    return SPoly([(BP - 0.5, Y_BOT)] + lp + [(BP - 0.5, y_top)]).buffer(0) & sbox(0, Y_BOT, 200, y_top)


def relief_polys(pattern, P, R):
    """Relief polygons (n, y); the same on both walls. [] for 'smooth'."""
    from shapely.ops import unary_union
    region = side_region(P, R)
    wins = sp.PATTERNS[pattern](region.buffer(-LAT_FRAME, join_style=2), LAT_RIB)
    if not wins:
        return []
    lat = region.difference(unary_union(wins))
    return [g.simplify(0.02) for g in getattr(lat, "geoms", [lat]) if g.area > 0.5]


def _face(poly, mirror=False):
    mx = (lambda c: (-c[0], c[1])) if mirror else (lambda c: (c[0], c[1]))
    f = make_face(Polyline(*[mx(c) for c in poly.exterior.coords], close=True))
    for ring in poly.interiors:
        f -= make_face(Polyline(*[mx(c) for c in ring.coords], close=True))
    return f


def relief_solid(pattern, P, R):
    polys = relief_polys(pattern, P, R)
    if not polys:
        return None
    parts = []
    for s in (-1, +1):
        org = BOXPL.from_local_coords((s * (HW - 0.2), 0, 0))          # sunk 0.2 mm into the wall: robust fuse
        pl = Plane(origin=org, x_dir=(N if s < 0 else -N), z_dir=U * s)
        for g in polys:
            parts.append(extrude(pl * _face(g, mirror=(s > 0)), LAT_H + 0.2))
    out = parts[0]
    for p in parts[1:]:
        out += p
    return out


# ---------------- backplate and mounting ----------------
def plate_region():
    from shapely.geometry import box as sbox
    sq = sbox(-COVER / 2, -COVER / 2, COVER / 2, COVER / 2)
    spine = sbox(U0 - SPINE_W / 2, Y_BOT, U0 + SPINE_W / 2, Y_DEVTOP)
    return sq.union(spine)


def pocket_pos():
    return [(U0, +HOLE_DY), (U0, -HOLE_DY)]


def lug_pos():
    return [(-BOX_LUG, 0.0), (+BOX_LUG, 0.0)]


def backplate():
    from shapely.geometry import box as sbox, Point
    from shapely.ops import unary_union
    reg = plate_region()
    plate = None
    for g in getattr(reg, "geoms", [reg]):
        f = BOXPL * extrude(_face(g.simplify(0.01)), BP)
        plate = f if plate is None else plate + f
    # cavity behind the 2.0 skin: rim, ribs, lug bosses and nut pads stay
    keep = [Point(*p).buffer(6.5) for p in lug_pos()]
    keep += [sbox(u - BLOCK[0] / 2, y - BLOCK[1] / 2, u + BLOCK[0] / 2, y + BLOCK[1] / 2) for u, y in pocket_pos()]
    keep += [sbox(-COVER / 2, y - 1.0, COVER / 2, y + 1.0) for y in (-20.0, 20.0)]
    cav = reg.buffer(-RIM).difference(unary_union(keep))
    for g in getattr(cav, "geoms", [cav]):
        if g.area > 4:
            plate -= BOXPL * Pos(0, 0, -1) * extrude(_face(g.simplify(0.01)), 1 + BP - SKIN)
    # star openwork through the skin wherever the box opening is NOT behind it (the ring round the
    # box and the spine above and below it); the skin over the box stays solid
    solid = [sbox(-BOX / 2 - 3, -BOX / 2 - 3, BOX / 2 + 3, BOX / 2 + 3)]
    solid += [Point(*p).buffer(6.5 + 1.2) for p in lug_pos()]
    solid += [sbox(u - BLOCK[0] / 2 - 1.2, y - BLOCK[1] / 2 - 1.2, u + BLOCK[0] / 2 + 1.2, y + BLOCK[1] / 2 + 1.2) for u, y in pocket_pos()]
    wreg = reg.buffer(-(RIM + 1.2)).difference(unary_union(solid))
    for w in sp.khatam(wreg, 1.4, s=10.0):
        plate -= BOXPL * Pos(0, 0, -1) * extrude(_face(w), BP + 2)
    return plate


def mount_cuts():
    cuts = []
    h = (BOX_CSK - BOX_HOLE) / 2
    for u, y in lug_pos():                                     # box screws: flush countersunk
        ax = BOXPL * Pos(u, y, 0)
        cuts.append(ax * Pos(0, 0, -1) * Cylinder(BOX_HOLE / 2, BP + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        cuts.append(ax * Pos(0, 0, BP - h) * Cone(BOX_HOLE / 2, BOX_CSK / 2, h + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        cuts.append(ax * Pos(0, 0, BP) * Cylinder(BOX_CSK / 2, 2, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    for u, y in pocket_pos():                                  # M3 nut pockets (open to the wall) + shank slots
        ax = BOXPL * Pos(u, y, 0)
        cuts.append(ax * Pos(0, 0, -1) * extrude(Rectangle(NUT_AF, 6.4 + TRAVEL), 1 + BP - SKIN))
        cuts.append(ax * Pos(0, 0, BP - SKIN - 1) * extrude(SlotCenterToCenter(TRAVEL, 3.4, rotation=90), SKIN + 2))
    u0, u1, y0, y1 = CABLE
    cuts.append(BOXPL * Pos(U0 + (u0 + u1) / 2, (y0 + y1) / 2, -1) * extrude(RectangleRounded(u1 - u0, y1 - y0, 3), BP + 2))
    return cuts


def build(pattern="khatam", lattice=True):
    P, Nn, R, _ = lip()
    sh = cut_lip(shell(), P, Nn, R)
    if lattice:
        rel = relief_solid(pattern, P, R)
        if rel is not None:
            sh = sh + rel
    part = (sh + backplate()) & front_of_wall()
    for c in mount_cuts():
        part -= c
    sols = sorted(part.solids(), key=lambda s: s.volume, reverse=True)
    if len(sols) != 1 or not mesh_ok(sols[0]):
        raise RuntimeError(f"part is not one watertight solid: {[round(x.volume, 1) for x in sols]}")
    return sols[0], [], (float(R.min()), float(R.max()))


def write_geom(out, pattern):
    O = vec(BOXPL.origin)
    pl = lambda u, y, n=0.0: list(BOXPL.from_local_coords((u, y, n)))
    json.dump(dict(variant="v7", pattern=pattern,
                   box_centre=list(O), u_axis=list(vec(U)), wall_normal=list(vec(N)), box=BOX, box_lugs_used=True,
                   hood_width=2 * HW, plate_t=BP, boss_t=BP, C_U=C_U, bracket_u_local=U0, hole_dy=HOLE_DY, variant_note="simple: flat, no bracket",
                   lug_points=[pl(u, y) for u, y in lug_pos()],
                   pocket_points=[pl(u, y) for u, y in pocket_pos()],
                   cable_window=CABLE, nut_travel=TRAVEL, orient_in_wall_frame=True),
              open(os.path.join(out, "geom.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "..", "v7"))
    ap.add_argument("--pattern", default="khatam", choices=list(sp.PATTERNS))
    ap.add_argument("--base", action="store_true", help="no relief: writes base.brep for the viewer")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    part, dropped, (rmin, rmax) = build(a.pattern, lattice=not a.base)
    print("C_U", C_U, "lip reach", round(rmin, 1), "..", round(rmax, 1), "valid", part.is_valid, "dropped", dropped)
    bb = part.bounding_box()
    print("bbox", [round(v, 1) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    if a.base:
        export_brep(part, os.path.join(a.out, "base.brep"))
    else:
        export_brep(part, os.path.join(a.out, "hood.brep"))
        export_step(part, os.path.join(a.out, "sunshade_hood_v7.step"))
    export_brep(v1.device_solid(), os.path.join(a.out, "device.brep"))
    export_brep(v1.plate_solid(), os.path.join(a.out, "plate.brep"))
    shutil.copy(os.path.join(HERE, "..", "v4", "params.json"), os.path.join(a.out, "params.json"))
    write_geom(a.out, a.pattern)

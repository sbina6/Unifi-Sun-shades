"""Sunshade v4: v3's function in the style of the arched car-shade pergola next to it.

- barrel-vault roof (segmental arch in front view, R5 fillets into the side walls)
- three raised arched ribs across the vault (like the pergola's arch ribs)
- raised S-diamond lattice on the outer side walls (reads as the pergola's lattice fascia, but
  stays solid so the morning sun can't get through)
- everything else from v3: integrated 20 deg wedge flush to the wall, plate on sliding nuts,
  lip cut to stay outside the camera picture (now computed on the arched outline)

Frame: doorbell frame (see sunshade_v3.py).  usage: python cad/sunshade_v4.py [outdir]
"""
import json, math, os, shutil, sys
import numpy as np
from build123d import *

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sunshade as v1
import sunshade_v3 as v3
from fov_limits import reach
from v3_profiles import side_reach
from scipy.ndimage import gaussian_filter1d, minimum_filter1d

XO = v3.X_OUT                  # 24.2 outer side face
WALL = v1.WALL                 # 2.2
CROWN_IN = 18.0                # inner crown height above the doorbell top
R_ARCH_O = 34.0                # outer vault radius
R_FIL_O = 5.0                  # outer fillet, side wall -> vault
CROWN_O = CROWN_IN + WALL
YC = CROWN_O - R_ARCH_O        # vault centre y (x = 0)
Y_BOT = -v1.DEV_H
RIB_H, RIB_W = 0.9, 1.6        # raised arched ribs
RIB_Z = (5.0, 15.0, 25.0)      # rib planes (behind the shortest lip, in front of the wall)
LAT_H = 0.9                    # lattice relief height
LAT_A, LAT_B, LAT_RIB, LAT_FRAME = 3.8, 5.8, 1.3, 2.6   # diamond half-diagonals, rib, frame
MARGIN = 0.6


def geom(d):
    """Outline offset d inward from the outer surface: side x, arch radius, fillet radius/centre,
    tangent points and the fillet's angular span (right half; left is mirrored)."""
    X, R, r = XO - d, R_ARCH_O - d, R_FIL_O - d
    yf = YC + math.sqrt((R - r) ** 2 - (X - r) ** 2)
    fc = (X - r, yf)
    phi = math.degrees(math.atan2(fc[1] - YC, fc[0]))      # direction centre->fillet centre
    return dict(X=X, R=R, r=r, fc=fc, yf=yf, phi=phi)


def profile_face(d, y_bot):
    g = geom(d)
    X, R, r, fc, yf, phi = g["X"], g["R"], g["r"], g["fc"], g["yf"], g["phi"]
    edges = [Line((X, y_bot), (X, yf)),
             CenterArc(fc, r, 0, phi),
             CenterArc((0, YC), R, phi, 180 - 2 * phi),
             CenterArc((-fc[0], fc[1]), r, 180 - phi, phi),
             Line((-X, yf), (-X, y_bot)),
             Line((-X, y_bot), (X, y_bot))]
    return make_face(Wire(edges))


def outline_mid(step=1.0):
    """Mid-surface points, outward normals and design reach around the U (left bottom -> right bottom)."""
    g = geom(WALL / 2)
    X, R, r, fc, yf, phi = g["X"], g["R"], g["r"], g["fc"], g["yf"], g["phi"]
    P, N, D = [], [], []
    def add(p, n, dz):
        P.append(p); N.append(n); D.append(dz)
    ys = np.arange(Y_BOT - 4, yf, step)
    for y in ys:
        add((-X, y), (-1, 0), side_reach(min(y, 6.4)))
    for a in np.linspace(180, 180 - phi, max(3, int(math.radians(phi) * r / step)), endpoint=False):
        t = math.radians(a); add((-fc[0] + r * math.cos(t), fc[1] + r * math.sin(t)), (math.cos(t), math.sin(t)), 99.0)
    for a in np.linspace(180 - phi, phi, int(math.radians(180 - 2 * phi) * R / step), endpoint=False):
        t = math.radians(a); add((R * math.cos(t), YC + R * math.sin(t)), (math.cos(t), math.sin(t)), 99.0)
    for a in np.linspace(phi, 0, max(3, int(math.radians(phi) * r / step)), endpoint=False):
        t = math.radians(a); add((fc[0] + r * math.cos(t), fc[1] + r * math.sin(t)), (math.cos(t), math.sin(t)), 99.0)
    for y in ys[::-1]:
        add((X, y), (1, 0), side_reach(min(y, 6.4)))
    return np.array(P), np.array(N, float), np.array(D)


def lip_reach():
    P, N, D = outline_mid()
    half = WALL / 2 + LAT_H / 2           # include the relief on the outside
    lim = np.array([min(reach(*(p - N[i] * WALL / 2)), reach(*(p + N[i] * half))) for i, p in enumerate(P)])
    R = np.minimum(np.minimum(D, 14.0), lim - MARGIN)
    R = minimum_filter1d(R, size=3, mode="nearest")
    for _ in range(4):
        R = gaussian_filter1d(R, sigma=1.5, mode="nearest")
        R = np.minimum(R, lim - MARGIN)
    return P, N, R, lim


def lip_cutter():
    P, N, R, _ = lip_reach()
    idx = list(range(0, len(P), 3))
    if idx[-1] != len(P) - 1:
        idx.append(len(P) - 1)
    rows = [[Vector(P[i][0] + N[i][0] * w, P[i][1] + N[i][1] * w, v1.Z_FRONT + R[i]) for i in idx]
            for w in (-2.5, 0.0, 2.5)]
    f = Face.make_surface_from_array_of_points(rows, tol=0.05)
    return extrude(f, 120, dir=(0, 0, 1))


def shell():
    z0, z1 = -40.0, v1.Z_FRONT + 40.0
    outer = Pos(0, 0, z0) * extrude(profile_face(0.0, Y_BOT), z1 - z0)
    inner = Pos(0, 0, z0) * extrude(profile_face(WALL, Y_BOT - 20), z1 - z0)
    return outer - inner


def vault_ribs():
    g = geom(0.0)
    band = profile_face(-RIB_H, Y_BOT) - profile_face(0.0, Y_BOT - 10)
    band = band & (Pos(0, g["yf"] + 50, 0) * Rectangle(200, 100))      # only over the fillets + vault
    ribs = None
    for z in RIB_Z:
        r = Pos(0, 0, z - RIB_W / 2) * extrude(band, RIB_W)
        ribs = r if ribs is None else ribs + r
    return ribs


def _face_from_shapely(poly):
    """build123d face (with holes) from a shapely Polygon in the (z, y) plane, placed later."""
    outer = Polyline(*[tuple(c) for c in poly.exterior.coords], close=True)
    f = make_face(outer)
    for ring in poly.interiors:
        f -= make_face(Polyline(*[tuple(c) for c in ring.coords], close=True))
    return f


def side_lattice():
    """Raised S-diamond lattice on both outer side faces, built as ONE 2D polygon per side,
    already clipped to the lip curve and the wall line (no 3D lip cut needed)."""
    from shapely.geometry import Polygon as SPoly, box as sbox
    from shapely.ops import unary_union
    g = geom(0.0)
    P, N, R, _ = lip_reach()
    side = P[:, 0] < -XO + 2.0                     # left-side samples (symmetric)
    ys, rs = P[side, 1], R[side]
    order = np.argsort(ys); ys, rs = ys[order], rs[order]
    y_top = g["yf"] - 1.0
    out_parts, n = [], 0
    for s in (+1, -1):
        zw_hi = max(v3.wall_z(s * XO), v3.wall_z(s * (XO + LAT_H)))      # wall line on this face
        lip = [(v1.Z_FRONT + float(np.interp(y, ys, rs)) - 0.4, y) for y in np.linspace(Y_BOT, y_top, 120)]
        region = SPoly([(zw_hi - 3.0, Y_BOT)] + lip + [(zw_hi - 3.0, y_top)]).buffer(0)
        region = region & sbox(-60, Y_BOT, 80, y_top)
        inner = region.buffer(-LAT_FRAME, join_style=2)                 # solid frame round the panel
        wins = v1.window_pattern(inner, a=LAT_A, b=LAT_B, rib=LAT_RIB, margin=0.0)
        n = len(wins)
        lat = region.difference(unary_union(wins))
        geoms = getattr(lat, "geoms", [lat])
        # local x = z, local y = y (right-handed => normal -x); extrude outward on each side
        pl = Plane(origin=(s * XO, 0, 0), x_dir=(0, 0, 1), z_dir=(-1, 0, 0))
        for gpoly in geoms:
            out_parts.append(extrude(pl * _face_from_shapely(gpoly.simplify(0.02)), LAT_H if s < 0 else -LAT_H))
    out = out_parts[0]
    for p in out_parts[1:]:
        out += p
    return out, n


def build():
    keep_wall = v3.front_of_wall()
    sh = (shell() + vault_ribs()) - lip_cutter()
    assert sh.bounding_box().max.Z < v1.Z_FRONT + 20, "lip cut failed"
    deco_lat, nlat = side_lattice()
    sh = sh + deco_lat
    body = v3.wedge_body()
    part = (sh + body) & keep_wall
    for c in v3.body_cuts():
        part -= c
    wins, nwin = v3.seat_windows()
    for w in wins:
        part -= w
    sols = sorted(part.solids(), key=lambda s: s.volume, reverse=True)
    return sols[0], [round(s.volume, 2) for s in sols[1:]], nwin, nlat


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "v4")
    os.makedirs(out, exist_ok=True)
    P, N, R, lim = lip_reach()
    print("lip: min margin to limit", round(float((lim - R).min()), 2), "max reach", round(float(R.max()), 1))
    part, dropped, nwin, nlat = build()
    print("valid", part.is_valid, "seat windows", nwin, "lattice diamonds/side", nlat, "dropped", dropped)
    bb = part.bounding_box()
    print("bbox", [round(v, 1) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    export_brep(part, os.path.join(out, "hood.brep"))
    export_step(part, os.path.join(out, "sunshade_hood_v4.step"))
    for f in ("device.brep", "plate.brep", "params.json", "v3_geom.json"):
        shutil.copy(os.path.join(HERE, "..", "v3", f), os.path.join(out, f))

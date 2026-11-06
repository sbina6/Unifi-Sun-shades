"""Sunshade v2: hood that reaches right up to the edge of the camera's picture.

Same flange, mounting, gaps and windows as v1 (sunshade.py). The side walls and roof are built
deep (EXT ahead of the doorbell front) and the camera's view volume (fisheye fit, with a safety
margin) is subtracted, so the shade covers every sun direction that is outside the picture.

usage: python cad/sunshade_v2.py [EXT_LEFT] [EXT_RIGHT] [OUTDIR]
  EXT_* = max forward reach (mm) of each side wall ahead of the doorbell front, "left/right"
  as seen standing in front of the doorbell (right = +x).
"""
import json, math, os, sys
import numpy as np
from build123d import *

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sunshade as v1

FISH = np.array([1.91883021e+01, 5.26733149e-02, -7.27681727e-04])
MARGIN_DEG = 3.0          # keep the shade this far outside the picture edge
LENS_Z_BACK = 0.5         # assume the lens could sit 0.5 mm further back (conservative)
LENS_Y_UP = 0.5           # ... and 0.5 mm higher


def theta_for_r(r):
    th = np.linspace(0, 95, 9501)
    rr = FISH[0] * th + FISH[1] * th ** 2 + FISH[2] * th ** 3
    return np.interp(r, rr, th)


def view_volume(R=260.0, n_side=60):
    """Solid of everything the camera can see (picture rectangle shrunk by MARGIN_DEG)."""
    L = v1.LENS.copy()
    L[2] -= 0.5 + LENS_Z_BACK            # v1.LENS is 0.5 ahead of the front face
    L[1] += LENS_Y_UP
    # rectangle border in image px, walked counter-clockwise
    hw, hh = 960.0, 1280.0
    pts = []
    for t in np.linspace(0, 1, n_side, endpoint=False): pts.append((hw, -hh + 2 * hh * t))
    for t in np.linspace(0, 1, n_side, endpoint=False): pts.append((hw - 2 * hw * t, hh))
    for t in np.linspace(0, 1, n_side, endpoint=False): pts.append((-hw, hh - 2 * hh * t))
    for t in np.linspace(0, 1, n_side, endpoint=False): pts.append((-hw + 2 * hw * t, -hh))
    dirs = []
    for u, w in pts:
        r = math.hypot(u, w)
        th = math.radians(theta_for_r(r) + MARGIN_DEG)
        ph = math.atan2(w, u)
        dirs.append((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
    apex = Vector(*L)
    ring = [apex + Vector(*d) * R for d in dirs]
    cap_c = apex + Vector(0, 0, R)
    faces = []
    N = len(ring)
    for i in range(N):
        a, b = ring[i], ring[(i + 1) % N]
        faces.append(Face(Wire.make_polygon([apex, a, b], close=True)))
        faces.append(Face(Wire.make_polygon([cap_c, b, a], close=True)))
    sh = Shell(faces)
    sol = Solid(sh)
    if sol.volume < 0:
        sol = Solid(Shell([f.reversed() if hasattr(f, "reversed") else f for f in faces]))
    return sol


def hood_v2(ext_left=40.0, ext_right=40.0):
    """ext_*: forward reach ahead of the doorbell front for the -x (left) and +x (right) walls."""
    Z_F = v1.Z_FRONT
    fl = Pos(0, (-v1.DEV_H + v1.Y_TOP) / 2) * Rectangle(2 * v1.X_OUT, v1.DEV_H + v1.Y_TOP)
    flange = extrude(fl, v1.T_FL)
    cuts, wins = v1.flange_cutouts()
    for c in cuts + wins:
        flange -= extrude(v1.poly_face(c), v1.T_FL)
    x0 = v1.DEV_W / 2 + v1.GAP_SIDE
    walls = None
    for s, ext in ((-1, ext_left), (+1, ext_right)):
        prof = [(0, -v1.DEV_H), (Z_F + ext, -v1.DEV_H), (Z_F + ext, v1.Y_TOP), (0, v1.Y_TOP)]
        f = make_face(Polyline(*[(x0, y, z) for z, y in prof], close=True))
        w = extrude(f, v1.WALL, dir=(1, 0, 0))
        if s < 0:
            w = mirror(w, Plane.YZ)
        walls = w if walls is None else walls + w
    depth = Z_F + max(ext_left, ext_right)
    roof = Pos(0, v1.Y_TOP_IN + v1.ROOF / 2, depth / 2) * Box(2 * v1.X_OUT, v1.ROOF, depth)
    raw = flange + walls + roof
    vv = view_volume()
    h = raw - vv
    # drop slivers: keep the largest solid only
    sols = sorted(h.solids(), key=lambda s: s.volume, reverse=True)
    h = sols[0]
    # soften: 0.8 mm fillet on the sharp front edges where OCC allows it
    return h, vv, [s.volume for s in sols[1:]]


if __name__ == "__main__":
    el = float(sys.argv[1]) if len(sys.argv) > 1 else 40.0
    er = float(sys.argv[2]) if len(sys.argv) > 2 else el
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "..", "v2")
    os.makedirs(out, exist_ok=True)
    h, vv, dropped = hood_v2(el, er)
    print("valid", h.is_valid, "vol", round(h.volume, 1), "mass g", round(h.volume / 1000 * 1.17, 1),
          "dropped slivers", [round(d, 2) for d in dropped])
    bb = h.bounding_box()
    print("bbox", [round(v, 1) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    export_brep(h, os.path.join(out, "hood.brep"))
    export_brep(vv, os.path.join(out, "view_volume.brep"))

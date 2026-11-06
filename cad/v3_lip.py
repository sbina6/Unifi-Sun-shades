"""v3 lip: one reach value R(u) around the hood's U outline (perimeter parameter u), kept under the
camera-view limit on both the inner and outer surface, then smoothed. Builds a smooth B-spline
cutter surface across the shell thickness."""
import math, os, sys
import numpy as np
from scipy.ndimage import gaussian_filter1d, minimum_filter1d
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sunshade as v1
from fov_limits import reach
from v3_profiles import side_reach

X_MID = v1.DEV_W / 2 + v1.GAP_SIDE + v1.WALL / 2      # 23.1 mid-surface of the side walls
R_MID = 10.0 - v1.WALL / 2                             # 8.9 mid radius of the top corners
CX, CY = X_MID - R_MID, v1.Y_TOP - 10.0 + 0.0          # corner centre (14.2, 6.4)
CY = 6.4
Y_ROOF_MID = v1.Y_TOP_IN + v1.ROOF / 2                 # 15.2
Y_BOT = -v1.DEV_H - 4.0
MARGIN = 0.6      # mm, on top of the 3 deg angular margin
ROOF_PEAK = 9.8


def outline(step=1.0):
    """Mid-surface points c(u) every ~step mm of perimeter, outward normals n(u), design reach."""
    pts, nrm, design = [], [], []
    side_n = int((CY - Y_BOT) / step)
    arc_n = int(math.pi / 2 * R_MID / step)
    roof_n = int(2 * CX / step)
    for y in np.linspace(Y_BOT, CY, side_n, endpoint=False):              # left side, upward
        pts.append((-X_MID, y)); nrm.append((-1, 0)); design.append(side_reach(y))
    for a in np.linspace(180, 90, arc_n, endpoint=False):                  # left corner
        t = math.radians(a); pts.append((-CX + R_MID * math.cos(t), CY + R_MID * math.sin(t)))
        nrm.append((math.cos(t), math.sin(t))); design.append(99.0)
    for x in np.linspace(-CX, CX, roof_n, endpoint=False):                 # roof
        pts.append((x, Y_ROOF_MID)); nrm.append((0, 1)); design.append(ROOF_PEAK * (1 - 0.35 * (x / CX) ** 2))
    for a in np.linspace(90, 0, arc_n, endpoint=False):                    # right corner
        t = math.radians(a); pts.append((CX + R_MID * math.cos(t), CY + R_MID * math.sin(t)))
        nrm.append((math.cos(t), math.sin(t))); design.append(99.0)
    for y in np.linspace(CY, Y_BOT, side_n):                               # right side, downward
        pts.append((X_MID, y)); nrm.append((1, 0)); design.append(side_reach(y))
    return np.array(pts), np.array(nrm, float), np.array(design)


def lip_reach():
    P, N, D = outline()
    half = v1.WALL / 2
    lim = np.array([min(reach(*(p - N[i] * half)), reach(*(p + N[i] * half))) for i, p in enumerate(P)])
    R = np.minimum(D, lim - MARGIN)
    # smooth from below: erode, then blur, then push down wherever the blur overshoots
    R = minimum_filter1d(R, size=3, mode="nearest")
    for _ in range(4):
        R = gaussian_filter1d(R, sigma=1.5, mode="nearest")
        R = np.minimum(R, lim - MARGIN)
    return P, N, R, lim


def cutter(z_front):
    """Solid in front of the lip surface (remove it from the shell)."""
    from build123d import Face, Vector, extrude
    P, N, R, _ = lip_reach()
    # every 3rd point (~3 mm): OCC booleans fail silently on a surface with ~360 poles per row
    idx = list(range(0, len(P), 3))
    if idx[-1] != len(P) - 1:
        idx.append(len(P) - 1)
    rows = [[Vector(P[i][0] + N[i][0] * w, P[i][1] + N[i][1] * w, z_front + R[i]) for i in idx]
            for w in (-2.0, 0.0, 2.0)]
    f = Face.make_surface_from_array_of_points(rows, tol=0.05)
    return extrude(f, 120, dir=(0, 0, 1))


if __name__ == "__main__":
    P, N, R, lim = lip_reach()
    print("min margin to limit (mm):", round(float((lim - R).min()), 2))
    for i in range(0, len(P), 20):
        print(f"  ({P[i][0]:6.1f},{P[i][1]:6.1f})  reach {R[i]:5.1f}  limit {lim[i]:5.1f}")

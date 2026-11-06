"""Max forward reach (mm ahead of the doorbell front) for side-wall inner faces and the roof underside
before a point enters the camera picture (3 deg margin, conservative lens position)."""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sunshade as v1
FISH = np.array([1.91883021e+01, 5.26733149e-02, -7.27681727e-04])
MARGIN = 3.0
def theta_edge(phi):
    """off-axis angle of the picture edge at image azimuth phi (rad)."""
    c, s = abs(math.cos(phi)), abs(math.sin(phi))
    r = min(960 / c if c > 1e-9 else 1e9, 1280 / s if s > 1e-9 else 1e9)
    th = np.linspace(0, 95, 9501); rr = FISH[0]*th + FISH[1]*th**2 + FISH[2]*th**3
    return float(np.interp(r, rr, th))
L = v1.LENS.copy(); L[2] -= 1.0; L[1] += 0.5      # same conservative lens as sunshade_v2
def reach(x, y):
    dx, dy = x - L[0], y - L[1]
    rho = math.hypot(dx, dy); phi = math.atan2(dy, dx)
    th = theta_edge(phi) + MARGIN
    return L[2] + rho / math.tan(math.radians(th)) - v1.Z_FRONT
if __name__ == "__main__":
    xs = 20 + v1.GAP_SIDE
    print("side wall inner face x=22: y -> reach")
    for y in [14, 10, 5, 0, -5, -10, -14.6, -20, -30, -40, -60, -80, -100, -120, -137]:
        print(f"  y {y:7.1f}  reach {reach(xs, y):6.1f}")
    print("roof underside y=14: x -> reach")
    for x in [0, 5, 10, 15, 20, 22]:
        print(f"  x {x:5.1f}  reach {reach(x, v1.Y_TOP_IN):6.1f}")

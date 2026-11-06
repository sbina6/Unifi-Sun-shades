"""Front-edge profiles for v3: smooth curves kept under the camera-view limit (cad/fov_limits.py).
Reach = mm ahead of the doorbell's front face (negative = behind it).
side_reach(y): side walls below Y_SWITCH.  roof_reach(|x|): roof and the top corner arcs."""
import numpy as np
from scipy.interpolate import PchipInterpolator
Y_SWITCH = 6.4                 # top corner arcs start here (outer R10, inner R7.8, centre x=14.2)
A_PTS = [(-137.0, 8.0), (-110, 6.8), (-80, 5.4), (-62, 3.6), (-51, 0.8), (-44, -1.6), (-38, 1.4),
         (-31, 5.8), (-22, 10.0), (-11, 12.0), (-2, 11.6), (3.0, 10.4), (Y_SWITCH, 8.5)]
B_PTS = [(0.0, 9.8), (8.0, 8.6), (12.0, 6.9), (14.2, 5.0), (15.5, 3.9), (16.9, 2.4), (18.1, 0.8),
         (19.0, -0.8), (19.7, -1.4), (20.2, 0.0), (20.6, 1.8), (21.0, 3.4), (21.5, 5.4), (22.0, 7.8),
         (23.0, 8.5), (26.0, 8.5)]
_A = PchipInterpolator([p[0] for p in A_PTS], [p[1] for p in A_PTS])
_B = PchipInterpolator([p[0] for p in B_PTS], [p[1] for p in B_PTS])
def side_reach(y):
    return float(_A(np.clip(y, -137.0, Y_SWITCH)))
def roof_reach(x):
    return float(_B(min(abs(x), 26.0)))

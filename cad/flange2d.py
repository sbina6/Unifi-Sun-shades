import sys; sys.path.insert(0, "cad")
from sunshade import *
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
cuts, wins = flange_cutouts()
print("windows", len(wins))
fig, ax = plt.subplots(figsize=(4, 10))
ax.add_patch(plt.Rectangle((-X_OUT, -DEV_H), 2*X_OUT, DEV_H + Y_TOP, fc="#e9a752"))
ax.add_patch(plt.Rectangle((-20, -137), 40, 137, fill=False, ec="k", ls="--"))
ax.add_patch(plt.Rectangle((-15.5, MID_Y-62.5), 31, 125, fill=False, ec="b", ls=":"))
for p in cuts + wins:
    x, y = p.exterior.xy; ax.fill(x, y, "w", ec="k", lw=0.5)
for yy in (MID_Y+37, MID_Y-37, MID_Y+46, MID_Y-46): ax.plot(0, yy, "r+")
ax.add_patch(plt.Circle((0, -88), 9, fill=False, ec="r"))
ax.set_aspect("equal"); ax.set_xlim(-30, 30); ax.set_ylim(-140, 20)
plt.savefig(sys.argv[1], dpi=80, bbox_inches="tight")

"""Charts for the sun study (Doha, wall facing 150 deg)."""
import json, math, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "..", "study")
TAG = sys.argv[1] if len(sys.argv) > 1 else "v2"
if TAG == "v3":
    F = {"no shade": json.load(open(os.path.join(S, "v3_none_170.json"))),
         "v3": json.load(open(os.path.join(S, "v3_hood_170.json")))}
    SHADE, SUB = "v3", "Doha, wall facing 150°, doorbell on the 20° wedge (camera 170°)"
    LEFT, RIGHT = "picture left = E (80°), morning sun", "picture right = W (260°)"
else:
    F = json.load(open(os.path.join(S, "sweep_150_full.json")))
    F["v2"] = F["v2 reach L20/R20"]
    SHADE, SUB = "v2", "Doha, wall facing 150°"
    LEFT, RIGHT = "picture left = ENE (60°), morning sun", "picture right = WSW (240°)"
FISH = np.array([1.91883021e+01, 5.26733149e-02, -7.27681727e-04])
C = ["#2a78d6", "#eb6834", "#1baf7a"]          # categorical slots 1-3 (validated all-pairs)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#dcdcd7", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})

def proj(d):
    th = math.degrees(math.acos(max(-1, min(1, d[2]))))
    r = FISH[0] * th + FISH[1] * th ** 2 + FISH[2] * th ** 3
    ph = math.atan2(d[1], d[0])
    return -r * math.cos(ph), r * math.sin(ph)   # picture as the camera sees it: its left is model +x

# ---- A: sun tracks in the camera's picture ----
fig, ax = plt.subplots(figsize=(6.4, 7.6), facecolor=SURF)
ax.set_facecolor(SURF)
ax.add_patch(plt.Rectangle((-960, -1280), 1920, 2560, fc="#eef1f4", ec=INK2, lw=1.2))
ax.text(0, -1250, "camera picture (1920 × 2560)", ha="center", va="bottom", color=INK2, fontsize=9)
rr = FISH[0] * 90 + FISH[1] * 8100 + FISH[2] * 729000
ax.add_patch(plt.Circle((0, 0), rr, fill=False, ec=GRID, lw=1, ls="--"))
ax.text(rr * 0.74, -rr * 0.74, "90° from the lens axis", color=INK2, fontsize=8, rotation=45, ha="center", va="center")
days = [("Jun 21 (summer)", "June 21"), ("Mar 21 / Sep 23 (equinox)", "Mar 21 / Sep 23"), ("Dec 21 (winter)", "December 21")]
v2 = F[SHADE]
for (key, lab), col in zip(days, C):
    rows = [r for r in v2[key]["rows"] if r["rel"][2] > 0 and not r.get("behind_wall")]
    xy = np.array([proj(r["rel"]) for r in rows])
    ax.plot(xy[:, 0], xy[:, 1], color=col, lw=2, label=lab, solid_capstyle="round")
    for r, (x, y) in zip(rows, xy):
        if abs(r["h"] - round(r["h"])) < 1e-6:
            sun = r["lens_in_sun"]
            ax.plot(x, y, "o", ms=8, mfc=SURF if sun else col, mec=col, mew=2, zorder=3)
            ax.annotate(f"{int(round(r['h'])):02d}", (x, y), xytext=(6, 4), textcoords="offset points", fontsize=8, color=INK2)
ax.plot([], [], "o", ms=8, mfc=INK2, mec=INK2, label=f"lens shaded by {SHADE}")
ax.plot([], [], "o", ms=8, mfc=SURF, mec=INK2, mew=2, label="lens in direct sun")
ax.set_xlim(-1750, 1750); ax.set_ylim(-1800, 2350); ax.set_aspect("equal")
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)
ax.text(-1700, 2330, "Where the sun is, seen from the lens", fontsize=13, color=INK, va="top", weight="bold")
ax.text(-1700, 2170, f"{SUB}.\nHourly markers, local time. Inside the frame the sun can't be blocked without the shade showing in the video.",
        fontsize=9, color=INK2, va="top")
ax.text(-1700, -1760, LEFT, fontsize=8, color=INK2)
ax.text(1700, -1760, RIGHT, fontsize=8, color=INK2, ha="right")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, frameon=False, fontsize=9, labelcolor=INK2)
plt.savefig(os.path.join(S, f"sun_in_camera_view_{TAG}.png"), dpi=150, bbox_inches="tight", facecolor=SURF)

# ---- B: direct sun energy on the doorbell per day ----
keys = ["Jun 21 (summer)", "May 1 / Aug 12", "Mar 21 / Sep 23 (equinox)", "Feb 5 / Nov 6", "Dec 21 (winter)"]
labels = ["Jun 21", "May 1 /\nAug 12", "Mar 21 /\nSep 23", "Feb 5 /\nNov 6", "Dec 21"]
designs = [("no shade", "No shade"), ("v3", "v3")] if TAG == "v3" else [("no shade", "No shade"), ("v1", "v1"), ("v2", "v2")]
fig, ax = plt.subplots(figsize=(7.6, 4.2), facecolor=SURF); ax.set_facecolor(SURF)
x = np.arange(len(keys)); bw = 0.26 if len(designs) == 3 else 0.36
for i, ((k, lab), col) in enumerate(zip(designs, C)):
    vals = [F[k][d]["Wh_on_doorbell"] for d in keys]
    bars = ax.bar(x + (i - (len(designs) - 1) / 2) * (bw + 0.02), vals, bw, color=col, label=lab, edgecolor=SURF, linewidth=1)
    if lab == SHADE:
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.6, f"{v:.1f}", ha="center", fontsize=8, color=INK)
ax.set_xticks(x, labels)
ax.set_ylabel("Direct sun on the doorbell (Wh per day)")
ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.legend(frameon=False, ncol=3, loc="upper left", bbox_to_anchor=(0, 1.13), labelcolor=INK2)
ax.text(1.0, 1.10, "clear sky, " + SUB.split(", doorbell")[0], transform=ax.transAxes, ha="right", color=INK2, fontsize=9)
plt.savefig(os.path.join(S, f"sun_energy_by_day_{TAG}.png"), dpi=150, bbox_inches="tight", facecolor=SURF)
print("ok")

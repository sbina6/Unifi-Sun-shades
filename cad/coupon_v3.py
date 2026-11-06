"""v3 fit-test coupon: 62.00 X/Y frame + 56.60 Z tower (scale), plus the two fits v3 relies on:
sliding M3 nut channels 5.6 / 5.7 / 5.8 AF and M3 clearance holes 3.3 / 3.4 / 3.5. Axis-aligned."""
import os, sys
from build123d import *
out = sys.argv[1]
frame = extrude(Rectangle(62, 62), 2.5) - extrude(Rectangle(54, 54), 2.5)
tower = Pos(-28, -28, 0) * extrude(Rectangle(6, 6), 56.6)
block = Pos(8, -27, 0) * extrude(Rectangle(40, 8), 6.0)          # sits on the bottom bar
c = frame + tower + block
for i, af in enumerate((5.6, 5.7, 5.8)):
    x = -4 + i * 12
    c -= Pos(x, -27, 6.0 - 2.6) * extrude(Rectangle(af, 8.2), 2.6)    # nut channel, open at both ends and top
    c -= Pos(x, -27, 0) * extrude(Circle((3.3 + 0.1 * i) / 2), 6.0)  # clearance hole through
c = c.solids().sort_by(SortBy.VOLUME)[-1] if len(c.solids()) > 1 else c
export_brep(c, os.path.join(out, "coupon.brep"))
export_step(c, os.path.join(out, "fit_test_coupon_v3.step"))
print("coupon vol", round(c.volume, 1))

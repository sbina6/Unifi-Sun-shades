"""Islamic geometric patterns for the sunshade's side walls (2D, shapely only).

Each pattern takes `reg` (the polygon the pattern must stay inside, in the side wall's (z, y) plane)
and `rib` (bar width, mm) and returns WINDOW polygons: the areas where the shell shows through the
0.6 mm raised relief. Relief = side region minus windows, so every bar has the same width: each cell
of a tiling that covers the plane is shrunk by rib/2.

  khatam    8-point stars touching tip to tip, with 4-point diamonds between them (square grid)
  hexstar   6-point stars (hexagrams) touching tip to tip, curved triangles between them
  rosette   overlapping circles on a triangular grid (flower of life): petals and curved triangles
  octstar   octagons and squares (4.8.8) with an 8-point star island inside each octagon
  smooth    no relief
"""
import math
from shapely.geometry import Polygon, box as sbox
from shapely.ops import unary_union, polygonize
from shapely import affinity

R2 = math.sqrt(2.0)


def _ngon(r, n, rot_deg):
    return Polygon([(r * math.cos(math.radians(rot_deg + 360.0 * k / n)),
                     r * math.sin(math.radians(rot_deg + 360.0 * k / n))) for k in range(n)])


def star8(r, k=0.55):
    """Eight-point star: tips (radius r) on the axes and the diagonals, notches at radius k*r."""
    pts = []
    for m in range(16):
        a = math.radians(22.5 * m)
        rr = r if m % 2 == 0 else k * r
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return Polygon(pts)


def star6(r):
    """Hexagram, tips (radius r) at 30, 90, 150, ... degrees."""
    return unary_union([_ngon(r, 3, 90), _ngon(r, 3, 30)])


def _at(g, x, y):
    return affinity.translate(g, x, y)


def _finish(cells, reg, rib, join=2, amin=2.5):
    """Shrink every cell by rib/2 and keep the ones fully inside reg."""
    out, big = [], reg.buffer(1e-6)
    for c in cells:
        w = c.buffer(-rib / 2.0, join_style=join)
        for g in getattr(w, "geoms", [w]):
            if g.is_empty or g.area < amin:
                continue
            if big.contains(g):
                out.append(g)
    return out


def khatam(reg, rib, s=12.0):
    cx, cy = reg.centroid.x, reg.centroid.y
    x0, y0, x1, y1 = reg.bounds
    ni, nj = int((x1 - x0) / s) + 3, int((y1 - y0) / s) + 3
    st = star8(s / 2.0)
    stars = {(i, j): _at(st, cx + i * s, cy + j * s) for i in range(-ni, ni + 1) for j in range(-nj, nj + 1)}
    cells = list(stars.values())
    for i in range(-ni, ni):
        for j in range(-nj, nj):
            sq = sbox(cx + i * s, cy + j * s, cx + (i + 1) * s, cy + (j + 1) * s)
            g = sq.difference(unary_union([stars[(i, j)], stars[(i + 1, j)], stars[(i, j + 1)], stars[(i + 1, j + 1)]]))
            cells += list(getattr(g, "geoms", [g]))
    return _finish(cells, reg, rib)


def hexstar(reg, rib, r=7.0):
    cx, cy = reg.centroid.x, reg.centroid.y
    x0, y0, x1, y1 = reg.bounds
    a1, a2 = (math.sqrt(3) * r, r), (0.0, 2 * r)
    n = int(max(x1 - x0, y1 - y0) / r) + 4
    pts = {}
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = cx + i * a1[0] + j * a2[0], cy + i * a1[1] + j * a2[1]
            if x0 - 3 * r < x < x1 + 3 * r and y0 - 3 * r < y < y1 + 3 * r:
                pts[(i, j)] = (x, y)
    st = star6(r)
    stars = {k: _at(st, *p) for k, p in pts.items()}
    cells = list(stars.values())
    for (i, j), p in pts.items():
        for tri in (((i, j), (i + 1, j), (i, j + 1)), ((i + 1, j), (i, j + 1), (i + 1, j + 1))):
            if all(k in pts for k in tri):
                g = Polygon([pts[k] for k in tri]).difference(unary_union([stars[k] for k in tri]))
                cells += list(getattr(g, "geoms", [g]))
    return _finish(cells, reg, rib)


def rosette(reg, rib, d=12.0, k=0.8, amin=8.0):
    """Circles of radius k*d on a triangular grid of spacing d: neighbours overlap in petals, the
    rest of each circle is a six-lobed rosette, and curved triangles fill the gaps."""
    from shapely.geometry import Point
    cx, cy = reg.centroid.x, reg.centroid.y
    x0, y0, x1, y1 = reg.bounds
    n = int(max(x1 - x0, y1 - y0) / d) + 4
    rings = []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = cx + i * d + j * d / 2.0, cy + j * d * math.sqrt(3) / 2.0
            if x0 - 2 * d < x < x1 + 2 * d and y0 - 2 * d < y < y1 + 2 * d:
                rings.append(Point(x, y).buffer(k * d, 48).exterior)
    cells = list(polygonize(unary_union(rings)))
    return _finish(cells, reg, rib, join=1, amin=amin)


def octstar(reg, rib, s=13.0):
    cx, cy = reg.centroid.x, reg.centroid.y
    x0, y0, x1, y1 = reg.bounds
    ni, nj = int((x1 - x0) / s) + 3, int((y1 - y0) / s) + 3
    rc = (s / 2.0) / math.cos(math.radians(22.5))
    octa = _ngon(rc, 8, 22.5)
    island = star8(0.30 * s, 0.5)
    dia = _ngon(s * (1 - 1 / R2), 4, 0)
    wins = []
    for i in range(-ni, ni + 1):
        for j in range(-nj, nj + 1):
            w = _at(octa, cx + i * s, cy + j * s).buffer(-rib / 2.0, join_style=2).difference(_at(island, cx + i * s, cy + j * s))
            wins.append(w)
            wins.append(_at(dia, cx + (i + .5) * s, cy + (j + .5) * s).buffer(-rib / 2.0, join_style=2))
    out, big = [], reg.buffer(1e-6)
    for w in wins:
        for g in getattr(w, "geoms", [w]):
            if not g.is_empty and g.area > 2.5 and big.contains(g):
                out.append(g)
    return out


def smooth(reg, rib):
    return None


PATTERNS = {"khatam": khatam, "hexstar": hexstar, "rosette": rosette, "octstar": octstar, "smooth": smooth}
LABELS = {"khatam": "8-point star", "hexstar": "6-point star", "rosette": "Rosette", "octstar": "Octagon and star", "smooth": "Smooth"}

"""Islamic geometric patterns for the sunshade's side walls (2D, shapely only).

Each pattern takes `reg` (the polygon the pattern must stay inside, in the side wall's (z, y) plane)
and `rib` (bar width, mm) and returns WINDOW polygons: the areas where the shell shows through the
0.6 mm raised relief. Relief = side region minus windows, so every bar has the same width: each cell
of a tiling that covers the plane is shrunk by rib/2.

  khatam    8-point stars touching tip to tip, with 4-point diamonds between them (square grid)
  hexstar   6-point stars (hexagrams) touching tip to tip, curved triangles between them
  rosette   overlapping circles on a triangular grid (flower of life): petals and curved triangles
  octstar   octagons and squares (4.8.8) with an 8-point star island inside each octagon
  dodecastar 12-point stars touching tip to tip, with curved triangles between them
  arcade    a row of pointed arches (the mihrab / arcade profile)
  mashrabiya circles and diamonds on a square grid, like a turned-wood screen
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


def _fit(g, reg, big, amin=2.5, clip_min=9.0):
    """Windows inside reg are kept whole. Ones that run off the edge are CLIPPED to reg, so the pattern
    fills the whole face and ends at the frame; slivers under about 0.9 mm wide are dropped."""
    if g.is_empty:
        return []
    if big.contains(g):
        return [g] if g.area >= amin else []
    c = g.intersection(reg)
    if c.is_empty:
        return []
    c = c.buffer(-0.45, join_style=2).buffer(0.45, join_style=2)
    return [q for q in getattr(c, "geoms", [c]) if q.geom_type == "Polygon" and q.area >= clip_min]


def _finish(cells, reg, rib, join=2, amin=2.5):
    """Shrink every cell by rib/2 and keep (or clip) the ones that fall in reg."""
    out, big = [], reg.buffer(1e-6)
    for c in cells:
        w = c.buffer(-rib / 2.0, join_style=join)
        for g in getattr(w, "geoms", [w]):
            out += _fit(g, reg, big, amin)
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
            out += _fit(g, reg, big)
    return out


def star12(r, k=0.62):
    """Twelve-point star: tips (radius r) every 30 degrees from 0, notches at radius k*r."""
    pts = []
    for m in range(24):
        a = math.radians(15.0 * m)
        rr = r if m % 2 == 0 else k * r
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return Polygon(pts)


def dodecastar(reg, rib, r=7.0):
    """12-point stars on a triangular grid, tips touching along the grid directions."""
    cx, cy = reg.centroid.x, reg.centroid.y
    x0, y0, x1, y1 = reg.bounds
    a1, a2 = (2 * r, 0.0), (r, math.sqrt(3) * r)
    n = int(max(x1 - x0, y1 - y0) / r) + 4
    pts = {}
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = cx + i * a1[0] + j * a2[0], cy + i * a1[1] + j * a2[1]
            if x0 - 3 * r < x < x1 + 3 * r and y0 - 3 * r < y < y1 + 3 * r:
                pts[(i, j)] = (x, y)
    st = star12(r)
    stars = {k: _at(st, *p) for k, p in pts.items()}
    cells = list(stars.values())
    for (i, j), p in pts.items():
        for tri in (((i, j), (i + 1, j), (i, j + 1)), ((i + 1, j), (i, j + 1), (i + 1, j + 1))):
            if all(k in pts for k in tri):
                g = Polygon([pts[k] for k in tri]).difference(unary_union([stars[k] for k in tri]))
                cells += list(getattr(g, "geoms", [g]))
    return _finish(cells, reg, rib)


def arcade(reg, rib, w=11.0, spring=7.0):
    """A row of pointed arches along the wall (x = distance from the wall, y = along it), points outward.
    Each cell is w wide; neighbours share a bar of width rib."""
    from shapely.geometry import Point
    x0, y0, x1, y1 = reg.bounds
    n0 = x0 + 0.5
    ns = n0 + spring
    cells = []
    k = int((y1 - y0) / w)
    ya = (y0 + y1) / 2 - k * w / 2
    for i in range(k):
        yc = ya + (i + 0.5) * w
        c1 = Point(ns, yc + w / 2).buffer(w, 48)
        c2 = Point(ns, yc - w / 2).buffer(w, 48)
        point = c1.intersection(c2).intersection(sbox(ns, yc - w / 2, ns + w, yc + w / 2))
        cells.append(unary_union([sbox(n0, yc - w / 2, ns, yc + w / 2), point]))
    wins = _finish(cells, reg, rib)
    big = reg.buffer(1e-6)
    tip = ns + 0.866 * w
    for i in range(k):                                # a small round window above every arch, where the face is tall enough
        yc = ya + (i + 0.5) * w
        wins += _fit(Point(tip + rib + 3.0, yc).buffer(2.8, 24), reg, big, 4.0)
    return wins


def mashrabiya(reg, rib, p=10.0, rc=3.2, dd=2.6):
    """Circles on a square grid with a small diamond at the centre of every cell."""
    from shapely.geometry import Point
    cx, cy = reg.centroid.x, reg.centroid.y
    x0, y0, x1, y1 = reg.bounds
    ni, nj = int((x1 - x0) / p) + 3, int((y1 - y0) / p) + 3
    dia = _ngon(dd, 4, 0)
    wins, big = [], reg.buffer(1e-6)
    for i in range(-ni, ni + 1):
        for j in range(-nj, nj + 1):
            for g in (Point(cx + i * p, cy + j * p).buffer(rc, 32), _at(dia, cx + (i + .5) * p, cy + (j + .5) * p)):
                wins += _fit(g, reg, big, 4.0)
    return wins


def smooth(reg, rib):
    return None


PATTERNS = {"khatam": khatam, "hexstar": hexstar, "dodecastar": dodecastar, "rosette": rosette, "octstar": octstar, "arcade": arcade, "mashrabiya": mashrabiya, "smooth": smooth}
LABELS = {"khatam": "8-point star", "hexstar": "6-point star", "dodecastar": "12-point star", "rosette": "Rosette", "octstar": "Octagon and star", "arcade": "Pointed arches", "mashrabiya": "Mashrabiya", "smooth": "Smooth"}

"""Sun-path study for a doorbell on a wall facing FACING_DEG (compass, true north), Doha, Qatar.

Model frame (same as sunshade.py): x to the right when you stand in front of the wall looking
at it, y up, z out of the wall. Standing in front of a wall that faces 150 deg, your right is
compass 60 deg (ENE) and your left is 240 deg (WSW).
"""
import math
import numpy as np

LAT, LON, TZ = 25.2854, 51.5310, 3.0       # Doha, UTC+3, no DST
FACING_DEG = 150.0


def sun_position(doy, hour_local, lat=LAT, lon=LON, tz=TZ):
    """NOAA solar position (elevation deg, azimuth deg clockwise from true north)."""
    g = 2 * math.pi / 365 * (doy - 1 + (hour_local - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    tst = hour_local * 60 + eqt + 4 * lon - 60 * tz
    ha = math.radians(tst / 4 - 180)
    la = math.radians(lat)
    cz = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    zen = math.acos(max(-1, min(1, cz)))
    el = 90 - math.degrees(zen)
    az = math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(la) - math.tan(decl) * math.cos(la))) + 180
    return el, az % 360


def to_model(el, az, facing=FACING_DEG):
    """Unit sun direction in the model frame."""
    e, a = math.radians(el), math.radians(az)
    east, north, up = math.cos(e) * math.sin(a), math.cos(e) * math.cos(a), math.sin(e)
    f = math.radians(facing)
    n = np.array([math.sin(f), math.cos(f)])              # wall normal (E, N)
    r = np.array([math.sin(f - math.pi / 2), math.cos(f - math.pi / 2)])  # viewer's right = facing - 90
    return np.array([east * r[0] + north * r[1], up, east * n[0] + north * n[1]])


DAYS = {"Jun 21 (summer)": 172, "May 1 / Aug 12": 121, "Mar 21 / Sep 23 (equinox)": 80,
        "Feb 5 / Nov 6": 36, "Dec 21 (winter)": 355}


def day_track(doy, step_min=5, facing=FACING_DEG):
    out = []
    for m in range(0, 24 * 60, step_min):
        h = m / 60
        el, az = sun_position(doy, h)
        if el <= 0.5:
            continue
        d = to_model(el, az, facing)
        out.append(dict(h=h, el=el, az=az, d=d, front=d[2] > 0))
    return out

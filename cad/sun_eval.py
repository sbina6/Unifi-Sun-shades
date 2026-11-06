"""Ray-trace a shade design against the sun path (sunpath.py).

For each sun position: direct-beam energy on the doorbell's exposed faces (front, top, sides),
whether the lens is shaded, and whether the sun is inside the camera image.
Numpy Moller-Trumbore (no rtree/embree). Days run in a 'spawn' pool.

usage: python cad/sun_eval.py <hood.brep or 'none'> <out.json> [facing_deg]
"""
import json, math, os, sys, multiprocessing as mp
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FISH = np.array([1.91883021e+01, 5.26733149e-02, -7.27681727e-04])


def in_image(v, margin_px=0.0):
    """v: direction(s) from the lens (model frame, optical axis +z). True if it lands in the 1920x2560 frame."""
    v = np.atleast_2d(v)
    n = np.linalg.norm(v, axis=1)
    th = np.degrees(np.arccos(np.clip(v[:, 2] / n, -1, 1)))
    r = FISH[0] * th + FISH[1] * th ** 2 + FISH[2] * th ** 3
    ph = np.arctan2(v[:, 1], v[:, 0])
    u, w = r * np.cos(ph), r * np.sin(ph)
    return (v[:, 2] > 0) & (np.abs(u) < 960 - margin_px) & (np.abs(w) < 1280 - margin_px)


def mesh_tris(path_brep, tol=0.1):
    from build123d import import_brep, export_stl
    import trimesh
    tmp = f"/tmp/_se_{os.getpid()}_{os.path.basename(path_brep)}.stl"
    export_stl(import_brep(path_brep), tmp, tolerance=tol, angular_tolerance=0.3)
    m = trimesh.load(tmp)
    return m


def occluded(P, d, V0, E1, E2, chunk=400):
    """P (n,3) origins, d (3,) direction, triangles as V0/E1/E2 (t,3). Returns bool (n,)."""
    out = np.zeros(len(P), bool)
    h = np.cross(d, E2)                    # (t,3)
    a = np.einsum("ij,ij->i", E1, h)       # (t,)
    ok = np.abs(a) > 1e-9
    V0, E1, E2, h, a = V0[ok], E1[ok], E2[ok], h[ok], a[ok]
    f = 1.0 / a
    for s in range(0, len(P), chunk):
        p = P[s:s + chunk]
        sv = p[:, None, :] - V0[None]      # (c,t,3)
        u = f[None] * np.einsum("ctk,tk->ct", sv, h)
        q = np.cross(sv, E1[None])
        v = f[None] * np.einsum("ctk,k->ct", q, d)
        t = f[None] * np.einsum("ctk,tk->ct", q, E2)
        hit = (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4)
        out[s:s + chunk] = hit.any(1)
    return out


def device_samples(dev_brep, n_target=1800, seed=2):
    import trimesh
    m = mesh_tris(dev_brep, tol=0.1)
    pts, fi = trimesh.sample.sample_surface_even(m, n_target * 2, seed=seed)
    nrm = m.face_normals[fi]
    keep = nrm[:, 2] > -0.5                # drop the back (against the plate)
    pts, nrm = pts[keep], nrm[keep]
    w = m.area_faces[m.face_normals[:, 2] > -0.5].sum() / len(pts)
    return pts + nrm * 0.05, nrm, w


def dni(el):
    """Clear-sky beam irradiance, W/m2 (Meinel air-mass model, hazy desert factor 0.7)."""
    am = 1 / max(math.sin(math.radians(el)), 0.02)
    return 1353 * 0.7 ** (am ** 0.678)


def eval_day(args):
    hood_brep, doy, facing, step = args
    from sunpath import day_track
    P = json.load(open(os.path.join(HERE, "..", "v1", "params.json")))
    lens = np.array(P["LENS"])
    pts, nrm, w = device_samples(os.path.join(HERE, "..", "v1", "device.brep"))
    if hood_brep != "none":
        m = mesh_tris(hood_brep)
        tri = m.vertices[m.faces]
        tri = tri[tri[:, :, 2].max(1) > P["T_FL"] + 0.05]   # flange behind the body can't shade it
        V0, E1, E2 = tri[:, 0], tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    rows = []
    for s in day_track(doy, step, facing):
        d = s["d"]
        I = dni(s["el"])
        cos = nrm @ d
        lit_mask = cos > 0
        if hood_brep != "none" and lit_mask.any():
            occ = occluded(pts[lit_mask], d, V0, E1, E2)
            lit = np.zeros(len(pts), bool); lit[np.where(lit_mask)[0][~occ]] = True
            lens_sh = bool(occluded(lens[None], d, V0, E1, E2)[0])
        else:
            lit = lit_mask
            lens_sh = False
        lens_sun = bool(d[2] > 0 and not lens_sh)
        rows.append(dict(h=round(s["h"], 3), el=round(s["el"], 2), az=round(s["az"], 1),
                         rel=[round(float(x), 4) for x in d],
                         watts=float((cos[lit] * w).sum() * 1e-6 * I),           # W on the doorbell
                         watts_bare=float((cos[lit_mask] * w).sum() * 1e-6 * I),
                         lens_in_sun=lens_sun, sun_in_image=bool(in_image(d)[0]),
                         lit_area_frac=float(lit.mean())))
    return doy, rows


def evaluate(hood_brep, facing, days, step=10):
    ctx = mp.get_context("spawn")
    with ctx.Pool(min(4, len(days))) as pool:
        res = pool.map(eval_day, [(hood_brep, d, facing, step) for d in days.values()])
    out = {}
    for (name, doy), (_, rows) in zip(days.items(), res):
        hrs = step / 60
        out[name] = dict(
            doy=doy,
            Wh_on_doorbell=round(sum(r["watts"] for r in rows) * hrs, 2),
            Wh_bare=round(sum(r["watts_bare"] for r in rows) * hrs, 2),
            peak_W=round(max([r["watts"] for r in rows] + [0]), 2),
            lens_sun_hours=round(sum(r["lens_in_sun"] for r in rows) * hrs, 2),
            sun_in_image_hours=round(sum(r["sun_in_image"] for r in rows) * hrs, 2),
            lens_sun_outside_image_hours=round(sum(r["lens_in_sun"] and not r["sun_in_image"] for r in rows) * hrs, 2),
            rows=rows)
    return out


if __name__ == "__main__":
    from sunpath import DAYS
    hood = sys.argv[1]
    facing = float(sys.argv[3]) if len(sys.argv) > 3 else 150.0
    res = evaluate(hood, facing, DAYS)
    json.dump(res, open(sys.argv[2], "w"))
    for k, v in res.items():
        print(f"{k:28s} Wh {v['Wh_on_doorbell']:6.2f} (bare {v['Wh_bare']:6.2f})  peak {v['peak_W']:5.2f} W  "
              f"lens-sun {v['lens_sun_hours']:4.2f} h  sun-in-image {v['sun_in_image_hours']:4.2f} h  "
              f"lens-sun-avoidable {v['lens_sun_outside_image_hours']:4.2f} h")

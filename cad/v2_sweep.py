"""Compare v2 reach options against the Doha sun path for a 150 deg wall."""
import json, os, sys, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sun_eval import evaluate, in_image
from sunpath import DAYS
SCR = sys.argv[1]
FACING = float(sys.argv[2]) if len(sys.argv) > 2 else 150.0
P = json.load(open(os.path.join(HERE, "..", "v1", "params.json")))

def fov_frac(brep):
    import trimesh
    from build123d import import_brep, export_stl
    export_stl(import_brep(brep), brep + ".stl", tolerance=0.05)
    m = trimesh.load(brep + ".stl")
    pts, _ = trimesh.sample.sample_surface(m, 1_500_000, seed=1)
    return float(in_image(pts - np.array(P["LENS"])).mean() * 100)   # % of surface samples in view

def summarise(name, brep):
    res = evaluate(brep, FACING, DAYS)
    row = {"design": name}
    for k, v in res.items():
        row[k] = (v["Wh_on_doorbell"], v["lens_sun_hours"], v["lens_sun_outside_image_hours"], v["sun_in_image_hours"])
    if brep != "none":
        row["mass_g"] = None
    return row, res

if __name__ == "__main__":
    rows = []
    designs = [("no shade", "none", None), ("v1", os.path.join(HERE, "..", "v1", "hood.brep"), None)]
    for el, er in [(20, 20), (30, 30), (40, 40), (60, 60), (10, 40), (40, 10)]:
        d = os.path.join(SCR, f"v2_{el}_{er}")
        if not os.path.exists(os.path.join(d, "hood.brep")):
            out = subprocess.run([sys.executable, os.path.join(HERE, "sunshade_v2.py"), str(el), str(er), d],
                                 capture_output=True, text=True).stdout
        designs.append((f"v2 reach L{el}/R{er}", os.path.join(d, "hood.brep"), d))
    allres = {}
    for name, brep, d in designs:
        row, res = summarise(name, brep)
        if brep != "none":
            from build123d import import_brep
            row["mass_g"] = round(import_brep(brep).volume / 1000 * 1.17, 1)
            row["surface_in_view_%"] = round(fov_frac(brep), 4)
        rows.append(row); allres[name] = res
        print(json.dumps(row))
    json.dump(dict(rows=rows), open(os.path.join(SCR, f"sweep_{int(FACING)}.json"), "w"), indent=1)
    json.dump(allres, open(os.path.join(SCR, f"sweep_{int(FACING)}_full.json"), "w"))

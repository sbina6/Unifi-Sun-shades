"""Sensitivity of v2 to the wall bearing (compass error / magnetic vs true north)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sun_eval import evaluate
from sunpath import DAYS
if __name__ == "__main__":
    out = {}
    for f in map(float, sys.argv[2:]):
        r = evaluate(sys.argv[1], f, DAYS)
        out[f] = {k: dict(Wh=v["Wh_on_doorbell"], Wh_bare=v["Wh_bare"], avoidable_lens_h=v["lens_sun_outside_image_hours"]) for k, v in r.items()}
        print(f, {k[:6]: (v["Wh"], v["Wh_bare"], v["avoidable_lens_h"]) for k, v in out[f].items()}, flush=True)

"""protocols.json (from compare.py) -> site/protocols.json: compact rows for the page and make_bundle.py,
ranked by sensor-category breadth then named signals, with each decoder's key table."""
import json
import os
import re

MS = "../dudu/ms-src/sources"
SENSOR = ["door", "climate", "radar", "tpms", "speed_rpm", "odometer_trip", "fuel_consumption", "temperature",
          "battery_electric", "lights", "warnings", "steering_angle", "time_compass", "camera_360"]


def keys(dec):
    """canbox key -> FYT key id pairs: the first int[][] table of pairs in the decoder class."""
    p = os.path.join(MS, dec + ".java")
    if not os.path.exists(p):
        return []
    s = open(p, encoding="utf-8", errors="replace").read()
    m = re.search(r"int\[\]\[\] \w+ = \{((?:new int\[\]\{-?\d+, -?\d+\}(?:, )?)+)\};", s)
    return [[int(a), int(b)] for a, b in re.findall(r"\{(-?\d+), (-?\d+)\}", m.group(1))] if m else []


P = json.load(open("protocols.json"))
out = []
for i, p in enumerate(P):
    sig = []
    for s in p["signals"]:
        d = s["decode"][0] if s["decode"] else {"value": "", "when": []}
        sig.append([s["code"], s["name"], s["category"], s["frames"],
                    d["value"].replace("Spanned.SPAN_PRIORITY", "0xFF0000")[:140], " & ".join(d["when"])[:180]])
    out.append({"i": i, "d": p["decoder"], "p": p["parser"], "m": p["makers"],
                "pr": [[x["company"], x["car"], x["canbox"], x["id"]] for x in p["profiles"]],
                "b": sum(1 for c in SENSOR if p["categories"].get(c)), "n": p["signals_named"], "t": p["signals_total"],
                "c": p["categories"], "f": p["frames"], "s": sig, "k": keys(p["decoder"])})
out.sort(key=lambda p: (p["b"], p["n"]), reverse=True)
os.makedirs("site", exist_ok=True)
json.dump(out, open("site/protocols.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(out), "protocols")

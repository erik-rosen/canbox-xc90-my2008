"""Join decoder (com.syu.ms) and parser (com.syu.canbus) per profile; rank protocols by signals.

A "signal" is a code the decoder writes from frame bytes. Its name comes from the parser
(U_* constants), the shared door slots 0-5 or the shared climate slots (FinalCanbus U_AIR_*).
"""
import collections
import json
import os
import re
import sqlite3

ROOT = os.path.dirname(os.path.abspath(__file__))
sys_path = os.path.join(ROOT, "inventory.py")
import importlib.util
spec_ = importlib.util.spec_from_file_location("inventory", sys_path)
inv_mod = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(inv_mod)
category = inv_mod.category

FINAL = open(os.path.join(ROOT, "jadx-canbus/sources/com/syu/module/canbus/FinalCanbus.java")).read()
AIR = {int(v): k for k, v in re.findall(r"public static final int (U_AIR_[A-Z0-9_]+) = (\d+);", FINAL)
       if not k.endswith(("_BEGIN", "_END"))}
DOOR = {0: "U_DOOR_ENGINE", 1: "U_DOOR_FL", 2: "U_DOOR_FR", 3: "U_DOOR_RL", 4: "U_DOOR_RR", 5: "U_DOOR_BACK"}
GLOBAL = {1031: "G_VEHICLE_SPEED_TO_MAIN(?)", 1032: "G_1032(?)"}


def parser_names():
    out = {}
    for path in __import__("glob").glob(os.path.join(ROOT, "jadx-canbus/sources/com/syu/module/canbus/Callback_*.java")):
        name = os.path.basename(path)[:-5]
        src = open(path, encoding="utf-8", errors="replace").read()
        consts = {}
        for k, v in re.findall(r"public static final int (U_[A-Z0-9_]+) = (\d+);", src):
            if k.endswith(("_BEGIN", "_END")) or k in ("U_CNT_MAX", "U_MAX"):
                continue
            consts.setdefault(int(v), k)
        out[name] = {"names": consts, "door": "DoorHelper" in src, "air": "AirHelper" in src}
    return out


def main():
    spec = json.load(open(os.path.join(ROOT, "spec-ms.json")))
    parsers = parser_names()
    dec = dict(l.rstrip("\n").split("\t") for l in open(os.path.join(ROOT, "resolved-ms.tsv")))
    par = {k: v.split("/")[-1] for k, v in (l.rstrip("\n").split("\t") for l in open(os.path.join(ROOT, "resolved-bytecode.tsv")))}
    db = sqlite3.connect(os.path.join(ROOT, "pu/assets/canbus.db"))
    rows = db.execute("""select b.id_value, c.canbus_company_name_en, s.canbus_carset_name_en, t.canbus_cartype_en, b.canbus_canbox_en
                         from canbus_canbox b join canbus_company c on c.id=b.company_id join canbus_carset s on s.id=b.carset_id
                         join canbus_cartype t on t.id=b.cartype_id where b.id_value>0""").fetchall()
    pairs = collections.defaultdict(list)
    for idv, comp, carset, cartype, canbox in rows:
        pairs[(dec.get(str(idv)), par.get(str(idv)))].append(
            {"id": idv, "company": comp, "car": f"{carset} {cartype}", "canbox": canbox})

    protocols = []
    for (d, p), profs in pairs.items():
        if not d or not p or p == "Callback_0000_null":
            continue
        writes = spec.get(d, {}).get("writes", [])
        pinfo = parsers.get(p, {"names": {}, "door": False, "air": False})
        sig = {}
        for w in writes:
            c = w["code"]
            nm = pinfo["names"].get(c) or (DOOR.get(c) if c <= 5 else None) or (AIR.get(c) if 10 <= c <= 96 else None) or GLOBAL.get(c)
            if nm is None:
                nm = f"code_{c}"
            s = sig.setdefault(c, {"code": c, "name": nm, "category": category(nm) if not nm.startswith("code_") else "unnamed",
                                    "frames": set(), "decode": []})
            cmd, sub, pos = w["frame"]
            if cmd is not None:
                s["frames"].add(f"0x{cmd:02X}" + (f"/0x{sub:02X}" if sub is not None else ""))
            if len(s["decode"]) < 3:
                s["decode"].append({"value": w["value"], "when": w["when"][-3:]})
        for s in sig.values():
            s["frames"] = sorted(s["frames"])
        named = [s for s in sig.values() if s["category"] != "unnamed"]
        cats = collections.Counter(s["category"] for s in named)
        protocols.append({"decoder": d, "parser": p, "profiles": profs,
                          "makers": sorted({x["company"] for x in profs}),
                          "signals_total": len(sig), "signals_named": len(named), "categories": dict(cats),
                          "frames": sorted({f for s in sig.values() for f in s["frames"]}),
                          "signals": sorted(sig.values(), key=lambda s: s["code"])})
    json.dump(protocols, open(os.path.join(ROOT, "protocols.json"), "w"), ensure_ascii=False)

    SENSOR = ["door", "climate", "radar", "tpms", "speed_rpm", "odometer_trip", "fuel_consumption", "temperature",
              "battery_electric", "lights", "warnings", "steering_angle", "time_compass", "camera_360"]
    def breadth(p):
        return sum(1 for c in SENSOR if p["categories"].get(c))
    print(f"{len(protocols)} decoder+parser pairs")
    print("\nTop 20 by sensor-category breadth, then named signals:")
    for p in sorted(protocols, key=lambda p: (breadth(p), p["signals_named"]), reverse=True)[:20]:
        print(f"  {p['parser'][9:]:34s} {p['decoder']:16s} breadth={breadth(p):2d} named={p['signals_named']:4d}"
              f" total={p['signals_total']:4d} frames={len(p['frames']):3d} {','.join(p['makers'])[:30]}")
    print("\nThe protocols the canbox firmware can emulate, and the Volvo ones:")
    for pid in (51, 160, 131232, 20, 112, 589841, 15466950, 7930310, 2490812, 5046725):
        for p in protocols:
            if any(x["id"] == pid for x in p["profiles"]):
                pr = next(x for x in p["profiles"] if x["id"] == pid)
                print(f"  {pid:9d} {pr['company']:11s} {pr['car'][:22]:22s} {pr['canbox'][:14]:14s} -> {p['parser'][9:]:30s}"
                      f" breadth={breadth(p):2d} named={p['signals_named']:3d} {dict(sorted(p['categories'].items()))}")


if __name__ == "__main__":
    main()

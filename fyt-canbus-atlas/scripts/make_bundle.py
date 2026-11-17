"""Forum bundle: fyt-canbus-protocols.md (post), fyt-canbus-profiles.csv (every settings entry),
fyt-canbus-spec.json (every signal of every protocol). Profile ids are not unique in canbus.db
(5,108 entries, 5,068 ids), so every entry is kept and shared ids prefer the Raise/HiWorld name."""
import collections
import csv
import json
import sqlite3
import sys

OUT = sys.argv[1]
P = json.load(open("site/protocols.json"))
for k, p in enumerate(P):
    p["rank"] = k + 1
SENSOR = ["door", "climate", "radar", "tpms", "speed_rpm", "odometer_trip", "fuel_consumption", "temperature",
          "battery_electric", "lights", "warnings", "steering_angle", "time_compass", "camera_360"]
LABEL = {"door": "doors", "climate": "climate", "radar": "radar", "tpms": "TPMS", "speed_rpm": "speed/rpm",
         "odometer_trip": "trip", "fuel_consumption": "fuel", "temperature": "temperature", "battery_electric": "battery",
         "lights": "lights", "warnings": "warnings", "steering_angle": "steering angle", "time_compass": "time",
         "camera_360": "camera", "carset": "settings", "audio_media": "media", "carinfo_raw": "car info (raw)",
         "other": "other", "unnamed": "unnamed"}
PREFER = {"RZC(Raise)": 0, "HIWORLD": 1}

db = sqlite3.connect("pu/assets/canbus.db")
rows = db.execute("""select b.id_value, c.canbus_company_name_en, s.canbus_carset_name_en, t.canbus_cartype_en, b.canbus_canbox_en
  from canbus_canbox b join canbus_company c on c.id=b.company_id join canbus_carset s on s.id=b.carset_id
  join canbus_cartype t on t.id=b.cartype_id where b.id_value>0 order by b.id_value, c.id""").fetchall()
entries = collections.defaultdict(list)
for idv, comp, carset, cartype, canbox in rows:
    entries[idv].append((comp, carset, cartype, canbox))
dec = dict(l.rstrip("\n").split("\t") for l in open("resolved-ms.tsv"))
par = {k: v.split("/")[-1] for k, v in (l.rstrip("\n").split("\t") for l in open("resolved-bytecode.tsv"))}
bykey = {(p["d"], p["p"]): p for p in P}


def name(idv):
    """The settings path for an id: Canbox → Cars for → Models for → Config."""
    e = sorted(entries[idv], key=lambda x: PREFER.get(x[0], 9))[0]
    return " → ".join(e)


def generic(p):
    """The least model-specific entry of a protocol: model ALL first, then a Raise/HiWorld name."""
    ids = {x[3] for x in p["pr"]}
    cands = [(idv, e) for idv in ids for e in entries[idv]]
    idv, e = sorted(cands, key=lambda c: (c[1][2] != "ALL", "ALL" not in c[1][3], PREFER.get(c[1][0], 9), c[0]))[0]
    return " → ".join(e), idv


def has(p):
    return ", ".join(LABEL[c] for c in SENSOR if p["c"].get(c))


# 1. every settings entry
with open(f"{OUT}/fyt-canbus-profiles.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["profile_id", "profile_id_hex", "canbus_id", "car_id", "canbox_maker", "cars_for", "model", "config",
                "decoder_class_com.syu.ms", "parser_class_com.syu.canbus", "protocol_rank", "sensor_categories",
                "named_signals", "categories"])
    for idv, comp, carset, cartype, canbox in rows:
        d, pp = dec.get(str(idv)), par.get(str(idv))
        p = bykey.get((d, pp))
        w.writerow([idv, f"0x{idv:08X}", idv & 0xFFFF, idv >> 16, comp, carset, cartype, canbox, d, pp,
                    p["rank"] if p else "", p["b"] if p else 0, p["n"] if p else 0,
                    "; ".join(f"{LABEL.get(c, c)} {n}" for c, n in sorted(p["c"].items())) if p else ""])

# 2. full spec
spec = [{"rank": p["rank"], "decoder": p["d"], "parser": p["p"], "makers": p["m"], "sensor_categories": p["b"],
         "named_signals": p["n"], "codes_written": p["t"], "categories": p["c"], "frames": p["f"],
         "key_table_canbox_to_fyt": p["k"],
         "profiles": [{"id": idv, "settings": [" → ".join(e) for e in entries[idv]]}
                      for idv in sorted({x[3] for x in p["pr"]})],
         "signals": [{"code": s[0], "name": s[1], "category": s[2], "frames": s[3], "value": s[4], "when": s[5]} for s in p["s"]]}
        for p in P]
json.dump({"source": "FYT com.syu.canbus build 2126013012, com.syu.ms and ProtocolUpdate canbus.db (DUDU7, Android 13, UIS7870), decompiled 2026-10",
           "notes": "B[0] = command byte, B[1] = length, B[2].. = data (Raise-style); some makers test B[1] as the command. "
                    "'when' = branch conditions in the decoder. Profile ids are not unique: one id can have several settings names.",
           "protocols": spec}, open(f"{OUT}/fyt-canbus-spec.json", "w"), ensure_ascii=False, indent=1)

# 3. the post
L = []
add = L.append
add("# FYT canbus protocols: every car profile, decoded and ranked\n")
add("I decompiled the canbus apps on an FYT-platform head unit (DUDU7, Android 13, Unisoc UIS7870; FYT `com.syu.canbus` "
    "build 2126013012) to find which canbus profile carries the most signals. Useful if you build or reflash your own canbox, "
    "for example with the open `canbox` firmware that emulates Raise and HiWorld protocols.\n")
add(f"**Short version:** {len(rows):,} settings entries ({len(entries):,} distinct profile ids) from 66 canbox makers reduce to "
    f"{len(P)} distinct protocols. The richest is HiWorld Peugeot/Citroën \"PSA ALL\": 162 signals in 12 sensor categories, "
    "including TPMS, trip computer, lights and warnings. Among Raise protocols, Toyota \"ALL 2013\" is the most complete "
    "(131 signals, with TPMS and a trip computer). Raise VW PQ has 91 signals but no TPMS, lights or clock.\n")
add("## How FYT turns a canbox frame into a value\n")
add("1. The canbox sends UART frames to the MCU (Raise: `2E CMD LEN DATA… CHK`, HiWorld: `5A A5 …`).")
add("2. **`com.syu.ms`** picks a *decoder* class for the selected profile (807 classes, factory `kt.h0(int id)`). "
    "Its `V2(byte[] frame, int offset, int len)` turns bytes into numbered codes with `kt.w0(code, value)`.")
add("3. **`com.syu.canbus`** picks a *parser* class (`Callback_NNNN_<maker>_<car>`, 640 classes, factory "
    "`HandlerCanbus.getCallbackCanbusById`). It names the codes (`U_CUR_SPEED = 109`) and draws the screens.")
add("4. Other apps can read the same codes from module 7 of FYT's `com.syu.ms` binder (`IRemoteToolkit`).\n")
add("A profile id is `carId << 16 | canbusId`: the low 16 bits pick the protocol family, the high 16 bits the car variant. "
    "The names in the settings menu come from `assets/canbus.db` in `ProtocolUpdate.apk`. Codes 0–5 are the doors (hood, FL, "
    "FR, RL, RR, boot), 10–96 the shared climate slots (`U_AIR_*`), 98 and up are per parser.\n")
add("## Top 25 protocols by sensor-category coverage\n")
add("Sensor categories: doors, climate, radar, TPMS, speed/rpm, trip, fuel, temperature, battery, lights, warnings, "
    "steering angle, time, camera. Settings and media are not counted. \"Pick\" is the least model-specific entry "
    "(Canbox → Cars for → Models for → Config).\n")
add("| # | Parser | Pick in canbus settings | Ids | Sensor cats | Signals | Has |")
add("|--:|---|---|--:|--:|--:|---|")
for p in P[:25]:
    st, idv = generic(p)
    add(f"| {p['rank']} | `{p['p'].replace('Callback_', '')}` | {st} (id {idv}) | {len({x[3] for x in p['pr']})} | "
        f"{p['b']} | {p['n']} | {has(p)} |")
add("")
add("## Protocols the open canbox firmware can already frame\n")
add("| Settings entry | Parser | Sensor cats | Signals | Has |")
add("|---|---|--:|--:|---|")
for pid in (51, 160, 20, 112, 589841, 655612):
    p = bykey[(dec[str(pid)], par[str(pid)])]
    add(f"| {name(pid)} (id {pid}) | `{p['p'].replace('Callback_', '')}` | {p['b']} | {p['n']} | {has(p)} |")
add("\nRaise VW MQB and HiWorld MQB are no richer than PQ in this build: doors, climate and speed only.\n")
add("## Volvo XC90 (2004–2013) profiles\n")
add("| Settings entry | Parser | Signals | Has |")
add("|---|---|--:|---|")
for pid in (7930310, 2490812, 15466950, 5046725):
    p = bykey[(dec[str(pid)], par[str(pid)])]
    add(f"| {name(pid)} (id {pid}) | `{p['p'].replace('Callback_', '')}` | {p['n']} | {has(p)} |")
add("\nAll four are thin. Raise VW PQ (id 51) carries more than any Volvo profile.\n")
psa = bykey[(dec["655612"], par["655612"])]
add(f"## Full spec: HiWorld PSA ALL (`{psa['p'].replace('Callback_', '')}`, decoder `{psa['d']}`)\n")
add("Pick **HIWORLD → Peugeot/Citroen → ALL → ALL** (id 655612). The same decoder serves all 57 HiWorld "
    "Peugeot/Citroën/DS/Opel entries.\n")
add("Frames: " + ", ".join(f"`{f}`" for f in psa["f"]) + "\n")
add("`B[0]` is the command byte and `B[2]…` the data. \"When\" is the decoder branch the value is written in.\n")
groups = collections.defaultdict(list)
for s in psa["s"]:
    groups[s[2]].append(s)
for c in [*SENSOR, "carinfo_raw", "carset", "audio_media", "other", "unnamed"]:
    if c not in groups:
        continue
    add(f"### {LABEL.get(c, c)} ({len(groups[c])})\n")
    add("| Code | Name | Frame | Value from bytes | When |")
    add("|--:|---|---|---|---|")
    for s in groups[c]:
        add(f"| {s[0]} | `{s[1]}` | {' '.join(s[3]) or '?'} | `{s[4].replace('|', '¦')}` | `{s[5].replace('|', '¦')}` |")
    add("")
add("## Method and limits\n")
add("- Pulled read-only from the head unit: `/odm/app/190000000_com.syu.canbus`, `com.syu.ms` and `ProtocolUpdate.apk` "
    "(`assets/canbus.db`). Decompiled with jadx.")
add("- The profile → decoder and parser mapping comes from interpreting the Dalvik bytecode of both factory methods for every id. "
    "jadx's Java for `HandlerCanbus` mis-maps 1,008 profiles (switch fall-through from case 452 on), so don't trust the decompiled switch.")
add("- Byte layouts are read from the decoders' `V2()` source. 84 % of writes have their frame identified; the rest are in "
    "helper methods. Names are FYT's own constants; categories are keyword-based and can misfile a few.")
add("- Not covered: key-code names beyond each decoder's key table, head unit → car commands, and whether a particular car "
    "actually puts the data on its CAN bus.")
add("- Attached: `fyt-canbus-profiles.csv` (every settings entry with its decoder, parser and signal counts) and "
    "`fyt-canbus-spec.json` (every signal of every protocol).")
open(f"{OUT}/fyt-canbus-protocols.md", "w").write("\n".join(L) + "\n")
print("entries", len(rows), "ids", len(entries))

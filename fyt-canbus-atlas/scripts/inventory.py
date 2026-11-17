"""Inventory of every car parser in FYT's com.syu.canbus (DUDU7 build 2126013012).

For each Callback_NNNN_<maker>_<car>.java: the named update codes it declares (U_* constants),
whether it hooks the shared door / climate / radar / tyre code ranges, a category per signal,
and which car profiles in ProtocolUpdate's canbus.db select it (id_value & 0xFFFF == NNNN).
Writes inventory.json and prints a summary.
"""
import collections
import glob
import json
import os
import re
import sqlite3

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "jadx-canbus/sources/com/syu")
DB = os.path.join(ROOT, "pu/assets/canbus.db")

CONST = re.compile(r"public static final int (U_[A-Z0-9_]+) = (\d+);")
STRUCT = {"BEGIN", "END", "CNT_MAX", "MAX", "MISC_BEGIN", "MISC_END"}

# keyword -> category; first match wins, so specific words go first
CATS = [
    # settings the head unit can show and change (lock behaviour, lamp delays, units...): not sensor readings
    ("carset", r"CARSET|^SET_|_SET$|_SET_|AUTOLOCK|AUTO_LOCK|UNLOCK|_LOCK|LOCK_|SENSITIVITY|_DELAY|DELAY_|CLOSE_\w*TIME|"
               r"LANGUAGE|_UNIT|UNIT_|_MODE_SET|DAYTIME_RUN|WELCOME|FOLLOW_ME|MIRROR_FOLD|REMOTE_|KEY_UNLOCK|2TIMES"),
    ("audio_media", r"^CD_|_CD_|DISC|TRACK_|RADIO|USB|IPOD|_FM|_AM$|BAND|PRESET|SONG|PLAY|MEDIA|AMP_|_AMP|EQ_|BASS|TREBLE|BALANCE|FADER|VOLUME"),
    ("tpms", r"TIRE|TYRE|TPMS|PRESS(URE)?_(FL|FR|RL|RR)|TIRE_"),
    ("radar", r"RADAR|PARK_(SENSOR|ASSIST)|SONAR|DISTANCE_(FRONT|REAR)"),
    ("door", r"DOOR|TRUNK|HOOD|BONNET|TAIL_?GATE|SUNROOF|WINDOW"),
    ("climate", r"AIR|AC_|_AC$|CLIMATE|FAN|BLOW|SEAT_(HEAT|COLD|VENT)|DEFROST|STEER(ING)?_HEAT"),
    ("speed_rpm", r"SPEED|RPM|ENGINE_SPEED|ROTATE"),
    ("odometer_trip", r"MILE|ODO|TRIP|DRIVE_(TIME|DIS)|DISTANCE|RANGE|ENDURANCE|AVG|AVERAGE|TRAVEL"),
    ("fuel_consumption", r"OIL_EXPEND|CONSUM|FUEL|OIL|PETROL|GAS"),
    ("temperature", r"TEMP"),
    ("battery_electric", r"BATTERY|VOLT|CHARGE|SOC|EV_|ELECTRIC|MOTOR"),
    ("lights", r"LIGHT|LAMP|HEADLIGHT|FOG|ILLUM"),
    ("warnings", r"WARN|ALARM|FAULT|ERROR|BELT|BRAKE|HANDBRAKE"),
    ("steering_angle", r"WHEEL_ANGLE|STEER(ING)?_ANGLE|ANGLE|TRACK"),
    ("time_compass", r"TIME|CLOCK|DATE|COMPASS|DIRECTION"),
    ("audio_media", r"AMP|EQ|VOL|BASS|TREBLE|BALANCE|FADE|SOUND|CD|RADIO|MEDIA|TRACK_|DISC|USB|BT_|PHONE"),
    ("camera_360", r"CAMERA|360|PANORAMA|VIEW|BACKCAR|REVERSE"),
    ("carset", r"CARSET|SET_|_SET"),
    ("carinfo_raw", r"CARINF|CARINFO|INFO"),
]


def category(name):
    n = name[2:]
    for cat, pat in CATS:
        if re.search(pat, n):
            return cat
    return "other"


def frame_hint(name):
    """U_CARINF_D41_D11_D1_B5 -> 'frame 0x41, sub 0x11, data 1, bit 5' (Raise-style names)."""
    m = re.search(r"_D([0-9A-F]{2})(?:_D([0-9A-F]{2}))?(?:_D(\d+))?(?:_D(\d+))?(?:_B(\d+))?", name)
    if not m:
        return None
    frame, sub, d1, d2, bits = m.groups()
    parts = [f"frame 0x{frame}"]
    if sub:
        parts.append(f"sub 0x{sub}")
    if d1:
        parts.append(f"data {d1}" + (f"-{d2}" if d2 else ""))
    if bits:
        parts.append(f"bits {bits}")
    return ", ".join(parts)


def profiles():
    db = sqlite3.connect(DB)
    rows = db.execute("""select b.id_value & 65535, b.id_value, c.canbus_company_name_en, s.canbus_carset_name_en,
                                t.canbus_cartype_en, b.canbus_canbox_en
                         from canbus_canbox b join canbus_company c on c.id=b.company_id
                         join canbus_carset s on s.id=b.carset_id join canbus_cartype t on t.id=b.cartype_id
                         where b.id_value > 0""").fetchall()
    out = collections.defaultdict(list)
    for low, full, company, carset, cartype, canbox in rows:
        out[low].append({"id": full, "company": company, "carset": carset, "cartype": cartype, "canbox": canbox})
    return out


def main():
    prof = profiles()
    inv = []
    for path in sorted(glob.glob(os.path.join(SRC, "module/canbus/Callback_[0-9]*.java"))):
        fname = os.path.basename(path)[:-5]
        m = re.match(r"Callback_(\d+)_?(.*)", fname)
        num, rest = int(m.group(1)), m.group(2)
        src = open(path, encoding="utf-8", errors="replace").read()
        consts = {k: int(v) for k, v in CONST.findall(src)}
        cnt = consts.get("U_CNT_MAX")
        named = {k: v for k, v in consts.items() if k[2:] not in STRUCT and not k.endswith(("_BEGIN", "_END"))}
        sig = []
        for k, v in sorted(named.items(), key=lambda kv: kv[1]):
            sig.append({"name": k, "code": v, "category": category(k), "frame": frame_hint(k)})
        uses = {
            "door": "DoorHelper" in src,
            "climate": "AirHelper" in src,
            "radar": bool(re.search(r"Radar|radar|Parking|ui\.parking", src)),
            "tpms": bool(re.search(r"Tire|tire|Tpms|TPMS", src)),
        }
        cats = collections.Counter(s["category"] for s in sig)
        for k, used in uses.items():
            if used and cats.get(k, 0) == 0:
                cats[k] = cats.get(k, 0)        # mark presence below via 'uses'
        inv.append({"num": num, "class": fname, "maker_token": rest.split("_")[0], "name": rest,
                    "codes_total": cnt, "named": len(sig), "uses_shared": uses, "categories": dict(cats),
                    "signals": sig, "profiles": prof.get(num, [])})
    json.dump(inv, open(os.path.join(ROOT, "inventory.json"), "w"), ensure_ascii=False, indent=1)

    print(f"{len(inv)} parsers, {sum(len(p['profiles']) for p in inv)} profiles mapped,"
          f" {len([n for n in prof if n not in {p['num'] for p in inv}])} profile parser ids without a class")
    def score(p):
        return len([c for c in p["categories"] if c not in ("other", "carset", "audio_media")]) * 100 + p["named"]
    print("\nTop 25 by category coverage (then named signals):")
    for p in sorted(inv, key=score, reverse=True)[:25]:
        makers = sorted({x["company"] for x in p["profiles"]})
        print(f"  {p['num']:5d} {p['name'][:38]:38s} named={p['named']:4d} total={p['codes_total']} "
              f"cats={len(p['categories'])} {','.join(makers)[:40]}")
    print("\nCurrent (0051):")
    p = next(x for x in inv if x["num"] == 51)
    print(json.dumps({k: p[k] for k in ("class", "codes_total", "named", "uses_shared", "categories")}, indent=1))


if __name__ == "__main__":
    main()

# FYT canbus protocol atlas

Which canbus profile on an FYT head unit carries the most signals, and what each protocol decodes
from the canbox's UART frames. Built 2026-10-14 from the DUDU7 (Android 13, UIS7870), FYT
`com.syu.canbus` build 2126013012. Interactive page: `page/index.html`, which needs the
`protocols.json` that `make_site_data.py` writes (not committed; rebuild it with the pipeline below).
It is how this firmware's protocol was chosen (Raise VW PQ) and why the XC90 body state goes out in
the 0x41/0x11-12 side channel (see `../XC90-MY2008-SETUP.md`).

| File | What |
|---|---|
| `fyt-canbus-protocols.md` | The write-up (forum post): how it works, ranking, firmware-emulatable protocols, Volvo XC90, full PSA ALL spec |
| `fyt-canbus-profiles.csv` | Every settings entry (5,106): canbox → cars for → model → config, decoder, parser, rank, signal counts |
| `fyt-canbus-spec.json` | Every decoded signal of all 652 protocols: code, name, category, frame, byte expression, branch |
| `scripts/` | The pipeline (below) |
| `page/index.html` | The interactive page (needs `protocols.json` next to it) |

Not in the repo, by design: the APKs and the decompiled FYT sources (vendor code).

## Rerun on another FYT build

```bash
# from the head unit (adb, read-only)
adb pull /odm/app/190000000_com.syu.canbus/190000000_com.syu.canbus.apk canbus.apk
adb pull "$(adb shell pm path com.syu.ms | cut -d: -f2)" ms.apk
adb pull /odm/app/ProtocolUpdate/ProtocolUpdate.apk protocolupdate.apk
unzip -o protocolupdate.apk 'assets/*.db' -d pu
jadx -d jadx-canbus --no-res canbus.apk
jadx -d ../dudu/ms-src --no-res ms.apk                # extract_spec.py reads ../dudu/ms-src/sources
python3 -m venv venv && venv/bin/pip install androguard
venv/bin/python scripts/resolve_bytecode.py canbus.apk                          # -> resolved-bytecode.tsv (parser per id)
venv/bin/python scripts/resolve_bytecode.py ms.apk "Lj0/kt;" h0 resolved-ms.tsv # -> decoder per id (class/method names are obfuscated per build)
python3 scripts/extract_spec.py      # -> spec-ms.json (byte-level writes per decoder)
python3 scripts/compare.py           # -> protocols.json (decoder + parser joined, ranked)
python3 scripts/make_site_data.py    # -> site/protocols.json (page data, input to make_bundle.py)
python3 scripts/make_bundle.py OUTDIR
```

The scripts expect to run from one working directory holding `canbus.apk`, `pu/assets/canbus.db`,
`jadx-canbus/` and the `resolved-*.tsv` files; `ms` paths are relative (`../dudu/ms-src`).

## Why bytecode, not the decompiled Java

jadx's Java for `HandlerCanbus.getCallbackCanbusById` mis-maps 1,008 of the 5,068 ids (switch
fall-through from case 452 on), and loading FYT's classes outside the app fails in their static
initialisers. `resolve_bytecode.py` steps through the Dalvik instructions of the factory for each
id instead, and stops on any instruction it does not model.

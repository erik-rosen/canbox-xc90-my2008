Following up on this thread: I decompiled FYT's canbus stack on my DUDU7 (Android 13, UIS7870, `com.syu.canbus` build 2126013012) and mapped every canbus profile to the code that decodes it. So we no longer have to guess which protocol has the best support. The full results are attached (summary, a CSV of every settings entry, and a JSON with the byte layout of every signal).

**@Mikescotland**, it isn't impossible after all. The trick is that the canbus app is only half of it.

**How the head unit decodes a canbox frame**

1. The canbox sends UART frames, e.g. Raise `2E CMD LEN DATA… CHK`. CHK is the sum of CMD, LEN and DATA, XOR `0xFF`.
2. `com.syu.ms` (not the canbus app) picks a **decoder** class for the selected profile and turns the bytes into numbered values (`kt.w0(code, value)`).
3. `com.syu.canbus` picks a **parser** class (`Callback_NNNN_<maker>_<car>`) that names those values (`U_CUR_SPEED = 109`) and draws the screens.
4. The profile you pick in Settings → Vehicle → CANBUS is an id `carId << 16 | canbusId`. The names in that menu come from `canbus.db` inside `ProtocolUpdate.apk`.

**Which protocol has the best support**

5,106 settings entries from 66 canbox makers reduce to 652 distinct protocols. Counting sensor categories (doors, climate, radar, TPMS, speed/rpm, trip, fuel, temperature, battery, lights, warnings, steering, time, camera):

- **HiWorld PSA** (HIWORLD → Peugeot/Citroen → ALL → ALL): 12 categories, 162 signals. TPMS, trip computer, lights, warnings.
- **Raise Toyota 2013** (RZC(Raise) → Toyota → ALL → 2013): 10 categories, 131 signals. TPMS with 4 pressures, trip computer, seatbelts left and right.
- **Raise Toyota Low** (RZC(Raise) → Toyota → ALL → Low): 6 categories, 167 signals. Radar and steering, plus a lot of media and settings.
- **Raise VW PQ** (RZC(Raise) → Volkswagen → PQ → Low): 8 categories, 91 signals. Rpm, speed, battery, outside temperature, odometer, fuel.
- **Raise VW MQB** (RZC(Raise) → Volkswagen → MQB ALL → Low): 3 categories, 40 signals. Doors, climate and speed only.

So Mikescotland is right that Raise Toyota is the richest Raise protocol. HiWorld PSA beats it overall. Raise VW MQB is surprisingly thin in this build. All the Volvo XC90 profiles are poor: 5 to 22 signals, nothing but doors, climate and speed.

**MUTE on Raise Toyota**

It's there, just on other key codes than VW. FYT key 12 is mute. Canbox key `0x22` maps to it in "Toyota ALL Low", and `0x53` in "Toyota ALL 2013". Each decoder's full key table (canbox key → FYT key id) is in the JSON.

**@cmpt: steering angle on Raise Toyota**

The head-unit side of `2E 29 02 xx xx CHK` in the Raise Toyota decoder:

- `0x29` with 2 data bytes: angle **low byte first**, read as a **12-bit signed** value (sign bit `0x800`), full scale ±500. Example frames: +200 is `2E 29 02 C8 00 0C`, and −200 is `2E 29 02 38 FF 9D`.
- Newer firmware can use `0x7D` sub `0x08` instead: `2E 7D 03 08 lo hi CHK`, 16-bit signed, ±540. Once the head unit has seen one of those, it ignores `0x29`. That's the "new addresses like 0x7d" Mikescotland mentioned.
- The display scale is set by `persist.fyt.track_angle_max` (default 40).
- For comparison, Raise VW PQ uses `2E 26 02 lo hi CHK`, 16-bit signed, ±540.

The CAN → UART translation happens entirely in the canbox firmware. There is no lookup table on the head unit, so in canbox-xc90-my2008 it's `canbox_raise_vw_wheel_process()` in `canbox.c`. Mode 21 / PID 06 on `7B0` is a diagnostic request, so the canbox would have to poll it. Most Toyotas also broadcast the steering angle unprompted (the open-source Toyota DBCs call it `STEER_ANGLE_SENSOR`, id `0x25`), which is easier: scale it to ±500 and send `0x29`.

**@Michalisgk: DUDU6**

I can only check DUDU7. The decoders live in FYT's `com.syu.ms` and `com.syu.canbus`, so any unit with the same FYT build should behave the same. To compare builds: `adb shell dumpsys package com.syu.canbus | grep versionCode` (mine is 2126013012).

**How it was done, briefly**

- Pulled `com.syu.canbus`, `com.syu.ms` and `ProtocolUpdate.apk` read-only over adb and decompiled them with jadx.
- Mapped every profile id to its decoder and parser by stepping through the bytecode of FYT's two selection methods. The decompiled Java for one of them gets about 1,000 profiles wrong, so don't trust it.
- Read the byte layout from each decoder's `V2()` method. About 84 % of values have their frame identified; the rest sit in helper methods.
- Not covered: head unit → car commands (settings changes), and whether your car actually has a given value on its CAN bus. That part still needs a sniffer.

Attached:
- `fyt-canbus-protocols.md`: summary, top 25, and the complete HiWorld PSA spec
- `fyt-canbus-profiles.csv`: every settings entry with its decoder, parser and signal counts (find your car)
- `fyt-canbus-spec.json`: every signal of every protocol, with frame, bytes and conditions

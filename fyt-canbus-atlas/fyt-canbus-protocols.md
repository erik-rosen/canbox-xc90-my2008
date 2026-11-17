# FYT canbus protocols: every car profile, decoded and ranked

I decompiled the canbus apps on an FYT-platform head unit (DUDU7, Android 13, Unisoc UIS7870; FYT `com.syu.canbus` build 2126013012) to find which canbus profile carries the most signals. Useful if you build or reflash your own canbox, for example with the open `canbox` firmware that emulates Raise and HiWorld protocols.

**Short version:** 5,106 settings entries (5,068 distinct profile ids) from 66 canbox makers reduce to 652 distinct protocols. The richest is HiWorld Peugeot/Citroën "PSA ALL": 162 signals in 12 sensor categories, including TPMS, trip computer, lights and warnings. Among Raise protocols, Toyota "ALL 2013" is the most complete (131 signals, with TPMS and a trip computer). Raise VW PQ has 91 signals but no TPMS, lights or clock.

## How FYT turns a canbox frame into a value

1. The canbox sends UART frames to the MCU (Raise: `2E CMD LEN DATA… CHK`, HiWorld: `5A A5 …`).
2. **`com.syu.ms`** picks a *decoder* class for the selected profile (807 classes, factory `kt.h0(int id)`). Its `V2(byte[] frame, int offset, int len)` turns bytes into numbered codes with `kt.w0(code, value)`.
3. **`com.syu.canbus`** picks a *parser* class (`Callback_NNNN_<maker>_<car>`, 640 classes, factory `HandlerCanbus.getCallbackCanbusById`). It names the codes (`U_CUR_SPEED = 109`) and draws the screens.
4. Other apps can read the same codes from module 7 of FYT's `com.syu.ms` binder (`IRemoteToolkit`).

A profile id is `carId << 16 | canbusId`: the low 16 bits pick the protocol family, the high 16 bits the car variant. The names in the settings menu come from `assets/canbus.db` in `ProtocolUpdate.apk`. Codes 0–5 are the doors (hood, FL, FR, RL, RR, boot), 10–96 the shared climate slots (`U_AIR_*`), 98 and up are per parser.

## Top 25 protocols by sensor-category coverage

Sensor categories: doors, climate, radar, TPMS, speed/rpm, trip, fuel, temperature, battery, lights, warnings, steering angle, time, camera. Settings and media are not counted. "Pick" is the least model-specific entry (Canbox → Cars for → Models for → Config).

| # | Parser | Pick in canbus settings | Ids | Sensor cats | Signals | Has |
|--:|---|---|--:|--:|--:|---|
| 1 | `0252_WC2_PSAALL` | HIWORLD → Peugeot/Citroen → ALL → ALL (id 655612) | 57 | 12 | 162 | doors, climate, radar, TPMS, speed/rpm, trip, fuel, battery, lights, warnings, time, camera |
| 2 | `0282_WC2_MingJueRuiTeng` | HIWORLD → MG → MG GS → 2015 (id 282) | 3 | 12 | 103 | doors, climate, radar, TPMS, speed/rpm, trip, fuel, temperature, battery, warnings, time, camera |
| 3 | `0374_XP1_ZiYouGuang` | XP(Simple) → Jeep → Cherokee → XP(L) (id 374) | 29 | 11 | 420 | doors, climate, TPMS, speed/rpm, trip, fuel, lights, warnings, steering angle, time, camera |
| 4 | `0298_XP1_2015SIYU_CRV` | RZC(Raise) → Honda → CRV → 2015.Low (id 298) | 140 | 11 | 285 | doors, climate, speed/rpm, trip, fuel, temperature, battery, lights, warnings, time, camera |
| 5 | `0265_RZC_ZhongTaiT600` | RZC(Raise) → ZOTYE → Zotye T600 → RZC (id 265) | 27 | 11 | 139 | doors, climate, radar, TPMS, speed/rpm, trip, fuel, battery, lights, warnings, camera |
| 6 | `0450_ZHTD_BWM_CarUi` | ZHTD → Porsche → ALL → ZHTD (id 655810) | 11 | 11 | 91 | doors, climate, speed/rpm, trip, fuel, temperature, lights, warnings, steering angle, time, camera |
| 7 | `0348_DAOJUN_XP1_ATS` | DaoJun → Cadillac → ATS → AUTO (id 348) | 14 | 11 | 62 | doors, climate, radar, TPMS, speed/rpm, trip, fuel, battery, lights, warnings, time |
| 8 | `0020_XP1_Camry2013` | RZC(Raise) → Toyota → ALL → 2013 (id 20) | 12 | 10 | 131 | doors, climate, TPMS, speed/rpm, trip, fuel, battery, warnings, time, camera |
| 9 | `0439_RZC_Jianghuai_All` | RZC(Raise) → JAC → JAC L6 → RZC (id 2163143) | 10 | 10 | 93 | doors, climate, TPMS, speed/rpm, trip, temperature, battery, lights, warnings, camera |
| 10 | `0001_WC1_DaZhong` | HIWORLD → Volkswagen → PQ → HiWord (id 1) | 34 | 10 | 51 | doors, climate, radar, speed/rpm, trip, fuel, temperature, battery, lights, warnings |
| 11 | `0139_RZC_XP1_JiLiEC7` | RZC(Raise) → Geely → GEELY EC7 → RZC (id 139) | 60 | 9 | 175 | doors, climate, TPMS, speed/rpm, trip, battery, lights, warnings, camera |
| 12 | `0025_XP1_GM_H` | XP(Simple) → GM/Chevrolet → ALL → XP(H) (id 25) | 15 | 9 | 128 | doors, climate, radar, speed/rpm, trip, battery, lights, warnings, camera |
| 13 | `0439_OUDI_Haval_H9` | RZC(Raise) → HAVAL → HAVAL H9 → 2016-2017.LOW (id 8651204) | 10 | 9 | 102 | doors, climate, speed/rpm, fuel, temperature, battery, lights, warnings, camera |
| 14 | `0244_RZC_XP1_HavalH2` | RZC(Raise) → HAVAL → HAVAL H2 → 2014-2016 (id 244) | 39 | 9 | 98 | doors, climate, speed/rpm, fuel, temperature, battery, lights, warnings, camera |
| 15 | `0439_LUZ_Toyato_All` | LZ(HZ) → Toyota → ALL → 2.0.Air.Right View (id 10879431) | 40 | 9 | 98 | doors, climate, radar, speed/rpm, trip, fuel, warnings, time, camera |
| 16 | `0454_TD_Lexus_All` | 6606 → Toyota → PRADO → 2018-2023.YL 3.0 (id 16384454) | 1 | 9 | 98 | doors, climate, TPMS, speed/rpm, trip, fuel, battery, steering angle, time |
| 17 | `0419_FengShenAX7` | HIWORLD → BESTURN → Besturn X80 → 2017.High.ALL (id 131491) | 21 | 9 | 73 | doors, climate, speed/rpm, trip, fuel, temperature, lights, warnings, camera |
| 18 | `0448_LZ_BWM_CarUi` | 6606 → Ford → ALL → Keep original (id 983488) | 30 | 9 | 69 | doors, climate, TPMS, speed/rpm, trip, fuel, temperature, warnings, camera |
| 19 | `0329_RZC_XP1_DongNanDX7` | RZC(Raise) → SouthEast → SOUTHEAST DX7 → 2015-2017 (id 329) | 12 | 9 | 50 | doors, climate, TPMS, speed/rpm, trip, fuel, lights, warnings, camera |
| 20 | `0448_LZ_BWM_CarUi` | LZ(HZ) → BMW → Keep original → LZ (id 448) | 1 | 9 | 48 | doors, climate, TPMS, speed/rpm, trip, fuel, temperature, warnings, camera |
| 21 | `0002_XP1_DaZhong` | XP(Simple) → Volkswagen → ALL → XP (id 2) | 5 | 9 | 46 | doors, climate, radar, TPMS, speed/rpm, trip, fuel, battery, warnings |
| 22 | `0326_XFY_DX7` | XFY → SouthEast → SOUTHEAST DX7 → XFY (id 326) | 1 | 9 | 38 | doors, climate, TPMS, speed/rpm, trip, fuel, battery, time, camera |
| 23 | `0047_XP1_CRV2012` | RZC(Raise) → Honda → CRV → 2012 (id 47) | 3 | 9 | 27 | doors, climate, speed/rpm, trip, fuel, battery, warnings, steering angle, time |
| 24 | `0373_RZC_XP1_ZiYouGuang` | RZC(Raise) → Jeep → Cherokee → 2015-2018 (id 373) | 50 | 8 | 180 | doors, climate, TPMS, speed/rpm, lights, warnings, time, camera |
| 25 | `0334_RZC_XP1_Focus2015` | RZC(Raise) → Ford → Focus → 2005-2018.Low (id 334) | 84 | 8 | 174 | doors, climate, TPMS, speed/rpm, trip, fuel, steering angle, time |

## Protocols the open canbox firmware can already frame

| Settings entry | Parser | Sensor cats | Signals | Has |
|---|---|--:|--:|---|
| RZC(Raise) → Volkswagen → PQ → Low (id 51) | `0051_RZC_DaZhong` | 8 | 91 | doors, climate, radar, speed/rpm, trip, fuel, battery, warnings |
| RZC(Raise) → Volkswagen → MQB ALL → Low (id 160) | `0160_RZC_XP1_DaZhong_GaoErFu7` | 3 | 40 | doors, climate, speed/rpm |
| RZC(Raise) → Toyota → ALL → 2013 (id 20) | `0020_XP1_Camry2013` | 10 | 131 | doors, climate, TPMS, speed/rpm, trip, fuel, battery, warnings, time, camera |
| RZC(Raise) → Toyota → ALL → Low (id 112) | `0112_RZC_XP1_Carmy` | 6 | 167 | doors, climate, radar, speed/rpm, battery, steering angle |
| HIWORLD → Volkswagen → MQB ALL → HiWord (id 589841) | `0017_WC2_GaoErFu7` | 2 | 40 | doors, climate |
| HIWORLD → Peugeot/Citroen → ALL → ALL (id 655612) | `0252_WC2_PSAALL` | 12 | 162 | doors, climate, radar, TPMS, speed/rpm, trip, fuel, battery, lights, warnings, time, camera |

Raise VW MQB and HiWorld MQB are no richer than PQ in this build: doors, climate and speed only.

## Volvo XC90 (2004–2013) profiles

| Settings entry | Parser | Signals | Has |
|---|---|--:|---|
| RZC(Raise) → VOLVO → XC90 → 2004-2013 (id 7930310) | `0452_RZC_Volvo_XC60` | 22 | doors, climate, speed/rpm |
| HIWORLD → VOLVO → XC90 → 2004-2013 (id 2490812) | `0444_WC_Volvo_All` | 22 | doors, climate |
| OD → VOLVO → XC90 → 2004-2013 (id 15466950) | `0454_OD_Volvo_XC90` | 5 | doors |
| LZ(HZ) → VOLVO → XC90 → LZ(HZ) (id 5046725) | `0453_LZ_Volvo_XC90` | 5 | doors |

All four are thin. Raise VW PQ (id 51) carries more than any Volvo profile.

## Full spec: HiWorld PSA ALL (`0252_WC2_PSAALL`, decoder `j0/h8`)

Pick **HIWORLD → Peugeot/Citroen → ALL → ALL** (id 655612). The same decoder serves all 57 HiWorld Peugeot/Citroën/DS/Opel entries.

Frames: `0x31`, `0x42`, `0x71`, `0x72`, `0x76`, `0x79`, `0x81`, `0x82`, `0x83`, `0x85`, `0x93`, `0x94`, `0x97`, `0xC1`

`B[0]` is the command byte and `B[2]…` the data. "When" is the decoder branch the value is written in.

### doors (5)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 1 | `U_DOOR_FL` | 0x83 | `(B[4] >> 7) & 1` | `B[1] == -125 & B[1] == 18 & ht.X == 0` |
| 2 | `U_DOOR_FR` | 0x83 | `(B[4] >> 6) & 1` | `B[1] == -125 & B[1] == 18 & ht.X == 0` |
| 3 | `U_DOOR_RL` | 0x83 | `(B[4] >> 5) & 1` | `B[1] != 33 & B[1] == -125 & B[1] == 18` |
| 4 | `U_DOOR_RR` | 0x83 | `(B[4] >> 4) & 1` | `B[1] != 33 & B[1] == -125 & B[1] == 18` |
| 5 | `U_DOOR_BACK` | 0x83 | `(B[4] >> 3) & 1` | `B[1] != 33 & B[1] == -125 & B[1] == 18` |

### climate (23)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 10 | `U_AIR_POWER` | 0x31 | `((B[2] & 255) >> 6) & 1` | `B[1] == 49` |
| 11 | `U_AIR_AC` | 0x31 | `((B[2] & 255) >> 0) & 1` | `B[1] == 49` |
| 12 | `U_AIR_CYCLE` | 0x31 | `((B[3] & 255) >> 4) & 1` | `B[1] == 49` |
| 13 | `U_AIR_AUTO` | 0x31 | `((B[2] & 255) >> 3) & 1` | `B[1] == 49` |
| 16 | `U_AIR_REAR_DEFROST` | 0x31 | `((B[4] & 255) >> 5) & 1` | `B[1] == 49` |
| 18 | `U_AIR_BLOW_UP_LEFT` | 0x31 | `i5` | `B[1] == 49` |
| 19 | `U_AIR_BLOW_BODY_LEFT` | 0x31 | `i4` | `B[1] == 49` |
| 20 | `U_AIR_BLOW_FOOT_LEFT` | 0x31 | `i6` | `B[1] == 49` |
| 21 | `U_AIR_WIND_LEVEL_LEFT` | 0x31 | `B[7] & 255` | `B[1] == 49` |
| 22 | `U_AIR_BLOW_UP_RIGHT` | 0x31 | `i8` | `B[1] == 49` |
| 23 | `U_AIR_BLOW_BODY_RIGHT` | 0x31 | `i7` | `B[1] == 49` |
| 24 | `U_AIR_BLOW_FOOT_RIGHT` | 0x31 | `i9` | `B[1] == 49` |
| 27 | `U_AIR_TEMP_LEFT` | 0x31 | `-2` | `B[1] == 49 & (B[8] & 255) == 254` |
| 28 | `U_AIR_TEMP_RIGHT` | 0x31 | `-2` | `B[1] == 49 & (B[9] & 255) == 254` |
| 42 | `U_AIR_REAR_POWER` | 0x31 | `((B[2] & 255) >> 4) & 1` | `B[1] == 49` |
| 51 | `U_AIR_WIND_STRENGTH` | 0x31 | `B[5] & 255 & 3` | `B[1] == 49` |
| 53 | `U_AIR_ACMAX` | 0x31 | `((B[2] & 255) >> 5) & 1` | `B[1] == 49` |
| 54 | `U_AIR_AQS` | 0x31 | `((B[3] & 255) >> 3) & 1` | `B[1] == 49` |
| 55 | `U_AIR_MONO` | 0x31 | `((B[2] & 255) >> 2) & 1` | `B[1] == 49` |
| 65 | `U_AIR_FRONT_DEFROST` | 0x31 | `((B[4] & 255) >> 4) & 1` | `B[1] == 49` |
| 122 | `U_AUTO_AC_ENABLED` | 0x76 | `((B[2] & 255) >> 7) & 1` | `B[1] == 118` |
| 152 | `U_AIR_BY_AUTO_KEY` | 0x82 | `(B[2] >> 7) & 1` | `B[1] != 33 & B[1] == -126` |
| 153 | `U_IN_OUT_AIR_BY_AUTO_KEY` | 0x82 | `(B[2] >> 6) & 1` | `B[1] != 33 & B[1] == -126` |

### radar (3)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 164 | `U_RADAR_MUTE` | 0x82 | `B[8] & 255` | `B[1] != 33 & B[1] == -126` |
| 171 | `U_SHOW_RADAR` | 0xC1 | `2` | `B[1] == -63 & ((B[3] & 255) & 32) == 0` |
| 172 | `U_RADAR_VOL` | 0xC1 | `1` | `B[1] == -63 & (((B[3] & 255) >> 1) & 3) == 0` |

### TPMS (8)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 107 | `U_TPMS_STATE` | 0x42 | `(B[3] & 255) ¦ ((B[2] << 8) & 65280)` | `B[1] != 33 & B[1] == 66` |
| 108 | `U_TIRE_SHOW_STATE` | 0x71 | `((B[2] & 255) >> 7) & 1` | `B[1] != 33 & B[1] == 113` |
| 138 | `U_PRESSURE_FL` | 0x81 | `((B[2] & 255) >> 7) & 1` | `B[1] != 33 & B[1] == -127` |
| 139 | `U_PRESSURE_FR` | 0x81 | `((B[2] & 255) >> 6) & 1` | `B[1] != 33 & B[1] == -127` |
| 140 | `U_PRESSURE_RL` | 0x81 | `((B[2] & 255) >> 5) & 1` | `B[1] != 33 & B[1] == -127` |
| 141 | `U_PRESSURE_RR` | 0x81 | `((B[2] & 255) >> 4) & 1` | `B[1] != 33 & B[1] == -127` |
| 143 | `U_EXIST_TPMS` | 0x81 | `((B[2] & 255) >> 2) & 1` | `B[1] != 33 & B[1] == -127` |
| 144 | `U_SHOW_TIRE_BACKUP` | 0x81 | `((B[2] & 255) >> 1) & 1` | `B[1] != 33 & B[1] == -127` |

### speed/rpm (6)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 102 | `U_AVERAGE_SPEED` | 0x83 | `B[5] & 255` | `B[1] != 33 & B[1] == -125 & B[1] == 20` |
| 123 | `U_CURRENT_SPEED` | 0x76 | `((B[2] & 255) >> 6) & 1` | `B[1] == 118` |
| 151 | `U_MUTIL_AVERAGE_SPEED` | 0x81 | `((B[11] & 255) >> 7) & 1` | `B[1] != 33 & B[1] == -127` |
| 161 | `U_ENGINE_SPEED` | 0x82 | `B[5] & 255` | `B[1] != 33 & B[1] == -126` |
| 179 | `U_174008_SPEED_LIMIT_ENABLE` | 0x72 | `((B[2] & 255) >> 1) & 1` | `B[1] != 33 & B[1] == 114` |
| 188 | `U_174008_SPEED_LIMIT` | 0x79 | `((B[2] & 255) >> 1) & 1` | `B[1] == 121` |

### trip (5)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 99 | `U_DRIVING_MILEAGE` | 0x83 | `((B[4] & 255) << 8) ¦ (B[5] & 255)` | `B[1] != 33 & B[1] == -125 & B[1] == 19` |
| 103 | `U_CUR_TRIP_OIL_EXPEND` | 0x83 | `((B[2] & 255) << 8) ¦ (B[3] & 255)` | `B[1] != 33 & B[1] == -125 & B[1] == 21` |
| 146 | `U_MUTIL_AVERAGE_CONSUMPTION` | 0x81 | `B[4] & 255` | `B[1] != 33 & B[1] == -127` |
| 149 | `U_MUTIL_TRAVELLING_TIME` | 0x81 | `B[7] & 255` | `B[1] != 33 & B[1] == -127` |
| 150 | `U_MUTIL_DISTANCE_TRAVELLED` | 0x81 | `B[8] & 255` | `B[1] != 33 & B[1] == -127` |

### fuel (6)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 98 | `U_CUR_OIL_EXPEND` | 0x83 | `((B[2] & 255) << 8) ¦ (B[3] & 255)` | `B[1] != 33 & B[1] == -125 & B[1] == 19` |
| 100 | `U_OPTIMAL_OIL_EXPEND` | 0x83 | `((B[2] & 255) << 8) ¦ (B[3] & 255)` | `B[1] != 33 & B[1] == -125 & B[1] == 20` |
| 145 | `U_MUTIL_CURRENT_CONSUMPTION` | 0x81 | `B[3] & 255` | `B[1] != 33 & B[1] == -127` |
| 147 | `U_MUTIL_CONVENIENCE_CONSUMER` | 0x81 | `B[5] & 255` | `B[1] != 33 & B[1] == -127` |
| 154 | `U_WARNNING_LOW_OIL` | 0x82 | `(B[2] >> 5) & 1` | `B[1] != 33 & B[1] == -126` |
| 159 | `U_LAST_OIL` | 0x82 | `B[3] & 255` | `B[1] != 33 & B[1] == -126` |

### battery (2)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 155 | `U_WARNNING_LOW_BATTERY` | 0x82 | `(B[2] >> 4) & 1` | `B[1] != 33 & B[1] == -126` |
| 160 | `U_BATTERY_VOLTAGE` | 0x82 | `B[4] & 255` | `B[1] != 33 & B[1] == -126` |

### lights (2)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 169 | `U_LIGHT_LEAVING_HOME` | 0xC1 | `((B[2] & 255) >> 5) & 1` | `B[1] == -63` |
| 170 | `U_LIGHT_COMING_HOME` | 0xC1 | `((B[2] & 255) >> 3) & 1` | `B[1] == -63` |

### warnings (3)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 156 | `U_WARNNING_LIFE_BELT` | 0x82 | `(B[2] >> 3) & 1` | `B[1] != 33 & B[1] == -126` |
| 157 | `U_WARNNING_CLEANNING_FLUID` | 0x82 | `(B[2] >> 2) & 1` | `B[1] != 33 & B[1] == -126` |
| 158 | `U_WARNNING_HANDLE_BRAKE` | 0x82 | `(B[2] >> 1) & 1` | `B[1] != 33 & B[1] == -126` |

### time (1)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 101 | `U_DRIVING_TIME` | 0x83 | `(B[7] & 255) ¦ ((B[6] & 255) << 8)` | `B[1] != 33 & B[1] == -125 & B[1] == 20` |

### camera (2)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 104 | `U_CAR_CAMERA_MODE` | 0x83 | `(B[7] & 255) ¦ ((B[6] & 255) << 8)` | `B[1] != 33 & B[1] == -125 & B[1] == 19` |
| 175 | `U_CAR_RIGHTCAMERA_STATE` | 0x71 | `((B[3] & 255) >> 5) & 1` | `B[1] != 33 & B[1] == 113` |

### settings (60)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 109 | `U_LOCK_UNLOCK_FEEDBACK_TONE` | 0x71 | `((B[2] & 255) >> 6) & 1` | `B[1] != 33 & B[1] == 113` |
| 110 | `U_2TIMES_KEY_UNLOCK` | 0x71 | `((B[2] & 255) >> 5) & 1` | `B[1] != 33 & B[1] == 113` |
| 111 | `U_UNLOCK_BY_DRIVERS_DOOR_OPEN` | 0x71 | `((B[2] & 255) >> 3) & 1` | `B[1] != 33 & B[1] == 113` |
| 118 | `U_OPEN_CLOSE_DOOR_UNLOCK` | 0x72 | `((B[2] & 255) >> 7) & 1` | `B[1] != 33 & B[1] == 114` |
| 119 | `U_OPEN_CLOSE_AUTO_LOCK` | 0x72 | `((B[2] & 255) >> 6) & 1` | `B[1] != 33 & B[1] == 114` |
| 124 | `U_AUTOLOCK_BY_SPEED` | 0x76 | `((B[2] & 255) >> 4) & 3` | `B[1] == 118` |
| 125 | `U_AUTOLOCK_BY_SHIFT_FROM_P` | 0x76 | `((B[2] & 255) >> 3) & 1` | `B[1] == 118` |
| 126 | `U_AUTOLOCK_BY_SHIFT_TO_P` | 0x76 | `((B[2] & 255) >> 0) & 7` | `B[1] == 118` |
| 128 | `U_DAYTIME_RUNING_LIGHTS_ON` | 0x76 | `((B[3] & 255) >> 6) & 1` | `B[1] == 118` |
| 131 | `U_LOCK_UNLOCK_LAMP_FLASH` | 0x76 | `((B[3] & 255) >> 3) & 1` | `B[1] == 118` |
| 132 | `U_REMOTE_2PRESS_UNLOCK` | 0x76 | `((B[3] & 255) >> 2) & 1` | `B[1] == 118` |
| 133 | `U_UNLOCK_BY_SMART_DOOR` | 0x76 | `((B[3] & 255) >> 0) & 3` | `B[1] == 118` |
| 134 | `U_SMARTLOCK_AND_ONE_KEY_BOOT` | 0x79 | `((B[2] & 255) >> 7) & 1` | `B[1] == 121` |
| 135 | `U_CLOSE_INSIDELAMP_TIME` | 0x79 | `((B[2] & 255) >> 6) & 1` | `B[1] == 121` |
| 136 | `U_SENSITIVITY_OPEN_BIGLAMP` | 0x79 | `((B[2] & 255) >> 5) & 1` | `B[1] == 121` |
| 137 | `U_CLOSE_BIGLAMP_TIME` | 0x79 | `((B[2] & 255) >> 4) & 1` | `B[1] == 121` |
| 180 | `U_174008_THEME_COLOR_SET_ENABLE` | 0x72 | `(B[2] & 255) & 1` | `B[1] != 33 & B[1] == 114` |
| 189 | `U_174008_THEME_COLOR_SET` | 0x79 | `(B[2] & 255) & 1` | `B[1] == 121` |
| 208 | `U_CARSET_D79_D2_B1` | 0x79 | `((B[4] & 255) >> 1) & 1` | `B[1] == 121` |
| 209 | `U_CARSET_D79_D2_B0` | 0x79 | `((B[4] & 255) >> 0) & 1` | `B[1] == 121` |
| 210 | `U_CARSET_D79_D3_B76` | 0x79 | `(B[5] >> 6) & 3` | `B[1] == 121` |
| 211 | `U_CARSET_D79_D3_B5` | 0x79 | `(B[5] >> 5) & 1` | `B[1] == 121` |
| 212 | `U_CARSET_D79_D3_B4` | 0x79 | `(B[5] >> 4) & 1` | `B[1] == 121` |
| 213 | `U_CARSET_D93_D0_B7` | 0x93 | `(B[2] >> 7) & 1` | `B[1] == -109` |
| 214 | `U_CARSET_D93_D0_B6` | 0x93 | `(B[2] >> 6) & 1` | `B[1] == -109` |
| 215 | `U_CARSET_D93_D0_B5` | 0x93 | `(B[2] >> 5) & 1` | `B[1] == -109` |
| 216 | `U_CARSET_D93_D1_B70` | 0x93 | `B[3] & 255` | `B[1] == -109` |
| 217 | `U_CARSET_D93_D2_B70` | 0x93 | `B[4] & 255` | `B[1] == -109` |
| 218 | `U_CARSET_D97_D0_B30` | 0x97 | `(B[2] >> 0) & 15` | `B[1] == -105` |
| 219 | `U_CARSET_D97_D1_B5` | 0x97 | `(B[3] >> 5) & 1` | `B[1] == -105` |
| 220 | `U_CARSET_D97_D1_B4` | 0x97 | `(B[3] >> 4) & 1` | `B[1] == -105` |
| 221 | `U_CARSET_D97_D1_B3` | 0x97 | `(B[3] >> 3) & 1` | `B[1] == -105` |
| 222 | `U_CARSET_D97_D1_B2` | 0x97 | `(B[3] >> 2) & 1` | `B[1] == -105` |
| 223 | `U_CARSET_D97_D1_B1` | 0x97 | `(B[3] >> 1) & 1` | `B[1] == -105` |
| 224 | `U_CARSET_D97_D1_B0` | 0x97 | `(B[3] >> 0) & 1` | `B[1] == -105` |
| 225 | `U_CARSET_D97_D2_B5` | 0x97 | `(B[4] >> 5) & 1` | `B[1] == -105` |
| 226 | `U_CARSET_D97_D2_B4` | 0x97 | `(B[4] >> 4) & 1` | `B[1] == -105` |
| 227 | `U_CARSET_D97_D2_B3` | 0x97 | `(B[4] >> 3) & 1` | `B[1] == -105` |
| 228 | `U_CARSET_D97_D2_B2` | 0x97 | `(B[4] >> 2) & 1` | `B[1] == -105` |
| 229 | `U_CARSET_D97_D2_B1` | 0x97 | `(B[4] >> 1) & 1` | `B[1] == -105` |
| 230 | `U_CARSET_D97_D2_B0` | 0x97 | `(B[4] >> 0) & 1` | `B[1] == -105` |
| 231 | `U_CARSET_D97_D3_D4` | 0x97 | `((B[6] << 8) & 65280) ¦ (B[5] & 255)` | `B[1] == -105` |
| 232 | `U_CARSET_D97_D5_B70` | 0x97 | `B[7] & 255` | `B[1] == -105` |
| 233 | `U_CARSET_D97_D6_B70` | 0x97 | `B[8] & 255` | `B[1] == -105` |
| 234 | `U_CARSET_D97_D7_B7` | 0x97 | `(B[9] >> 7) & 1` | `B[1] == -105` |
| 235 | `U_CARSET_D97_D7_B6` | 0x97 | `(B[9] >> 6) & 1` | `B[1] == -105` |
| 236 | `U_CARSET_D97_D7_B5` | 0x97 | `(B[9] >> 5) & 1` | `B[1] == -105` |
| 237 | `U_CARSET_D97_D7_B4` | 0x97 | `(B[9] >> 4) & 1` | `B[1] == -105` |
| 238 | `U_CARSET_D97_D7_B3` | 0x97 | `(B[9] >> 3) & 1` | `B[1] == -105` |
| 239 | `U_CARSET_D97_D7_B2` | 0x97 | `(B[9] >> 2) & 1` | `B[1] == -105` |
| 240 | `U_CARSET_D97_D8_B70` | 0x97 | `B[10] & 255` | `B[1] == -105` |
| 248 | `U_CARSET_D79_D4_B20` | 0x79 | `7 & (B[6] >> 0)` | `B[1] == 121` |
| 249 | `U_CARSET_D79_D5_B76` | 0x79 | `(B[7] >> 6) & 3` | `B[1] == 121` |
| 250 | `U_CARSET_D79_D5_B54` | 0x79 | `(B[7] >> 4) & 3` | `B[1] == 121` |
| 251 | `U_CARSET_D79_D5_B32` | 0x79 | `(B[7] >> 2) & 3` | `B[1] == 121` |
| 252 | `U_CARSET_D79_D5_B1` | 0x79 | `(B[7] >> 1) & 1` | `B[1] == 121` |
| 254 | `U_CARSET_D79_D6_B21` | 0x79 | `3 & (B[8] >> 1)` | `B[1] == 121` |
| 255 | `U_CARSET_D79_D6_B0` | 0x79 | `(B[8] >> 0) & 1` | `B[1] == 121` |
| 256 | `U_CARSET_D79_D6_B4` | 0x79 | `(B[8] >> 4) & 1` | `B[1] == 121` |
| 257 | `U_CARSET_D79_D6_B3` | 0x79 | `(B[8] >> 3) & 1` | `B[1] == 121` |

### media (6)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 106 | `U_FEEDBACK_LAMP_ENABLED` | 0x83 | `(B[7] & 255) ¦ ((B[6] & 255) << 8)` | `B[1] != 33 & B[1] == -125 & B[1] == 21` |
| 116 | `U_CAR_PLAY_STATE` | 0x71 | `((B[3] & 255) >> 2) & 1` | `B[1] != 33 & B[1] == 113` |
| 127 | `U_OPEN_BIGLAMP_BY_WIPER` | 0x76 | `((B[3] & 255) >> 7) & 1` | `B[1] == 118` |
| 130 | `U_CAR_BT_STATE` | 0x76 | `((B[3] & 255) >> 4) & 1` | `B[1] == 118` |
| 165 | `U_DRIVER_DISPLAY_DISTANCE_WARNNING` | 0x82 | `((B[11] & 255) >> 7) & 1` | `B[1] != 33 & B[1] == -126` |
| 167 | `U_CAR_PLAY_PROGRESS` | 0x85 | `((B[3] & 255) >> 7) & 1` | `B[1] == -123` |

### other (30)

| Code | Name | Frame | Value from bytes | When |
|--:|---|---|---|---|
| 105 | `U_SYSTEM_KEY_WITH_EKEY_ENABLED` | 0x83 | `B[5] & 255` | `B[1] != 33 & B[1] == -125 & B[1] == 21` |
| 112 | `U_MIRROR_WIPERS_REAR_WIN_WIPING_IN_RESERVE` | 0x71 | `((B[3] & 255) >> 7) & 1` | `B[1] != 33 & B[1] == 113` |
| 113 | `U_MIRROR_WIPERS_AUTO_WIPING_IN_RAIN` | 0x71 | `((B[3] & 255) >> 6) & 1` | `B[1] != 33 & B[1] == 113` |
| 114 | `U_DRIVER_ACC` | 0x71 | `((B[3] & 255) >> 4) & 1` | `B[1] != 33 & B[1] == 113` |
| 115 | `U_CAR_MID_ENABLE` | 0x71 | `((B[3] & 255) >> 3) & 1` | `B[1] != 33 & B[1] == 113` |
| 117 | `U_OPEN_CLOSE_CONVENIENCE` | 0x71 | `((B[3] & 255) >> 1) & 1` | `B[1] != 33 & B[1] == 113` |
| 120 | `U_MIRROR_WIPERS_FOLDIN_WHEN_PARKED` | 0x72 | `((B[2] & 255) >> 5) & 1` | `B[1] != 33 & B[1] == 114` |
| 121 | `U_MIRROR_WIPERS_LOW_WHILE_REVESING` | 0x72 | `((B[2] & 255) >> 4) & 1` | `B[1] != 33 & B[1] == 114` |
| 129 | `U_VALID_VENTILATION_ENABLED` | 0x76 | `((B[3] & 255) >> 5) & 1` | `B[1] == 118` |
| 142 | `U_PRESSURE_BACKUP` | 0x81 | `((B[2] & 255) >> 3) & 1` | `B[1] != 33 & B[1] == -127` |
| 148 | `U_MUTIL_ECO_TIPS` | 0x81 | `B[6] & 255` | `B[1] != 33 & B[1] == -127` |
| 162 | `U_PARK_BESIDE_ROAD` | 0x82 | `B[6] & 255` | `B[1] != 33 & B[1] == -126` |
| 163 | `U_PARK_IN_CARPORT` | 0x82 | `B[7] & 255` | `B[1] != 33 & B[1] == -126` |
| 166 | `U_MIRROR_WIPERS_SYN_ADJUST` | 0x85 | `((B[2] & 255) >> 7) & 1` | `B[1] == -123` |
| 168 | `U_CAR_PE_ENABLE` | 0x94 | `B[2] & 255` | `B[1] == -108` |
| 177 | `U_174008_LANE_MAINTAIN_ENABLE` | 0x72 | `((B[2] & 255) >> 3) & 1` | `B[1] != 33 & B[1] == 114` |
| 178 | `U_174008_FATIGUE_DETECTION_ENABLE` | 0x72 | `((B[2] & 255) >> 2) & 1` | `B[1] != 33 & B[1] == 114` |
| 181 | `U_174008_AMBIENT_MODE_ENABLE` | 0x72 | `((B[3] & 255) >> 7) & 1` | `B[1] != 33 & B[1] == 114` |
| 182 | `U_174008_DRIVE_MODE_ENABLE` | 0x72 | `((B[3] & 255) >> 5) & 1` | `B[1] != 33 & B[1] == 114` |
| 183 | `U_174008_ION_PURIFIER_ENABLE` | 0x72 | `((B[3] & 255) >> 6) & 1` | `B[1] != 33 & B[1] == 114` |
| 184 | `U_174008_INCENSE_TYPE_ENABLE` | 0x72 | `((B[3] & 255) >> 4) & 1` | `B[1] != 33 & B[1] == 114` |
| 185 | `U_174008_INCENSE_CONCENTRATION` | 0x79 | `((B[4] & 255) >> 6) & 3` | `B[1] == 121` |
| 186 | `U_174008_LANE_MAINTAIN` | 0x79 | `((B[2] & 255) >> 3) & 1` | `B[1] == 121` |
| 187 | `U_174008_FATIGUE_DETECTION` | 0x79 | `((B[2] & 255) >> 2) & 1` | `B[1] == 121` |
| 190 | `U_174008_AMBIENT_MODE` | 0x79 | `((B[3] & 255) >> 6) & 3` | `B[1] == 121` |
| 191 | `U_174008_DRIVE_MODE` | 0x79 | `((B[3] & 255) >> 5) & 1` | `B[1] == 121` |
| 192 | `U_174008_ION_PURIFIER` | 0x79 | `((B[3] & 255) >> 3) & 3` | `B[1] == 121` |
| 193 | `U_174008_INCENSE_TYPE` | 0x79 | `((B[3] & 255) >> 1) & 3` | `B[1] == 121` |
| 196 | `U_174008_PANNEL_BRIGHT_ENABLE` | 0x72 | `((B[3] & 255) >> 3) & 1` | `B[1] != 33 & B[1] == 114` |
| 197 | `U_174008_PANNEL_BRIGHT` | 0x79 | `((B[4] & 255) >> 2) & 15` | `B[1] == 121` |

## Method and limits

- Pulled read-only from the head unit: `/odm/app/190000000_com.syu.canbus`, `com.syu.ms` and `ProtocolUpdate.apk` (`assets/canbus.db`). Decompiled with jadx.
- The profile → decoder and parser mapping comes from interpreting the Dalvik bytecode of both factory methods for every id. jadx's Java for `HandlerCanbus` mis-maps 1,008 profiles (switch fall-through from case 452 on), so don't trust the decompiled switch.
- Byte layouts are read from the decoders' `V2()` source. 84 % of writes have their frame identified; the rest are in helper methods. Names are FYT's own constants; categories are keyword-based and can misfile a few.
- Not covered: key-code names beyond each decoder's key table, head unit → car commands, and whether a particular car actually puts the data on its CAN bus.
- Attached: `fyt-canbus-profiles.csv` (every settings entry with its decoder, parser and signal counts) and `fyt-canbus-spec.json` (every signal of every protocol).

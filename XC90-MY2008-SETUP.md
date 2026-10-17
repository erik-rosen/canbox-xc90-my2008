# XC90 MY2008: build, flash and sniff (Erik's setup)

How this fork is built, flashed and extended for Erik's 2008 XC90 with a DUDUAUTO DUDU7 head
unit (FYT platform, profile Raise VW PQ). Signals are in `xc90_2008my_lowspeed.dbc`; the head-unit
side (the Bil app, FYT codes, cameras) is in the openclaw repo, `projects/car-link/README.md`.
Upstream's own notes for the XC90 are in `volvoxc90.md`.

## Build (macOS, Apple silicon)

Toolchain: Arm GNU Toolchain 15.2 (`arm-gnu-toolchain-15.2.rel1-darwin-arm64-arm-none-eabi`),
unpacked in `~/opt` (no Homebrew formula). libopencm3 is in the tree.

```bash
export PATH=$(ls -d ~/opt/arm-gnu-toolchain-*/bin):$PATH
make -B volvo_od2.bin          # the canbox in the car is the "volvo_od2" board (STM32F103, 64 KB)
arm-none-eabi-size volvo_od2.elf
```

The build prints a stack of upstream warnings; none are errors. `volvo_od2.bin` is in git, so
rebuild before committing a source change.

**Replay before flashing.** Handlers can be checked on the Mac against a recorded log: compile
`car.c` + `canbox.c` for the host with stubs for `hw_usart_write` and the tick functions, feed
the frames of a GVRET CSV through the handlers with their real timestamps (so the
`in_process` timeouts behave), and print each Raise frame when it changes. That harness lived in
a session scratchpad and has to be rewritten; it took ~60 lines.

## Flash (ST-Link V2, openocd 0.12)

`brew install open-ocd`. The SWD pads are CON2 on the canbox PCB (see `volvoxc90.md` for the
pinout). Erik's board answers with **CPUTAPID 0x2ba01477**; openocd's default (0x1ba01477) fails
with an idcode mismatch, and the unlock dance in `make flash_volvo_od2` is not needed (the chip
isn't read-protected). What worked on 2026-10-16:

```bash
cat > /tmp/ocd-flash.cfg <<'EOF'
set CPUTAPID 0x2ba01477
source [find interface/stlink.cfg]
source [find target/stm32f1x.cfg]
init
reset halt
program volvo_od2.bin 0x08000000 verify
reset run
exit
EOF
openocd -f /tmp/ocd-flash.cfg
```

- **Back up first** with the same config, replacing the `program` line by
  `dump_image <file> 0x08000000 0x10000`. Backups are in
  `~/code/canbox-xc90-my2008-flash-backups/` on macbookm1: `canbox-before-2026-10-16.bin` (what
  was in the car) and `volvo_od2-august-build.bin`. Flashing one of them back is the undo.
- The settings page at **0x0800FC00** (protocol, car, backlight, camera delay) sits above the
  program and survives a `program` of `volvo_od2.bin`; no reconfiguration is needed after a
  flash. A full-chip erase would wipe it: then set protocol Raise VW (PQ) and car "XC90 2008MY" again
  over the debug UART (see `README.md`).

## Sniffing the bus (GVRET + SavvyCAN)

Hardware: an Arduino Due with CAN transceivers (github.com/erik-rosen/can_sniffer_tools), on the
low-speed body bus (125 kbit/s) behind the head unit. **Rule: never transmit on the car's bus.**

- Firmware: GVRET (github.com/collin80/GVRET) with the libraries `due_can`, `can_common`,
  `MCP2515`, `due_wire`, `DueFlashStorage`, `Wire_EEPROM` and `SdFat-beta/SdFat` (all collin80),
  symlinked into one `libs/` folder. Before building, set the defaults in `GVRET.ino`:
  `CAN0Speed`/`CAN1Speed = 125000`, `CAN0ListenOnly`/`CAN1ListenOnly = true` (CAN_MR_ABM: no ACK,
  no TX). The defaults only apply while the stored settings version mismatches, and SavvyCAN
  can change them, so keep "Listen only" ticked in SavvyCAN too.

  ```bash
  arduino-cli compile -b arduino:sam:arduino_due_x --libraries $PWD/libs --output-dir $PWD/build $PWD/GVRET
  arduino-cli upload  -b arduino:sam:arduino_due_x -p /dev/cu.usbmodem101 --input-dir $PWD/build $PWD/GVRET
  ```
  Use the Due's **native** USB port (`/dev/cu.usbmodem101`).
- SavvyCAN V220 (arm64) lives in `~/Applications/SavvyCAN.app`. The release signature is broken
  and macOS kills it on start (exit 137); fix once with
  `codesign --force --deep -s - ~/Applications/SavvyCAN.app`. Only one program can hold the serial
  port: quit SavvyCAN before scripting the Due directly.
- GVRET binary protocol, for scripts: send `0xE7 0xE7` to enter binary mode; frames arrive as
  `F1 00 <ts u32> <id u32, bit 31 = extended> <len | bus << 4> <data>`. All XC90 low-speed IDs
  are extended (29-bit).
- **Workflow that decoded the DBC:** one capture per feature. Erik works the control in the car
  and notes what he did, step by step ("A: fan off", "B: fan step 1"…); the analysis lines the
  notes up with the log, finds the ID, byte and bits that change only at those steps, and checks
  scaling across steps. Discard the first rows of a capture (stale frames left in the buffer).
  Then: add the signal to the table in `tools/make_dbc.py` (never hand-edit the DBC), regenerate
  with cantools, write the handler in `cars/xc90_2008my.c`, replay, flash.
- Not on the low-speed bus: temperature setpoints, seat heat, the climate AUTO flag, front fog
  state, the passenger and rear window states. The high-speed bus (OBD 6/14, 500 kbit/s) is
  untested.

## What the firmware sends the head unit

- **0x21 climate** (Raise VW PQ): power, AC, recirculation, rear window heater and fan step
  (`B[3] & 15`, 0–7). Unknown temperatures go out as 0xFF, which FYT's pop-up shows as "NO". The
  bit meanings FYT's decoder really uses are commented in `canbox.c`.
- **Side channel 0x41/0x11 and 0x41/0x12** (`canbox_raise_vw_carinfo_process`, XC90 MY2008 only):
  lock, indicators, driver window, sunroof, main beam, rear fog, rear-window lock, brake pedal.
  FYT's VW PQ decoder passes them through unchanged as canbus codes 113–117 and 140–143, which the
  Bil and Signaler apps read. Layout in the comment above that function.

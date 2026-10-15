"""Generate ../xc90_2008my_lowspeed.dbc from the table below (pip install cantools). Intel bit = byte*8+bit; Motorola start = MSB position."""
import os
import cantools
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "xc90_2008my_lowspeed.dbc")
from cantools.database.can import Database, Message, Signal
from cantools.database.conversion import NamedSignalConversion, LinearConversion

def S(name, start, length=1, order="little_endian", scale=1, offset=0, unit=None, choices=None, comment=None, mn=None, mx=None):
    conv = NamedSignalConversion(scale, offset, choices, False) if choices else LinearConversion(scale, offset, False)
    return Signal(name, start, length, order, False, conversion=conv, unit=unit, comment=comment,
                  minimum=mn, maximum=mx, receivers=["XC90"])

M = [
 (0x0217FFC, "LightsSpeed", "Light switch module and vehicle speed (firmware lsm0 + vel handlers).", [
   S("FrontFogButton_n", 22, comment="Drops to 0 for about 1 s when the front fog button is pressed (also seen once during a climate step, so treat with care). The front fog STATE is not on this bus."),
   S("DaytimeRunningLights", 25, comment="Set with the light switch at off (F2); cleared at parking (F4) and low beam (F8). Confirmed 2026-10-15."),
   S("ParkLights", 26), S("LowBeam", 27, comment="The parking bit clears when low beam is selected."),
   S("CruiseControl", 46, 2, choices={1: "Off", 2: "On"}, comment="Cruise control main switch. Confirmed 2026-10-16. The +, -, resume buttons are not on this bus."),
   S("VehicleSpeed", 41, 10, "big_endian", 0.25, unit="km/h", comment="Low 10 bits of bytes 5-6, /4. Firmware: confirmed working.")]),
 (0x0A10408, "TurnLamps", "Turn indicator lamps, toggling with the flash (about 1.5 Hz). Only sent while indicators run; hazards set both bits (0x0E). Confirmed 2026-10-15/16.", [
   S("TurnLampLeft", 57), S("TurnLampRight", 58)]),
 (0x131726C, "SteeringWheelModule", "Steering wheel module: keys (firmware swm handler), turn and wiper stalks.", [
   S("ClimateDemand", 0, 6, comment="Byte 0 bits 0-5. Jumps with temperature setpoint changes and decays; 0 with AC off; 0x1F briefly after a climate button. Climate controller demand, NOT the displayed setpoint. Bit 7 toggles every frame."),
   S("RearWiperSwitch", 12, comment="Rear wiper switch on. Confirmed 2026-10-15."),
   S("WiperHigh", 33), S("WiperMedium", 34), S("WiperIntermittent", 35, comment="Front wiper stalk: off, intermittent, medium, high (bits 3, 2, 1). All clear = off. Confirmed 2026-10-15."),
   S("WiperUnknown", 36, comment="Set for 0.5 s once after the stalk went to off. Possibly the washer; unconfirmed."),
   S("WiperInterval", 37, 3, comment="Interval ring position 0-7 (faster wipes with higher values: about 19, 12, 8 s at standstill). Confirmed 2026-10-15."),
   S("TripWheel", 40, 3, comment="Trip computer thumbwheel on the left stalk. Changes on every notch (seen 0, 3, 5, 7, then 4 turning back); encoding unclear, probably a rotary code."),
   S("WiperSingle", 47, comment="Stalk pushed up for a single wipe. Confirmed 2026-10-15."),
   S("NavRight", 48, comment="Left and right are swapped compared with MY2007."), S("NavLeft", 49), S("NavDown", 50), S("NavUp", 51),
   S("NavBack", 52), S("NavEnter", 53),
   S("TurnStalkRight", 54, comment="Confirmed 2026-10-15."), S("TurnStalkLeft", 55, comment="Confirmed 2026-10-15."),
   S("KeyPrev", 56), S("KeyNext", 57), S("KeyVolumeDown_n", 58, comment="Active low."), S("KeyVolumeUp_n", 59, comment="Active low."),
   S("KeyHangup", 60), S("TripReset", 63, comment="Trip computer reset button (end of the left stalk). Confirmed 2026-10-16."), S("KeyPickup", 61, comment="Pickup and hangup are swapped compared with MY2007.")]),
 (0x12173BE, "DoorsRadarLock", "Rear electronic module: doors, rear park assist (firmware rem handler) and central locking.", [
   S("RearRadarActive", 16), S("RearRadarDistance", 27, 5, comment="Nearest obstacle, one value for all rear sensors. The firmware scales 0..31 to 0..99."),
   S("BonnetA", 40, comment="Firmware treats bit 0 or bit 6 as bonnet open."), S("DoorFL", 41), S("DoorFR", 42), S("DoorRL", 43), S("DoorRR", 44),
   S("Tailgate", 45), S("BonnetB", 46),
   S("CentralLock", 56, 2, choices={1: "Locked", 2: "Unlocked", 3: "LockedArmed"}, comment="Central locking state (inside button and key fob, confirmed 2026-10-15/16). 3 appears 26 s after locking with the fob, probably the alarm arming; unconfirmed. After a fob lock most modules stop sending within 3 s and the bus is silent about 1 minute later; the fob unlock wakes it, first frame 0x1B500000.")]),
 (0x14034A2, "DriverDoorModule", "Driver door module: window switches, rear-window lock, driver window state.", [
   S("PassengerWindowUpSwitch", 16), S("PassengerWindowDownSwitch", 18),
   S("RearWindowLock", 23, comment="Rear-window lock button state, 1 = rear windows locked. Confirmed 2026-10-15."),
   S("RearLeftWindowUpSwitch", 28), S("RearLeftWindowDownSwitch", 29), S("RearRightWindowUpSwitch", 30), S("RearRightWindowDownSwitch", 31),
   S("DriverWindow", 32, 2, choices={1: "Closed", 2: "Open"}, comment="Confirmed 2026-10-15. No such state was seen for the other windows."),
   S("LockedEcho", 44, comment="Set while locked (follows CentralLock).")]),
 (0x1E0162A, "Sunroof", None, [
   S("SunroofState", 16, 8, choices={0: "Closed", 1: "Moving", 2: "Open"}, comment="00 closed, 01 briefly while moving, 02 open (tilted vs slid not yet separated). Confirmed 2026-10-15."),
   S("WiperSingleEcho", 53, comment="Follows WiperSingle.")]),
 (0x2510020, "SteeringAngle", "Steering angle, sign-magnitude, coarse. The firmware notes the direction is reversed.", [
   S("SteeringDirection", 42, choices={0: "Negative", 1: "Positive"}), S("SteeringAngleMagnitude", 48, 6)]),
 (0x2616CFC, "RearFog", None, [
   S("RearFogA", 21, comment="Rear fog light on. Confirmed 2026-10-15 (one of the two bits is probably the switch, the other the lamp)."),
   S("RearFogB", 31)]),
 (0x2803008, "IllumRpmBeam", "Illumination (firmware lsm1), main beam and engine rpm.", [
   S("HighBeam", 12, comment="Main beam, including a flash. Confirmed 2026-10-15."),
   S("NightIllumination", 18, 2), S("EngineSpeed", 51, 12, "big_endian", unit="rpm", comment="Low 12 bits of bytes 6-7. Firmware: confirmed working.")]),
 (0x2006428, "IgnitionWiper", "Key position (firmware acc handler) and front wiper motor.", [
   S("WiperMotorRunning", 9, comment="Set briefly at the start and end of each wipe."),
   S("IgnitionOn", 13, comment="Byte 1: 0xE3 running (bit 7 toggles), 0x43 key at accessory, 0x03 key out. Seen at switch-off 2026-10-16; the bus stayed awake after key out."),
   S("AccessoryOn", 14),
   S("WiperParked", 23, comment="0 for about 1 s during each front wipe. Confirmed 2026-10-15.")]),
 (0x3200428, "GearBrakeRear", "Gear selector (firmware gear handler), brake pedal, rear wiper output.", [
   S("RearWiperActive", 18, comment="On while the rear wiper runs. Confirmed 2026-10-15."),
   S("BrakePedal", 34, comment="Brake pedal pressed. Confirmed 2026-10-15."),
   S("GearPosition", 52, 3, choices={1: "P", 2: "R", 3: "N", 4: "D"})]),
 (0x4000002, "Odometer", "Firmware: confirmed working.", [S("OdometerKm", 47, 24, "big_endian", unit="km")]),
 (0x381526C, "FuelLevel", "Byte 5 increments slowly (counter).", [
   S("FuelLevelPercent", 48, 8, unit="%", comment="Firmware: likely correct; tank 80 l on the V8.")]),
 (0x2202262, "DriverBelt", None, [
   S("ParkingBrakeEcho", 31, comment="Follows ParkingBrakeApplied."),
   S("DriverBeltBuckled", 35, comment="Firmware: confirmed working.")]),
 (0x3A04004, "ParkingBrake", None, [
   S("ParkingBrakeApplied", 8, choices={0: "Released", 1: "Applied"}, comment="1 = applied: released and reapplied with the pedal on 2026-10-15. The firmware sends ~bit (park_break = ~msg[1] & 1) and calls it confirmed; check which sense the head unit expects.")]),
 (0x3C01428, "OutsideTemp", None, [S("OutsideTempRaw", 48, 8, comment="Scaling not worked out (firmware TODO); read 0 on 2026-10-15.")]),
 (0x4200002, "ClimateBlower", "Climate blower and recirculation. Confirmed 2026-10-15.", [
   S("RecirculationFlap", 0, 8, unit="%", comment="100 (0x64) in manual recirculation, 0 in off and auto."),
   S("BlowerRamp", 24, 8, comment="Follows BlowerLevel with a larger scale and wraps past 0xFF. Use BlowerLevel."),
   S("BlowerLevel", 56, 8, choices={0: "Off", 0x11: "Step1", 0x20: "Step2", 0x2F: "Step3", 0x40: "Step4", 0x54: "Step5", 0x6C: "Step6", 0x86: "Step7"},
     comment="Fan step. Ramps through about one intermediate value per 0.7 s between steps. AUTO and defrost choose their own value (defrost: 0x86).")]),
 (0x0E01008, "ClimateAc", "Bytes 3 and 5 move with blower load. The firmware's commented-out ccm handler guessed recirculation was in byte 1 here; it is in 0x4200002 byte 0.", [
   S("AcOff", 3, 2, choices={0: "On", 3: "Off"}, comment="0x03 with AC on, 0x1B with AC off (also when the fan is at 0). Confirmed 2026-10-15.")]),
 (0x0C00402, "ClimateHeaters", "Byte 3 tracks the climate demand like 0x131726C byte 0. Byte 7 is analog.", [
   S("RearWindowHeater", 55, comment="Confirmed 2026-10-15.")]),
 (0x3000042, "ClimateState", "Bytes 3 and 7 are analog climate values (air mix, probably evaporator or outlet temperature).", [
   S("AcActiveB", 32, comment="Clears with AC off."),
   S("DisplayEvent", 36, comment="Drops for about 0.1 s on trip computer READ and thumbwheel use, and on some climate changes. Meaning unclear."), S("AcActiveA", 55, comment="Clears with AC off.")]),
]
msgs = [Message(fid, name, 8, sigs, is_extended_frame=True, comment=c, senders=[]) for fid, name, c, sigs in M]
db = Database(msgs, nodes=[cantools.database.can.Node("XC90", None)], version="xc90-2008my-lowspeed-2")
txt = db.as_dbc_string()
hdr = ('CM_ "Volvo XC90 MY2008 (P2), low-speed CAN: 125 kbit/s, 29-bit ids, OBD pins 3/11. Decoded by passive sniffing '
       '(GVRET listen-only) and from canbox-xc90-my2008 cars/xc90_2008my.c; signals marked Confirmed were checked step by step on '
       '2026-10-15. NOT on this bus: the temperature setpoints (both sides), seat heat, an AUTO flag, front fog state, and the '
       'passenger and rear window states.";\n')
txt = txt.replace("\nCM_ BO_", "\n" + hdr + "CM_ BO_", 1)
open(OUT, "w").write(txt)
db2 = cantools.database.load_file(OUT)
print(len(db2.messages), "messages,", sum(len(m.signals) for m in db2.messages), "signals")
for m in db2.messages: print(f"  0x{m.frame_id:07X} {m.name}")

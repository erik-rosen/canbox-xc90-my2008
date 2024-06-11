# Volvo XC90 (2007+)

First of all, im not responsible for any damage or anything that happens to your devices/car.

This is a project for advenced people, everyone can attempt it, all information  is available on the internet. If you have a problem, first of all search well the intertet, i won't reply matters that i consider trivial.

It will only work on XC90 Mark I - 2007MY and after. The canbus codes change between model years.

Now to the point.

What you will need:

    Brain
    Volvo canbox -> Model  OD OLO 02 
    Stm32 programmer -> Stlink v2
    Computer -> Preferably linux

What you might need:
    Serial to USB adapter -> uart to usb 3.3v logic
    Dupont cables
    Soldering iron


## Revert back

We will be writing a new firmware to the canbox, if you want to reverse the canbox, you are lucky!! i hacked the canbox and extracted the original chinese firmware: 

https://github.com/jesusvallejo/VolvoCanBusFirmware 

Just download the firmware and flash it. The procedure is the same as when flashing the custom firmware.

## Flashing ( Linux )
### Set up

- Download firmware: volvo_od2.bin 
- Download openocd -> apt install openocd
- Connect the Stm32 programmer and the can box:
    - Open the canbox to expose the pcb
    - With the conector to the left you will see 4 vias at the bottom, name in pcb silkscreen is CON2
    - Left to right the conector is:  CON2 -> VCC(3.3v) SWDIO GND SWCLK 
    - Connect accordingly with your Stm32 programmer, you could solder some cables or use dupont males or whatever.

- Edit the file ocd-program.cfg, the first two lines configure the CPU of the canbox.
    - if it is an original stm32 (not likelly):
        `
        #set CPUTAPID 0x2ba01477
        set CPUTAPID 0X1ba01477
        `

    - if fake stm32:
        `
        set CPUTAPID 0x2ba01477
        #set CPUTAPID 0X1ba01477
        `

    More info regarding this and fake stm32 can be found on the internet.

### Flash firmware
Save, connect to the usb the programmer and execute,dont waste time or you will loose the programming window time: 
    
`openocd -f ocd-program.cfg`

Too slow example:

`
        Open On-Chip Debugger 0.12.0
        Licensed under GNU GPL v2
        For bug reports, read
            http://openocd.org/doc/doxygen/bugs.html
        Info : auto-selecting first available session transport "hla_swd". To override use 'transport select <transport>'.
        Info : The selected transport took over low-level target control. The results might differ compared to plain JTAG/SWD
        Info : clock speed 1000 kHz
        Info : STLINK V2J38S7 (API v2) VID:PID 0483:3748
        Info : Target voltage: 3.183865
        Error: init mode failed (unable to connect to the target)
`

Correct flashing example :

`
        Open On-Chip Debugger 0.12.0
        Licensed under GNU GPL v2
        For bug reports, read
            http://openocd.org/doc/doxygen/bugs.html
        Info : auto-selecting first available session transport "hla_swd". To override use 'transport select <transport>'.
        Info : The selected transport took over low-level target control. The results might differ compared to plain JTAG/SWD
        Info : clock speed 1000 kHz
        Info : STLINK V2J38S7 (API v2) VID:PID 0483:3748
        Info : Target voltage: 3.180234
        Info : [stm32f1x.cpu] Cortex-M3 r1p1 processor detected
        Info : [stm32f1x.cpu] target has 6 breakpoints, 4 watchpoints
        Info : starting gdb server for stm32f1x.cpu on 3333
        Info : Listening on port 3333 for gdb connections
        [stm32f1x.cpu] halted due to debug-request, current mode: Thread 
        xPSR: 0x01000000 pc: 0x080041c8 msp: 0x20004000
        Info : device id = 0x20036410
        Info : flash size = 128 KiB
        [stm32f1x.cpu] halted due to debug-request, current mode: Thread 
        xPSR: 0x01000000 pc: 0x080041c8 msp: 0x20004000
        [stm32f1x.cpu] halted due to debug-request, current mode: Thread 
        xPSR: 0x01000000 pc: 0x080041c8 msp: 0x20004000
        ** Programming Started **
        Warn : Adding extra erase range, 0x0800e290 .. 0x0800e3ff
        ** Programming Finished **
        ** Verify Started **
        ** Verified OK **
`
### Windows 
Download a stm32 flashing program and flash the volvo_od2.bin firmware. See linux for the connections between the programmer and the canbox.
You may run into problems.

## Configuration 

### Serial (UART -> USB)

By default the canbox will be set up as a Volvo XC90 canbox, and the mode to VW (PQ). A serial adapter can be used as stated on the original project to change this, and other parameters. See README.md
    

### Head unit.


Connect again the canbox to the car.

You could need to change the CAN settings on your head unit factory settings to VW PQ. With the original OUDI XC90 setting everything seems to work.
This project is attempting to add climate visualization, when time comes you will need to change to VW your head unit settings PQ to visualize it.

The original setting is:
    
    Canbox: 04:OuDi
    Cars for: 3C:Volvo
    Models for: 02:XC90
    Config: Public
    Logo: 


If camera trajectory is reversed, change it on the HU settings . 
If next/prev are the otherway round, change it on the HU settings.
If the doors are mixed, chage it in the HU, if not showing turn it on. 

The head unit factory settings menu changes with the provided password:

    8888
    123456

## Advantages

Enter phone button will accept and reject/hangup, exit phone button will trigger the assistant (ok google/ siri).
Other buttons should behave as expected.

If you have RTI, those buttons can also be mapped, it would be nice to know more chinese payloads to use these too. Unless it makes sense i wont be accepting requests to map those buttons, read the code and map them to what ever you need. 

You could use the pins of the canbox as originally intended (I'm doing it):
    Acc pin to power on/off the head unit almost instantly after taking out the key.
    Powering the reverse camera,delay after changing to D, you can see for 1.5s the backup camera.

Day/Night mode is based on the cars illum sensor.

## Will continue...
We could try to preassure the Legend guy so he asks to the "Factory" the payloads that the HU accepts, id like to map accept to accept and reject to reject, not like it is right now one button for both.

Acc visualization might get never implemented, canbus reverse engineer is not easy, and takes too much time.

If any one wants to take the time to add more information about flashing on windows or whatever, feel free to pull request.

















    






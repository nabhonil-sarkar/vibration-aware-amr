# NUCLEO-F401RE pin plan (v0.1, 17 Nov 2026)

Board identified by the student as NUCLEO-F401RE. Pins checked against ST UM1724 (Nucleo-64 user manual, Arduino connector table for F401RE/F411RE). Not yet wired or tested.

## Signal wiring

| Function | Nucleo pin (Arduino name) | MCU pin | Goes to |
|---|---|---|---|
| Left motor PWM | D7 | PA8 (TIM1_CH1) | TB6612 PWMA |
| Left motor dir 1 | D2 | PA10 | TB6612 AIN1 |
| Left motor dir 2 | D4 | PB5 | TB6612 AIN2 |
| Right motor PWM | D8 | PA9 (TIM1_CH2) | TB6612 PWMB |
| Right motor dir 1 | D5 | PB4 | TB6612 BIN1 |
| Right motor dir 2 | D6 | PB10 | TB6612 BIN2 |
| Driver enable | D9 | PC7 | TB6612 STBY |
| Left encoder A | A0 | PA0 (TIM2_CH1) | left motor encoder A |
| Left encoder B | A1 | PA1 (TIM2_CH2) | left motor encoder B |
| Right encoder A | D12 | PA6 (TIM3_CH1) | right motor encoder A |
| Right encoder B | D11 | PA7 (TIM3_CH2) | right motor encoder B |
| I2C SCL | D15 | PB8 | both IMUs SCL |
| I2C SDA | D14 | PB9 | both IMUs SDA |
| Link to Pi | USB (ST-LINK) | PA2/PA3 (USART2) | Pi 5 USB port, appears as /dev/ttyACM0 |
| Status LED | LD2 (on board) | PA5 | do not connect anything to D13 |
| Stop button | B1 (on board, blue) | PC13 | press = motors off |

Keep clear: D0/D1 (they carry the USB serial link by default), D13 (LED).

## Power and ground

- Nucleo: powered from the Pi's USB through the ST-LINK USB socket (power jumper in its default U5V position). One cable carries power, programming and the serial link.
- TB6612 VCC (logic): Nucleo 3V3. TB6612 VM (motor): 12 V from the relay output. TB6612 GND: common ground.
- Encoders: VCC to Nucleo 3V3, GND to GND. Motor connector order confirmed with a meter on both motors (17 Nov): 1 M1, 2 GND, 3 A, 4 B, 5 VCC, 6 M2 (A/B may be swapped: flip ENC_INVERT if counts run backwards).
- IMUs (GY-521 type): VCC to 3V3, GND to GND, SCL/SDA as above. Chassis IMU AD0 to GND (address 0x68); deck IMU AD0 to 3V3 (address 0x69). Connect both IMUs before powering up; the firmware sets them up only at boot.
- All grounds common: battery negative, buck output negative, TB6612 GND, Nucleo GND, encoder and IMU GND.

## Limits to respect

- The TB6612 is rated about 1.2 A continuous per channel (3.2 A peak); the motor's stall current (~1.3 A) is just above the continuous rating. Don't hold a wheel stalled; the firmware's PWM limit (default 600 of 1000) and slew limit help.
- TB6612 VM maximum is 15 V; a fully charged 3S Li-Po is 12.6 V.

## Flashing

Arduino IDE 2 -> Preferences -> Additional boards manager URLs: `https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json`; Boards Manager: install "STM32 MCU based boards" (3.1.0 used). Tools: Board "Nucleo-64", Board part number "Nucleo F401RE" (check it: it can reset to C031C6 when a sketch is reopened).

**Do not use Upload method "Mass Storage" on this board.** On 17 Nov 2026, sketches of about 44 KB and larger never started after a drag-and-drop upload, although the IDE reported "Upload complete"; 13 and 22 KB sketches worked. The firmware is about 46 KB. Cause: the board's ST-LINK firmware. Two ways that work:

1. **IDE debugger (used on 17 Nov, works):** Sketch -> Optimize for Debugging; Tools -> Debug symbols "Symbols Enabled (-g)"; click the Debug button. It flashes over SWD and stops at a breakpoint; press Continue, or end the session and press the board's RESET. The firmware then runs on its own after every reset.
2. **STM32CubeProgrammer (recommended):** install it from st.com, then Tools -> Upload method "STM32CubeProgrammer (SWD)". Its Firmware upgrade button also updates the ST-LINK, which should fix drag-and-drop.

Serial Monitor: 230400 baud, New Line. Uploading drops the monitor's connection: close and reopen it afterwards. Only keep one IDE window with a monitor open.

Checked on 17 Nov 2026 (one IMU wired, motors not connected): `T` lines at 100 Hz; IMU 1 reads about 0.96 g at rest; `P,0,0` sets flags to 9 then 10 after 0.5 s (command received, timeout works).

## Bench order (wheels off the ground, relay off until step 4)

1. Flash, open the Serial Monitor: an `I,...` line shows. `imu1_who`/`imu2_who` show 0x68 for MPU6050 (0x70 or 0x71 means an MPU6500/9250 clone; the firmware still works).
2. `T,...` lines stream at 100 Hz. Do NOT turn the wheels by hand to test the encoders: the worm gearbox is likely self-locking and forcing it can strip the gears. Use the motor instead (steps 3 and 4).
3. Relay on. Commands time out after 0.5 s, so use the test script, which re-sends them: `python3 ../drive_link_test.py --pwm 150 0 --seconds 3` (add `--port COM5` or similar on Windows). The left wheel must turn forward; if not, flip `LEFT_MOTOR_INVERT`. While it turns forward, `encL` must count up; if not, flip `LEFT_ENC_INVERT`. Same for the right with `--pwm 0 150`.
4. Counts per wheel revolution: put a tape mark on the wheel at the top, run `--pwm 150 0 --seconds 30`, count the turns (estimate the last part-turn from where the mark stops), and divide the final `encL` by the turns. Write this number down: it converts m/s to counts/s.
5. Stop sending: within 0.5 s the wheels stop, the LED blinks fast, and flags bit 1 is set. This is Wednesday's pass check.
6. Speed loop: `V,<counts/s>,<counts/s>` and tune `K,kp,ki,kf` until speed follows the target without oscillating.

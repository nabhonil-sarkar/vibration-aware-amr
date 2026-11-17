# Build log, 17 November 2026

First assembly day. Photos taken during the build; numbers are the student's caliper readings.

| Photo | What it shows |
| --- | --- |
| [01](01_baseplate_printed.jpg) | Printed baseplate (part 01). Some small holes printed undersize or skinned over; they are opened with 3.4 / 4.5 mm drills as needed |
| [02](02_motor_wheel_fitted_top.jpg) | JGY-370-CE motor with the wheel fitted on its brass hex adapter |
| [03](03_motor_can_and_encoder.jpg) | Motor can (marked XYT-12V-6000) and Hall encoder board |
| [04](04_wheel_gap_side.jpg) | Side view: gap between gearbox face and wheel, measured 6.1 mm |
| [05](05_encoder_end_with_wheel.jpg) | Encoder end with the wheel fitted |
| [06](06_encoder_board_connector.jpg) | Encoder board: two Hall sensors, 6-pin connector labelled only at pin 1 (M1) |
| [07](07_motor_label_JGY-370-CE.jpg) | Motor label: XYT JGY-370-CE, DC 12 V 40 RPM |
| [08](08_caliper_motor_overall_length.jpg) | Overall motor length, about 86.6 mm |
| [09](09_caliper_wheel_width.jpg) | Wheel width, 26.90 mm |
| [10](10_ball_caster_side.jpg) | 12 mm nylon ball caster |
| [11](11_ball_caster_base_slots.jpg) | Caster base: two U-slots, 3.3 mm wide, centres 14.7 mm apart |

Other measurements: wheel diameter 66.32 mm; gearbox 46.46 x 31.76 x 22.38 mm; caster 18 mm from mounting face to ball bottom, flange 1.9 mm thick. These drove the v05.2 revision of parts 10 to 15 ([cad/v05](../../../cad/v05)).

Also done today: wheels fitted (grub screws on the shaft flat, centre screw into the adapter); STM32 board identified as a NUCLEO-F401RE and first firmware written ([firmware](../../../firmware)); wiring diagram v1 drawn ([docs/wiring](../../wiring)). Later the same day: firmware v0.2 flashed and running (see below). Not yet done: motor driver wiring, any powered motor test.

## Later on 17 November: battery, firmware, screenshots

| Photo | What it shows |
| --- | --- |
| [12](12_print_files_folder.png) | Screenshot: the v05.2 print files (parts 10 to 15) ready to print |
| [13](13_firmware_running_serial_monitor.png) | Screenshot: firmware v0.2 running on the Nucleo; Arduino IDE Serial Monitor showing the 100 Hz `T,...` telemetry with IMU 1 readings |
| [14](14_arduino_board_settings.png) | Screenshot: Arduino IDE board settings (Nucleo-64, F401RE, COM3). The upload method shown, Mass Storage, is the one that fails for binaries this size on this board; the firmware was flashed with the IDE debugger instead (see [PIN_PLAN.md](../../../firmware/nucleo_f401re_base/PIN_PLAN.md)) |
| [15](15_battery_position_v05_2.png) | Planned battery position on the v05.2 baseplate: flat under the controller shelf, 85 mm side across the robot, two velcro straps through the existing strap slots, switch and cable toward the robot's right |
| [16](16_baseplate_top_view.jpg) | Printed baseplate, top view |
| [17](17_battery_on_baseplate.jpg) | Battery test-placed on the baseplate |
| [18](18_battery_label.jpg) | Battery label: DC 12480, 12.6 to 10.8 V, 4800 mAh |
| [19](19_battery_switch_end.jpg) | Battery end with the built-in on/off switch |
| [20](20_battery_cable_end.jpg) | Battery cable end |
| [21](21_battery_with_cable.jpg) | Battery with its DC barrel-plug cable |
| [22](22_nucleo_wired_imu.jpg) | NUCLEO-F401RE (MB1136 rev C) wired to the IMU: I2C on D15/D14, supply and ground from the power header, USB to the PC |

Battery measured 85 x 56.7 x 24 mm. The label gives no discharge-current rating.

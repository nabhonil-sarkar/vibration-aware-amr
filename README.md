# Vibration-Aware Autonomous Mobile Robot

An Individual Major Project investigating whether payload-IMU feedback and bounded motion adaptation can reduce vibration during indoor transport of a representative fragile payload.

The robot is a **custom two-wheel differential-drive platform with a rear ball caster**, a passively isolated payload deck and a **1 kg carried-load target**. It is not a TurtleBot. Speed is adapted from measured payload vibration; active vibration cancellation is not part of the project.

**Current stage (17 November 2026): IMP Part B, first physical build.** The v05 baseplate is printed and the remaining parts are printing. Motors, wheels and caster have been measured and the drive parts rebuilt to suit. The NUCLEO-F401RE firmware and wiring diagram are written but not yet flashed, wired or tested. No vibration, docking or navigation result exists yet.

![AMR v05.2 concept](cad/v05/images/AMR_v05_2_Concept.png)

## What is here

| Folder | Contents | Evidence status |
| --- | --- | --- |
| [cad/v05](cad/v05) | **Current design.** Single-piece baseplate robot: STEP and STL of every printed part, full assembly STEP, generators, checks, renders, measured dimensions | Geometry checks only; baseplate printed, other parts printing or not yet printed; no load test |
| [firmware](firmware) | NUCLEO-F401RE base controller: TB6612 PWM, encoders, two IMUs, serial link to the Pi, 0.5 s command timeout; Pi-side link test | Syntax-checked only; not compiled for the board, flashed or run |
| [docs/wiring](docs/wiring) | Wiring diagram v1 (PNG/SVG/PDF) and its generator | Planned connections; not yet wired |
| [docs/build_log](docs/build_log) | Dated build photos and measurements | Photos of the real parts |
| [software/vibration_aware_control](software/vibration_aware_control) | Python controller core, ROS 2 adapter, unit tests and synthetic demo | 20 offline tests pass; hardware untested |
| [software/aruco_stations](software/aruco_stations) | ArUco station seeking (pickup, drop-off, recharge), printable markers, dry-run runner | Offline tests and a synthetic simulation only; not run on the robot |
| [software/lidar_slam_examples](software/lidar_slam_examples) | RPLIDAR A1 capture and simple scan-matching SLAM examples for the Pi 5 | Replayed on recorded A1 scans; mapping is further work |
| [cad/full_robot_v04](cad/full_robot_v04), [cad/printing_x1c_pla](cad/printing_x1c_pla), [cad/chassis_v03](cad/chassis_v03), [cad/concept_v02](cad/concept_v02) | Earlier concepts and the v03 split chassis | Superseded by v05; kept for the design history |
| [simulation/four_wheel_alternative](simulation/four_wheel_alternative) | MATLAB kinematics for the earlier skid-steer alternative | Not the current robot |
| [docs](docs) | Project status and repository scope | Planning documentation |

## Hardware in use

Raspberry Pi 5 (logging, camera, LiDAR, speed-adaptation decisions), NUCLEO-F401RE (wheel control, encoders, IMU acquisition, command timeout), TB6612FNG driver, 2 x JGY-370-CE 12 V 40 RPM worm-gear Hall-encoder motors, 66 mm wheels, 12 mm ball caster, 2 x MPU-6050 IMUs (chassis and isolated deck), RPLIDAR A1, Raspberry Pi AI Camera, 12 V Li-Po with a 5.1 V buck for the Pi and a relay motor cut-off.

![Wiring diagram v1](docs/wiring/AMR_Wiring_Diagram_v1.png)

## Start here

- **Printing:** [cad/v05/README.md](cad/v05/README.md) has the part list, insert and screw table, and the measured dimensions.
- **Firmware:** [firmware/nucleo_f401re_base/PIN_PLAN.md](firmware/nucleo_f401re_base/PIN_PLAN.md) has the pin table, flashing steps and the bench order. Test with the wheels off the ground.
- **Controller tests** (Python 3.10 or newer, standard library only):

```sh
cd software/vibration_aware_control
python -m unittest discover -s tests -v
python -m vibration_aware_control.demo
```

The demo chart shows command adaptation and a sensor-dropout stop on synthetic input. It does **not** show achieved physical vibration reduction.

## Planned experiment

Fixed slow, fixed fast and speed-adaptive runs over a bump track, five runs each, logging both IMUs; isolated deck against rigid deck if isolators are sourced in time. The outline targets at least 20 % lower RMS payload vibration for no more than 20 % longer journey time. **These are targets, not results.**

## Before physical use

The 5 A fuse is not yet fitted; until it is, battery tests are short and supervised and the motors are not powered from the battery. Confirm the encoder connector pin order with a meter before wiring. The software is not safety-rated; first drives are at low speed with the wheels off the ground and the relay cut-off within reach.

See [project status](docs/PROJECT_STATUS.md) for what is done and what is open. Academic submissions and personal forms are intentionally kept outside this repository. No open-source licence has been selected.

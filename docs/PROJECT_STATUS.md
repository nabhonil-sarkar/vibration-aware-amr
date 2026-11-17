# Project status

Snapshot: 17 November 2026. Report due 25 November 2026. The previous snapshot (7 October) is in this file's Git history.

## Done

- Risk assessment signed by the supervisor and the lab engineer.
- All parts from the parts list bought (Kuriosity, Singapore) except the items under "Not yet sourced".
- v05 design: single-piece printed baseplate, motor cradles, caster block, skids, payload deck and sensor bridge ([cad/v05](../cad/v05)).
- Baseplate printed (17 Nov). Parts 00, 02 to 08 printing.
- Motors, wheels and caster measured with vernier calipers; parts 10 to 15 rebuilt from the measurements (v05.2) and checked in CAD for interference.
- Wheels fitted to the motors.
- STM32 board identified as a NUCLEO-F401RE; pin plan and base firmware v0.1 written ([firmware](../firmware)); wiring diagram v1 drawn ([docs/wiring](wiring)).
- Offline software: vibration-aware control core (20 tests), ArUco station seeking (offline tests, synthetic simulation), LiDAR capture and SLAM examples (replayed on recorded scans).
- Pi 5, AI Camera and RPLIDAR A1 bench-verified in October.

## Not yet done

- Firmware compiled, flashed and run on the Nucleo; Pi-to-Nucleo link and timeout test.
- Wiring on the robot; Pi running from the battery through the buck.
- Printing and fit-checking parts 10 to 15; full mechanical assembly.
- First drives, IMU logging, trial runs, analysis.
- ArUco station seeking on the real camera and robot.

## Not yet sourced or confirmed

- 5 A inline fuse and holder.
- Four soft payload isolators about 14 mm tall.
- Half-size breadboard.
- The lab engineer's acceptance of the relay motor cut-off in place of a mushroom E-stop.
- Battery maximum discharge current.

## Still assumed in the design

- Motor shaft centred top to bottom and 11 mm from the gearbox free end (adjustable by 15 mm in the baseplate slots).
- Isolator height 14 mm (sets riser length).
- Encoder connector pin order beyond pin 1 (to be confirmed with a meter).
- Camera hole pattern 21 x 12.5 mm.

## Scope

Recommended: keep the vibration comparison and the ArUco station demo; report LiDAR SLAM mapping and a web dashboard as further work. Active vibration cancellation is outside the scope.

No physical assembly result, vibration improvement, docking performance or autonomous navigation result is claimed.

# Project status

Snapshot: 25 November 2026 (report due today). Earlier snapshots (7 October, 17 November) are in this file's Git history.

## Done

- Risk assessment signed by the supervisor and the lab engineer.
- Parts from the parts list bought (Kuriosity, Singapore) except the items under "Not yet sourced".
- Motors, wheels and caster measured with vernier calipers; drive parts rebuilt from the measurements.
- NUCLEO-F401RE firmware v0.2 flashed through the debugger (SWD) and running: 100 Hz telemetry, commands received, 0.5 s command timeout works (driver disabled 0.47 s after the last command). Mass-storage upload does not start programs of about 44 KB or more on this board.
- Encoder connector order confirmed with a meter: 1 M1, 2 GND, 3 A, 4 B, 5 VCC, 6 M2.
- Right motor bench test, 18 Nov: PWM 150 of 1000 does not start the worm gearbox; PWM 300 turns it at about 1,070 encoder counts/s.
- Both motors mounted on the first baseplate and run under firmware command, 19 Nov.
- Motor cradle v05.2 cracked on first fit; replaced by the clamping v05.3 cradle ([cad/v05](../cad/v05)).
- Baseplate v05.4 (M3-width outer motor slots, IMU slots, motor-wire holes) printed, 24 Nov; assembly started.
- Sensor bridge assembled: RPLIDAR A1 on its own legs with the USB adapter under it, AI Camera on the front tab ([docs/assembly](assembly)).
- Pi 5 bring-up, 24 Nov (robot not moving, Pi on mains):
  - RPLIDAR A1 live: health Good, about 7 scans per second, about 145 returns per scan ([sample results](../software/lidar_slam_examples/sample_results/real_lidar_live_2026-11-24)).
  - AI Camera (IMX500) detected; the ArUco station finder ran with `--picamera` at 1014 x 760 without errors (no marker in view).
  - Pi to Nucleo link over USB (`/dev/ttyACM0`): telemetry received continuously.
  - No under-voltage with the LiDAR and camera connected (`throttled=0x0`).
- Offline software: vibration-aware control core (20 tests), ArUco station seeking (13 tests, synthetic simulation), LiDAR capture and SLAM examples (9 tests, replays).

## Not yet done

- Both IMUs wired and read; axis check by tilting.
- Left motor results recorded; encoder counts per wheel turn; speed-loop tuning.
- Full assembly on the v05.4 baseplate; Pi running from the battery through the buck.
- LiDAR angle offset relative to the robot's front.
- ArUco distance and bearing check against a printed marker; station finding on the moving robot.
- First drives, IMU logging, vibration trials, analysis.

## Not yet sourced or confirmed

- 5 A inline fuse and holder.
- Four soft payload isolators about 14 mm tall (the printed 14 mm rigid spacers give the rigid-deck condition).
- M4 x 25 screws for the rigid spacers.
- The lab engineer's acceptance of the relay motor cut-off in place of a mushroom E-stop.
- Battery maximum discharge current.

## Still assumed in the design

- Motor shaft centred top to bottom in the gearbox (the left motor is mounted upside down).
- Isolator height 14 mm (sets riser length).
- Camera hole pattern 21 x 12.5 mm (check against the board).

## Scope

Kept: the vibration comparison and ArUco station finding. Reported as further work: LiDAR SLAM mapping, Nav2 navigation and a web dashboard. Active vibration cancellation is outside the scope.

No vibration improvement, docking performance or autonomous navigation result is claimed.

## Pi network note

Over a direct Ethernet cable the Pi's `netplan-eth0` connection is set to link-local addressing (`nmcli connection modify netplan-eth0 ipv4.method link-local ipv6.method link-local`); with DHCP it kept restarting and dropping SSH. Set `ipv4.method auto` again to use a router. From Windows, `amr-pi.local` resolves over IPv6, so use `ssh nabhonil@amr-pi.local` without `-4`.

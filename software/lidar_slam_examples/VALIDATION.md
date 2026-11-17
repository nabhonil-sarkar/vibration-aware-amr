# Validation - 28 October 2026

Tested locally on Windows with Python 3.12, NumPy 2.5.4, SciPy 1.18.1,
Matplotlib 3.11.2, pyserial 3.5 and rplidar-roboticia 0.9.5.
The Pi instructions use Raspberry Pi OS scientific-library packages instead.

## Passed

- Nine automated tests: angle/units/invalid-return filtering; known rigid
  transform recovery; free/occupied/unknown grid cells; rejected-scan map
  preservation; synthetic movement estimation; SDK partial-revolution handling;
  JSONL round-trip; independent shutdown steps following a processing error;
  exported PGM orientation and YAML origin.
- The motion test estimates a 0.6 m translation plus 10-degree rotation from
  35 synthetic scans, with test limits of 8 cm position error and 2 degrees
  heading error. Ground truth is not passed into the estimator.
- Full SLAM command on 80 synthetic scans completed, with 80 accepted and
  zero rejected. Output images and map exports were generated.
- LiDAR and SLAM commands each replayed the user's original 7 October
  `lidar-test.txt`: 56 complete inferred revolutions. All 56 were accepted by
  the mapper. The first/last partial revolutions were discarded.
- The three generated preview images were visually inspected.
- Installed Python driver's constructor and scan-method signatures match the
  calls used by the scripts.
- All three wiring PDF pages were rendered and visually checked.

## Not established

- No connection to the physical Pi, serial adapter or STM32 was made for this
  task. Live serial operation, actual motor stop, Pi installation, real-time
  throughput and interactive desktop plotting remain to be tested.
- The real recording is a mostly stationary bench scene, not a traversed room.
  Its replay tests parsing and map accumulation, not navigation or pose accuracy.
- A successful synthetic test does not validate mapping accuracy in a real room.
  ICP may drift or accept incorrect matches in ambiguous geometry. No loop closure,
  encoder fusion, IMU fusion, Nav2 integration or autonomous driving is included.
- Proposed motor wiring is conditional on actual purchased driver/motors and
  verified power ratings. Physical STM pin assignment awaits the board model.

## Sample results

- `sample_results/real_lidar_replay/scan.png`: last scan of the old bench log.
- `sample_results/real_slam_replay/map.png`: local map accumulated from that log.
- `sample_results/synthetic_slam/map.png`: artificial room demonstration,
  prominently labelled SYNTHETIC DEMO.

The original bench logs remain unchanged in the project evidence folder.
These examples have not been installed on the Pi or pushed to GitHub.

Note, 17 November 2026: the 28 October wiring PDF checked above was drawn for different motors and driver. It is not in this repository; the current diagram is in `docs/wiring`.

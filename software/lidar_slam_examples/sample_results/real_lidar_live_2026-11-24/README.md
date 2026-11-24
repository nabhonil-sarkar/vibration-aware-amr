# Live RPLIDAR A1 run on the Raspberry Pi 5, 24 November 2026

Hardware result. The LiDAR was on the assembled sensor bridge, connected through its USB adapter to the Pi 5, with the Pi on its mains supply. The robot was not moving.

Command: `python lidar_example.py --live --seconds 15` (run folder `lidar_20261124_193832_071292`).

| Measure | Value |
| --- | --- |
| Device | Model 24, firmware 1.29, hardware 7; health Good |
| Scans | 96 complete revolutions in 13.5 s, about 7.0 per second |
| Returns | 13,889 in total, about 145 per scan |
| Farthest return | 7.3 m |
| Pi power | `vcgencmd get_throttled` = 0x0 with the LiDAR and camera connected |

Files: `scan.png` (latest scan, plotted by the example), `scan_zoomed_angles.png` (last 15 scans, zoomed to 2.5 m, with the LiDAR's own angles), `scans.jsonl` (raw returns), `summary.json`.

Conditions and limits: a cluttered lab bench, so the farthest return reflects the room, not the sensor's range. An earlier 30 s run (203 scans) was partly blocked by hands near the scan head and is not kept. The angle between the LiDAR's zero and the robot's front has not been measured yet. This is a stationary capture, not a map.

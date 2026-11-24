# Validation, 13 November 2026

Tested away from the robot, on a Linux machine. No Raspberry Pi, camera, marker print or motor was involved.

## Passed

- 13 automated tests, run on OpenCV 5.0.0 and again on OpenCV 4.10.0 (the version family in Raspberry Pi OS Trixie).
- Detection on rendered frames: all four station ids read at 0.5, 1.5 and 2.5 m; distance within 5 % and bearing within 2 degrees
  of the rendered truth; a marker turned 45 degrees still read; a marker facing away and a non-station id were ignored.
- Decision logic: no forward command without the target in view; turns towards the marker; stops when the marker is lost,
  then searches towards the side it was last seen; gives up after the search timeout; stops on long gaps between frames
  and on backwards time; commands stay within limits under 3000 random inputs.
- Whole chain in simulation (`sample_results/`): pick-up, drop-off and recharge all reached in 89.6 simulated seconds.
  The drop-off marker was moved at 32 s while the robot was driving to it; the robot found it again and completed the run.
  Stopping error was 13 to 14 mm and heading error under 0.1 degrees at each station, against the outline targets of 30 mm and 5 degrees.
- `run_stations.py` exercised end to end on a folder of rendered frames (dry run, log and annotated pictures written).
- Marker sheet rendered and checked: marker and check bar are 100 mm on the A4 page.

## Not established

- The Pi camera path (`--picamera`, picamera2) has not been run. It may need adjusting on the real Pi.
- Nothing here has seen a real printed marker, real lighting, lens distortion or motion blur.
- The simulated accuracy is not a hardware result. The simulated robot has perfect geometry and only 3 % drive noise.
- Distances on the real camera are approximate until the field of view is checked or the camera is calibrated.
- No motor commands are sent, so driving, stopping distance and docking accuracy on the real robot are untested.
- No obstacle avoidance. No map. Not safety-rated.

## Update, 24 November 2026: first run on the Raspberry Pi 5

- `rpicam-hello --list-cameras` lists the AI Camera (IMX500).
- `python3 run_stations.py --picamera --seconds 60 --save-frames` ran on the Pi 5 at 1014 x 760 for 45 s without errors. No marker was in view, so it stayed in SEARCH and ended FAILED when the search timed out, as designed.
- Still not established: detection, distance and bearing against a printed marker on the real camera; anything on the moving robot.

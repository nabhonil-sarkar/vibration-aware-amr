# ArUco station finding ("seek by sight")

Prepared for Nabhonil Sarkar, 13 November 2026. Vibration-aware AMR, Individual Major Project Part B.

The robot recognises stations by ArUco markers and drives to them in a set order using only the camera.
Move a marker and the robot turns until it finds it again. No map and no navigation software are needed.

| Marker id | Station |
| --- | --- |
| 0 | pick-up |
| 1 | drop-off |
| 2 | recharge |
| 3 | spare |

**Status: tested offline only.** The detection and decision code passes its tests on rendered camera frames.
It has not been run on the Pi, has not seen a real marker, and does not move the robot.

## Files

| File | Purpose |
| --- | --- |
| `stations.py` | Marker detection, distance and bearing, and the station-seeking logic |
| `run_stations.py` | Runs it on the Pi camera, a webcam or a folder of pictures. Dry run: logs commands, sends none |
| `simulate.py` | Offline test of the whole chain with a simulated robot; moves one station mid-run |
| `make_markers.py` | Makes the printable marker sheet |
| `test_stations.py` | 13 offline tests |
| `markers/AMR_Station_Markers_A4.pdf` | The four markers, one A4 page each |
| `sample_results/` | Output of the offline simulation, labelled SYNTHETIC |

## 1. Print the markers

Print `markers/AMR_Station_Markers_A4.pdf` at 100 % ("actual size", not "fit to page") on matte paper.
Measure the black bar on each page: it must be exactly 100 mm. Cut along the dashed line, keeping the white border,
and stick each marker flat on stiff card. Stand it upright with its centre about 135 mm above the floor, which is camera height.

## 2. Try it on the laptop first

Needs Python 3.10 or newer with `opencv-python`, `numpy` and `matplotlib`.

```
python -m unittest -v test_stations.py
python simulate.py --out my_sim
```

With a laptop webcam you can hold a printed marker up and watch the log:

```
python run_stations.py --webcam 0 --seconds 30 --save-frames
```

## 3. Try it on the Pi, by hand

Copy the folder to the Pi from Windows PowerShell, then log in:

```
scp -r .\aruco_stations nabhonil@amr-pi.local:~/
ssh nabhonil@amr-pi.local
```

On the Pi:

```
sudo apt install -y python3-opencv python3-picamera2 python3-numpy
cd ~/aruco_stations
python3 run_stations.py --picamera --seconds 60 --save-frames
```

Nothing drives. Carry the robot or the camera towards a marker and read the printed lines: the state should go
from SEARCH to APPROACH when the marker is in view, the distance should fall, and it should report "arrived" at about 0.35 m.
Each run saves `station_log.csv`, `summary.json` and annotated pictures in a new folder under `runs/`.

## 4. Check the distance reading

The camera is not calibrated. Distances come from an assumed 66 degree horizontal field of view.
Put a marker exactly 1.00 m in front of the lens and look at the reported distance. If it reads high, raise `--hfov`
a little; if it reads low, lower it. Repeat at 0.50 m and 2.00 m. Record what you measured: this is evidence for the report.

## How it decides

| State | What the robot is told to do |
| --- | --- |
| SEARCH | Turn on the spot until the target marker is seen. Gives up after about two full turns |
| APPROACH | Turn to keep the marker centred and drive forward, slowing as it gets close |
| DWELL | Stopped at the station for 3 seconds, then move to the next target |
| DONE / FAILED | Stopped |

It only ever commands forward motion in a frame where the target marker is actually detected.
If the marker disappears it stops, waits one second, then turns towards the side it last saw it on.
Speeds are capped at 0.10 m/s and 0.6 rad/s, and it never reverses. The settings are in `SeekConfig` in `stations.py`.

## Limits you should state in the report

- It needs a clear line of sight. It does not go around obstacles and it is not collision avoidance.
- It faces the marker but does not square up to it. Approached from the side, it arrives at that same angle.
  The marker angle is logged at arrival so you can report it.
- Markers seen at more than about 60 degrees off square, in glare, or blurred by fast turning may not read.
- Maximum range depends on marker size and picture size. Measure it; do not assume the simulated range.

## Connecting it to the motors (later)

`run_stations.py` has an empty `send_command(v, w)` function. Leave it empty until the STM32 drive link,
its command timeout and the hardwired E-stop are working. In the planned chain this code is the source of the driving command,
and the vibration-aware controller then limits that command before it reaches the motors.

Markers use the OpenCV ArUco dictionary DICT_4X4_50.

# Raspberry Pi 5 + RPLIDAR A1 examples

Prepared for Nabhonil Sarkar, 28 October 2026. Host: Raspberry Pi OS 64-bit
(Debian Trixie), `nabhonil@amr-pi.local`, A1 development kit with CP2102 USB adapter.

## What you get

| File | Purpose |
|---|---|
| `lidar_example.py` | Read scans, print nearest measured return, record raw scans, save a scan picture. |
| `slam_example.py` | Estimate sensor movement with scan-to-map ICP and accumulate a 2D occupancy map. |
| `scans.py` | Shared live, replay and synthetic scan sources; sensor cleanup. |
| `mapping.py` | Small, readable SLAM implementation using NumPy and SciPy. |
| `test_examples.py` | Offline tests for geometry, map cells, replay, cleanup and synthetic movement. |

These are educational examples, not the final ROS/Nav2 navigation stack.
The SLAM example jointly estimates pose and builds a map, but has **no loop
closure, wheel odometry, IMU fusion, global relocalization or motion control**.
Neither program drives the wheels or requires the STM board. The AI camera
is not used by either example. No successful run on the physical Pi is claimed.

## 1. Copy the folder to the Pi

Extract the delivered ZIP on your laptop. In **Windows PowerShell**, go into
the extracted parent folder (the one containing `AMR_LiDAR_SLAM_Examples`) and run:

```powershell
scp -r .\AMR_LiDAR_SLAM_Examples nabhonil@amr-pi.local:~/
ssh nabhonil@amr-pi.local
```

The following commands run **inside the Pi SSH terminal**:

```bash
cd ~/AMR_LiDAR_SLAM_Examples
sudo apt update
sudo apt install -y python3-venv python3-pip python3-numpy python3-scipy python3-matplotlib
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install 'pyserial==3.5' 'rplidar-roboticia==0.9.5'
```

The Pi's packaged scientific libraries avoid lengthy compilation on the Pi.
For an ordinary separate Python environment on a laptop, install `requirements.txt`
with `python -m pip install -r requirements.txt`. Python 3.10+ is required.
Do not install the different `rplidar` package alongside `rplidar-roboticia`;
both use the Python import name `rplidar`.

## 2. Try the examples without hardware first

```bash
python lidar_example.py --demo
python slam_example.py --demo
```

Each command prints its output directory. Runs get new timestamped directories
under `runs/`; an explicit `--output` must name a new directory. The demo is a
synthetic room and does not prove real sensor performance. It contains known
slow motion; the SLAM estimator does not receive that ground truth.

## 3. Read your physical A1 LiDAR

Connect the A1 through its supplied USB adapter to the Pi. Stop any existing
`ultra_simple` SDK process first: only one program may use the serial port.

```bash
ls -l /dev/serial/by-id/
python lidar_example.py --live --seconds 30
```

Default serial path:

```text
/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0
```

If the path differs, use the actual path with `--port`, for example:

```bash
python lidar_example.py --live --port /dev/ttyUSB0 --seconds 30
```

Baud rate is 115200, matching the successful A1 bench test. If access is denied:

```bash
sudo usermod -aG dialout "$USER"
exit
```

Reconnect with SSH, enter the project directory and activate `.venv` again.
Do not run the scripts as root merely to avoid the permissions step.

Outputs: `scans.jsonl` (raw returns), `scan.png` (latest scan), `summary.json`.
Nearest return is a diagnostic reading, **not collision-avoidance logic**.

## 4. Try local SLAM

```bash
python slam_example.py --live --seconds 60
```

Keep the LiDAR upright and level. Start stationary in a room with several
visible walls/corners, then move the whole sensor/platform slowly by hand.
Avoid fast turns, people close to the scanner and a view containing only one
flat wall. Leave wheel motor power off for these initial manual trials.
Keep the spinning head and cables clear. A stationary sensor gives a local
view; it cannot explore the room without being moved.

Outputs:

| Output | Meaning |
|---|---|
| `map.png` | Occupancy map with the estimated sensor trajectory. |
| `map.pgm` + `map.yaml` | Trinary map image and metadata; ROS-style file format only, not a tested Nav2 setup. |
| `trajectory.csv` | Scan index, source time, accepted/rejected flag, pose and matching error. |
| `scans.jsonl` | Raw scans for repeatable replay. |
| `summary.json` | Method, source, accepted/rejected scans and errors. |

Black means occupied, white free, grey unknown. Map default is 20 x 20 m,
5 cm cells. Initial pose is (0, 0, 0); this is a local arbitrary frame.
The sensor's zero-angle ray defines +X; +Y and yaw are counterclockwise.
Physical scanner mounting orientation relative to the robot is not calibrated.

The mapper filters zero-quality/zero-distance returns and readings outside
0.15-8 m, then keeps the nearest return per 1-degree bin. Filtered returns do
not clear free space. It matches against earlier accepted scan endpoints,
checks overlap/residual/jumps and skips rejected scans without changing the map.
After 10 consecutive rejects it saves the partial map and exits with an error.
Accepted matches can still be wrong in repetitive or moving scenes. Drift is
expected; this is not a globally consistent survey or a reliable localization
system. Map memory and scan-point count are bounded for a small example.

## 5. Stop and view results

Press **Ctrl+C** to stop early. Live input attempts scan stop, motor stop and
serial disconnect even if processing raises an error. This cleanup is tested
with a fake adapter, not yet with your hardware. If the head keeps spinning,
disconnect the adapter USB after the program exits; do not hold the head.
Forced termination or power loss cannot execute Python cleanup.

Ordinary SSH has no graphical desktop. Omit `--plot`; pictures are still saved.
On the Pi desktop, add `--plot` for an updating plot window. Closing that window
stops the run. An interactive plot may reduce scan-processing throughput.

To download all runs, use **a separate Windows PowerShell window**, not the Pi prompt:

```powershell
scp -r nabhonil@amr-pi.local:~/AMR_LiDAR_SLAM_Examples/runs "$env:USERPROFILE\Downloads\"
```

Then open the images in your laptop's Downloads/runs folder.

## Replay previous evidence

The recorded SDK logs from 7 October are supported:

```bash
python lidar_example.py --replay /home/nabhonil/lidar-test.txt
python slam_example.py --replay /home/nabhonil/lidar-test.txt
```

For our own recordings:

```bash
python slam_example.py --replay runs/REPLACE_WITH_LIDAR_RUN/scans.jsonl
```

SDK text has no timestamps or scan IDs. Revolutions are inferred from large
angle wraps; first and last partial revolutions are discarded. Its `source_time`
values are scan indices, not elapsed seconds. SDK replay cannot establish scan
frequency, real-time throughput or motion speed. Do not merge the baseline and
bag logs as one continuous trajectory: sensor orientation changed between them.

## Troubleshooting

- **No serial device:** check the adapter cable, power and `lsusb`.
- **Wrong descriptor / wrong start flag / buffer error:** stop other readers,
  reconnect the adapter, and retry headless. These scripts fail and save evidence
  rather than silently inventing scans. Pi throughput remains to be tested.
- **No map / ten rejects:** move more slowly, use a static scene with several
  corners, keep the scanner level, and start a fresh run. Do not treat a failed
  map as valid navigation data.
- **Wiring:** see [docs/wiring](../../docs/wiring) (board identified as a NUCLEO-F401RE on
  17 Nov 2026). No MCU flashing is needed for these examples.

## Tests and references

Run offline tests with `python -m unittest -v test_examples.py`.
See `VALIDATION.md` for checks actually run and their limitations.

- Python A1 driver: https://github.com/Roboticia/RPLidar
- Driver package: https://pypi.org/project/rplidar-roboticia/0.9.5/
- Official SDK (your earlier bench test): https://github.com/Slamtec/rplidar_sdk
- Nearest-neighbour API: https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.cKDTree.query.html
- Wiring diagram: [docs/wiring](../../docs/wiring).

Dependencies are third-party packages, installed separately under their own
licences. This package does not bundle their source or binaries.

# Vibration-aware controller for Nabhonil's custom AMR

This is a first software prototype for your own robot, not a TurtleBot package. It is intended for ROS 2 Jazzy on Ubuntu 24.04 / Raspberry Pi 5. The calculation and demonstration also run on Windows without ROS, MATLAB, or special plugins.

**Status: offline core tests passed; ROS integration and physical robot operation are NOT yet tested. Do not connect directly to powered wheels before completing the commissioning checks below.**

## What it does

The payload IMU measures acceleration. The controller removes the constant part of that signal, filters high-frequency noise, and calculates how strongly the payload is shaking over a short window. When that value rises above a configurable threshold, it reduces the requested driving and turning speeds. It returns to normal gradually when the shaking settles.

It adapts motion; it does not move the isolators or provide active vibration cancellation. Wheel-speed PID, SLAM, navigation, IMU hardware drivers and motor control are separate systems and are not implemented here.

The intended command path is:

```text
Nav2 / selected teleop source -> vibration controller -> collision/safety gate
                                                     -> wheel controller / MCU
Payload IMU -----------------> vibration controller
Hardwired E-stop ------------------------------------> motor power cutoff
```

All motion sources must pass through the intended selection/safety chain. There must be only one final publisher to the drive command topic. Keep collision monitoring downstream so a stop cannot be overridden by this controller. A separate motor-command timeout on the MCU is essential: a crashed process cannot publish a stop. This is not a safety-rated controller.

## Files

| File | Purpose |
|---|---|
| `vibration_aware_control/core.py` | Filtering, RMS measurement, speed adaptation, command ramping and watchdog logic. No ROS dependency. |
| `vibration_aware_control/ros_node.py` | Receives IMU and velocity messages; publishes adapted velocity and status. |
| `config/controller.yaml` | Starting settings: thresholds, filters, limits, frames and timeouts. |
| `launch/vibration.launch.py` | Starts the ROS node with the configuration file. |
| `vibration_aware_control/demo.py` | Synthetic sensor demonstration with baseline/adaptive commands and a sensor dropout. |
| `tests/test_core.py` | Automated checks of normal operation, slowdown, recovery, stopping and invalid/missing data. |
| `demo_outputs/` | Generated CSV, summary and optional plot. These are synthetic, not experimental results. |
| `package.xml`, `setup.py`, `setup.cfg`, `resource/` | ROS/Python installation metadata. Replace the placeholder maintainer email before distribution. |

## Try it on Windows now

Open a terminal in this package folder (the one containing this README and `setup.py`). With Python 3.10 or newer:

```powershell
python -m unittest discover -s tests -v
python -m vibration_aware_control.demo
```

The core and CSV demo use only Python's standard library. For the optional PNG figure, install `matplotlib` and rerun:

```powershell
python -m pip install matplotlib
python -m vibration_aware_control.demo
```

In the demonstration, motion begins after a stationary warmup. High synthetic vibration is imposed from 6–12 s; the adaptive command slows while the baseline does not. At 16 s the IMU signal is interrupted; both modes stop and remain disabled even after data resumes. Both modes receive the SAME imposed vibration signal. The demo therefore demonstrates controller behaviour, not achieved vibration reduction or journey-time improvement.

## Algorithm and units

1. Receive approximately 100 acceleration samples/s in **m/s²** from the IMU attached to the payload deck. Not the chassis IMU.
2. Apply a first-order 1 Hz high-pass and 20 Hz low-pass filter per axis. These are gradual cutoffs, not a perfect rectangular frequency band. Configure the sensor's hardware anti-alias filter as well.
3. Calculate the vector RMS: `sqrt(mean(ax_filtered² + ay_filtered² + az_filtered²))` over the last 0.5 s. This is a sample-weighted estimate; near-uniform sampling is assumed.
4. Enter adaptation at 0.35 m/s², leave it below 0.20 m/s². This difference (hysteresis) reduces repeated switching.
5. During adaptation, scale = `1 - 0.75 * clamp((RMS - 0.20) / (1.00 - 0.20), 0, 1)`. Thus scale ranges from 1.0 to 0.25. Its fall/rise rates are separately limited.
6. Apply the same scale to linear and angular target velocities, then ramp the two outputs independently. Baseline mode disables vibration adaptation but retains the same base limits, input checks and watchdogs.

The example maximum speeds are 0.30 m/s and 0.60 rad/s. Acceleration/jerk requests are limited and reduced as the vibration scale falls. These are **command-shaping limits**, not guarantees about the physical acceleration or jerk of the robot/payload. Independent axis ramps can change turning curvature during transitions. Stops, exact-target clamps and hard maximum-speed clamps take precedence over jerk smoothing; abrupt input changes can therefore create jerk discontinuities. A falling acceleration limit is approached through the jerk limiter, not instantaneously imposed. Retune after measuring wheel response.

The minimum scale is a motion setting, NOT a declaration that any vibration level is safe. There is no validated fragile-payload damage threshold or shock-trip protection here. The 60 m/s² per-axis input guard catches implausible/out-of-range readings for this prototype and requires re-enable after a fault; it is not a calibrated impact detector or universal IMU saturation check.

## Assumptions and limitations

- Indoor, approximately level travel with a rigidly mounted payload IMU and limited tilt. A high-pass filter rejects constant gravity/bias; it **does not** fully compensate gravity during rotation and does not separate vibration from all commanded motion. Low-frequency motion below the cutoff is deliberately attenuated.
- No orientation quaternion is used in this version. If significant pitch/roll occurs, add calibrated attitude-based gravity compensation and validate the metric against a reference measurement. Do not label this metric full-band dynamic acceleration in reports.
- The accelerometer is already correctly scaled and calibrated by its driver. Sensor noise, mounting resonance, saturation and aliasing still need measurement. An IMU driver is NOT included.
- Samples arrive near 100 Hz. A minimum sample count rejects obviously slow streams, but transport jitter and dropped samples can still bias the RMS. Record and inspect actual timestamps/rate.
- ROS publishers use synchronized clocks, nonzero increasing timestamps and the expected frame IDs. Stamped commands must be expressed in `base_link`; no coordinate transformation is performed.
- The command interface is forward/reverse speed plus yaw rate. It can sit above a two-wheel differential drive or four-wheel skid-steer base. It does not assume wheel diameter/track or implement skid compensation. Those belong in the wheel controller.
- Slower travel is a hypothesis for reducing vibration, not a universal rule: resonances can make some lower speeds worse. Real trials must establish the useful speed range.
- Feedback reacts after vibration is measured. It cannot prevent the first impact and its filter/ramp delays must be considered. It does not replace passive isolation, retention, safe route selection or collision avoidance.
- No hardware-performance percentage is claimed. Your planned 20% RMS reduction / <=20% journey-time penalty remains a test objective.

## ROS 2 installation (on Ubuntu, not ordinary Windows Python)

Install ROS 2 Jazzy, colcon and rosdep first. Copy this complete `vibration_aware_control` folder into `~/amr_ws/src/`. Then:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/amr_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select vibration_aware_control
source install/setup.bash
ros2 launch vibration_aware_control vibration.launch.py
```

All parameters are startup-only. Edit the YAML and restart while disarmed; changing parameters live is not supported. The launch file also accepts `params_file:=/absolute/path/controller.yaml`. For Gazebo, use `use_sim_time:=true` and make sure all publishers use the same ROS clock. Watchdogs remain wall-monotonic: pausing simulation disarms the controller, and resuming requires fresh data/warmup and manual re-enable.

### Interfaces

| Topic/service | Type | Direction |
|---|---|---|
| `/payload/imu` | `sensor_msgs/msg/Imu` | Input; acceleration in m/s², frame `payload_imu_link`, ~100 Hz |
| `/cmd_vel_requested` | `geometry_msgs/msg/TwistStamped` by default | Input; `base_link`, fresh command stream |
| `/cmd_vel_vibration` | Same velocity type as input | Output at 50 Hz; connect to downstream safety gate |
| `/vibration/status` | `std_msgs/msg/String` containing JSON | Output at 10 Hz: RMS, scale, state, speed, enabled flag |
| `/vibration/enable` | `std_srvs/srv/SetBool` | Explicit enable/disable |

Set `stamped_commands: false` only if the upstream AND downstream components require `Twist`. Unstamped commands lack header age checks; they still have arrival-time watchdogs. Nav2 Jazzy supports both types, so configure/remap all relevant publishers/subscribers consistently rather than assuming they match. The node rejects wrong frames, stale/duplicate stamps, unavailable acceleration and non-planar commands.

### First commissioning — wheels raised and motor power isolated initially

1. Check the hardwired E-stop, retention, wiring, fusing, independent MCU watchdog and downstream collision-stop path with your lab supervisor. Keep the controller's output disconnected from motor actuation while verifying interfaces.
2. Confirm IMU units, axes, timestamp, frame, noise and hardware sampling/filter settings. A stationary raw accelerometer that includes gravity typically reads approximately 9.81 m/s² in vector magnitude. Record a stationary dataset before tuning thresholds.
3. Publish the real payload IMU continuously and a continuous **zero** command stream. Wait at least 1.5 s for the filter to settle. Zero commands alone do not prove the robot is physically stationary: verify that separately.
4. Check `/vibration/status`. The controller starts disabled and requires fresh inputs and a zero requested command to enable:

```bash
ros2 topic echo /vibration/status
ros2 service call /vibration/enable std_srvs/srv/SetBool '{data: true}'
```

5. Observe the output with motor power still isolated. Test requested stop, unplugged IMU, stale command and process termination. Verify the downstream MCU stops if this process disappears. Never bypass a fault to make it move.
6. Only after those checks, test raised wheels at very low settings, then a clear supervised floor area with a non-fragile dummy load. Verify collision avoidance, braking distance and Nav2 behaviour under speed scaling.

To disable:

```bash
ros2 service call /vibration/enable std_srvs/srv/SetBool '{data: false}'
```

IMU silence beyond 0.10 s, command silence beyond 0.30 s, invalid data or a long control-loop gap disarms the prototype. A watchdog detection produces a zero command at the next running timer tick; it is not an instantaneous motor brake. Once recovered, send zero commands, allow the filter to settle as needed and explicitly re-enable. A fault does not automatically restart movement.

## How this should develop as the project progresses

1. Confirm the actual IMU model/driver and microcontroller. Integrate the payload IMU publisher; this package deliberately avoids inventing a hardware wiring/interface choice.
2. Record stationary and baseline route data with the actual dummy payload. Tune filter band/window to the mechanical vibration spectrum, distinguish noise from vibration and document why thresholds were chosen.
3. Measure speed tracking, stopping distance, low-speed stalling and isolator resonance. Revise speed/acceleration/jerk settings; coordinate scaling with Nav2 progress checking and collision monitoring.
4. Add validated gravity compensation if tilt matters, plus sensor-specific saturation checks and appropriate shock handling once requirements are known.
5. Run at least 10 matched baseline and 10 adaptive trips using the same payload, route, tyres, isolation and measurement settings. Interleave modes to reduce battery/floor-condition bias. For baseline, restart with `adaptive: false`; keep all safety and base motion limits identical.
6. Record raw IMU, requested/adapted/final motor commands, odometry and status with rosbag2. Calculate consistent whole-trip metrics offline: band-limited RMS, peaks, journey time, failures and variability. Controller rolling RMS/status is diagnostic, not a substitute for a full trial analysis. Do not claim success from the synthetic demo.

Example recording command (add the actual final motor-command topic):

```bash
ros2 bag record /payload/imu /cmd_vel_requested /cmd_vel_vibration /vibration/status /odom
```

## Verification and references

The automated tests exercise the ROS-independent core. ROS imports are syntax-checked only in the present Windows environment; a ROS 2 runtime/colcon build and real message-level integration test remain required on the Pi/Ubuntu system. The wrapper intentionally uses ordinary ROS messages and has no specific MCU dependency.

- [Nav2 Jazzy TwistSubscriber: configurable Twist/TwistStamped interface](https://api.nav2.org/nav2-jazzy/html/classnav2__util_1_1TwistSubscriber.html)
- [Nav2 Jazzy collision monitor configuration](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/collision_monitor/configuring_collision_monitor_node/)
- [Official sensor_msgs/Imu message definition](https://github.com/ros2/common_interfaces/blob/jazzy/sensor_msgs/msg/Imu.msg)

The reference design does not require a Codex plugin. Hardware testing requires your actual ROS 2 installation and IMU driver, not an AI plugin.

# Verification — 23 September 2026

- Windows, Python 3.12 bundled runtime.
- `python -m unittest discover -s tests -v`: **20 tests passed**.
- `python -m compileall -q vibration_aware_control launch`: passed Python syntax compilation.
- Synthetic demonstration executed and CSV, JSON and PNG generated; plot visually inspected.
- Synthetic peak filtered RMS: 1.16147 m/s²; minimum requested speed scale: 0.25.
- IMU dropout detected; adapted output remained zero after dropout and subsequent sensor recovery without re-enable.
- ROS `rclpy` is not installed in this environment. ROS node imports/execution, colcon installation, topic QoS/interoperability, launch and actual hardware behaviour have **not** been runtime-tested.

Tests cover startup disabled, warmup, rejection of low sensor rate, constant-gravity rejection, normal speed, vibration slowdown/recovery, baseline mode, stale IMU, stale commands, non-finite inputs, immediate commanded stop, enabling only with zero commands, reverse motion, proportional velocity caps, backwards IMU time, delayed control loop, initial acceleration/jerk ramp, randomized output bounds, parameter validation and the synthetic dropout scenario.

These results establish software-core behaviour under the included inputs. They do not establish real-time guarantees, general closed-loop stability, collision safety, payload protection or achieved vibration reduction. The prototype is not ready for unsupervised physical operation.

# Four-wheel skid-steer kinematics

This folder retains a preliminary base-MATLAB simulation for the earlier
four-wheel skid-steer alternative. The current chassis uses two driven wheels
and a rear castor. Do not use these results as validation of that chassis.

## Run the model

Open `skid_steer_kinematics.m` in MATLAB and select **Run**, or execute:

```matlab
run('skid_steer_kinematics.m')
```

The script creates an `outputs` folder containing:

- `skid_steer_trajectory.png`
- `skid_steer_motion_profiles.png`
- `skid_steer_summary.csv`
- `skid_steer_timeseries.csv`
- `skid_steer_results.mat`

## Model equations

The left-front and left-rear wheels share velocity `vL`, while the
right-front and right-rear wheels share velocity `vR`.

```text
linear velocity:  v = (vR + vL) / 2
ideal yaw rate:   omega = (vR - vL) / trackWidth
skid yaw rate:    omegaSkid = turnEfficiency * omega
wheel speed:      wheelOmega = sideVelocity / wheelRadius
```

## Current assumptions

- Chassis: 340 x 270 mm, carried over from the concept CAD.
- Wheel diameter: 70 mm.
- Centre-to-centre track width: 270 mm, derived from the provisional
  298 mm outside-to-outside CAD dimension and 28 mm wheel width.
- Wheelbase: 250 mm, provisional for this unselected four-wheel alternative.
- Turn efficiency: 0.80, used only to illustrate tyre-scrub effects.

These are preliminary simulation values, not experimental results. The turn
efficiency must later be estimated from commanded yaw versus measured yaw or
motion-capture/odometry data.

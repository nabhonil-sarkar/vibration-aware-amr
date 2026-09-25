# Project status

Snapshot: 25 September 2026.

The outline has been approved. At the 23 September meeting, the student and supervisor agreed to use the outline's parts list and try a 3D-printed chassis. This repository records subsequent engineering work without modifying the submitted outline.

## Completed artefacts

- Fusion V2 full-robot concept and three coloured subsystem sheets.
- A preliminary MATLAB four-wheel alternative study with simulated outputs.
- A ROS-independent vibration-aware control core and synthetic demonstration, with 20 passing unit tests.
- A ROS 2 adapter and launch/configuration files, not yet runtime-tested.
- V03 split chassis geometry: four panels, four splice plates, a castor adapter blank and a separate fit coupon. Closed meshes, valid solids, nine assembly solids after STEP reimport, and no positive-volume overlap between assembled printed parts were checked.

No physical assembly, vibration improvement, docking performance or autonomous navigation result is claimed.

## Decisions and unresolved interfaces

- Use two driven wheels and a rear castor as the working build basis. The four-wheel MATLAB model is retained as an alternative study, not quietly treated as the same robot.
- Pi 5 availability differs from the Pi 4 named in the historical outline and concept. Update mounting, power and interface documentation during implementation.
- The current carried-load target is 1 kg, including the carrier and secured dummy payload. Earlier concept parameters contain provisional values such as 1500 g; they are not the current requirement.
- V03 is a chassis-base package, not a finished robot. Motor brackets, castor-specific holes, payload risers/deck, battery tray, guards and anti-tip interfaces still need verified hardware geometry.
- The V03 front payload-support provision moved from the old concept's X = +35 mm to +55 mm to clear splice plates. Coordinate the deck revision accordingly.
- Printer, material, motor stall current, driver, battery/charger/regulators and exact MCU remain to be verified before fabrication or purchase.

## Next implementation sequence

1. Verify the BOM against lab stock and supplier specifications, including complete power compatibility and long-lead items.
2. Confirm printer access and build area; print and measure the fit coupon, then release a chassis revision with verified interfaces.
3. Review risk controls and assemble the chassis, fused power system, independent motor E-stop and encoder-controlled drive.
4. Validate IMU acquisition, timing, units and calibration. Integrate odometry and the robot model before navigation.
5. Configure ROS 2/Gazebo, SLAM and Nav2, then integrate motion adaptation and visual docking.
6. Run controlled trials and report measured outcomes and failure modes.

This dependency chain protects the critical path from procurement and chassis fabrication through safe drive integration to sensing and experimental evidence. Detailed dates need to be agreed for Part B; the historical outline schedule is not evidence that those milestones are complete.

## Experimental clarifications to resolve

- Define the research question and the final whole-trial RMS/peak metrics.
- Validate gravity removal and filtering. The current controller uses a 0.5-second rolling vector RMS after first-order 1 Hz high-pass and 20 Hz low-pass filters, which is not full tilt compensation or a whole-trial metric.
- Specify unique vibration and integrated trial counts and declare any overlap.
- Match payload, route, nominal limits, tyres, isolation and other relevant conditions between baseline and adaptive modes.
- Define docking position error by absolute distance and orientation error by absolute wrapped angle against an independent reference.
- Select elastomers from supported mass, mechanical properties and measured response; do not infer isolation performance from appearance.
- Strengthen vibration/isolation sources, correct the Gazebo reference to Harmonic in future reports, and avoid treating 0.5g as a universal safety limit.

MPPI, a custom dashboard and a powered latch remain stretch objectives. Active cancellation is outside the core scope.

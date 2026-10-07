# Project status

Snapshot: 7 October 2026. CAD verification dates from 2 October; print-file preparation from 4 October. No subsequent physical results have been reported.

The outline has been approved. At the 23 September meeting, the student and supervisor agreed to use the outline's parts list and try a 3D-printed chassis. This repository records subsequent engineering work without modifying the submitted outline.

## Completed artefacts

- Fusion V2 full-robot concept and three coloured subsystem sheets.
- A preliminary MATLAB four-wheel alternative study with simulated outputs.
- A ROS-independent vibration-aware control core and synthetic demonstration, with 20 passing unit tests.
- A ROS 2 adapter and launch/configuration files, not yet runtime-tested.
- V03 split chassis geometry: four panels, four splice plates, a castor adapter blank and a separate fit coupon. Closed meshes, valid solids, nine assembly solids after STEP reimport, and no positive-volume overlap between assembled printed parts were checked.
- V04 full-robot concept with the unchanged v03 chassis, Pi 5 reference, supported passive payload deck, separate rigid sensor bridge, retained battery envelope, guards and E-stop location. Actual native Fusion archive exported/reopened: 87 solid valid bodies; STEP round trip and static overlap checks recorded. Rear castor checked at 24 swivel positions in 15° steps, not a continuous swept-volume certification.
- X1 Carbon PLA chassis print package: ten STL files and equivalent millimetre-unit 3MF models, quantities, previews and a slicing guide. Mesh closure, single-volume geometry and nominal 256 mm XY fit with 5 mm margin checked. No slicing, G-code, actual printing or load validation is claimed.
- Dated supplier shortlist from Kuriosity and Cytron Singapore; exact hardware selections remain open.

No physical assembly, vibration improvement, docking performance or autonomous navigation result is claimed.

## Decisions and unresolved interfaces

- Use two driven wheels and a rear castor as the working build basis. The four-wheel MATLAB model is retained as an alternative study, not quietly treated as the same robot.
- Pi 5 replaces the historical Pi 4 implementation assumption. V04 includes a reference PCB with cooling/connector allowances; actual cooler, cables and regulated power remain to be verified.
- The current carried-load target is 1 kg. Conservatively include the isolated deck, carrier, restraint, dummy and payload instrumentation. Earlier concept values such as 1500 g are superseded; neither CAD volume nor the target proves capacity.
- V04 adds provisional motor saddles, risers/deck, tray, guards and anti-tip geometry. Their hardware interfaces, fasteners, isolation attachment and structural/stability behaviour remain unresolved. The current printable package is the v03 chassis base retained in v04.
- V04 drivetrain geometry is provisional: 120 mm wheels, 312 mm centre track, 28 mm castor and ground-based axle/chassis placement. Supplier candidates use different dimensions and require coordinated mount/clearance changes before adoption.
- The V03 front payload-support provision moved from the old concept's X = +35 mm to +55 mm to clear splice plates. Coordinate the deck revision accordingly.
- User-confirmed printer/material: Bambu Lab X1 Carbon, PLA 1.75 mm, physical plate 257 × 257 mm, maximum printable volume 256 × 256 × 256 mm. Nozzle, plate surface and final slicing settings remain unconfirmed. Old 220 mm bed assumptions are historical.
- Actual motors, driver, battery/charger/regulators, exact MCU and rated isolators are still unselected. E-stop CAD is an envelope, not an implemented power cutoff. Avoid a rigid continuous bolt or taut cable that bypasses payload isolation.

## Next implementation sequence

1. Verify the BOM against lab stock and supplier specifications, including complete power compatibility and long-lead items.
2. Use the supplied print package to print and measure the PLA fit coupon with the actual nozzle/plate profile. Resolve hardware mounts, review slicer output and inspect one prototype panel before committing to the rest.
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

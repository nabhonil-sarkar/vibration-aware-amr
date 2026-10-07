# Updated full robot v04 — concept prototype

2 October 2026, Singapore time. This revision continues the full robot concept with the existing v03 split chassis. It is not a fabrication release, selected supplier BOM, or evidence of physical testing.

## Files and opening

Open `Vibration_Aware_AMR_v04.f3d` in Autodesk Fusion. The native archive contains named internal solid components and reference parameters. Geometry was generated from source, imported as STEP, and exported by Fusion as an actual native archive. The imported solids do not recover a sketch-based feature history. Reference parameters document assumptions; changing them does not regenerate the imported bodies. Regenerate using the included geometry source, then run the Fusion exporter.

`Vibration_Aware_AMR_v04.step` is the source geometry assembly. `Vibration_Aware_AMR_v04_Fusion.step` is the companion exported by Fusion. The assembled, side and service PNGs show the actual geometry. Service view hides the isolated deck and carried components to expose the battery and mounts.

## What changed

- Preserved all nine v03 chassis solids and hole/slot patterns, translating their base datum to Z=40 mm in a provisional ground-based assembly. The four-panel 340 × 270 mm chassis remains split.
- Kept two driven wheels and one rear swivel castor. Added motor saddles, shafts, attached wheel guards and front anti-tip brackets with rollers 2 mm above the floor.
- Reconciled the ground geometry using new **provisional 120 mm drive wheels** (28 mm width), wheel-centre track **312 mm**, axle Z=60 mm, and a **provisional 28 mm castor** at axle Z=14 mm. These supersede the old 70/40 mm envelopes for this concept only, and are not procurement selections. The smaller castor is a packaging compromise whose rolling performance over real floor joints needs evaluation. A chosen larger castor will require changing chassis/drive height and its mount together.
- Added a supported removable battery tray above splice plates, retention bands, front electronics plate, rear electronics carriers and a rigid chassis-IMU pad. Battery dimensions 145 × 86 × 36 mm remain an envelope; chemistry, voltage and capacity are unspecified.
- Replaced the Pi 4 with a Pi 5 reference PCB, mounting standoffs, cooling allowance and connector envelopes. The reference PCB is 85 × 56 mm with a 58 × 49 mm mounting-hole pitch, based on the [Raspberry Pi reference drawing](https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf). That drawing is reference data, not production geometry. Actual cooler, ports, cables and physical board need checking.
- Added four rigid risers at X=-125/+55, Y=±72 mm. Each supports an unrated passive elastomer, then the isolated deck. Deck top is Z=122 mm. Carrier, dummy payload, retention and payload IMU ride on this deck.
- Kept LiDAR and navigation camera on a separate chassis-rigid bridge. LiDAR top is Z=201 mm, above the shown dummy payload at Z=162 mm. An accessible E-stop envelope is mounted rigidly at the front right; no electrical cutoff system is implemented by CAD.
- Recorded **1 kg total carried mass** as an untested requirement. For conservative budgeting here, include the isolated deck, carrier, retention, dummy and payload instrumentation. Their physical masses must be measured; 1 kg is not total robot mass or proven capacity.
- Recorded Bambu Lab X1 Carbon nominal 256 × 256 × 256 mm. The original four panels and the 230 × 190 mm deck fit that nominal XY size individually. Material, nozzle, plate exclusions, tolerances, wall/infill and slicer settings remain unconfirmed.

## Verification and its limits

Geometry checks found 87 individually valid solids, 87 solids after STEP reimport, and no positive-volume static overlaps above the 0.01 mm³ reporting tolerance. Drive tyres and castor touch Z=0; anti-tip rollers clear Z=0 by 2 mm. The castor tyre, axle and fork were checked against the fixed parts at 24 swivel positions, 15° apart, with no positive-volume clashes detected. This is a discrete check, not continuous swept-volume certification.

The Fusion verification report records whether the actual F3D was exported, reopened, and checked for the expected valid solid count. Consult the JSON reports for machine-readable evidence. Geometry validity does not establish strength, mass, isolation performance, stability, fastener access or fit.

## Interfaces to resolve before fabrication

1. Replace motor/wheel/hub/castor envelopes with measured or supplier dimensions. Saddles illustrate load paths but lack selected clamp hardware, motor screw patterns and torque retention. The castor adapter is intentionally blank at its vendor interface.
2. Select rated elastomers from the carried mass, stiffness, damping, static deflection and travel. The model shows a 4.5 mm coaxial bore as an interface placeholder. **Do not install a continuous rigid through-bolt that bypasses the elastomer isolation.** Design separate upper/lower stud attachments or the selected isolator's actual construction, and validate lateral retention and fail-safe stops.
3. Check printed riser strength, long-column buckling, chassis stiffness, deck deflection, proof load and bolt stacks with the lab. New parts are concept mounting geometry; original v03 STLs remain the only previously prepared print package. No v04 G-code or released printable mounting kit is supplied.
4. Mounts use existing provisions where possible. Side guard interfaces and some brackets need detailed fasteners. Tool and wrench access has not been certified; battery/electronics plates are removable to expose seam bolts. Fasteners and washers/nuts are not modeled.
5. Establish total mass and centre of mass with actual hardware. Nominal ground supports are the two drive contacts (0, ±156 mm) and rear castor contact (-155, 0 mm) in the shown orientation. Payload centre (-45, 0) lies within this nominal triangle, but this alone does not prove whole-robot stability. Account for castor orientation, acceleration, braking, turns and the non-contact anti-tip rollers.
6. Route flexible payload-IMU cable with slack and strain relief so it does not short-circuit isolation. Verify vibration travel, connector clearances, service access, LiDAR sight lines and camera docking view.
7. Resolve Pi 5 power/cooling, battery protection, fuses, wire routing, motor power cutoff, watchdog and guarding with selected hardware and lab procedures. Red E-stop geometry is only a location envelope.
8. Print and measure the existing v03 hole/slot coupon with intended material and fasteners before releasing the chassis or mounts. Confirm usable X1 Carbon plate area and lab settings.

Earlier CAD, approved outline and academic forms were preserved. No GitHub commit or push is part of this revision.

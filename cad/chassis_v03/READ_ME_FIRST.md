# AMR chassis v03 prototype

This is a new split, 3D-printable chassis-base design for Nabhonil Sarkar's custom vibration-aware robot. It follows the approved outline's two driven wheels and rear castor layout. It is not a TurtleBot chassis. Previous Fusion concept files and the approved outline have not been modified.

**Status: prototype geometry for review and fit testing, not a validated load-bearing design.** The 1 kg carried-load objective is a design requirement, not an achieved capacity. The complete robot mass is higher because the battery, motors, computers and structure also load the chassis.

## Which file to open

- `AMR_Chassis_v03_Assembly.step`: open/import this in Fusion to inspect the complete nine-part chassis assembly. STEP contains editable solid geometry, but does not recreate a native Fusion parametric feature timeline. Save a native Fusion copy after importing if required.
- `STEP`: individual solid parts, kept at their assembled coordinates for editing and comparison.
- `STL`: ten millimetre-scale mesh files, one per printed part including a test coupon. All are translated onto the print plane with their minimum Z at zero. Print each panel separately. STL is unitless internally: select millimetres and check its dimensions in the slicer.
- `PREVIEWS`: assembled, exploded and top-view pictures made from the actual generated geometry.
- `Print_Parts_List.csv`: quantities and measured geometry bounds; this is not a supplier purchasing list.
- `Mounting_Coordinates_mm.csv`: round-hole locations. The origin is at the assembled chassis centre, X points forward, Y points left and Z points up. These are proposed interfaces, not verified component dimensions.
- `Geometry_Checks.json`: solid validity, watertight-mesh, part-size and overlap checks. These are not structural or physical tests.
- `build_chassis.py`: regenerates the model using CadQuery 2.8. Dimensions and feature coordinates are defined in the source. Some dimensions are coupled to fixed feature coordinates: review all affected features when changing the envelope; this is not an arbitrary-size chassis configurator.

## Parts and geometry

The assembled footprint is 340 by 270 mm. Four panels each occupy approximately 169.8 by 134.8 mm, with a deliberate 0.4 mm gap at the two centre seams. The floor is 6 mm thick; outer rims rise another 14 mm. Internal ribs rise 8 mm above the floor. These provisional dimensions require print and stiffness evaluation.

Print one each of panels 01 to 04, joint plates 05 to 08, and rear castor adapter 09. The four top-mounted splice plates connect the panel seams. The castor adapter fits underneath the rear centre. Its four attachment holes match the chassis; the centre is intentionally blank until the actual castor's mounting pattern is known.

The provisional printer assumption is a 220 by 220 mm usable bed. Each part has been checked with a 5 mm allowance on each side for a brim. Confirm the real printer's usable area, excluded zones and nozzle/material configuration before slicing. No G-code is provided because the printer is unknown.

## Interfaces that still need confirmation

1. **Drive system:** the wheel/axle area is centred on X = 0. Side rims have a central 96 mm opening. Four 28 by 4.5 mm slots, centred at X = -20 and +20, Y = -112 and +112 mm, provide provisional motor-bracket attachment. Motor-specific brackets, shaft height, wheel offset, tyre clearance and fasteners are not yet designed. Do not assume these slots fit a selected motor.
2. **Rear castor:** the adapter is centred at X = -135, Y = 0. Its chassis attachment holes are X = -150/-120 and Y = -22/+22 mm. Add the purchased castor's pattern only after checking that it does not collide with these fixing holes. Castor overall height, wheel diameter, swivel sweep and ground clearance remain unresolved.
3. **Payload supports:** four 4.5 mm holes at X = -125/+55 and Y = -72/+72 mm provide proposed riser locations. The front pair differs from the old concept's X = +35 mm to clear the new seam plates. Risers, elastomer mounts and the elevated deck are not included in this base package and must be updated together.
4. **Electronics and rigid sensor bridge:** general 3.4 mm holes and provisional bridge points allow separate mounting plates or standoffs. They are not direct Raspberry Pi 5 or STM32 footprints. Verify board clearances, cooling, connectors and electrical insulation.
5. **Battery:** four 18 by 4 mm strap slots are centred at X = -70/+10 and Y = -48/+48 mm. The battery needs a protected tray/retention arrangement that clears the top seam plates and all fasteners. Verify the selected battery dimensions; no battery tray is included.
6. **Stability and guards:** verify the assembled centre of gravity stays within the driven-wheel/castor support triangle, including braking and turns. Front anti-tip supports, bumpers and wheel guards shown in the earlier concept are not supplied by this base package. Their interfaces require a later revision before powered operation.

## Start with the small fit coupon

`00_Hole_and_Slot_Fit_Coupon.stl` is 70 by 32 by 6 mm. With its long axis horizontal, the round holes run left to right as 3.4, 4.3, 4.5 and 4.7 mm, followed by a 15 by 4.5 mm slot. Test it using the intended printer, material and fasteners. Measure the printed features and adjust the design or slicer compensation if required. The coupon checks dimensional fit only, not chassis strength.

## Provisional assembly sequence

1. Confirm the motor/wheel and castor interfaces, print-bed size, material, and workshop approval. Resolve any mounting changes before a full print.
2. Slice with each supplied flat bottom on the bed. Inspect the preview for complete walls, floors, holes and no unsupported features. Use the printer/material supplier's profile and record all settings. Wall count, infill and layer height remain to be selected and tested; no load rating is inferred from these files.
3. Label the four panels and bring them together around the 0.4 mm centre gaps. Install the four splice plates on top. Add the castor adapter underneath the rear centre.
4. The five attachment groups use 20 M4 through-bolts in total, with nuts and washers. M4 x 20 mm is a preliminary length for the 12 mm plastic stack; check actual washer/nut thickness and thread protrusion before purchase. Use washers to spread contact pressure and tighten without crushing the print. No torque value is specified.
5. With power disconnected, check seam alignment, fastener access, rocking, mount deflection and cracking. Review staged static loading with the supervisor/lab technician, including the full robot mass and secured carried load. Revise weak joints or panels before powered testing.

No motor mounts, electronics, castor, payload deck, bolts, washers or nuts are represented as purchased/installed hardware. Printing and assembly have not been performed.

## Validation boundary

The automated checks establish that the nine assembly parts are valid single solids, exported STLs are closed and consistently wound, a STEP reimport preserves nine solids, and assembled printed parts do not overlap by positive volume. Contact between joint plates and floors is intentional. The coupon mesh is also checked for closure.

The checks do not establish material properties, layer adhesion, print quality, load capacity, fatigue life, vibration behaviour, fastener pull-through resistance, stability, wheel clearance or compatibility with actual hardware. No FEA has been completed.

The CAD source uses the documented STEP/STL export functions: [CadQuery import and export documentation](https://cadquery.readthedocs.io/en/latest/importexport.html).

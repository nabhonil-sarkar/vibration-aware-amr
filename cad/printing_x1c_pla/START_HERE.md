# AMR chassis — start printing

4 October 2026. Bambu Lab X1 Carbon; PLA, 1.75 mm filament. Physical plate 257 × 257 mm; printable volume 256 × 256 × 256 mm.

## Start with the fit coupon

1. Open Bambu Studio. Select your X1 Carbon with the nozzle actually installed, the actual plate surface, and the matching PLA filament profile. Use Generic PLA if the brand is unknown. Filament diameter is not nozzle diameter.
2. Import `3MF_Models/00_Hole_and_Slot_Fit_Coupon.3mf` as a model, or import its STL from `STL/`. The 3MF files contain geometry with explicit millimetre units; they are not sliced Bambu projects. If asked to import geometry only, choose that option.
3. Keep scale at 100%, with the supplied flat bottom on the plate. Coupon dimensions must be 70 × 32 × 6 mm. Never use “scale to fit”.
4. For a confirmed 0.4 mm nozzle, use the standard 0.20 mm process profile as a starting point. Coupon: 3 wall loops, 20% gyroid infill, 5 top and 5 bottom shell layers, supports off. For a different nozzle, use its matching standard process profile.
5. Slice Plate. Check Preview for complete floors, open holes and the slot, no floating paths, and no plate/exclusion warnings. Use temperatures and cooling from the selected PLA/plate profile. These starting settings have not been printer-tested.
6. Print Plate to your connected printer, or export the sliced plate to the printer's microSD card. Follow the lab's loading/bed-levelling procedure and inspect the first layer. A model STL/3MF must be sliced before the printer can run it.

Measure the finished coupon. With the long axis horizontal, holes run left to right as Ø3.4, Ø4.3, Ø4.5 and Ø4.7 mm, followed by a 15 × 4.5 mm slot. Test the actual M3/M4 fasteners. Record fit and dimensions before committing to the large panels. If holes need compensation, apply and verify it consistently; do not change the overall scale.

## Then print the chassis parts

Print one of each file 01–08. Each main panel is about 169.8 × 134.8 × 20 mm. Use one panel per plate, flat bottom down, with rims and ribs up. Joint plates are flat, 6 mm thick, and may be grouped with enough spacing; Auto Arrange must respect plate exclusions and any brim.

Suggested prototype starting settings for a confirmed 0.4 mm nozzle: standard 0.20 mm profile, 4 wall loops, 35% gyroid infill, 6 top and 6 bottom shell layers, supports off. Start with one panel and inspect it before printing the other three. Add a 5 mm outer brim if needed for adhesion and check clearance in Preview. Use the filament profile's temperatures and lab-approved speed/cooling settings. These settings are an engineering starting point, not a certified load rating. Slicer estimates determine actual filament use and print time.

File 09 is the blank rear-castor adapter, 54 × 64 × 6 mm. Its chassis attachment holes exist; the purchased castor's mounting pattern is not yet defined. Print it only for fitting, or finish that interface first.

`PRINT_LIST.csv` lists all ten meshes and quantities. STL and 3MF files are alternative formats of the same part: print either format, not both. All are single closed volumes; every part fits nominal printable XY with at least 5 mm margin. Bambu Studio's actual exclusions still take precedence.

## Assembly and scope

Use the reference assembled/exploded pictures. Bring panels 01–04 together around the designed 0.4 mm seam gaps. Plates 05–08 connect the seams on top; adapter 09 fits beneath the rear centre. The five attachment groups require 20 M4 through-bolts plus nuts and washers. M4 × 20 mm was a preliminary estimate; check the actual plastic/washer/nut stack and thread engagement. Tighten without crushing PLA.

This package is the nine-part chassis base preserved in the v04 robot assembly, plus the fit coupon. It does not include released motor mounts, risers, payload deck/isolation interfaces, electronics mounts or battery tray. Those need hardware-specific refinement. Do not print purchased-component envelopes from the full robot assembly. Strength, whole-robot stability and 1 kg carried-load capacity remain untested; start with dimensional fitting and review loading with the lab.

No G-code is supplied: nozzle size and plate surface are not yet confirmed. Select them in Bambu Studio to generate the printer-specific file. Old source notes assuming a 220 mm bed are superseded by the user-confirmed X1 Carbon dimensions above.

Profile sources: Bambu Studio's official preset repository (https://github.com/bambulab/BambuStudio/tree/master/resources/profiles/BBL) and Bambu plate guidance (https://us.store.bambulab.com/products/bambu-textured-pei-plate). The wall/infill suggestions above are project starting settings, not manufacturer structural specifications.

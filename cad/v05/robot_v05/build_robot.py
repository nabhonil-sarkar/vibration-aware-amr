"""Full robot concept v05.1 around the single-piece baseplate. Units mm.
+X front, +Y left, Z up, ground at Z = 0. Requires cadquery 2.x.

v05.1 changes (13 Nov 2026): drive rebuilt around the Kuriosity worm-gearbox encoder motor
(JGY-370 class: 46 x 32 x 25 mm gearbox, 6 mm shaft) held in a printed cradle that bolts into the
existing baseplate slots; 65 mm wheels; 12 mm ball caster on a printed block; pillars are solid
prints with heat-set inserts and short screws (no threaded rod); shelf posts are stacked M3 standoffs.
Purchased parts are INDICATIVE ENVELOPES until measured. Baseplate v05 is unchanged.
Run: python build_robot.py --out OUTPUT_DIRECTORY
"""
from pathlib import Path
import argparse, json, sys, pickle
import numpy as np
import cadquery as cq
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'chassis_v05'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_baseplate as B

# v05.2 (17 Nov 2026): MEASURED by the student with vernier calipers: wheel 66.32 dia x 26.90 wide,
# gearbox 46.46 x 31.76 x 22.38 mm, gearbox face to wheel inner face 6.1 mm, ball caster mounting face
# to ball bottom 18 mm. STILL ASSUMED: shaft centred top-to-bottom and 11 mm from the gearbox free end.
WHEEL_D, WHEEL_W, WHEEL_GAP = 66.32, 26.90, 6.1
AXLE_X, AXLE_Z = 43.0, WHEEL_D / 2          # 33.16
GB = dict(L=46.46, H=31.76, T=22.38)         # gearbox: length (X), height (Z), thickness (Y)
SHAFT_FROM_FREE_END = 11.0                   # ASSUMED (photo agrees roughly); cradle slots allow +-15 mm in X
GB_X1 = AXLE_X + SHAFT_FROM_FREE_END
GB_X0 = GB_X1 - GB['L']
GB_Y1 = 117.0                                # outboard face: puts the wheel 3 mm clear of the plate edge (y = 120)
GB_Y0 = GB_Y1 - GB['T']
CRADLE_Y_OUT = GB_Y1 + 0.25 + 2.0            # 2 mm outboard wall; leaves ~3.8 mm to the wheel
WHEEL_Y0 = GB_Y1 + WHEEL_GAP                 # wheel inner face, 123.1
TRACK = 2 * (WHEEL_Y0 + WHEEL_W / 2)
CASTER_H = 18.0                              # ball caster mounting face to floor (measured)
GB_Z0, GB_Z1 = AXLE_Z - GB['H'] / 2, AXLE_Z + GB['H'] / 2    # 16.5 .. 48.5
ROOF = 6.0
PLATE_Z = GB_Z1 + ROOF                       # 54.5: underside of baseplate
DZ = PLATE_Z - 56.0                          # upper parts were laid out for a 56 mm plate height
FLOOR = 62.0                                 # layout reference for upper parts (shifted by DZ at the end)

C = dict(plate=(0.25, 0.50, 0.75), printed=(0.55, 0.62, 0.70), cradle=(0.30, 0.66, 0.62), deck=(0.93, 0.56, 0.20),
         payload=(0.95, 0.95, 0.93), pcb=(0.10, 0.50, 0.28), dark=(0.16, 0.17, 0.19), motor=(0.42, 0.44, 0.47),
         tyre=(0.09, 0.09, 0.10), hub=(0.80, 0.80, 0.78), battery=(0.20, 0.24, 0.42), brass=(0.78, 0.63, 0.25),
         rubber=(0.75, 0.15, 0.13), lidar=(0.12, 0.12, 0.14), red=(0.85, 0.10, 0.10), yellow=(0.95, 0.78, 0.10),
         strap=(0.10, 0.10, 0.10), steel=(0.70, 0.72, 0.74), blue=(0.15, 0.30, 0.65), purple=(0.45, 0.25, 0.60),
         screw=(0.22, 0.22, 0.24), white=(0.92, 0.92, 0.90))


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))

def cylz(x, y, z0, z1, d):
    return cq.Workplane('XY').circle(d / 2).extrude(z1 - z0).translate((x, y, z0))

def cyly(x, z, y0, y1, d):
    return cq.Workplane('XY').circle(d / 2).extrude(y1 - y0).rotate((0, 0, 0), (1, 0, 0), -90).translate((x, y0, z))

def cylx(y, z, x0, x1, d):
    return cq.Workplane('XY').circle(d / 2).extrude(x1 - x0).rotate((0, 0, 0), (0, 1, 0), 90).translate((x0, y, z))

def poly(pts, z0, z1):
    return cq.Workplane('XY').polyline(pts).close().extrude(z1 - z0).translate((0, 0, z0))

def yr(s, a, b):
    return (a, b) if s > 0 else (-b, -a)


def build():
    parts = []  # (name, workplane, colour, group)

    def add(n, w, c, g, upper=True):
        parts.append((n, w.translate((0, 0, DZ)) if upper else w, C[c], g))

    def low(n, w, c, g='drive'):
        add(n, w, c, g, upper=False)

    # ---- chassis ----
    plate, _ = B.build()
    low('C_Baseplate_v05_Single_Piece', plate.translate((0, 0, PLATE_Z)), 'plate', 'chassis')

    # ---- drive module, built for the left side then mirrored ----
    cy = (GB_Y0 + GB_Y1) / 2
    motor = (box(GB_X0, GB_X1, GB_Y0, GB_Y1, GB_Z0, GB_Z1)
             .union(cylx(cy, AXLE_Z, GB_X0 - 30.8, GB_X0, 24.4))
             .union(cylx(cy, AXLE_Z, GB_X0 - 30.8 - 13, GB_X0 - 30.8, 22))
             .union(cyly(AXLE_X, AXLE_Z, GB_Y1, WHEEL_Y0 + 5, 6)))
    import build_print_parts as PP                                  # same cradle and cap as the print files
    cradle, cap = PP.cradle_left()
    wy0 = WHEEL_Y0
    coupling = cyly(AXLE_X, AXLE_Z, GB_Y1 + 0.5, wy0 + 1, 12).cut(cyly(AXLE_X, AXLE_Z, GB_Y1, wy0 + 2, 6))
    tyre = cyly(AXLE_X, AXLE_Z, wy0, wy0 + WHEEL_W, WHEEL_D).cut(cyly(AXLE_X, AXLE_Z, wy0 - 1, wy0 + WHEEL_W + 1, 46))
    hub = cyly(AXLE_X, AXLE_Z, wy0 + 1, wy0 + WHEEL_W - 1, 46).cut(cyly(AXLE_X, AXLE_Z, wy0, wy0 + 5, 6))
    plate_screws = [cylz(x, y, PLATE_Z + 6, PLATE_Z + 8.3, 7.0) for x in (18, 58) for y in (88, 100)]  # M3 head on a washer
    cap_screws = [cylz(x, y, GB_Z0 - 5, GB_Z0 - 3, 5.5) for x, y in ((10, 85), (52, 85), (57, 106))]
    module = [('Worm_Gearbox_Encoder_Motor_JGY370_CLASS_ENVELOPE', motor, 'motor'),
              ('Printed_Motor_Cradle', cradle, 'cradle'), ('Printed_Cradle_Cap', cap, 'cradle'),
              ('Wheel_Adapter_6mm', coupling, 'brass'), ('Tyre_66mm', tyre, 'tyre'), ('Wheel_Hub', hub, 'hub')]
    module += [(f'Cradle_To_Plate_Screw_M3_{i}', s, 'screw') for i, s in enumerate(plate_screws, 1)]
    module += [(f'Cap_Screw_M3_{i}', s, 'screw') for i, s in enumerate(cap_screws, 1)]
    for side, mirror in (('Left', False), ('Right', True)):
        for n, w, c in module:
            low(f'D_{side}_{n}', w.mirror('XZ') if mirror else w, c)

    # ---- rear ball caster on a printed block (uses the plate's 30 x 44 M4 pattern) ----
    low('D_Rear_Caster_Block_Printed', box(-112, -68, -30, 30, CASTER_H, PLATE_Z), 'cradle')
    low('D_Rear_Ball_Caster_12mm_Housing_ENVELOPE', cylz(-90, 0, 6, CASTER_H, 20).union(box(-103, -77, -6, 6, CASTER_H - 3, CASTER_H)), 'white')
    low('D_Rear_Ball_Caster_12mm_Ball', cq.Workplane('XY').sphere(6).translate((-90, 0, 6)).cut(box(-97, -83, -7, 7, 6, 13)), 'steel')
    for i, (x, y) in enumerate([(-105, 22), (-105, -22), (-75, 22), (-75, -22)], 1):
        low(f'D_Caster_Block_Screw_M3_{i}', cylz(x, y, PLATE_Z + 6, PLATE_Z + 8.3, 7.0), 'screw')

    # ---- front anti-tip skids, 3 mm above the floor ----
    for s, side in ((1, 'Left'), (-1, 'Right')):
        a, b = yr(s, 34, 66)
        skid = box(98, 112, a, b, PLATE_Z - 6, PLATE_Z).union(cylz(105, s * 50, 10, PLATE_Z - 6, 12)).union(cylz(105, s * 50, 3, 10, 16))
        low(f'D_Front_AntiTip_Skid_{side}', skid, 'printed')
        low(f'D_Skid_And_Column_Screw_M4_{side}', cylz(105, s * 60, PLATE_Z - 8.5, PLATE_Z - 6, 7.5), 'screw')
        low(f'D_Skid_Screw_M4_{side}', cylz(105, s * 40, PLATE_Z - 8.5, PLATE_Z - 6, 7.5), 'screw')

    # ---- tier 1: battery, Pi 5, power, chassis IMU ----
    add('E_Battery_145x86x36_ENVELOPE_NOT_SELECTED', box(-68, 18, -72.5, 72.5, FLOOR, 98), 'battery', 'electronics')
    for i, y0 in enumerate((30, -50), 1):
        band = box(-71.5, 22.5, y0, y0 + 20, 98, 99.5).union(box(-71.5, -70, y0, y0 + 20, FLOOR, 98)).union(box(21, 22.5, y0, y0 + 20, FLOOR, 98))
        add(f'E_Battery_Strap_{i}', band, 'strap', 'electronics')
    add('E_Pi5_Carrier_Plate', box(52, 112, -46, 46, FLOOR, 65), 'printed', 'electronics')
    add('E_Raspberry_Pi_5_PCB_REFERENCE', box(54, 110, -42.5, 42.5, 71, 72.6), 'pcb', 'electronics')
    for i, (x, y) in enumerate([(57.5, -39), (106.5, -39), (57.5, 19), (106.5, 19)], 1):
        add(f'E_Pi5_Standoff_M2p5_{i}', cylz(x, y, 65, 71, 5), 'brass', 'electronics')
    add('E_Pi5_Active_Cooler_Allowance', box(64, 100, -22, 20, 72.6, 88), 'dark', 'electronics')
    add('E_Pi5_USB_Ethernet_Allowance', box(58, 108, 25, 44, 72.6, 87), 'steel', 'electronics')
    add('E_Power_Regulator_GENERIC', box(-110, -85, 30, 62, FLOOR, 78), 'blue', 'electronics')
    add('E_Main_Fuse_Holder_GENERIC', box(-110, -80, -62, -48, FLOOR, 76), 'dark', 'electronics')
    add('E_Chassis_IMU_Rigid', box(-101, -80, -8, 8, FLOOR, 66), 'purple', 'electronics')

    # ---- controller shelf on stacked M3 standoffs (2 x 20 mm each) ----
    for i, (x, y) in enumerate([(-60, 80), (-60, -80), (0, 80), (0, -80)], 1):
        add(f'E_Shelf_Standoff_M3_20mm_Lower_{i}', cylz(x, y, FLOOR, 82, 5.5), 'brass', 'electronics')
        add(f'E_Shelf_Standoff_M3_20mm_Upper_{i}', cylz(x, y, 82, 102, 5.5), 'brass', 'electronics')
        add(f'E_Shelf_Screw_M3_{i}', cylz(x, y, 105, 107, 5.5), 'screw', 'electronics')
    add('E_Controller_Shelf', box(-80, 8, -88, 88, 102, 105), 'printed', 'electronics')
    add('E_STM32_Nucleo64_CLASS_PCB_UNIDENTIFIED', box(-78, 4.5, 6, 76, 111, 112.6), 'pcb', 'electronics')
    add('E_STM32_Headers', box(-60, -5, 10, 15, 112.6, 121).union(box(-60, -5, 67, 72, 112.6, 121)), 'dark', 'electronics')
    add('E_Motor_Driver_Carrier_Board', box(-62, -7, -62, -17, 111, 112.6), 'pcb', 'electronics')
    add('E_Motor_Driver_TB6612FNG_Module_ENVELOPE', box(-40, -15, -52, -27, 112.6, 117), 'red', 'electronics')
    add('E_Motor_Power_Screw_Terminals', box(-62, -50, -58, -21, 112.6, 124), 'blue', 'electronics')
    k = 1
    for (x0, x1, y0, y1) in [(-78, 4.5, 6, 76), (-62, -7, -62, -17)]:
        for x in (x0 + 3, x1 - 3):
            for y in (y0 + 3, y1 - 3):
                add(f'E_Board_Spacer_{k}', cylz(x, y, 105, 111, 5), 'brass', 'electronics'); k += 1

    # ---- isolated payload stage: printed risers with inserts, elastomer, deck ----
    risers = [(-90, 72), (-90, -72), (28, 76), (28, -76)]
    for i, (x, y) in enumerate(risers, 1):
        add(f'P_Printed_Riser_Insert_Both_Ends_{i}', cylz(x, y, FLOOR, 118, 14), 'printed', 'payload')
        add(f'P_Isolator_{i}_SOURCE_NOT_FOUND', cylz(x, y, 118, 132, 18), 'rubber', 'payload')
        add(f'P_Deck_Nut_M4_{i}', cylz(x, y, 136, 139.2, 8), 'screw', 'payload')
        low(f'P_Riser_Screw_M4_Under_Plate_{i}', cylz(x, y, PLATE_Z - 2.5, PLATE_Z, 7.5), 'screw', 'payload')
    dk = [(28, 90), (-88, 90), (-110, 68), (-110, -68), (-88, -90), (28, -90), (42, -76), (42, 76)]
    add('P_Isolated_Payload_Deck_152x180', poly(dk, 132, 136), 'deck', 'payload')
    tray = box(-109, 37, -60, 60, 136, 148).cut(box(-106, 34, -57, 57, 139, 149))
    add('P_Payload_Carrier_Tray', tray, 'printed', 'payload')
    add('P_Dummy_Payload_140x110x37_ENVELOPE', box(-106, 34, -55, 55, 139, 176), 'payload', 'payload')
    add('P_Dummy_Payload_Lid_Detail', box(-66, -6, -22, 22, 176, 179), 'printed', 'payload')
    add('P_Payload_IMU_On_Isolated_Deck', box(0, 21, 66, 82, 136, 140), 'purple', 'payload')

    # ---- rigid sensor bridge: printed columns with inserts ----
    cols = [(105, 60), (105, -60), (60, 76), (60, -76)]
    for i, (x, y) in enumerate(cols, 1):
        add(f'S_Printed_Bridge_Column_Insert_Both_Ends_{i}', cylz(x, y, FLOOR, 150, 12), 'printed', 'sensors')
        add(f'S_Bridge_Screw_M4_{i}', cylz(x, y, 154, 156.5, 7.5), 'screw', 'sensors')
    for i, (x, y) in enumerate(cols[2:], 3):
        low(f'S_Column_Screw_M4_Under_Plate_{i}', cylz(x, y, PLATE_Z - 2.5, PLATE_Z, 7.5), 'screw', 'sensors')
    add('S_Rigid_Sensor_Bridge_Plate', poly([(46, 90), (46, -90), (118, -66), (118, 66)], 150, 154), 'printed', 'sensors')
    add('S_LiDAR_A1_CLASS_Base_ENVELOPE', box(47, 117, -48.5, 48.5, 154, 172), 'lidar', 'sensors')
    add('S_LiDAR_A1_CLASS_Scan_Head_ENVELOPE', cylz(82, -13, 172, 207, 70), 'lidar', 'sensors')
    add('S_LiDAR_A1_CLASS_Motor_ENVELOPE', cylz(82, 35.5, 172, 190, 24), 'steel', 'sensors')
    add('S_Camera_Bracket', box(105, 107.5, -15, 15, 120, 150), 'printed', 'sensors')
    add('S_AI_Camera_25x24_ENVELOPE', box(107.5, 117, -12.5, 12.5, 124, 148), 'pcb', 'sensors')
    add('S_AI_Camera_Lens', cylx(0, 136, 117, 121, 10), 'dark', 'sensors')

    # ---- E-stop (location and shape only; no electrical cutoff is implied) ----
    add('S_EStop_Bracket_And_Post', box(-82, -62, -104, -92, FLOOR, 66).union(cylz(-74, -99, 66, 142, 12)), 'printed', 'sensors')
    add('S_EStop_Housing_ENVELOPE', cylz(-74, -99, 142, 150, 34), 'yellow', 'sensors')
    add('S_EStop_Button_ENVELOPE', cylz(-74, -99, 150, 162, 30), 'red', 'sensors')
    return parts


def clash_check(parts):
    clashes = []
    shapes = [(n, p.val(), p.val().BoundingBox()) for n, p, _, _ in parts]
    for i, (na, a, ba) in enumerate(shapes):
        for nb, b, bb in shapes[i + 1:]:
            if ba.xmax <= bb.xmin or bb.xmax <= ba.xmin or ba.ymax <= bb.ymin or bb.ymax <= ba.ymin or ba.zmax <= bb.zmin or bb.zmax <= ba.zmin:
                continue
            try:
                v = a.intersect(b).Volume()
            except Exception:
                v = float('nan')
            if not (v <= 0.01):
                clashes.append([na, nb, round(float(v), 3)])
    return clashes


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    parts = build()
    for n, p, _, _ in parts:
        assert p.val().isValid(), n
    asm = cq.Assembly(name='Vibration_Aware_AMR_v05_2_CONCEPT')
    for n, p, c, _ in parts:
        asm.add(p, name=n, color=cq.Color(*c))
    step = out / 'Vibration_Aware_AMR_v05_2_Concept.step'
    asm.export(str(step))
    n_re = len(cq.importers.importStep(str(step)).solids().vals())
    clashes = clash_check(parts)
    allb = [p.val().BoundingBox() for _, p, _, _ in parts]
    env = dict(x=[min(b.xmin for b in allb), max(b.xmax for b in allb)], y=[min(b.ymin for b in allb), max(b.ymax for b in allb)],
               z=[min(b.zmin for b in allb), max(b.zmax for b in allb)])
    slot_rows = (64.0, 76.0, 88.0, 100.0); slot_x = ((12.25, 37.75), (48.25, 73.75))
    cradle_screws = [(x, y) for x in (18, 58) for y in (88, 100)]
    fit = all(y in slot_rows and any(a <= x <= b for a, b in slot_x) for x, y in cradle_screws)
    report = dict(status='CONCEPT v05.2 - drive, wheel and caster from caliper measurements (17 Nov 2026); purchased parts elsewhere are indicative envelopes; not load tested',
                  parts=len(parts), solids_after_STEP_reimport=n_re, positive_volume_clashes=clashes,
                  overall_mm=dict(length=round(env['x'][1] - env['x'][0], 1), width=round(env['y'][1] - env['y'][0], 1), height=round(env['z'][1], 1)),
                  key_heights_mm=dict(plate_underside=PLATE_Z, deck_top=136 + DZ, payload_top=179 + DZ, lidar_top=207 + DZ,
                                      lowest_point_cradle_cap_screw=GB_Z0 - 5, skid_gap=3),
                  geometry=dict(wheel_diameter=WHEEL_D, track=round(TRACK, 1), drive_axle_x=AXLE_X, caster_x=-90, axle_to_caster=AXLE_X + 90),
                  baseplate_check=dict(cradle_screw_positions_xy=cradle_screws, all_land_in_existing_slots=bool(fit),
                                       note='Baseplate v05 is unchanged. Cradle screws use slot rows Y = 88 and 100 on each side.'),
                  assumptions_to_measure=['shaft 11 mm from gearbox free end and centred in height (ASSUMED, photo agrees roughly)',
                                          'motor can diameter and bearing boss size (cleared generously)'],
                  groups={g: sum(1 for p in parts if p[3] == g) for g in sorted(set(p[3] for p in parts))},
                  part_names=[p[0] for p in parts])
    (out / 'Assembly_Checks.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    meshes = []
    for n, p, c, g in parts:
        v, t = p.val().tessellate(0.2, 0.2)
        meshes.append(dict(name=n, colour=c, group=g, V=np.array([(q.x, q.y, q.z) for q in v]), T=np.array(t)))
    with open(out / '_meshes.pkl', 'wb') as fh:
        pickle.dump(meshes, fh)
    print(json.dumps({k: v for k, v in report.items() if k != 'part_names'}, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, required=True)
    run(ap.parse_args().out)

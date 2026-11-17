"""Print files for the AMR v05.1 printed parts. Units mm. Requires cadquery 2.x and trimesh.
Run: python build_print_parts.py --out OUTPUT_DIRECTORY

Every part is exported in its PRINT ORIENTATION with its lowest corner at the origin.
Insert bores follow the Kuriosity brass insert kit: M3 -> 4.0 mm hole, M4 -> 5.2 mm hole.
"""
from pathlib import Path
import argparse, csv, json, shutil, sys
import cadquery as cq
import trimesh
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / 'chassis_v05'))
import build_robot as R

M3_INS, M4_INS = 4.0, 5.2        # heat-set insert bores
M3_CL, M4_CL = 3.4, 4.5          # clearance holes (same as the v03 fit coupon)
M2_PILOT = 1.8                   # M2 screws cut their own thread in this hole (no nut, no insert)
PZ = R.PLATE_Z                    # 55.04 in v05.2
box, cylz, cyly, cylx, poly = R.box, R.cylz, R.cyly, R.cylx, R.poly


def drill(part, pts, d, z0=-50, z1=300):
    tool = cq.Workplane('XY').pushPoints(pts).circle(d / 2).extrude(z1 - z0).translate((0, 0, z0))
    return part.cut(tool)


def pillar(d, h):
    """Solid post with an M4 insert bore and a screw relief in each end."""
    p = cylz(0, 0, 0, h, d)
    for z0, z1 in ((0, 7), (h - 7, h)):
        p = p.cut(cylz(0, 0, z0, z1, M4_INS))
    for z0, z1 in ((0, 16), (h - 16, h)):
        p = p.cut(cylz(0, 0, z0, z1, 4.3))
    return p


def cradle_left():
    """v05.2: pocket from the measured gearbox (46.46 x 31.76 x 22.38), 0.3 / 0.25 mm clearance.
    Open behind the gearbox for the motor can (26 mm wide), clearance hole for the bearing boss on the
    inboard face, 2 mm outboard wall behind the shaft only (wheel is 6.1 mm from the gearbox face)."""
    x0, x1 = R.GB_X0 - 0.3, R.GB_X1 + 0.3            # pocket 47.06 long
    y0, y1 = R.GB_Y0 - 0.25, R.GB_Y1 + 0.25          # pocket 22.88 wide
    yo = R.CRADLE_Y_OUT
    zt = R.GB_Z1 + 0.2                               # pocket ceiling
    zb = R.GB_Z0
    yc = (R.GB_Y0 + R.GB_Y1) / 2
    c = (box(2, 64, 82, yo, zt, PZ)                  # roof
         .union(box(2, 62, 82, y0, zb, zt))          # inboard wall
         .union(box(x1, 62, 82, yo, zb, zt))         # front end wall
         .union(box(x0, 31, y1, yo, zb, zt)))        # outboard wall, gearbox only, open around the shaft
    c = c.cut(box(0, R.GB_X0 + 1.0, yc - 13, yo + 1, zb - 1, zt))     # motor can relief, 26 mm wide, 1 mm past the can joint
    c = c.cut(box(R.AXLE_X - 9, R.AXLE_X + 9, 80, y0 + 0.5, zb - 1, R.AXLE_Z + 9))   # bearing boss relief, open to the cap side (prints without overhang)
    roof_pts = [(x, y) for x in (18, 58) for y in (88, 100)]
    c = c.cut(cq.Workplane('XY').pushPoints(roof_pts).circle(M3_INS / 2).extrude(5.3).translate((0, 0, PZ - 5.3)))
    c = c.cut(cq.Workplane('XY').pushPoints([(58, 90), (58, 108)]).circle(M3_INS / 2).extrude(6.5).translate((0, 0, zb)))
    c = c.cut(cylz(10, 84.9, zb, zb + 9, 2.6))       # rear cap screw threads straight into the wall
    cap = box(2, 62, 82, yo, zb - 3, zb)
    cap = drill(cap, [(58, 90), (58, 108), (10, 84.9)], M3_CL, zb - 5, zb + 1)
    return c, cap


def build():
    parts = []  # dict(name, shape, qty, group, flip, depends, notes)

    def add(name, shape, qty, group, flip=False, depends='Nothing', notes=''):
        parts.append(dict(name=name, shape=shape, qty=qty, group=group, flip=flip, depends=depends, notes=notes))

    # ---------- group 1: ready to print ----------
    coupon = box(0, 44, 0, 16, 0, 10)
    coupon = coupon.cut(cq.Workplane('XY').pushPoints([(7, 8), (17, 8)]).circle(M3_INS / 2).extrude(6).translate((0, 0, 4)))
    coupon = coupon.cut(cq.Workplane('XY').pushPoints([(28, 8), (38, 8)]).circle(M4_INS / 2).extrude(7).translate((0, 0, 3)))
    add('00_Insert_Fit_Coupon', coupon, 1, 'ready', notes='Print first. Two M3 bores (4.0 mm) and two M4 bores (5.2 mm). Practise setting inserts here.')

    add('02_Bridge_Column_88mm', pillar(12, 88), 4, 'ready', notes='Print upright with a brim. M4 insert in each end.')
    add('03_Payload_Riser_56mm', pillar(14, 56), 4, 'ready', depends='Isolator height (assumed 14 mm)',
        notes='Print upright with a brim. M4 insert in each end. Reprint taller if the isolators are shorter than 14 mm.')

    dk = [(28, 90), (-88, 90), (-110, 68), (-110, -68), (-88, -90), (28, -90), (42, -76), (42, 76)]
    deck = poly(dk, 0, 4).edges('|Z').fillet(3)
    deck = drill(deck, [(-90, 72), (-90, -72), (28, 76), (28, -76)], M4_CL)
    deck = drill(deck, [(-60, 66), (-60, -66), (-20, 66), (-20, -66)], M3_CL)
    deck = drill(deck, [(x, y) for x in (0, 10, 20) for y in (70, 80)], 3.2)
    add('04_Isolated_Payload_Deck', deck, 1, 'ready', notes='Flat. Four 4.5 mm isolator holes, four 3.4 mm tray holes, six 3.2 mm holes for the payload IMU.')

    tray = box(-109, 37, -60, 60, 0, 12).cut(box(-106, 34, -57, 57, 3, 13))
    for x in (-60, -20):
        for s in (1, -1):
            a, b = (60, 72) if s > 0 else (-72, -60)
            tray = tray.union(box(x - 8, x + 8, a, b, 0, 3))
    tray = drill(tray, [(-60, 66), (-60, -66), (-20, 66), (-20, -66)], M3_CL)
    add('05_Payload_Carrier_Tray', tray, 1, 'ready', notes='Flat, open side up. Inside 140 x 114 mm. Four ears bolt to the deck with M3 x 10 and nuts.')

    shelf = box(-80, 8, -88, 88, 0, 3).edges('|Z').fillet(3)
    shelf = drill(shelf, [(x, y) for x in range(-70, 1, 10) for y in range(-80, 81, 10)], M3_CL)
    add('06_Controller_Shelf', shelf, 1, 'ready', notes='Flat. 10 mm grid of 3.4 mm holes so any STM32 board and driver can be mounted. Corner posts at (-60, +/-80) and (0, +/-80).')

    pic = box(52, 112, -46, 46, 0, 3).edges('|Z').fillet(3)
    pic = drill(pic, [(57.5, -39), (106.5, -39), (57.5, 19), (106.5, 19)], 2.7)
    pic = drill(pic, [(80, 20), (100, 20), (60, -20), (100, -20)], M3_CL)   # baseplate grid points clear of the Pi holes
    pic = drill(pic, [(105, 40), (105, -40)], 9.5)
    add('07_Pi5_Carrier_Plate', pic, 1, 'ready', notes='Flat. Pi 5 holes 58 x 49 mm (2.7 mm, M2.5). Four 3.4 mm holes bolt to the baseplate grid at (80, 20), (100, 20), (60, -20), (100, -20). Two 9.5 mm holes clear the skid nuts.')

    br = poly([(46, 90), (46, -90), (118, -66), (118, 66)], 150, 154).edges('|Z').fillet(3)
    br = drill(br, [(105, 60), (105, -60), (60, 76), (60, -76)], M4_CL)
    br = br.cut(cq.Workplane('XY', origin=(54, 0, 140)).slot2D(24, 10, 90).extrude(20))
    tab = box(102.5, 107.5, -15, 15, 120, 150)    # 5 mm thick so the M2 camera screws get a full-depth thread
    for y0 in (-15, 12):
        g = cq.Workplane('XY').polyline([(105, 150), (93, 150), (105, 135)]).close().extrude(3)
        tab = tab.union(g.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, y0 + 3, 0)))
    for y in (-10.5, 10.5):
        for z in (146, 133.5):
            tab = tab.cut(cylx(y, z, 100, 110, M2_PILOT))
    add('08_Sensor_Bridge_Plate_With_Camera_Tab', br.union(tab), 1, 'ready', flip=True,
        depends='LiDAR holes (drill to suit); camera hole pattern (check)',
        notes='Print top face down so the camera tab points up. Column holes are in. LiDAR holes are NOT in: mark them from the real LiDAR and drill. Camera holes are 1.8 mm pilot holes on the 21 x 12.5 mm Pi camera pattern: M2 x 6 screws thread straight into the 5 mm tab.')

    # ---------- group 2: hold until the bought parts are measured ----------
    cl, cap = cradle_left()
    dep = 'Measured 17 Nov (gearbox 46.46 x 31.76 x 22.38, wheel gap 6.1); shaft position still assumed'
    add('10_Motor_Cradle_Left', cl, 1, 'ready', flip=True, depends=dep, notes='v05.2. Roof on the bed. Four M3 inserts in the roof, two in the front wall. Open behind the gearbox for the motor can; slot in the inboard wall clears the bearing boss.')
    add('11_Motor_Cradle_Right', cl.mirror('XZ'), 1, 'ready', flip=True, depends=dep, notes='v05.2. Mirror of the left cradle.')
    add('12_Cradle_Cap_Left', cap, 1, 'ready', depends=dep, notes='v05.2. Flat. Two M3 x 6 into inserts, one M3 x 10 straight into the wall.')
    add('13_Cradle_Cap_Right', cap.mirror('XZ'), 1, 'ready', depends=dep, notes='v05.2. Mirror of the left cap.')

    cb = box(-112, -68, -30, 30, R.CASTER_H, PZ)
    cb = cb.cut(cq.Workplane('XY').pushPoints([(-105, 22), (-105, -22), (-75, 22), (-75, -22)]).circle(M3_INS / 2).extrude(5.3).translate((0, 0, PZ - 5.3)))
    # caster: 12 mm nylon ball caster, two open U-slots 3.3 mm wide, slot centres 14.7 mm apart (measured 17 Nov)
    cb = cb.cut(cq.Workplane('XY').pushPoints([(-90, 7.35), (-90, -7.35)]).circle(M3_INS / 2).extrude(10).translate((0, 0, R.CASTER_H)))
    add('14_Rear_Caster_Block', cb, 1, 'ready', depends='Measured 17 Nov: caster 18 mm tall, slot centres 14.7 mm',
        notes='v05.2: 37 mm tall for the measured 18 mm caster. Four M3 inserts on top match the baseplate castor pattern. Two M3 inserts in the underside, 14.7 mm apart across the robot, hold the caster: M3 x 6 or M3 x 10 through its U-slots.')

    sk = box(98, 120, 34, 66, PZ - 6, PZ).union(cylz(113, 50, 3, PZ - 6, 13))   # post set forward so the screw heads clear it
    sk = sk.faces('<Z').edges().fillet(4)
    sk = drill(sk, [(105, 40), (105, 60)], M4_CL, PZ - 7, PZ + 1)
    add('15_Front_AntiTip_Skid', sk, 2, 'ready', flip=True, depends='Ride height from the measured wheel (66.32 mm)',
        notes='v05.2. Block on the bed, post up. Tip sits 3 mm above the floor at the new ride height (plate underside 55.0 mm).')
    return parts


def orient(p):
    s = p['shape']
    if p['flip']:
        s = s.rotate((0, 0, 0), (1, 0, 0), 180)
    bb = s.val().BoundingBox()
    return s.translate((-bb.xmin, -bb.ymin, -bb.zmin))


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    folders = dict(ready=out / '1_Ready_to_print', hold=out / '2_Hold_until_parts_are_measured')
    other = out / 'Other_formats'
    for d in list(folders.values()) + [other / 'STL', other / 'STEP']:
        d.mkdir(parents=True, exist_ok=True)
    rows, report = [], []
    # baseplate: copy the already-released files unchanged
    bp = HERE.parent / 'chassis_v05' / 'package'
    shutil.copy(bp / 'AMR_Baseplate_v05_Single_Piece.3mf', folders['ready'] / '01_Baseplate_v05_Single_Piece.3mf')
    shutil.copy(bp / 'AMR_Baseplate_v05_Single_Piece.stl', other / 'STL' / '01_Baseplate_v05_Single_Piece.stl')
    shutil.copy(bp / 'AMR_Baseplate_v05_Single_Piece.step', other / 'STEP' / '01_Baseplate_v05_Single_Piece.step')
    rows.append(['01_Baseplate_v05_Single_Piece', 1, 240.0, 240.0, 12.0, 'Ready', 'Nothing',
                 'Unchanged from the earlier release. Flat, no supports. Any cut corner to the front-left of the bed.'])
    meshes = {}
    for p in build():
        s = orient(p)
        v = s.val()
        assert v.isValid(), p['name']
        n_solids = len(s.solids().vals())
        assert n_solids == 1, (p['name'], n_solids)
        bb = v.BoundingBox()
        stl = other / 'STL' / f"{p['name']}.stl"
        cq.exporters.export(s, str(stl), tolerance=0.03, angularTolerance=0.08)
        cq.exporters.export(s, str(other / 'STEP' / f"{p['name']}.step"))
        tm = folders[p['group']] / f"{p['name']}.3mf"
        cq.exporters.export(s, str(tm), tolerance=0.03, angularTolerance=0.08)
        m = trimesh.load_mesh(str(stl))
        assert m.is_watertight and m.is_winding_consistent and m.volume > 0, p['name']
        assert len(m.split()) == 1, p['name']
        m3 = trimesh.load(str(tm), force='mesh')
        assert abs(float(m3.volume) - float(m.volume)) < 1.0, p['name']
        assert bb.xlen <= 240 and bb.ylen <= 240 and bb.zlen <= 250, p['name']
        dims = [round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)]
        rows.append([p['name'], p['qty'], *dims, 'Ready' if p['group'] == 'ready' else 'HOLD', p['depends'], p['notes']])
        report.append(dict(part=p['name'], quantity=p['qty'], status=p['group'], print_size_mm=dims, volume_cm3=round(v.Volume() / 1000, 2),
                           solid_valid=True, stl_watertight=True, stl_components=1, threemf_volume_cm3=round(float(m3.volume) / 1000, 2)))
        tv, tt = v.tessellate(0.15, 0.15)
        meshes[p['name']] = (tv, tt, p['group'])
    with (out / 'PRINT_LIST.csv').open('w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh); w.writerow(['Part', 'Quantity', 'X mm', 'Y mm', 'Z mm', 'Status', 'Depends on', 'Notes'])
        w.writerows(rows)
    (out / 'Print_File_Checks.json').write_text(json.dumps(dict(
        status='Geometry and file checks only. Nothing here has been printed or load tested.',
        insert_bores_mm=dict(M3=M3_INS, M4=M4_INS), clearance_holes_mm=dict(M3=M3_CL, M4=M4_CL),
        baseplate='copied unchanged from the v05 release', parts=report), indent=2), encoding='utf-8')
    return meshes, rows


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, required=True)
    meshes, rows = run(ap.parse_args().out)
    import pickle, numpy as np
    pk = {k: (np.array([(q.x, q.y, q.z) for q in v]), np.array(t), g) for k, (v, t, g) in meshes.items()}
    pickle.dump(pk, open(HERE / '_print_meshes.pkl', 'wb'))
    for r in rows: print(r[:7])

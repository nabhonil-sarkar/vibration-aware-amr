"""v05.3 motor cradle (18 Nov 2026): replaces v05.2 parts 10-13 after the v05.2 outer wall cracked on the first fit.
Changes: no thin outboard wall; the gearbox is CLAMPED between the roof and the cap (pocket 0.3 mm shorter than the
gearbox, so the 3 cap screws squeeze it); two short 3 mm lips (one on the roof, one on the cap) stop it sliding outboard;
0.5 mm side clearance and 0.4 mm end clearance so it slides in by hand. Same roof screw holes and baseplate slots."""
import sys
from pathlib import Path
import cadquery as cq, trimesh
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / 'chassis_v05'))
import build_robot as R
from build_print_parts import M3_INS, M3_CL, PZ, box, cylz, drill
CS, CE, SQ, LIP_T, LIP_H = 0.5, 0.4, 0.3, 3.0, 4.0     # side clearance, end clearance, clamp squeeze, lip size

def cradle_v053():
    x0, x1 = R.GB_X0, R.GB_X1 + CE
    y0, y1 = R.GB_Y0 - CS, R.GB_Y1 + CS
    yo = y1 + LIP_T                                   # 120.5: outer face of both lips
    zt = R.GB_Z1                                      # roof underside = gearbox top (sets the axle height, unchanged)
    zb = R.GB_Z0 + SQ                                 # walls stop 0.3 mm short: cap squeezes the gearbox
    yc = (R.GB_Y0 + R.GB_Y1) / 2
    c = (box(2, 64, 82, yo, zt, PZ)                   # roof
         .union(box(2, 62, 82, y0, zb, zt))           # inboard wall
         .union(box(x1, 62, 82, yo, zb, zt))          # front end wall
         .union(box(x0 + 1.5, x1, y1, yo, zt - LIP_H, zt)))   # roof lip, outboard of the gearbox top edge
    c = c.cut(box(0, R.GB_X0 + 1.0, yc - 13, yo + 1, zb - 1, zt))                      # motor can relief
    c = c.cut(box(R.AXLE_X - 9, R.AXLE_X + 9, 80, y0 + 0.5, zb - 1, R.AXLE_Z + 9))      # bearing boss relief (inboard)
    roof_pts = [(x, y) for x in (18, 58) for y in (88, 100)]
    c = c.cut(cq.Workplane('XY').pushPoints(roof_pts).circle(M3_INS / 2).extrude(5.3).translate((0, 0, PZ - 5.3)))
    c = c.cut(cq.Workplane('XY').pushPoints([(58, 90), (58, 108)]).circle(M3_INS / 2).extrude(6.5).translate((0, 0, zb)))
    c = c.cut(cylz(10, 84.9, zb, zb + 9, 2.6))       # rear cap screw threads straight into the wall
    cap = box(2, 62, 82, yo, zb - 3, zb).union(box(x0 + 1.5, x1 - 0.4, y1, yo, zb, zb + LIP_H - 1))   # cap + 3 mm lip
    cap = drill(cap, [(58, 90), (58, 108), (10, 84.9)], M3_CL, zb - 5, zb + 1)
    return c, cap

if __name__ == '__main__':
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    cl, cap = cradle_v053()
    parts = {'10_Motor_Cradle_Left_v05_3': (cl, True), '11_Motor_Cradle_Right_v05_3': (cl.mirror('XZ'), True),
             '12_Cradle_Cap_Left_v05_3': (cap, False), '13_Cradle_Cap_Right_v05_3': (cap.mirror('XZ'), False)}
    for n, (s, flip) in parts.items():
        if flip: s = s.rotate((0, 0, 0), (1, 0, 0), 180)
        bb = s.val().BoundingBox(); s = s.translate((-bb.xmin, -bb.ymin, -bb.zmin))
        assert s.val().isValid() and len(s.solids().vals()) == 1, n
        for ext in ('stl', '3mf', 'step'):
            kw = {} if ext == 'step' else dict(tolerance=0.03, angularTolerance=0.08)
            cq.exporters.export(s, str(out / f'{n}.{ext}'), **kw)
        m = trimesh.load_mesh(str(out / f'{n}.stl')); assert m.is_watertight and len(m.split()) == 1, n
        b = s.val().BoundingBox(); print(n, round(b.xlen, 1), round(b.ylen, 1), round(b.zlen, 1), 'vol cm3', round(s.val().Volume() / 1000, 1))

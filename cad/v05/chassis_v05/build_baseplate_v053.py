"""AMR baseplate v05.3 (20 Nov 2026). Same layout and coordinates as v05 / v05.2, so every printed part still fits.
Changes, from the first print:
  * hole sizes up for printer shrinkage: M3 3.4 -> 3.6 mm, M4 4.5 -> 4.8 mm, motor slots 4.5 -> 4.8 mm wide
  * 0.6 mm chamfer round the bottom of every hole and slot, so first-layer squash (elephant foot) cannot skin them over
  * two 12 x 20 mm openings at (-74, +/-96) so each motor's 6-pin plug and cable can come up beside the shelf
  * two short slots for the chassis IMU (GY-521) at the rear left, clear of the caster block underneath
    (centres 14.0 to 17.6 mm apart, so they take the board's own hole spacing without measuring)
Run: python build_baseplate_v053.py --out DIR   (needs build_baseplate.py beside it, cadquery 2.x, trimesh)"""
import argparse, json, math, sys
from pathlib import Path
import cadquery as cq, trimesh
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_baseplate as B

M3, M4, SLOT_W, CHAMFER = 3.6, 4.8, 4.8, 0.6
IMU_SLOTS = [(-90.0, 40.1), (-90.0, 55.9)]       # each 3.6 wide, 5.4 long across the robot (Y)
IMU_SLOT = (5.4, 3.6)
MOTOR_WIRE_SLOTS = [(-74.0, 96.0), (-74.0, -96.0)]   # 12 wide x 20 long (across the robot): the 6-pin motor plug passes through
MOTOR_WIRE_SLOT = (20.0, 12.0)
grid_ref = B.grid_points()                         # computed with the original keep-outs, so the grid is unchanged


def build():
    P = B.P
    f, rw, rh, c = P['floor'], P['rim_width'], P['rim_height'], P['corner_chamfer']
    body = cq.Workplane('XY').polyline(B.outline(B.H, c)).close().extrude(f + rh).edges('|Z').fillet(4.0)
    inner_c = c - rw * (2 - math.sqrt(2))
    body = body.cut(cq.Workplane('XY', origin=(0, 0, f)).polyline(B.outline(B.H - rw, inner_c)).close()
                    .extrude(rh + 1).edges('|Z').fillet(2.0))
    tools = cq.Workplane('XY', origin=(0, 0, -5)).pushPoints(grid_ref).circle(M3 / 2).extrude(40)
    tools = tools.union(cq.Workplane('XY', origin=(0, 0, -5)).pushPoints(B.castor + B.deck + B.front).circle(M4 / 2).extrude(40))
    for x, y in B.motor_slots:
        tools = tools.union(cq.Workplane('XY', origin=(x, y, -5)).slot2D(B.MOTOR_SLOT[0] + (SLOT_W - B.MOTOR_SLOT[1]), SLOT_W, 0).extrude(40))
    for s in B.cable + B.strap:
        tools = tools.union(cq.Workplane('XY', origin=(s[0], s[1], -5)).slot2D(s[2], s[3], s[4]).extrude(40))
    for x, y in MOTOR_WIRE_SLOTS:
        tools = tools.union(cq.Workplane('XY', origin=(x, y, -5)).slot2D(MOTOR_WIRE_SLOT[0], MOTOR_WIRE_SLOT[1], 90).extrude(40))
    for x, y in IMU_SLOTS:
        tools = tools.union(cq.Workplane('XY', origin=(x, y, -5)).slot2D(IMU_SLOT[0], IMU_SLOT[1], 90).extrude(40))
    body = body.cut(tools)
    # chamfer the bottom edge of every hole and slot (inner wires of the underside face)
    bottom = body.faces('<Z').val()
    edges = [e for w in bottom.innerWires() for e in w.Edges()]
    body = body.newObject(edges).chamfer(CHAMFER)
    return body


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    part = build(); shape = part.val()
    assert len(part.solids().vals()) == 1 and shape.isValid()
    bb = shape.BoundingBox()
    name = 'AMR_Baseplate_v05_3_Single_Piece'
    cq.exporters.export(part, str(out / f'{name}.step'))
    for ext in ('stl', '3mf'):
        cq.exporters.export(part, str(out / f'{name}.{ext}'), tolerance=0.03, angularTolerance=0.08)
    mesh = trimesh.load_mesh(str(out / f'{name}.stl'))
    assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split()) == 1
    margin, gap = B.bed_clearance()
    assert bb.xlen <= B.P['bed'] and bb.ylen <= B.P['bed'] and gap > 3.0
    rep = dict(status='v05.3 print file: geometry and file checks only; not load tested',
               changes=['M3 holes 3.6 mm, M4 holes 4.8 mm, motor slots 4.8 mm wide', f'{CHAMFER} mm bottom chamfer on every hole and slot',
                        'two GY-521 slots at the rear left, (-90, 40.1) and (-90, 55.9), 3.6 x 5.4 mm',
                        'two motor-wire pass-throughs, 12 x 20 mm, at (-74, +/-96), 3.9 mm clear of the rim: behind each motor, just outside the shelf ends, big enough for the 6-pin plug'],
               unchanged='outline, thickness, all feature coordinates (v05 / v05.2 parts fit)',
               bounds_mm=[round(bb.xlen, 2), round(bb.ylen, 2), round(bb.zlen, 2)], volume_cm3=round(shape.Volume() / 1000, 1),
               grid_holes=len(grid_ref), m4_holes=len(B.castor + B.deck + B.front), stl_watertight=True,
               bed_edge_margin_mm=margin, clearance_to_exclusion_zone_mm=round(gap, 2))
    (out / 'Baseplate_v05_3_Checks.json').write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=1))

"""Payload deck v05.3 (23 Nov 2026): same outline and positions as part 04, for a quick reprint.
Changes: rear riser holes 6.0 mm (about 1 mm of play every way); front riser holes 6.0 mm wide slots with 4 mm of travel
front to back (those risers sit in motor slots); use an M4 washer under every head; M3 tray holes 3.6 mm; IMU holes 3.4 mm; 0.5 mm bottom chamfer on all holes."""
import sys
from pathlib import Path
import cadquery as cq, trimesh
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_print_parts import poly
dk = [(28, 90), (-88, 90), (-110, 68), (-110, -68), (-88, -90), (28, -90), (42, -76), (42, 76)]
d = poly(dk, 0, 4).edges('|Z').fillet(3)
tools = None
def add(t):
    global tools
    tools = t if tools is None else tools.union(t)
for x, y in [(28, 76), (28, -76)]:                       # front risers sit in motor slots: 6.0 wide, 4 mm travel front-back
    add(cq.Workplane('XY', origin=(x, y, -2)).slot2D(6.0 + 4.0, 6.0, 0).extrude(8))
for x, y in [(-90, 72), (-90, -72)]:                       # rear risers: 6.0 mm round, about 1 mm play every way
    add(cq.Workplane('XY', origin=(x, y, -2)).circle(3.0).extrude(8))
for x, y in [(-60, 66), (-60, -66), (-20, 66), (-20, -66)]:
    add(cq.Workplane('XY', origin=(x, y, -2)).circle(1.8).extrude(8))
for x in (0, 10, 20):
    for y in (70, 80):
        add(cq.Workplane('XY', origin=(x, y, -2)).circle(1.7).extrude(8))
d = d.cut(tools)
bottom = d.faces('<Z').val()
d = d.newObject([e for w in bottom.innerWires() for e in w.Edges()]).chamfer(0.5)
bb = d.val().BoundingBox(); d = d.translate((-bb.xmin, -bb.ymin, 0))
assert d.val().isValid() and len(d.solids().vals()) == 1
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
n = '04_Isolated_Payload_Deck_v05_3'
cq.exporters.export(d, str(out / f'{n}.step'))
for e in ('stl', '3mf'): cq.exporters.export(d, str(out / f'{n}.{e}'), tolerance=0.03, angularTolerance=0.08)
m = trimesh.load(str(out / f'{n}.stl')); assert m.is_watertight and len(m.split()) == 1
b = d.val().BoundingBox(); print(n, round(b.xlen, 1), round(b.ylen, 1), round(b.zlen, 1), 'watertight')

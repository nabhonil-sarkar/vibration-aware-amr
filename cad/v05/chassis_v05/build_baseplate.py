"""AMR single-piece baseplate v05. Units mm. Requires cadquery 2.x and trimesh.
Run: python build_baseplate.py --out OUTPUT_DIRECTORY

Replaces the four v03 panels + four splice plates with ONE print that fits a
Bambu Lab X1 Carbon (256 x 256 bed, 18 x 28 front-left exclusion zone).
Axis convention matches v03/v04: +X is FRONT, +Y is LEFT, Z up, origin at
plate centre, underside at Z = 0.
"""
from pathlib import Path
import argparse, csv, json, math
import cadquery as cq
import trimesh

P = dict(
    size=240.0,            # plate is size x size before corner cuts
    corner_chamfer=45.0,   # leg length of each corner cut
    floor=6.0,             # same floor thickness as v03 (same bolt lengths)
    rim_width=5.0, rim_height=6.0,
    m3_clearance=3.4, m4_clearance=4.5,   # same as v03 fit coupon
    grid_pitch=20.0,
    bed=256.0, bed_exclusion=(18.0, 28.0),  # Bambu X1 series front-left zone
)
H = P['size'] / 2

# ---------------- feature coordinates (x, y) ----------------
AXLE_X = 43.0  # nominal drive-axle line; slots allow roughly X = +10 ... +76
motor_slots = [(x, s * y) for x in (25.0, 61.0) for y in (64.0, 76.0, 88.0, 100.0) for s in (1, -1)]
MOTOR_SLOT = (30.0, 4.5)                    # length along X, width
castor = [(x, y) for x in (-105.0, -75.0) for y in (-22.0, 22.0)]    # v03 castor-adapter pattern 30 x 44
deck = [(x, y) for x in (-90.0, 90.0) for y in (-72.0, 72.0)]        # v03/v04 riser pattern 180 x 144
front = [(105.0, y) for y in (-60.0, -40.0, 40.0, 60.0)]             # bumper / anti-tip skid
cable = [(43.0, 44.0, 24.0, 10.0, 0), (43.0, -44.0, 24.0, 10.0, 0), (40.0, 0.0, 30.0, 12.0, 90)]
strap = [(x, y, 20.0, 4.0, 90) for x in (-72.0, 24.0) for y in (-40.0, 40.0)]


def outline(half, c):
    return [(half - c, half), (-(half - c), half), (-half, half - c), (-half, -(half - c)),
            (-(half - c), -half), (half - c, -half), (half, -(half - c)), (half, half - c)]


def slot_keepout(cx, cy, length, width, angle):
    lx, ly = (length, width) if angle == 0 else (width, length)
    return (cx - lx / 2, cx + lx / 2, cy - ly / 2, cy + ly / 2)


def dist_point_rect(px, py, r):
    dx = max(r[0] - px, 0, px - r[1]); dy = max(r[2] - py, 0, py - r[3])
    return math.hypot(dx, dy)


def grid_points():
    """20 mm M3 grid, dropping any point that would crowd another feature or the rim."""
    rects = [slot_keepout(x, y, MOTOR_SLOT[0], MOTOR_SLOT[1], 0) for x, y in motor_slots]
    rects += [slot_keepout(*c) for c in cable] + [slot_keepout(*s) for s in strap]
    m4 = castor + deck + front
    inner_c = P['corner_chamfer'] - P['rim_width'] * (2 - math.sqrt(2))
    lim = 2 * (H - P['rim_width']) - inner_c - 6 * math.sqrt(2)
    n = int((H - 20) // P['grid_pitch'])
    pts = []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = i * P['grid_pitch'], j * P['grid_pitch']
            if abs(x) + abs(y) > lim: continue
            if any(dist_point_rect(x, y, r) < 6.0 for r in rects): continue
            if any(math.hypot(x - a, y - b) < 9.0 for a, b in m4): continue
            pts.append((x, y))
    return pts


def build():
    f, rw, rh, c = P['floor'], P['rim_width'], P['rim_height'], P['corner_chamfer']
    body = cq.Workplane('XY').polyline(outline(H, c)).close().extrude(f + rh).edges('|Z').fillet(4.0)
    inner_c = c - rw * (2 - math.sqrt(2))
    pocket = (cq.Workplane('XY', origin=(0, 0, f)).polyline(outline(H - rw, inner_c)).close()
              .extrude(rh + 1).edges('|Z').fillet(2.0))
    body = body.cut(pocket)

    def drill(part, pts, d):
        tool = cq.Workplane('XY', origin=(0, 0, -5)).pushPoints(pts).circle(d / 2).extrude(40)
        return part.cut(tool)

    def slot(part, x, y, length, width, angle):
        tool = cq.Workplane('XY', origin=(x, y, -5)).slot2D(length, width, angle).extrude(40)
        return part.cut(tool)

    grid = grid_points()
    body = drill(body, grid, P['m3_clearance'])
    body = drill(body, castor + deck + front, P['m4_clearance'])
    for x, y in motor_slots: body = slot(body, x, y, MOTOR_SLOT[0], MOTOR_SLOT[1], 0)
    for s in cable + strap: body = slot(body, *s)
    return body, grid


def bed_clearance():
    """Plate centred on the bed. Returns edge margin and distance to the exclusion zone."""
    bed, (ex, ey) = P['bed'], P['bed_exclusion']
    margin = (bed - P['size']) / 2
    # nearest plate edge to the front-left corner is the chamfer: x + y = 2*margin + chamfer
    gap = (2 * margin + P['corner_chamfer'] - (ex + ey)) / math.sqrt(2)
    return margin, gap


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    part, grid = build()
    shape = part.val()
    assert len(part.solids().vals()) == 1 and shape.isValid()
    bb = shape.BoundingBox()
    name = 'AMR_Baseplate_v05_Single_Piece'
    cq.exporters.export(part, str(out / f'{name}.step'))
    cq.exporters.export(part, str(out / f'{name}.stl'), tolerance=0.05, angularTolerance=0.1)
    cq.exporters.export(part, str(out / f'{name}.3mf'), tolerance=0.05, angularTolerance=0.1)
    mesh = trimesh.load_mesh(str(out / f'{name}.stl'))
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0
    assert len(mesh.split()) == 1
    m3 = trimesh.load(str(out / f'{name}.3mf'), force='mesh')
    reimport = cq.importers.importStep(str(out / f'{name}.step'))
    assert len(reimport.solids().vals()) == 1
    margin, gap = bed_clearance()
    assert bb.xlen <= P['bed'] and bb.ylen <= P['bed'] and gap > 3.0

    report = dict(
        status='PROTOTYPE - geometry and file checks only; not load tested',
        parameters=P,
        bounds_mm=[round(bb.xlen, 3), round(bb.ylen, 3), round(bb.zlen, 3)],
        volume_cm3=round(shape.Volume() / 1000, 2),
        solid_valid=True, solids_after_STEP_reimport=1,
        stl_watertight=bool(mesh.is_watertight), stl_components=1,
        stl_volume_cm3=round(mesh.volume / 1000, 2),
        threemf_extents_mm=[round(float(v), 3) for v in m3.extents],
        threemf_volume_cm3=round(float(m3.volume) / 1000, 2),
        bed_fit=dict(bed_mm=P['bed'], edge_margin_mm_when_centred=margin,
                     clearance_to_front_left_exclusion_mm=round(gap, 2),
                     note='Any of the four cut corners can face the front-left exclusion zone.'),
        feature_counts=dict(m3_grid_holes=len(grid), m4_holes=len(castor + deck + front),
                            motor_slots=len(motor_slots), cable_openings=len(cable), strap_slots=len(strap)),
        replaces='v03 parts 01-08 (four panels and four splice plates)',
        still_compatible='v03 fit coupon (same 3.4 / 4.5 mm holes and 4.5 mm slot) and 09 castor adapter blank (same 30 x 44 mm M4 pattern)',
    )
    (out / 'Geometry_Checks.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    with (out / 'Mounting_Coordinates_mm.csv').open('w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh); w.writerow(['Purpose', 'X mm', 'Y mm', 'Size mm', 'Status'])
        for x, y in castor: w.writerow(['Castor adapter fixing (v03 pattern)', x, y, 'dia 4.5', 'Verify against actual castor'])
        for x, y in deck: w.writerow(['Payload riser provision (v03/v04 spacing)', x, y, 'dia 4.5', 'Verify hardware fit'])
        for x, y in front: w.writerow(['Front bumper / anti-tip provision', x, y, 'dia 4.5', 'Verify hardware fit'])
        for x, y in motor_slots: w.writerow(['Motor bracket slot (long axis along X)', x, y, '30 x 4.5 slot', 'Verify against actual bracket'])
        for x, y, l, wd, a in cable: w.writerow(['Cable opening', x, y, f'{l:g} x {wd:g} slot, long axis along {"X" if a == 0 else "Y"}', 'Deburr before routing cables'])
        for x, y, l, wd, a in strap: w.writerow(['Battery strap slot', x, y, f'{l:g} x {wd:g} slot, long axis along Y', 'Battery size not selected'])
        for x, y in grid: w.writerow(['General M3 grid (20 mm pitch)', x, y, 'dia 3.4', 'General mounting'])
    print(json.dumps(report, indent=2))
    return part, grid


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, required=True)
    run(ap.parse_args().out)

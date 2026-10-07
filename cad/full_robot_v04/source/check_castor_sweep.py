from pathlib import Path
import json
import cadquery as cq
OUT=Path(__file__).resolve().parent.parent
names=[p['name'] for p in json.loads((OUT/'Geometry_Checks.json').read_text())['parts']]
parts={n:cq.importers.importStep(str(OUT/'STEP_PARTS'/(n+'.step'))).val() for n in names}
moving={n:s for n,s in parts.items() if n.startswith('D_Rear_') and 'Swivel_Bearing' not in n}
hits=[]
for angle in range(0,360,15):
    for an,a in moving.items():
        rotated=a.rotate((-135,0,0),(-135,0,1),angle); ab=rotated.BoundingBox()
        for bn,b in parts.items():
            if bn in moving or 'Swivel_Bearing' in bn: continue
            bb=b.BoundingBox()
            if ab.zmax<=bb.zmin+1e-6 or bb.zmax<=ab.zmin+1e-6: continue
            v=rotated.intersect(b).Volume()
            if v>.01: hits.append([angle,an,bn,round(v,3)])
report=dict(angles_checked_deg=list(range(0,360,15)),moving_parts=list(moving),positive_volume_clashes=hits,
    note='Discrete rigid castor envelope check, 15 degree steps; not continuous swept-volume certification. No suspension travel.')
(OUT/'Castor_Sweep_Check.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))

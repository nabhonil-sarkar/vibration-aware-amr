"""v04 concept geometry in mm. CadQuery 2.8. No vendor-fit or load certification."""
from pathlib import Path
import json, math, argparse
import cadquery as cq

REPO = Path(__file__).resolve().parents[3]
CHASSIS_INPUT = Path(__file__).resolve().parent.parent/'INPUT_CHASSIS'
if not CHASSIS_INPUT.exists(): CHASSIS_INPUT = REPO/'cad/chassis_v03/STEP'
PARTS = []
BLUE=(.15,.48,.78); GREEN=(.20,.64,.48); ORANGE=(.95,.52,.16)
GREY=(.50,.55,.62); DARK=(.14,.17,.22); RED=(.87,.16,.18)
PURPLE=(.58,.36,.78); GOLD=(.91,.72,.23)

def box(l,w,h,x=0,y=0,z=0):
    return cq.Workplane('XY').box(l,w,h,centered=(True,True,False)).translate((x,y,z))
def cyl(d,h,x=0,y=0,z=0):
    return cq.Workplane('XY').circle(d/2).extrude(h).translate((x,y,z))
def ycyl(d,length,x,y,z):
    return cq.Workplane(cq.Plane(origin=(x,y,z),xDir=(1,0,0),normal=(0,1,0))).circle(d/2).extrude(length)
def zholes(s,points,d=3.4):
    return s.cut(cq.Workplane('XY',origin=(0,0,-10)).pushPoints(points).circle(d/2).extrude(260))
def add(name,s,color,status='Provisional concept; verify vendor interfaces'):
    shape=s.val(); assert shape.isValid(),name
    assert len(s.solids().vals())==1,(name,len(s.solids().vals()))
    PARTS.append((name,s,color,status)); return s
def post(name,x,y,z,h,d=10,hole=4.5,color=GREY):
    return add(name,zholes(cyl(d,h,x,y,z),[(x,y)],hole),color)

def build(out):
    out.mkdir(parents=True,exist_ok=True); (out/'STEP_PARTS').mkdir(exist_ok=True)
    # Exact v03 geometry, translated 40 mm above this concept's ground datum.
    cols=[BLUE,GREEN,ORANGE,PURPLE,GREY,GREY,GREY,GREY,DARK]
    for i,p in enumerate(sorted(CHASSIS_INPUT.glob('*.step'))):
        if p.stem.startswith('00_'): continue
        add('C_'+p.stem,cq.importers.importStep(str(p)).translate((0,0,40)),cols[len(PARTS)],
            'Unchanged v03 solid; imported history; prototype mounting provisions')

    # 120 mm wheels are deliberately new provisional envelopes. Axle at 60 mm;
    # 28 mm cylindrical motors are tangent to the 46 mm chassis floor top.
    for side,sy in [('Left',1),('Right',-1)]:
        y0=142 if sy==1 else -170
        wheel=ycyl(120,28,0,y0,60).cut(ycyl(8.4,30,0,y0-1,60))
        add(f'D_{side}_Drive_Tyre_120mm_PROVISIONAL',wheel,DARK)
        my=88 if sy==1 else -125
        motor=ycyl(28,37,0,my,60)
        add(f'D_{side}_Encoder_Gearmotor_Envelope',motor,GREY)
        shaft=ycyl(8,27,0,125 if sy==1 else -152,60)
        add(f'D_{side}_Axle_Envelope',shaft,GOLD)
        # Side tabs form a connected U bracket and leave 3 mm motor clearance.
        foot=box(52,32,4,0,sy*112,46)
        foot=foot.cut(ycyl(29,37,0,my,60))
        for sx in (-1,1): foot=foot.union(box(6,32,22,sx*20,sy*112,50))
        foot=zholes(foot,[(x,sy*112) for x in (-20,20)],4.5)
        add(f'D_{side}_Motor_Saddle_Custom_Interface_Blank',foot,ORANGE)
        # Roof clears tyre by 4 mm. Mounting feet lie on the floor beside slots.
        guard=box(96,40,4,0,sy*155,124)
        for sx in (-1,1):
            guard=guard.union(box(8,4,74,sx*44,sy*134,50))
            guard=guard.union(box(8,18,4,sx*44,sy*126,46))
        add(f'D_{side}_Wheel_Guard_Mounts_Unverified',guard,BLUE)

    cw=ycyl(28,20,-155,-10,14).cut(ycyl(6.4,22,-155,-11,14))
    add('D_Rear_Swivel_Castor_Tyre_28mm_PROVISIONAL',cw,DARK)
    add('D_Rear_Castor_Axle_Envelope',ycyl(6,28,-155,-14,14),GOLD)
    fork=box(38,4,18,-146,13,14).union(box(38,4,18,-146,-13,14))
    fork=fork.union(box(20,30,2,-135,0,30))
    fork=fork.cut(ycyl(6.4,34,-155,-17,14))
    add('D_Rear_Castor_Fork_20mm_Trail_PROVISIONAL',fork,GREY)
    add('D_Rear_Castor_Swivel_Bearing_Interface_Blank',cyl(16,2,-135,0,32),GOLD)
    # Castor-to-adapter centre is intentionally undrilled until vendor selection.

    for y in (-95,95):
        tip=ycyl(20,12,155,y-6,12).cut(ycyl(6.4,14,155,y-7,12))
        add(f'D_AntiTip_Roller_Y{y}_2mm_Floor_Gap',tip,DARK)
        add(f'D_AntiTip_Axle_Y{y}',ycyl(6,22,155,y-11,12),GOLD)
        bracket=box(32,28,4,150,y,36)
        for dy in (-10,10): bracket=bracket.union(box(26,4,24,155,y+dy,12))
        bracket=bracket.cut(ycyl(6.4,36,155,y-18,12))
        bracket=zholes(bracket,[(140,90 if y>0 else -90)],3.4)
        add(f'D_AntiTip_Bracket_Y{y}_Concept_Mount',bracket,ORANGE)

    # Battery tray raised above splice plates, supported at existing general holes.
    for x in (-100,60):
        for y in (-45,45): post(f'E_Battery_Tray_Spacer_{x}_{y}',x,y,46,8,8,3.4)
    tray=zholes(box(180,104,4,-20,0,54),[(x,y) for x in (-100,60) for y in (-45,45)])
    add('E_Battery_Tray_Removable_Mount_Plate',tray,BLUE)
    add('E_Battery_145x86x36_Envelope_SELECTION_PENDING',box(145,86,36,-30,0,58),DARK)
    for x in (-70,10):
        strap=box(10,94,2,x,0,95)
        for y in (-46,46): strap=strap.union(box(10,2,37,x,y,58))
        add(f'E_Battery_Retention_Band_X{x}_1mm_Clearance',strap,ORANGE)

    # Front removable electronics plate is beneath the rigid sensor platform.
    for x in (100,140):
        for y in (-45,45): post(f'E_Electronics_Plate_Spacer_{x}_{y}',x,y,46,16,8,3.4)
    plate=zholes(box(98,100,4,115,0,62),[(x,y) for x in (100,140) for y in (-45,45)])
    # Pi drawing: reference 85 x 56, 58 x 49 hole spacing; supplier reference only.
    pi_holes=[(76+dx,-6.5+dy) for dx in (0,58) for dy in (0,49)]
    plate=zholes(plate,pi_holes,2.7)
    add('E_Front_Electronics_Mount_Plate',plate,BLUE)
    for i,(x,y) in enumerate(pi_holes): post(f'E_Pi5_Standoff_{i+1}',x,y,66,8,5,2.7)
    pcb=zholes(box(85,56,1.6,115,18,74),pi_holes,2.7)
    add('E_Raspberry_Pi_5_Reference_PCB_NOT_VENDOR_CAD',pcb,GREEN,
        '85 x 56 mm reference PCB; 58 x 49 mm hole pitch; physical fit still required')
    add('E_Pi5_Active_Cooling_Allowance',box(42,36,28,111,18,75.6),GREY)
    add('E_Pi5_USB_Ethernet_Connector_Allowance',box(15,52,16,157,18,75.6),GREY)
    add('E_Pi5_GPIO_Connector_Allowance',box(51,5,10,106,43.5,75.6),DARK)
    # MCU footprint is intentionally generic and clearly named.
    add('E_MCU_Carrier_Mount_Block',box(74,30,8,115,-29,66),GREY)
    add('E_STM32_MCU_70x28x12_GENERIC_Envelope',box(70,28,12,115,-29,74),GREEN)
    for y,label,color in [(110,'Motor_Driver',PURPLE),(-110,'Power_Fuse_Regulators',ORANGE)]:
        for x in (-140,-100): post(f'E_{label}_Spacer_{x}',x,y-20 if y>0 else y+20,46,18,8,3.4)
        coords=[(x,y-20 if y>0 else y+20) for x in (-140,-100)]
        carrier=zholes(box(60,48,4,-120,y-4 if y>0 else y+4,64),coords)
        add('E_'+label+'_Mount_Plate',carrier,BLUE)
        add('E_'+label+'_GENERIC_Envelope',box(54,30,18,-120,y,68),color)
    add('E_Chassis_IMU_Rigid_Mount_Pad',box(20,20,4,55,0,58),GREY)
    add('E_Chassis_IMU_GENERIC_Envelope',box(18,16,6,55,0,62),GREEN)

    # Four load paths: chassis -> hollow riser -> elastomer -> isolated deck.
    loc=[(x,y) for x in (-125,55) for y in (-72,72)]
    for i,(x,y) in enumerate(loc,1):
        post(f'P_Rigid_Payload_Riser_{i}',x,y,46,54,20,4.5,PURPLE)
        post(f'P_Passive_Elastomer_{i}_UNRATED',x,y,100,16,24,4.5,ORANGE)
    deck=zholes(box(230,190,6,-35,0,116),loc,4.5)
    add('P_Isolated_Payload_Deck_1kg_TOTAL_CARRIED_TARGET',deck,GOLD)
    carrier=box(160,126,3,-45,0,122)
    for y in (-61,61): carrier=carrier.union(box(160,4,20,-45,y,125))
    for x in (-123,33): carrier=carrier.union(box(4,118,20,x,0,125))
    add('P_Dummy_Payload_Carrier_And_Retention_Rails',carrier,BLUE)
    add('P_Secured_Dummy_Payload_140x110x37_Envelope',box(140,110,37,-45,0,125),PURPLE)
    band=box(10,126,2,-45,0,164)
    for y in (-62,62): band=band.union(box(10,2,42,-45,y,122))
    # Slot through rails for band; the band contacts carrier base only.
    old=PARTS[-2]; cut=old[1]
    for y in (-62,62): cut=cut.cut(box(12,2.4,44,-45,y,122))
    PARTS[-2]=(old[0],cut,old[2],old[3])
    add('P_Payload_Retention_Band_2mm_Clearance',band,ORANGE)
    add('P_Payload_IMU_On_Isolated_Deck',box(20,16,6,56,0,122),GREEN)

    for i,(x,y) in enumerate([(x,y) for x in (85,145) for y in (-67,67)],1):
        post(f'S_Rigid_Sensor_Bridge_Column_{i}',x,y,46,96,10,3.4,GREY)
    bridge=zholes(box(82,146,4,115,0,142),[(x,y) for x in (85,145) for y in (-67,67)],3.4)
    add('S_Chassis_Rigid_Sensor_Bridge',bridge,BLUE)
    add('S_LiDAR_70x55_A1_CLASS_Envelope',cyl(70,55,115,0,146),RED)
    # Camera moved forward, and kept rigid; small bracket attached to bridge edge.
    camera_bracket=box(10,34,24,151,42,146)
    add('S_Rigid_Camera_Bracket_Interface_Blank',camera_bracket,GREY)
    add('S_Navigation_Camera_GENERIC_Envelope',box(24,32,22,168,42,148),DARK)
    foot=zholes(box(24,24,4,140,-90,46),[(140,-90)])
    arm=foot.union(box(8,8,40,140,-90,50)).union(box(32,48,4,145,-102,90))
    add('S_EStop_Chassis_Rigid_Accessible_Bracket',arm,BLUE)
    add('S_EStop_30x24_Envelope_MOTOR_CUTOFF_PENDING',cyl(30,24,145,-108,94),RED)
    for x in (-174,174): add(f'C_Bumper_X{x}_Material_Unconfirmed',box(8,230,20,x,0,40),DARK)

    report=[]; asm=cq.Assembly(name='AMR_v04_PROVISIONAL_1kg_Target')
    for name,s,col,status in PARTS:
        sh=s.val(); bb=sh.BoundingBox()
        assert sh.isValid() and len(s.solids().vals())==1,name
        cq.exporters.export(s,str(out/'STEP_PARTS'/f'{name}.step'))
        asm.add(s,name=name,color=cq.Color(*col))
        report.append(dict(name=name,color=col,status=status,volume_mm3=round(sh.Volume(),4),
            bounds_mm=[round(v,3) for v in (bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax)]))
    asm.export(str(out/'Vibration_Aware_AMR_v04.step'))
    overlaps=[]
    for i,(an,a,_,_) in enumerate(PARTS):
        ab=a.val().BoundingBox()
        for bn,b,_,_ in PARTS[i+1:]:
            bb=b.val().BoundingBox()
            if any([ab.xmax<=bb.xmin+1e-6,bb.xmax<=ab.xmin+1e-6,ab.ymax<=bb.ymin+1e-6,bb.ymax<=ab.ymin+1e-6,ab.zmax<=bb.zmin+1e-6,bb.zmax<=ab.zmin+1e-6]): continue
            v=a.val().intersect(b.val()).Volume()
            if v>0.01: overlaps.append(dict(a=an,b=bn,volume_mm3=round(v,4)))
    imported=cq.importers.importStep(str(out/'Vibration_Aware_AMR_v04.step'))
    checks=dict(status='CONCEPT PROTOTYPE - NOT FABRICATION RELEASE',parts=report,
        solid_count=len(PARTS),reimported_STEP_solids=len(imported.solids().vals()),overlaps=overlaps,
        ground_contacts_mm={'left_drive':0,'right_drive':0,'rear_castor':0,'front_anti_tip':2},
        dimensions_mm={'chassis_ground_datum':40,'drive_diameter':120,'drive_axle':60,'drive_track_CENTRE':312,
        'drive_outside_width':340,'castor_diameter':28,'castor_axle':14,'castor_trail':20,
        'castor_swivel_centre_x':-135,'castor_contact_x_as_shown':-155,'deck_bottom':116,'deck_top':122,
        'lidar_top':201,'print_envelope_nominal':[256,256,256]},
        mass_requirement='1000 g TOTAL carried: deck, carrier, dummy, retention and payload instrumentation; not demonstrated',
        limitations=['Geometry checks only','Castor swivel sweep and ground contact shown in one orientation',
        'Motor saddle clamps/hardware not selected','No physical mass/COM or stability validation',
        'No stiffness, proof-load, vibration or electrical tests','No dynamic isolator travel or cable routing validation'])
    (out/'Geometry_Checks.json').write_text(json.dumps(checks,indent=2))
    (out/'fusion_parts.json').write_text(json.dumps(report,indent=2))
    expected={p['name']+'.step' for p in report}
    for p in (out/'STEP_PARTS').glob('*.step'):
        if p.name not in expected: p.unlink()  # Stale outputs of this generator only.
    print(json.dumps({k:v for k,v in checks.items() if k!='parts'},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();build(args.out)

"""AMR prototype chassis. Units mm. Requires cadquery 2.8 and trimesh.
Run: python build_chassis.py --out OUTPUT_DIRECTORY
Source parameters, not a Fusion feature timeline, control regeneration.
"""
from pathlib import Path
import argparse
import json
import csv
import math
import zipfile
import cadquery as cq
import trimesh

P = dict(length=340.0, width=270.0, floor=6.0, rim_width=6.0,
         rim_height=14.0, rib_width=6.0, rib_height=8.0, seam_gap=0.4,
         m4_clearance=4.5, m3_clearance=3.4, joint_thickness=6.0,
         provisional_bed_x=220.0, provisional_bed_y=220.0)

def box(l,w,h,x=0,y=0,z=0):
    return cq.Workplane('XY').box(l,w,h,centered=(True,True,False)).translate((x,y,z))

def holes(part, points, diameter):
    if not points: return part
    tool=cq.Workplane('XY',origin=(0,0,-10)).pushPoints(points).circle(diameter/2).extrude(50)
    return part.cut(tool)

def slot(part,x,y,length,width,angle=0):
    tool=cq.Workplane('XY',origin=(x,y,-10)).slot2D(length,width,angle).extrude(50)
    return part.cut(tool)

def run(out):
    out.mkdir(parents=True,exist_ok=True)
    for f in ['STEP','STL','PREVIEWS']: (out/f).mkdir(exist_ok=True)
    length,width,floor=P['length'],P['width'],P['floor']
    base=box(length,width,floor).edges('|Z').fillet(5)
    # End rims and split side rims. The central 96 mm side gap allows shafts
    # and wheel/gearbox clearance; actual wheel geometry remains to be checked.
    for sx in (-1,1): base=base.union(box(6,width-10,14,sx*(length/2-3),0,6))
    for sy in (-1,1):
        for sx in (-1,1):
            base=base.union(box(117,6,14,sx*106.5,sy*132,6))
            base=base.union(box(6,85,8,sx*110,sy*77.5,6))
    # Assembly joint patterns, distinct from component-specific mounting holes.
    x_joint=[(x,y0+dy) for y0 in (-70,70) for x in (-24,24) for dy in (-9,9)]
    y_joint=[(x0+dx,y) for x0 in (-75,75) for dx in (-9,9) for y in (-24,24)]
    caster=[(x,y) for x in (-150,-120) for y in (-22,22)]
    deck=[(x,y) for x in (-125,55) for y in (-72,72)]
    general=[(x,y) for x in (-140,-100,-60,60,100,140) for y in (-90,-45,45,90)]
    bridge=[(x,y) for x in (85,145) for y in (-67,67)]
    base=holes(base,x_joint+y_joint+caster+deck,P['m4_clearance'])
    base=holes(base,general+bridge,P['m3_clearance'])
    for x in (-20,20):
        for y in (-112,112): base=slot(base,x,y,28,4.5,0)
    for x in (-70,10):
        for y in (-48,48): base=slot(base,x,y,18,4,0)
    parts=[]
    colours=[(0.12,0.48,0.78),(0.20,0.67,0.56),(0.91,0.54,0.20),(0.59,0.40,0.76)]
    for i,(sx,sy,name) in enumerate([(1,1,'01_Front_Left_Panel'),(1,-1,'02_Front_Right_Panel'),(-1,1,'03_Rear_Left_Panel'),(-1,-1,'04_Rear_Right_Panel')]):
        lx=(length-P['seam_gap'])/2; ly=(width-P['seam_gap'])/2
        crop=box(lx,ly,40,sx*(length+P['seam_gap'])/4,sy*(width+P['seam_gap'])/4,-5)
        part=base.intersect(crop)
        parts.append((name,part,colours[i]))
    # Four removable top-side splice plates. Standard through bolts/nuts,
    # no printed threads or assumed heat-set inserts.
    for i,y in enumerate((-70,70),5):
        plate=box(80,32,6,0,y,6).edges('|Z').fillet(3)
        plate=holes(plate,[(x,y+dy) for x in (-24,24) for dy in (-9,9)],4.5)
        parts.append((f'{i:02d}_Transverse_Joint_Plate',plate,(0.73,0.76,0.80)))
    for i,x in enumerate((-75,75),7):
        plate=box(32,80,6,x,0,6).edges('|Z').fillet(3)
        plate=holes(plate,[(x+dx,y) for dx in (-9,9) for y in (-24,24)],4.5)
        parts.append((f'{i:02d}_Longitudinal_Joint_Plate',plate,(0.73,0.76,0.80)))
    adapter=box(54,64,6,-135,0,-6).edges('|Z').fillet(4)
    adapter=holes(adapter,caster,4.5)
    parts.append(('09_Rear_Castor_Adapter_Blank',adapter,(0.30,0.38,0.49)))
    coupon=box(70,32,6).edges('|Z').fillet(3)
    for x,d in [(-25,3.4),(-12.5,4.3),(0,4.5),(12.5,4.7)]: coupon=holes(coupon,[(x,0)],d)
    coupon=slot(coupon,25,0,15,4.5,90)

    assembly=cq.Assembly(name='AMR_Chassis_v03_PROTOTYPE')
    reports=[]
    for name,part,col in parts:
        shape=part.val()
        assert len(part.solids().vals())==1 and shape.isValid(),name
        assembly.add(part,name=name,color=cq.Color(*col))
        cq.exporters.export(part,str(out/'STEP'/f'{name}.step'))
        bb=shape.BoundingBox()
        printable=part.translate((-bb.xmin,-bb.ymin,-bb.zmin))
        path=out/'STL'/f'{name}.stl'
        cq.exporters.export(printable,str(path),tolerance=0.06,angularTolerance=0.1)
        mesh=trimesh.load_mesh(str(path))
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0,name
        assert len(mesh.split())==1,name
        assert bb.xlen+10 <= P['provisional_bed_x'] and bb.ylen+10 <= P['provisional_bed_y'],name
        reports.append(dict(part=name,bounds_mm=[round(bb.xlen,3),round(bb.ylen,3),round(bb.zlen,3)],volume_cm3=round(shape.Volume()/1000,3),solid_valid=True,stl_watertight=True,stl_components=1))
    assembly.export(str(out/'AMR_Chassis_v03_Assembly.step'))
    reimport=cq.importers.importStep(str(out/'AMR_Chassis_v03_Assembly.step'))
    assert len(reimport.solids().vals())==9
    intersections=[]
    for i,(name,a,_) in enumerate(parts):
        for bname,b,_ in parts[i+1:]:
            common=a.val().intersect(b.val()).Volume()
            if common>1e-4: intersections.append([name,bname,common])
    assert not intersections,intersections
    bb=coupon.val().BoundingBox()
    cq.exporters.export(coupon.translate((-bb.xmin,-bb.ymin,0)),str(out/'STL'/'00_Hole_and_Slot_Fit_Coupon.stl'),tolerance=0.06,angularTolerance=0.1)
    cq.exporters.export(coupon,str(out/'STEP'/'00_Hole_and_Slot_Fit_Coupon.step'))
    cm=trimesh.load_mesh(str(out/'STL'/'00_Hole_and_Slot_Fit_Coupon.stl'))
    assert cm.is_watertight and cm.volume>0
    report=dict(status='PROTOTYPE NOT RELEASED FOR LOAD BEARING USE',parameters=P,parts=reports,assembly_solids_after_STEP_reimport=9,overlapping_pairs=intersections,checks='Geometry and file integrity only. Not structural FEA or physical proof testing.',total_solid_volume_cm3=round(sum(v['volume_cm3'] for v in reports),2))
    (out/'Geometry_Checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    with (out/'Print_Parts_List.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f); w.writerow(['Part','Quantity','X mm','Y mm','Z mm','Status'])
        for r in reports: w.writerow([r['part'],1,*r['bounds_mm'],'Provisional prototype'])
        w.writerow(['00_Hole_and_Slot_Fit_Coupon',1,70,32,6,'Print and measure first'])
    with (out/'Mounting_Coordinates_mm.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['Purpose','X mm','Y mm','Diameter mm','Status'])
        for purpose,coords,dia in [('X seam joints',x_joint,4.5),('Y seam joints',y_joint,4.5),('Castor adapter fixing',caster,4.5),('Payload riser provision',deck,4.5),('General mounting',general,3.4),('Rigid sensor bridge provision',bridge,3.4)]:
            for x,y in coords:w.writerow([purpose,x,y,dia,'Verify hardware fit; joint geometry matched internally'])
    # Scientific CAD previews from the exact exported geometry, not generated images.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy
    from PIL import Image, ImageDraw, ImageFont
    for exploded in (False,True):
        renderer=vtk.vtkRenderer();renderer.SetBackground(1,1,1)
        for i,(name,part,col) in enumerate(parts):
            verts,tris=part.val().tessellate(0.5)
            shift=(0,0,0)
            if exploded:
                if i<4:
                    bb=part.val().BoundingBox();shift=(math.copysign(15,(bb.xmin+bb.xmax)),math.copysign(15,(bb.ymin+bb.ymax)),0)
                elif i<8:shift=(0,0,30)
                else:shift=(0,0,-20)
            vs=[(v.x+shift[0],v.y+shift[1],v.z+shift[2]) for v in verts]
            points=vtk.vtkPoints()
            for v in vs:points.InsertNextPoint(*v)
            cells=vtk.vtkCellArray()
            for tri in tris:
                cells.InsertNextCell(3)
                for k in tri:cells.InsertCellPoint(k)
            poly=vtk.vtkPolyData();poly.SetPoints(points);poly.SetPolys(cells)
            normals=vtk.vtkPolyDataNormals();normals.SetInputData(poly);normals.SetFeatureAngle(40);normals.Update()
            mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
            actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(*col)
            actor.GetProperty().SetAmbient(.25);actor.GetProperty().SetDiffuse(.75)
            renderer.AddActor(actor)
        camera=renderer.GetActiveCamera();camera.SetPosition(390,-460,560);camera.SetFocalPoint(0,0,0);camera.SetViewUp(0,0,1);camera.ParallelProjectionOn()
        renderer.ResetCamera();camera.Zoom(1.15)
        window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.SetSize(1600,1000);window.AddRenderer(renderer);window.Render()
        capture=vtk.vtkWindowToImageFilter();capture.SetInput(window);capture.ReadFrontBufferOff();capture.Update()
        imdata=capture.GetOutput();arr=vtk_to_numpy(imdata.GetPointData().GetScalars()).reshape(1000,1600,-1)
        canvas=Image.new('RGB',(1600,1200),'white');canvas.paste(Image.fromarray(arr[::-1]),(0,100))
        draw=ImageDraw.Draw(canvas)
        from matplotlib.font_manager import findfont
        preview_font = findfont('DejaVu Sans')
        font=ImageFont.truetype(preview_font,32);small=ImageFont.truetype(preview_font,23)
        draw.text((800,35),'AMR chassis v03 | '+('Exploded assembly' if exploded else 'Assembled chassis'),font=font,fill='#192935',anchor='mt')
        draw.text((800,1100),'340 x 270 mm | Four bolted panels | Two-wheel drive and rear castor layout',font=small,fill='#192935',anchor='mt')
        draw.text((800,1140),'PROTOTYPE - mounting interfaces and load capacity require validation',font=small,fill='#9b3b20',anchor='mt')
        canvas.save(out/'PREVIEWS'/('Chassis_Exploded.png' if exploded else 'Chassis_Assembled.png'))
        window.Finalize()
    # Orthographic view with part identities and explicit axis convention.
    fig,ax=plt.subplots(figsize=(12,9));fig.patch.set_facecolor('white')
    for name,part,col in parts[:8]:
        for face in part.val().Faces():
            if face.normalAt().z>0.99:
                verts,tris=face.tessellate(0.12)
                for tri in tris:
                    ax.fill([verts[j].x for j in tri],[verts[j].y for j in tri],color=col,linewidth=0,antialiased=False)
    for i,(x,y) in enumerate([(85,40),(85,-40),(-85,40),(-85,-40)],1):
        ax.text(x,y,f'Panel {i}',ha='center',fontsize=12,color='black',bbox=dict(facecolor='white',alpha=.8,edgecolor='none',pad=2))
    ax.annotate('',xy=(170,150),xytext=(-170,150),arrowprops=dict(arrowstyle='<->'))
    ax.text(0,154,'340 mm',ha='center');ax.annotate('',xy=(185,135),xytext=(185,-135),arrowprops=dict(arrowstyle='<->'))
    ax.text(191,0,'270 mm',rotation=90,va='center')
    ax.set(xlim=(-190,210),ylim=(-155,178),aspect='equal',xlabel='X (mm) — FRONT is +X',ylabel='Y (mm) — LEFT is +Y')
    ax.set_title('Chassis top view — provisional mounting pattern',fontsize=16,pad=18)
    fig.tight_layout();fig.savefig(out/'PREVIEWS'/'Chassis_Top_View.png',dpi=160);plt.close(fig)
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    run(parser.parse_args().out)

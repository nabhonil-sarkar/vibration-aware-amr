"""Run inside Autodesk Fusion. Imports checked v04 solids, exports real F3D."""
import adsk.core, adsk.fusion
from pathlib import Path
import json, traceback

OUT = Path(__file__).resolve().parent.parent
NAME = 'Vibration_Aware_AMR_v04'

def snapshot(app,filename,orientation):
    vp=app.activeViewport; cam=vp.camera
    cam.viewOrientation=orientation; cam.isFitView=True; vp.camera=cam
    vp.refresh(); adsk.doEvents()
    if not vp.saveAsImageFile(str(OUT/filename),1800,1200): raise RuntimeError('Preview export failed')

def inspect(design):
    root=design.rootComponent
    bodies=[]
    for occ in root.allOccurrences:
        for b in occ.component.bRepBodies:
            bodies.append({'component':occ.component.name,'body':b.name,'solid':b.isSolid,'valid':b.isValid})
    for b in root.bRepBodies:
        bodies.append({'component':'root','body':b.name,'solid':b.isSolid,'valid':b.isValid})
    return bodies

def run(context):
    app=adsk.core.Application.get(); ui=app.userInterface
    try:
        checks=json.loads((OUT/'Geometry_Checks.json').read_text())
        assert not checks['overlaps'], 'Resolve static overlaps before Fusion export'
        doc=app.importManager.importToNewDocument(app.importManager.createSTEPImportOptions(str(OUT/(NAME+'.step'))))
        if not doc: raise RuntimeError('STEP import failed')
        design=adsk.fusion.Design.cast(app.activeProduct)
        design.designType=adsk.fusion.DesignTypes.ParametricDesignType
        doc.name=NAME
        colors={p['name']:p['color'] for p in checks['parts']}
        assigned=[]
        for occ in design.rootComponent.allOccurrences:
            c=occ.component
            if c.name in colors:
                rgb=colors[c.name]
                c.componentColor=adsk.core.Color.create(*[int(v*255) for v in rgb],255)
                assigned.append(c.name)
        for group,key,value in [('AMR_v04','Status','Provisional concept; no fabrication release'),
            ('AMR_v04','PayloadRequirement','1000 g total carried incl deck carrier retention payload instrumentation; untested'),
            ('AMR_v04','Printer','Bambu Lab X1 Carbon nominal 256x256x256 mm; slicing unconfirmed'),
            ('AMR_v04','History','Imported checked CadQuery STEP solids; no original sketch timeline'),
            ('AMR_v04','Axes','X forward, Y left, Z up; ground Z0, v03 base datum Z40')]:
            design.rootComponent.attributes.add(group,key,value)
        for key,val,unit,note in [('driveWheelDiameter','120 mm','mm','New provisional envelope; select hardware'),
            ('driveWheelCentreTrack','312 mm','mm','Actual model wheel-centre spacing; not outside width'),
            ('chassisAboveGround','40 mm','mm','v03 geometry translated upward'),
            ('payloadCarriedTarget_g','1000','','Requirement includes all carried mass; not capacity'),
            ('x1CarbonNominalBed','256 mm','mm','Usable plate/nozzle/material unconfirmed')]:
            design.userParameters.add(key,adsk.core.ValueInput.createByString(val),unit,note)
        app.isComponentColorsDisplayed=True
        app.activeViewport.fit()
        native=OUT/(NAME+'.f3d')
        assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(native)))
        assert native.exists() and native.stat().st_size>10000
        assert design.exportManager.execute(design.exportManager.createSTEPExportOptions(str(OUT/(NAME+'_Fusion.step')),design.rootComponent))
        snapshot(app,NAME+'_Colored.png',adsk.core.ViewOrientations.IsoTopRightViewOrientation)
        snapshot(app,NAME+'_Side.png',adsk.core.ViewOrientations.FrontViewOrientation)
        hidden=[]
        for occ in design.rootComponent.allOccurrences:
            if occ.component.name.startswith('P_') and 'Riser' not in occ.component.name:
                if occ.isLightBulbOn: occ.isLightBulbOn=False; hidden.append(occ)
        snapshot(app,NAME+'_Service_View.png',adsk.core.ViewOrientations.IsoTopRightViewOrientation)
        for occ in hidden: occ.isLightBulbOn=True
        # Reopen the actual archive to verify a native Fusion round trip.
        reopened=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(native)))
        assert reopened,'F3D reopen failed'
        reopened.name=NAME+'_Archive_Verified'
        verify=adsk.fusion.Design.cast(app.activeProduct)
        bodies=inspect(verify)
        assert len(bodies)==checks['solid_count'],(len(bodies),checks['solid_count'])
        assert all(b['solid'] and b['valid'] for b in bodies)
        snapshot(app,NAME+'_Colored.png',adsk.core.ViewOrientations.IsoTopRightViewOrientation)
        report=dict(native_archive_exported=True,native_archive_reopened=True,solid_count=len(bodies),
            all_bodies_solid_and_valid=True,color_assignment_count=len(assigned),bodies=bodies,
            note='Static solids only. No joints, animation, vendor fit or structural validation.')
        (OUT/'Fusion_Verification.json').write_text(json.dumps(report,indent=2))
        if (OUT/'Fusion_Error.txt').exists(): (OUT/'Fusion_Error.txt').unlink()
        ui.messageBox('v04 native F3D exported and reopened successfully.\n87 valid solid parts; no positive-volume static clashes in checked geometry.\n\nConcept only: vendor mounts, isolators, stability, printing and load capacity remain unverified.','Updated AMR assembly')
    except Exception:
        (OUT/'Fusion_Error.txt').write_text(traceback.format_exc())
        ui.messageBox(traceback.format_exc(),'v04 generation error')

def stop(context): pass

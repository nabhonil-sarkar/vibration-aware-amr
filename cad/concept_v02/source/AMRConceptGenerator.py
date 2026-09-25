import adsk.core
import adsk.fusion
import colorsys
import traceback
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parent / "exports"


def mm(value):
    return value / 10.0


def transform_at(x=0, y=0, z=0):
    matrix = adsk.core.Matrix3D.create()
    matrix.translation = adsk.core.Vector3D.create(mm(x), mm(y), mm(z))
    return matrix


def new_component(root, name, x=0, y=0, z=0):
    occurrence = root.occurrences.addNewComponent(transform_at(x, y, z))
    component = occurrence.component
    component.name = name

    # Assign each component a repeatable, high-contrast colour.  Fusion displays
    # these colours when Application.isComponentColorsDisplayed is enabled.
    colour_index = root.occurrences.count - 1
    hue = (colour_index * 0.61803398875) % 1.0
    saturation = 0.48 + 0.12 * (colour_index % 3)
    value = 0.72 + 0.18 * ((colour_index // 3) % 2)
    red, green, blue = colorsys.hsv_to_rgb(hue, saturation, value)
    component.componentColor = adsk.core.Color.create(
        int(red * 255), int(green * 255), int(blue * 255), 255
    )
    return component


def create_box(root, name, width, depth, height, x=0, y=0, z=0):
    component = new_component(root, name, x, y, z)
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = name + "_Footprint"
    corner_a = adsk.core.Point3D.create(mm(-width / 2), mm(-depth / 2), 0)
    corner_b = adsk.core.Point3D.create(mm(width / 2), mm(depth / 2), 0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(corner_a, corner_b)
    profile = sketch.profiles.item(0)
    feature = component.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByString(f"{height} mm"),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    feature.name = name + "_Extrude"
    body = feature.bodies.item(0)
    body.name = name
    return component, body


def create_vertical_cylinder(root, name, diameter, height, x=0, y=0, z=0):
    component = new_component(root, name, x, y, z)
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = name + "_Profile"
    sketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0), mm(diameter / 2)
    )
    profile = sketch.profiles.item(0)
    feature = component.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByString(f"{height} mm"),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    feature.name = name + "_Extrude"
    body = feature.bodies.item(0)
    body.name = name
    return component, body


def create_wheel(root, name, diameter, width, x=0, y=0, z=0):
    component = new_component(root, name, x, y, z)
    sketch = component.sketches.add(component.xZConstructionPlane)
    sketch.name = name + "_Profile"
    sketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0), mm(diameter / 2)
    )
    profile = sketch.profiles.item(0)
    feature = component.features.extrudeFeatures.addSimple(
        profile,
        adsk.core.ValueInput.createByString(f"{width} mm"),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    feature.name = name + "_Extrude"
    body = feature.bodies.item(0)
    body.name = name
    return component, body


def cut_mounting_holes(component, hole_diameter, coordinates, plate_thickness):
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = "Mounting_Hole_Grid"
    circles = sketch.sketchCurves.sketchCircles
    for x, y in coordinates:
        circles.addByCenterRadius(adsk.core.Point3D.create(mm(x), mm(y), 0), mm(hole_diameter / 2))
    profiles = adsk.core.ObjectCollection.create()
    for index in range(sketch.profiles.count):
        profiles.add(sketch.profiles.item(index))
    extrudes = component.features.extrudeFeatures
    input_feature = extrudes.createInput(profiles, adsk.fusion.FeatureOperations.CutFeatureOperation)
    input_feature.setDistanceExtent(False, adsk.core.ValueInput.createByString(f"{plate_thickness} mm"))
    cut = extrudes.add(input_feature)
    cut.name = "Mounting_Holes_Cut"


def add_reference_parameters(design):
    parameters = [
        ("chassisLength", "340 mm", "Provisional overall base-plate length"),
        ("chassisWidth", "270 mm", "Provisional overall base-plate width"),
        ("baseThickness", "4 mm", "Prototype plate thickness"),
        ("wheelDiameter", "70 mm", "Placeholder drive-wheel diameter"),
        ("wheelWidth", "28 mm", "Placeholder drive-wheel width"),
        ("driveTrackWidth", "298 mm", "Outside-to-outside provisional drive-wheel track"),
        ("casterDiameter", "40 mm", "Soft-tread rear caster clearance envelope"),
        ("payloadDeckHeight", "92 mm", "Top of isolated payload deck above ground datum"),
        ("payloadDeckLength", "230 mm", "Isolated payload-deck length"),
        ("payloadDeckWidth", "190 mm", "Isolated payload-deck width"),
        ("isolatorHeight", "16 mm", "Provisional elastomer isolator height"),
        ("lidarDiameter", "70 mm", "RPLIDAR A1 clearance envelope"),
        ("payloadMassTarget", "1500 g", "Provisional representative payload limit"),
    ]
    for name, expression, comment in parameters:
        try:
            design.userParameters.add(
                name,
                adsk.core.ValueInput.createByString(expression),
                "mm" if not name.endswith("MassTarget") else "g",
                comment,
            )
        except Exception:
            pass


def build_model(design):
    root = design.rootComponent
    # Fusion owns the root component name for a new unsaved document.
    # The exported design files carry the project name instead.
    add_reference_parameters(design)

    # V02 retains two-wheel differential drive after comparing it with four-wheel
    # skid steer.  The simpler layout reduces tyre scrub, turning current and
    # odometry risk while the caster and anti-tip details address stability.
    base_component, _ = create_box(root, "00_Chassis_Base_Plate", 340, 270, 4, 0, 0, 30)
    mounting_points = [
        (-150, -115), (-150, 115), (150, -115), (150, 115),
        (-100, -85), (-100, 85), (0, -85), (0, 85), (100, -85), (100, 85),
    ]
    cut_mounting_holes(base_component, 5, mounting_points, 4)

    # Drive modules: wide central track for a compact turn radius and stable load path.
    create_wheel(root, "01_Left_Drive_Wheel", 70, 28, 0, -163, 35)
    create_wheel(root, "02_Right_Drive_Wheel", 70, 28, 0, 135, 35)
    create_box(root, "03_Left_Wheel_Guard", 94, 5, 42, 0, -131, 31)
    create_box(root, "04_Right_Wheel_Guard", 94, 5, 42, 0, 131, 31)

    # Rear swivel caster: a soft-tread wheel, fork plates and a rigid swivel stem.
    create_wheel(root, "05_Rear_Caster_Soft_Tread", 40, 24, -132, -12, 20)
    create_box(root, "06_Rear_Caster_Fork_Left", 42, 4, 26, -132, -17, 20)
    create_box(root, "07_Rear_Caster_Fork_Right", 42, 4, 26, -132, 17, 20)
    create_box(root, "08_Rear_Caster_Fork_Bridge", 28, 38, 5, -132, 0, 43)
    create_vertical_cylinder(root, "09_Rear_Caster_Swivel_Stem", 16, 10, -132, 0, 48)

    # Front anti-tip rollers normally clear the floor and engage only on a pitch event.
    create_wheel(root, "10_Front_AntiTip_Roller_Left", 20, 14, 154, -92, 11)
    create_wheel(root, "11_Front_AntiTip_Roller_Right", 20, 14, 154, 78, 11)
    create_box(root, "12_Front_AntiTip_Bracket_Left", 34, 5, 18, 150, -77, 16)
    create_box(root, "13_Front_AntiTip_Bracket_Right", 34, 5, 18, 150, 92, 16)

    create_box(root, "20_Left_Gearmotor_Envelope", 82, 32, 32, 0, -114, 34)
    create_box(root, "21_Right_Gearmotor_Envelope", 82, 32, 32, 0, 114, 34)

    # The heaviest item is placed low and close to the drive axle to reduce pitch
    # moment and keep the centre of gravity inside the three-point support polygon.
    create_box(root, "22_Low_Central_Battery_12V_Envelope", 145, 86, 42, -30, 0, 34)
    create_box(root, "23_Battery_Retention_Crossbar", 12, 100, 12, -30, 0, 72)
    create_box(root, "24_Raspberry_Pi_4_Envelope", 90, 65, 24, 100, 66, 34)
    create_box(root, "25_STM32_Nucleo_Envelope", 110, 60, 24, 92, -68, 34)
    create_box(root, "26_Motor_Driver_Envelope", 72, 52, 22, -118, 86, 34)
    create_box(root, "27_Power_Distribution_Envelope", 72, 48, 22, -118, -88, 34)
    create_vertical_cylinder(root, "28_Chassis_IMU_Envelope", 24, 8, 58, 0, 34)

    # Fixed sensor bridge: LiDAR remains rigidly referenced to the chassis so
    # vibration isolation cannot introduce mapping-frame motion.
    for index, (x, y) in enumerate([(82, -67), (82, 67), (145, -67), (145, 67)], 1):
        create_vertical_cylinder(root, f"30_Sensor_Bridge_Standoff_{index}", 10, 42, x, y, 34)
    create_box(root, "34_Rigid_Sensor_Bridge", 92, 150, 4, 113, 0, 76)
    create_vertical_cylinder(root, "35_RPLIDAR_A1_Rigid_Envelope", 70, 55, 113, 0, 80)
    create_box(root, "36_USB_Camera_Rigid_Envelope", 45, 28, 28, 145, 76, 80)
    create_vertical_cylinder(root, "37_Emergency_Stop_Envelope", 36, 32, 145, -78, 80)

    # Four elastomer elements support a mechanically separate payload deck.
    isolator_locations = [(-125, -72), (-125, 72), (35, -72), (35, 72)]
    for index, (x, y) in enumerate(isolator_locations, 1):
        create_vertical_cylinder(root, f"40_Elastomer_Isolator_{index}", 24, 16, x, y, 76)
    create_box(root, "44_Isolated_Payload_Deck", 230, 190, 4, -45, 0, 92)
    create_box(root, "45_Fragile_Payload_Envelope", 145, 112, 42, -55, 0, 96)
    create_box(root, "46_Payload_Retention_Rail_Left", 160, 8, 24, -55, -63, 96)
    create_box(root, "47_Payload_Retention_Rail_Right", 160, 8, 24, -55, 63, 96)
    create_vertical_cylinder(root, "48_Payload_IMU_Envelope", 24, 8, -55, 0, 138)

    create_box(root, "50_Front_Energy_Absorbing_Bumper", 12, 230, 28, 164, 0, 28)
    create_box(root, "51_Rear_Energy_Absorbing_Bumper", 12, 230, 28, -164, 0, 28)

    return root


def export_model(app, design, root):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    export_manager = design.exportManager

    fusion_path = OUTPUT_DIR / "Vibration_Aware_AMR_Concept_v02.f3d"
    fusion_options = export_manager.createFusionArchiveExportOptions(str(fusion_path))
    export_manager.execute(fusion_options)

    step_path = OUTPUT_DIR / "Vibration_Aware_AMR_Concept_v02.step"
    step_options = export_manager.createSTEPExportOptions(str(step_path), root)
    export_manager.execute(step_options)

    viewport = app.activeViewport
    camera = viewport.camera
    camera.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
    camera.isFitView = True
    viewport.camera = camera
    viewport.refresh()
    image_path = OUTPUT_DIR / "Vibration_Aware_AMR_Concept_v02.png"
    viewport.saveAsImageFile(str(image_path), 1800, 1200)

    app.isComponentColorsDisplayed = True
    viewport.refresh()
    coloured_image_path = OUTPUT_DIR / "Vibration_Aware_AMR_Concept_v02_Colored.png"
    viewport.saveAsImageFile(str(coloured_image_path), 1800, 1200)


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = build_model(design)
        app.activeViewport.fit()
        export_model(app, design, root)
        document.name = "Vibration_Aware_AMR_Concept_v02"
        ui.messageBox(
            "Improved V02 concept created and exported as F3D, STEP and PNG, including a component-coloured CAD render.\n\n"
            "V02 retains two-wheel differential drive with a detailed rear caster, front anti-tip rollers, a low central battery, an isolated payload deck and a chassis-rigid LiDAR bridge.\n\n"
            "All purchased-part bodies are clearance envelopes and must be replaced with verified dimensions before fabrication.",
            "AMR Concept Generator",
        )
    except Exception:
        ui.messageBox("Generation failed:\n{}".format(traceback.format_exc()), "AMR Concept Generator")


def stop(context):
    pass

import bpy
import math
import mathutils

def create_svo_tricolor_scene(subdivision_levels=6, use_gpu=True):
    """
    Generates 3D 'SVO' text with the Russian Flag (White, Blue, Red) procedural material
    and ultra-dense subdivision (20M+ polygons) rendered via Cycles OptiX GPU.
    """
    # 1. Clear existing objects
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    # 2. Create Text Object
    text_curve = bpy.data.curves.new(type="FONT", name="SVO_Text")
    text_curve.body = "SVO"
    text_curve.extrude = 0.18
    text_curve.bevel_depth = 0.04
    text_curve.bevel_resolution = 6
    text_curve.resolution_u = 16
    text_curve.align_x = 'CENTER'
    text_curve.align_y = 'CENTER'
    text_curve.size = 2.2

    text_obj = bpy.data.objects.new(name="SVO_Object", object_data=text_curve)
    bpy.context.collection.objects.link(text_obj)
    text_obj.location = (0, 0, 0)
    text_obj.rotation_euler = (math.radians(90), 0, 0)

    # 3. Convert to Mesh and Apply High-Density Subdivision
    bpy.context.view_layer.objects.active = text_obj
    text_obj.select_set(True)
    bpy.ops.object.convert(target='MESH')

    if subdivision_levels > 0:
        subsurf = text_obj.modifiers.new(name="Subsurf", type='SUBSURF')
        subsurf.subdivision_type = 'SIMPLE'
        subsurf.levels = subdivision_levels
        subsurf.render_levels = subdivision_levels
        # Level 6 produces 20,047,872 polygons directly in the mesh data
        bpy.ops.object.modifier_apply(modifier="Subsurf")

    text_obj.select_set(False)

    # 4. Russian Flag Procedural Shader (White top, Blue middle, Red bottom)
    mat = bpy.data.materials.new(name="Russian_Flag_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    output_node.location = (600, 0)

    bsdf_node = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf_node.location = (300, 0)

    ramp_node = nodes.new(type="ShaderNodeValToRGB")
    ramp_node.location = (50, 0)
    ramp_node.color_ramp.interpolation = 'CONSTANT'

    # Color mapping:
    # 0.0 - 0.3333: Red (Bottom)
    # 0.3333 - 0.6667: Blue (Middle)
    # 0.6667 - 1.0: White (Top)
    elements = ramp_node.color_ramp.elements
    elements[0].position = 0.0
    elements[0].color = (0.82, 0.02, 0.04, 1.0) # Red

    blue_elem = ramp_node.color_ramp.elements.new(0.3333)
    blue_elem.color = (0.00, 0.12, 0.65, 1.0)   # Blue

    elements[2].position = 0.6667
    elements[2].color = (0.98, 0.98, 0.99, 1.0) # White

    sep_node = nodes.new(type="ShaderNodeSeparateXYZ")
    sep_node.location = (-150, 0)

    tex_coord = nodes.new(type="ShaderNodeTexCoord")
    tex_coord.location = (-350, 0)

    links.new(tex_coord.outputs["Generated"], sep_node.inputs[0])
    links.new(sep_node.outputs["Y"], ramp_node.inputs["Fac"])
    links.new(ramp_node.outputs["Color"], bsdf_node.inputs["Base Color"])
    links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])

    for inp in bsdf_node.inputs:
        if inp.name == "Roughness":
            inp.default_value = 0.12
        elif inp.name == "Metallic":
            inp.default_value = 0.20
        elif inp.name in ("Coat Weight", "Clearcoat"):
            inp.default_value = 1.0

    text_obj.data.materials.append(mat)

    # 5. Studio Lighting Setup
    lights = [
        ("Key_Light", 900.0, 3.0, (3, -4, 4), (math.radians(45), 0, math.radians(35))),
        ("Fill_Light", 450.0, 4.0, (-4, -3, 2), (math.radians(45), 0, math.radians(-45))),
        ("Rim_Light", 1400.0, 5.0, (0, 3.5, 3), (math.radians(-45), 0, 0))
    ]
    for name, energy, size, loc, rot in lights:
        light_data = bpy.data.lights.new(name=name, type='AREA')
        light_data.energy = energy
        light_data.size = size
        light_obj = bpy.data.objects.new(name=name, object_data=light_data)
        bpy.context.collection.objects.link(light_obj)
        light_obj.location = loc
        light_obj.rotation_euler = rot

    # 6. Camera Setup
    cam_data = bpy.data.cameras.new(name="Camera")
    cam = bpy.data.objects.new(name="Camera", object_data=cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = (0.0, -6.2, 0.15)
    direction = (text_obj.location + mathutils.Vector((0, 0, 0.2))) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    # Dark studio world background
    world = bpy.context.scene.world
    if world and world.use_nodes:
        bg_node = next((n for n in world.node_tree.nodes if n.type == "BACKGROUND"), None)
        if bg_node:
            bg_node.inputs[0].default_value = (0.05, 0.05, 0.07, 1.0)
            bg_node.inputs[1].default_value = 1.0

    # 7. Cycles GPU OptiX Configuration
    if use_gpu:
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.device = 'GPU'
        bpy.context.scene.cycles.use_denoising = True
        try:
            bpy.context.scene.cycles.denoiser = 'OPTIX'
        except Exception:
            pass

        cycles_pref = bpy.context.preferences.addons.get('cycles')
        if cycles_pref:
            cpref = cycles_pref.preferences
            try:
                cpref.compute_device_type = 'OPTIX'
            except Exception:
                cpref.compute_device_type = 'CUDA'
            cpref.get_devices()
            for d in cpref.devices:
                if d.type in ('OPTIX', 'CUDA'):
                    d.use = True

    print(f"Mesh polygons: {len(text_obj.data.polygons):,}")
    print(f"Mesh vertices: {len(text_obj.data.vertices):,}")

if __name__ == "__main__":
    create_svo_tricolor_scene()

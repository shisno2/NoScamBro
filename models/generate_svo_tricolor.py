import bpy
import math
import mathutils

def create_svo_tricolor_scene(subdivision_levels=6):
    """
    Creates 3D 'SVO' text with Russian Flag (tricolor) shader and ultra-high density subdivision.
    - subdivision_levels=5 -> ~5,011,968 polygons (~4 GB RAM)
    - subdivision_levels=6 -> ~20,047,872 polygons (~16 GB RAM)
    - Theoretical 167M+ polygons requires ~138 GB RAM in uncompressed BMesh or
      Cycles Camera-Space Micropolygon Adaptive Subdivision (dicing).
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
        # Note: applying Level 6 yields 20,047,872 polygons directly into mesh data
        bpy.ops.object.modifier_apply(modifier="Subsurf")

    # 4. Russian Flag Procedural Shader (Top: White, Middle: Blue, Bottom: Red)
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

    # Russian Flag colors:
    # 0.0 - 0.3333: Red (Bottom)
    # 0.3333 - 0.6667: Blue (Middle)
    # 0.6667 - 1.0: White (Top)
    elements = ramp_node.color_ramp.elements
    elements[0].position = 0.0
    elements[0].color = (0.85, 0.03, 0.05, 1.0) # Russian Red

    elements[1].position = 0.6667
    elements[1].color = (1.0, 1.0, 1.0, 1.0)    # White

    blue_elem = ramp_node.color_ramp.elements.new(0.3333)
    blue_elem.color = (0.0, 0.22, 0.85, 1.0)   # Russian Blue

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
    # Key Light
    key_light_data = bpy.data.lights.new(name="Key_Light", type='AREA')
    key_light_data.energy = 600
    key_light_data.size = 3
    key_light = bpy.data.objects.new(name="Key_Light", object_data=key_light_data)
    bpy.context.collection.objects.link(key_light)
    key_light.location = (3, -4, 4)
    key_light.rotation_euler = (math.radians(45), 0, math.radians(35))

    # Fill Light
    fill_light_data = bpy.data.lights.new(name="Fill_Light", type='AREA')
    fill_light_data.energy = 300
    fill_light_data.size = 4
    fill_light_data.color = (0.85, 0.9, 1.0)
    fill_light = bpy.data.objects.new(name="Fill_Light", object_data=fill_light_data)
    bpy.context.collection.objects.link(fill_light)
    fill_light.location = (-4, -3, 2)
    fill_light.rotation_euler = (math.radians(45), 0, math.radians(-45))

    # Rim Light
    rim_light_data = bpy.data.lights.new(name="Rim_Light", type='AREA')
    rim_light_data.energy = 800
    rim_light_data.size = 5
    rim_light_data.color = (1.0, 0.98, 0.95)
    rim_light = bpy.data.objects.new(name="Rim_Light", object_data=rim_light_data)
    bpy.context.collection.objects.link(rim_light)
    rim_light.location = (0, 3.5, 3)
    rim_light.rotation_euler = (math.radians(-45), 0, 0)

    # 6. Camera Setup
    cam_data = bpy.data.cameras.new(name="Camera")
    cam = bpy.data.objects.new(name="Camera", object_data=cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = (0.0, -4.6, 0.05)
    direction = (text_obj.location + mathutils.Vector((0, 0, 0.35))) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    # Dark studio background
    world = bpy.context.scene.world
    if world and world.use_nodes:
        bg_node = next((n for n in world.node_tree.nodes if n.type == "BACKGROUND"), None)
        if bg_node:
            bg_node.inputs[0].default_value = (0.04, 0.04, 0.06, 1.0)
            bg_node.inputs[1].default_value = 1.0

    print(f"Total evaluated polygons: {len(text_obj.data.polygons):,}")
    print(f"Total evaluated vertices: {len(text_obj.data.vertices):,}")

if __name__ == "__main__":
    create_svo_tricolor_scene()

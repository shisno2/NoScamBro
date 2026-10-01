import bpy
import math
import mathutils

def create_svo_silver_scene():
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

    # 3. Create Silver Material
    mat = bpy.data.materials.new(name="Silver_Material")
    mat.use_nodes = True
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf:
        for inp in bsdf.inputs:
            if inp.name in ("Base Color", "BaseColor"):
                inp.default_value = (0.98, 0.98, 0.99, 1.0)
            elif inp.name == "Metallic":
                inp.default_value = 1.0
            elif inp.name == "Roughness":
                inp.default_value = 0.08
    text_obj.data.materials.append(mat)

    # 4. Lighting Setup
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

    # 5. Camera Setup
    cam_data = bpy.data.cameras.new(name="Camera")
    cam = bpy.data.objects.new(name="Camera", object_data=cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = (0.0, -4.6, 0.1)
    direction = (text_obj.location + mathutils.Vector((0, 0, 0.35))) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    # World background
    world = bpy.context.scene.world
    if world and world.use_nodes:
        bg_node = next((n for n in world.node_tree.nodes if n.type == "BACKGROUND"), None)
        if bg_node:
            bg_node.inputs[0].default_value = (0.04, 0.04, 0.06, 1.0)
            bg_node.inputs[1].default_value = 1.0

if __name__ == "__main__":
    create_svo_silver_scene()

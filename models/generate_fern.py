"""
Generate Fern (Sousou no Frieren) in 3D in Blender.
Recreates the character in her iconic seated W-sit pose with oversized black coat,
purple hair, Victorian ruffled collar, anime face and cel-shaded materials.
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler, Matrix

def setup_scene():
    for obj in list(bpy.data.objects):
        if obj.name.startswith("Fern_"):
            bpy.data.objects.remove(obj, do_unlink=True)
            
    # Seamless warm-white studio world
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg_node = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    bg_color = (0.96, 0.95, 0.95, 1.0)
    bg_node.inputs['Color'].default_value = bg_color
    bg_node.inputs['Strength'].default_value = 1.0

    # Floor
    floor = bpy.data.objects.get("Floor")
    if not floor:
        bpy.ops.mesh.primitive_plane_add(size=20.0, location=(0, 0, 0))
        floor = bpy.context.active_object
        floor.name = "Floor"
        floor_mat = bpy.data.materials.new("FloorMat")
        floor_mat.use_nodes = True
        floor.data.materials.append(floor_mat)
    floor.scale = (8.0, 8.0, 1.0)
    floor_bsdf = next(n for n in floor.data.materials[0].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    floor_bsdf.inputs['Base Color'].default_value = bg_color
    floor_bsdf.inputs['Roughness'].default_value = 0.95

    # Camera setup (High-angle portrait framing)
    cam = bpy.data.objects.get("MainCamera")
    if not cam:
        cam_data = bpy.data.cameras.new("MainCamera")
        cam = bpy.data.objects.new("MainCamera", cam_data)
        bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = (0.0, -2.15, 1.75)
    cam.rotation_euler = (math.radians(55), 0, 0)
    cam.data.lens = 42
    bpy.context.scene.render.resolution_x = 731
    bpy.context.scene.render.resolution_y = 1024

    # 3-Point Lighting
    def get_or_create_light(name, type_str, loc, energy, size, color):
        obj = bpy.data.objects.get(name)
        if not obj:
            data = bpy.data.lights.new(name, type=type_str)
            obj = bpy.data.objects.new(name, data)
            bpy.context.collection.objects.link(obj)
        obj.location = loc
        obj.data.energy = energy
        if hasattr(obj.data, 'size'):
            obj.data.size = size
        obj.data.color = color
        return obj

    get_or_create_light("KeyLight", 'AREA', (-1.5, -2.0, 2.8), 180.0, 2.0, (1.0, 0.98, 0.96))
    get_or_create_light("FillLight", 'AREA', (1.8, -1.5, 2.2), 100.0, 2.2, (0.95, 0.96, 1.0))
    get_or_create_light("RimLight", 'SPOT', (0.0, 1.5, 2.5), 150.0, 1.0, (0.88, 0.85, 1.0))

def create_toon_materials():
    def get_toon_mat(name, base_color, shadow_color, mix_factor=0.08):
        mat = bpy.data.materials.get(name)
        if not mat:
            mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        
        diffuse = nt.nodes.new("ShaderNodeBsdfDiffuse")
        diffuse.location = (-400, 100)
        diffuse.inputs['Roughness'].default_value = 0.4
        
        s2rgb = nt.nodes.new("ShaderNodeShaderToRGB")
        s2rgb.location = (-200, 100)
        nt.links.new(diffuse.outputs['BSDF'], s2rgb.inputs['Shader'])
        
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.location = (0, 100)
        ramp.color_ramp.color_mode = 'RGB'
        ramp.color_ramp.interpolation = 'LINEAR'
        ramp.color_ramp.elements[0].position = 0.32
        ramp.color_ramp.elements[0].color = shadow_color
        ramp.color_ramp.elements[1].position = 0.60
        ramp.color_ramp.elements[1].color = base_color
        nt.links.new(s2rgb.outputs['Color'], ramp.inputs['Fac'])
        
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = 'RGBA'
        mix.location = (180, 100)
        mix.inputs['Factor'].default_value = mix_factor
        mix.inputs[6].default_value = base_color
        nt.links.new(ramp.outputs['Color'], mix.inputs[7])
        
        emit = nt.nodes.new("ShaderNodeEmission")
        emit.location = (320, 100)
        nt.links.new(mix.outputs['Result'], emit.inputs['Color'])
        emit.inputs['Strength'].default_value = 1.0
        
        output = nt.nodes.new("ShaderNodeOutputMaterial")
        output.location = (460, 100)
        nt.links.new(emit.outputs['Emission'], output.inputs['Surface'])
        return mat

    def get_emission_mat(name, color, strength=1.0):
        mat = bpy.data.materials.get(name)
        if not mat:
            mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        emit = nt.nodes.new("ShaderNodeEmission")
        emit.inputs['Color'].default_value = color
        emit.inputs['Strength'].default_value = strength
        output = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(emit.outputs['Emission'], output.inputs['Surface'])
        return mat

    get_toon_mat("ToonSkin", (0.99, 0.86, 0.77, 1.0), (0.84, 0.66, 0.60, 1.0), 0.15)
    get_toon_mat("ToonHair", (0.42, 0.22, 0.56, 1.0), (0.22, 0.08, 0.30, 1.0), 0.10)
    get_emission_mat("ToonHairHL", (0.75, 0.58, 0.88, 1.0), 1.2)
    get_toon_mat("ToonCoat", (0.14, 0.14, 0.16, 1.0), (0.07, 0.07, 0.09, 1.0), 0.05)
    get_toon_mat("ToonShirt", (0.94, 0.94, 0.96, 1.0), (0.78, 0.78, 0.84, 1.0), 0.12)
    get_emission_mat("ToonSclera", (0.98, 0.98, 0.99, 1.0), 1.0)
    get_toon_mat("ToonIris", (0.68, 0.25, 0.90, 1.0), (0.32, 0.08, 0.48, 1.0), 0.35)
    get_emission_mat("ToonPupil", (0.08, 0.03, 0.12, 1.0), 1.0)
    get_emission_mat("ToonSparkle", (1.0, 1.0, 1.0, 1.0), 3.5)
    get_emission_mat("ToonLash", (0.16, 0.09, 0.20, 1.0), 1.0)
    get_emission_mat("ToonMouth", (0.85, 0.42, 0.48, 1.0), 1.0)
    get_emission_mat("ToonBlush", (0.98, 0.48, 0.56, 1.0), 1.2)

def assign_mat(obj, mat_name):
    mat = bpy.data.materials.get(mat_name)
    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

def make_disc(name, center, radius, scale, rot_euler, mat_name, segs=16):
    bm = bmesh.new()
    verts = []
    for s in range(segs):
        ang = 2 * math.pi * s / segs
        lx = radius * math.cos(ang) * scale[0]
        lz = radius * math.sin(ang) * scale[1]
        v_local = Vector((lx, 0, lz))
        v_rot = rot_euler.to_matrix() @ v_local
        verts.append(bm.verts.new(center + v_rot))
    bm.faces.new(verts)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign_mat(obj, mat_name)
    return obj

def build_character():
    # 1. W-Sitting Legs
    for sign in [-1, 1]:
        name = f"Fern_Leg_{'L' if sign < 0 else 'R'}"
        bm = bmesh.new()
        num_sides = 16
        p_hip = Vector((sign * 0.14, -0.10, 0.34))
        p_mid_thigh = Vector((sign * 0.32, -0.32, 0.24))
        p_knee = Vector((sign * 0.48, -0.52, 0.16))
        p_mid_calf = Vector((sign * 0.60, -0.24, 0.11))
        p_ankle = Vector((sign * 0.66, 0.05, 0.08))
        p_foot = Vector((sign * 0.68, 0.18, 0.06))
        
        sections = [
            (p_hip, 0.155, 0.145),
            (p_mid_thigh, 0.150, 0.140),
            (p_knee, 0.130, 0.120),
            (p_mid_calf, 0.105, 0.095),
            (p_ankle, 0.080, 0.070),
            (p_foot, 0.060, 0.050),
        ]
        prev_ring = []
        for i, (center, rx, ry) in enumerate(sections):
            ring = []
            tangent = (sections[i+1][0] - center).normalized() if i < len(sections) - 1 else (center - sections[i-1][0]).normalized()
            up = Vector((0, 0, 1))
            normal = up.cross(tangent).normalized()
            binormal = tangent.cross(normal).normalized()
            for s in range(num_sides):
                angle = 2 * math.pi * s / num_sides
                offset = normal * (math.cos(angle) * rx) + binormal * (math.sin(angle) * ry)
                pos = center + offset
                if pos.z < 0.01:
                    pos.z = 0.01
                ring.append(bm.verts.new(pos))
            if prev_ring:
                for s in range(num_sides):
                    s_next = (s + 1) % num_sides
                    bm.faces.new([prev_ring[s], prev_ring[s_next], ring[s_next], ring[s]])
            prev_ring = ring
        bm.faces.new(reversed(prev_ring))
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        sub = obj.modifiers.new("Subdivision", 'SUBSURF')
        sub.levels = 2
        for p in mesh.polygons:
            p.use_smooth = True
        assign_mat(obj, "ToonSkin")
        
        # Knee blush
        knee_center = p_knee + Vector((0, -0.02, 0.02))
        make_disc(f"Fern_KneeBlush_{'L' if sign < 0 else 'R'}", knee_center, 0.065, (1.1, 0.9), Euler((math.radians(45), sign * math.radians(20), 0)), "ToonBlush", 14)

    # 2. Coat Torso & Draped Hood
    bm_coat = bmesh.new()
    num_sides = 18
    layers = [
        (Vector((0.0, -0.06, 0.94)), 0.20, 0.16),
        (Vector((0.0, -0.10, 0.82)), 0.27, 0.22),
        (Vector((0.0, -0.12, 0.65)), 0.29, 0.24),
        (Vector((0.0, -0.14, 0.48)), 0.32, 0.28),
        (Vector((0.0, -0.15, 0.30)), 0.34, 0.30),
        (Vector((0.0, -0.16, 0.14)), 0.36, 0.32),
        (Vector((0.0, -0.16, 0.03)), 0.38, 0.34),
    ]
    prev_ring = []
    for i, (center, rx, ry) in enumerate(layers):
        ring = []
        for s in range(num_sides):
            angle = 2 * math.pi * s / num_sides
            fold = 1.0 + 0.05 * math.sin(s * 3.0 + i)
            x = center.x + math.cos(angle) * rx * fold
            y = center.y + math.sin(angle) * ry * fold
            z = max(0.01, center.z)
            ring.append(bm_coat.verts.new(Vector((x, y, z))))
        if prev_ring:
            for s in range(num_sides):
                s_next = (s + 1) % num_sides
                bm_coat.faces.new([prev_ring[s], prev_ring[s_next], ring[s_next], ring[s]])
        prev_ring = ring
    mesh_coat = bpy.data.meshes.new("Fern_Coat")
    bm_coat.to_mesh(mesh_coat)
    bm_coat.free()
    obj_coat = bpy.data.objects.new("Fern_Coat", mesh_coat)
    bpy.context.collection.objects.link(obj_coat)
    sub = obj_coat.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = 2
    for p in mesh_coat.polygons:
        p.use_smooth = True
    assign_mat(obj_coat, "ToonCoat")

    # Draped Hood
    bm_h = bmesh.new()
    num_s = 16
    hood_rings = [
        (Vector((0.0, 0.04, 1.02)), 0.24, 0.14, 0.10),
        (Vector((0.0, 0.12, 0.98)), 0.30, 0.20, 0.16),
        (Vector((0.0, 0.16, 0.90)), 0.32, 0.22, 0.18),
        (Vector((0.0, 0.14, 0.80)), 0.28, 0.18, 0.14),
        (Vector((0.0, 0.08, 0.72)), 0.20, 0.12, 0.08),
    ]
    prev_h = []
    for center, rx, ry, rz in hood_rings:
        ring = []
        for s in range(num_s):
            ang = 2 * math.pi * s / num_s
            ring.append(bm_h.verts.new(Vector((
                center.x + math.cos(ang) * rx,
                center.y + math.sin(ang) * ry,
                center.z + math.cos(ang * 0.5) * rz
            ))))
        if prev_h:
            for s in range(num_s):
                s_next = (s + 1) % num_s
                bm_h.faces.new([prev_h[s], prev_h[s_next], ring[s_next], ring[s]])
        prev_h = ring
    bm_h.faces.new(prev_h)
    mesh_h = bpy.data.meshes.new("Fern_Hood")
    bm_h.to_mesh(mesh_h)
    bm_h.free()
    obj_h = bpy.data.objects.new("Fern_Hood", mesh_h)
    bpy.context.collection.objects.link(obj_h)
    sub = obj_h.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = 2
    for p in mesh_h.polygons:
        p.use_smooth = True
    assign_mat(obj_h, "ToonCoat")

    # 3. Oversized Baggy Sleeves
    for sign in [-1, 1]:
        name = f"Fern_Sleeve_{'L' if sign < 0 else 'R'}"
        bm = bmesh.new()
        num_sides = 14
        sections = [
            (Vector((sign * 0.30, -0.08, 0.86)), 0.13, 0.13),
            (Vector((sign * 0.25, -0.18, 0.68)), 0.15, 0.15),
            (Vector((sign * 0.19, -0.28, 0.48)), 0.16, 0.16),
            (Vector((sign * 0.14, -0.36, 0.28)), 0.15, 0.15),
            (Vector((sign * 0.09, -0.42, 0.12)), 0.13, 0.13),
            (Vector((sign * 0.05, -0.44, 0.02)), 0.11, 0.11),
        ]
        prev_verts = []
        for i, (center, rx, ry) in enumerate(sections):
            ring = []
            tangent = (sections[i+1][0] - center).normalized() if i < len(sections) - 1 else (center - sections[i-1][0]).normalized()
            up = Vector((0, 0, 1))
            normal = up.cross(tangent).normalized()
            binormal = tangent.cross(normal).normalized()
            for s in range(num_sides):
                angle = 2 * math.pi * s / num_sides
                wrinkle = 1.0 + 0.07 * math.sin(s * 2.0 + i * 2.0)
                offset = normal * (math.cos(angle) * rx * wrinkle) + binormal * (math.sin(angle) * ry * wrinkle)
                pos = center + offset
                if pos.z < 0.01:
                    pos.z = 0.01
                ring.append(bm.verts.new(pos))
            if prev_verts:
                for s in range(num_sides):
                    s_next = (s + 1) % num_sides
                    bm.faces.new([prev_verts[s], prev_verts[s_next], ring[s_next], ring[s]])
            prev_verts = ring
        bm.faces.new(reversed(prev_verts))
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        sub = obj.modifiers.new("Subdivision", 'SUBSURF')
        sub.levels = 2
        for p in mesh.polygons:
            p.use_smooth = True
        assign_mat(obj, "ToonCoat")

    # 4. White Victorian Shirt Bib & Ruffled Collar
    bm_s = bmesh.new()
    num_u, num_v = 8, 8
    for i in range(num_u):
        u = i / (num_u - 1)
        z = 0.72 + u * 0.24
        w = 0.12 + (1.0 - u) * 0.05
        y = -0.14 - u * 0.03
        for j in range(num_v):
            v = j / (num_v - 1)
            x = (v - 0.5) * 2.0 * w
            y_fold = y - 0.010 * math.cos(x * 30.0)
            bm_s.verts.new(Vector((x, y_fold, z)))
    bm_s.verts.ensure_lookup_table()
    for i in range(num_u - 1):
        for j in range(num_v - 1):
            v1 = bm_s.verts[i * num_v + j]
            v2 = bm_s.verts[i * num_v + (j + 1)]
            v3 = bm_s.verts[(i + 1) * num_v + (j + 1)]
            v4 = bm_s.verts[(i + 1) * num_v + j]
            bm_s.faces.new([v1, v2, v3, v4])
    mesh_s = bpy.data.meshes.new("Fern_ShirtBib")
    bm_s.to_mesh(mesh_s)
    bm_s.free()
    obj_s = bpy.data.objects.new("Fern_ShirtBib", mesh_s)
    bpy.context.collection.objects.link(obj_s)
    sub = obj_s.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = 1
    assign_mat(obj_s, "ToonShirt")

    bm_c = bmesh.new()
    num_frills = 36
    center_c = Vector((0.0, -0.12, 1.02))
    r_cx, r_cy = 0.14, 0.12
    ring_b, ring_m, ring_t = [], [], []
    for s in range(num_frills):
        ang = 2 * math.pi * s / num_frills
        frill = 0.02 * math.sin(s * 4.0)
        ring_b.append(bm_c.verts.new(Vector((
            center_c.x + math.cos(ang) * (r_cx - 0.01),
            center_c.y + math.sin(ang) * (r_cy - 0.01),
            center_c.z - 0.04
        ))))
        ring_m.append(bm_c.verts.new(Vector((
            center_c.x + math.cos(ang) * r_cx,
            center_c.y + math.sin(ang) * r_cy,
            center_c.z + 0.02
        ))))
        ring_t.append(bm_c.verts.new(Vector((
            center_c.x + math.cos(ang) * (r_cx + 0.035 + frill),
            center_c.y + math.sin(ang) * (r_cy + 0.035 + frill),
            center_c.z + 0.06 + frill * 0.4
        ))))
    for s in range(num_frills):
        s_next = (s + 1) % num_frills
        bm_c.faces.new([ring_b[s], ring_b[s_next], ring_m[s_next], ring_m[s]])
        bm_c.faces.new([ring_m[s], ring_m[s_next], ring_t[s_next], ring_t[s]])
    mesh_c = bpy.data.meshes.new("Fern_Collar")
    bm_c.to_mesh(mesh_c)
    bm_c.free()
    obj_c = bpy.data.objects.new("Fern_Collar", mesh_c)
    bpy.context.collection.objects.link(obj_c)
    sub = obj_c.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = 2
    for p in mesh_c.polygons:
        p.use_smooth = True
    assign_mat(obj_c, "ToonShirt")

    # 5. Neck, Anime Head & Pointed Ears
    bm_n = bmesh.new()
    num_s = 16
    ring_b, ring_t = [], []
    for s in range(num_s):
        ang = 2 * math.pi * s / num_s
        x = 0.085 * math.cos(ang)
        y = -0.12 + 0.085 * math.sin(ang)
        ring_b.append(bm_n.verts.new(Vector((x, y, 0.96))))
        ring_t.append(bm_n.verts.new(Vector((x, y, 1.14))))
    for s in range(num_s):
        s_next = (s + 1) % num_s
        bm_n.faces.new([ring_b[s], ring_b[s_next], ring_t[s_next], ring_t[s]])
    mesh_n = bpy.data.meshes.new("Fern_Neck")
    bm_n.to_mesh(mesh_n)
    bm_n.free()
    obj_n = bpy.data.objects.new("Fern_Neck", mesh_n)
    bpy.context.collection.objects.link(obj_n)
    sub = obj_n.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = 1
    for p in mesh_n.polygons:
        p.use_smooth = True
    assign_mat(obj_n, "ToonSkin")

    bm_head = bmesh.new()
    num_lat, num_lon = 16, 24
    center_head = Vector((0.0, -0.18, 1.28))
    grid = []
    for i in range(num_lat):
        lat = math.pi * i / (num_lat - 1)
        z_norm = math.cos(lat)
        r_layer = math.sin(lat)
        if z_norm < -0.2:
            taper = 0.5 + 0.5 * (z_norm + 1.0) / 0.8
            rx = 0.25 * taper
            ry = 0.23 * taper
            rz = 0.27
            y_offset = -0.05 * (1.0 - taper)
        elif z_norm < 0.2:
            rx, ry, rz = 0.29, 0.26, 0.27
            y_offset = -0.02
        else:
            rx, ry, rz = 0.28, 0.27, 0.27
            y_offset = 0.0
        z = center_head.z + z_norm * rz
        row = []
        for j in range(num_lon):
            lon = 2 * math.pi * j / num_lon
            x = center_head.x + math.sin(lon) * rx * r_layer
            y = center_head.y + math.cos(lon) * ry * r_layer + y_offset
            if -0.35 < z_norm < 0.15 and math.cos(lon) < -0.2:
                x *= 1.06
                y -= 0.015
            row.append(bm_head.verts.new(Vector((x, y, z))))
        grid.append(row)
    for i in range(num_lat - 1):
        for j in range(num_lon):
            j_next = (j + 1) % num_lon
            bm_head.faces.new([grid[i][j], grid[i][j_next], grid[i+1][j_next], grid[i+1][j]])
    mesh_head = bpy.data.meshes.new("Fern_Head")
    bm_head.to_mesh(mesh_head)
    bm_head.free()
    obj_head = bpy.data.objects.new("Fern_Head", mesh_head)
    bpy.context.collection.objects.link(obj_head)
    sub = obj_head.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = 2
    for p in mesh_head.polygons:
        p.use_smooth = True
    assign_mat(obj_head, "ToonSkin")

    for sign in [-1, 1]:
        bm_e = bmesh.new()
        base = Vector((sign * 0.27, -0.14, 1.25))
        tip  = Vector((sign * 0.40, -0.05, 1.28))
        v0 = bm_e.verts.new(base + Vector((0, -0.04, -0.05)))
        v1 = bm_e.verts.new(base + Vector((0,  0.04, -0.03)))
        v2 = bm_e.verts.new(base + Vector((0,  0.03,  0.05)))
        v3 = bm_e.verts.new(base + Vector((0, -0.04,  0.04)))
        vt = bm_e.verts.new(tip)
        bm_e.faces.new([v0, v1, v2, v3])
        bm_e.faces.new([v0, v1, vt])
        bm_e.faces.new([v1, v2, vt])
        bm_e.faces.new([v2, v3, vt])
        bm_e.faces.new([v3, v0, vt])
        mesh_e = bpy.data.meshes.new(f"Fern_Ear_{'L' if sign < 0 else 'R'}")
        bm_e.to_mesh(mesh_e)
        bm_e.free()
        obj_e = bpy.data.objects.new(mesh_e.name, mesh_e)
        bpy.context.collection.objects.link(obj_e)
        sub = obj_e.modifiers.new("Subdivision", 'SUBSURF')
        sub.levels = 2
        for p in mesh_e.polygons:
            p.use_smooth = True
        assign_mat(obj_e, "ToonSkin")

    # 6. Anime Eyes & Face Expression
    for sign in [-1, 1]:
        prefix = f"Fern_Eye_{'L' if sign < 0 else 'R'}"
        eye_pos = Vector((sign * 0.125, -0.442, 1.25))
        rot = Euler((math.radians(112), -sign * math.radians(5), 0))
        
        make_disc(f"{prefix}_Sclera", eye_pos, 0.076, (1.0, 1.25), rot, "ToonSclera", 20)
        iris_pos = eye_pos + Vector((0, -0.003, 0.002))
        make_disc(f"{prefix}_Iris", iris_pos, 0.062, (0.95, 1.18), rot, "ToonIris", 20)
        pupil_pos = iris_pos + Vector((0, -0.002, 0.002))
        make_disc(f"{prefix}_Pupil", pupil_pos, 0.028, (0.90, 1.15), rot, "ToonPupil", 16)
        h1_pos = iris_pos + Vector((0.016, -0.004, 0.024))
        make_disc(f"{prefix}_HL1", h1_pos, 0.018, (1.0, 1.0), rot, "ToonSparkle", 12)
        h2_pos = iris_pos + Vector((-0.018, -0.004, -0.020))
        make_disc(f"{prefix}_HL2", h2_pos, 0.010, (1.0, 1.0), rot, "ToonSparkle", 10)
        
        # Winged lash
        bm_lash = bmesh.new()
        num_s = 12
        w = 0.088
        for k in range(num_s):
            t = k / (num_s - 1)
            lx = (t - 0.5) * w
            lz = 0.048 * math.sin(t * math.pi)
            flare = 0.016 * (t**2 if sign > 0 else (1.0 - t)**2)
            p1 = eye_pos + Vector((lx * 1.05, -0.006, 0.046 + lz + flare))
            p2 = eye_pos + Vector((lx * 1.05, -0.006, 0.070 + lz * 0.7 + flare))
            bm_lash.verts.new(p1)
            bm_lash.verts.new(p2)
        bm_lash.verts.ensure_lookup_table()
        for k in range(num_s - 1):
            bm_lash.faces.new([
                bm_lash.verts[k * 2],
                bm_lash.verts[k * 2 + 1],
                bm_lash.verts[(k + 1) * 2 + 1],
                bm_lash.verts[(k + 1) * 2]
            ])
        mesh_lash = bpy.data.meshes.new(f"{prefix}_Lash")
        bm_lash.to_mesh(mesh_lash)
        bm_lash.free()
        obj_lash = bpy.data.objects.new(mesh_lash.name, mesh_lash)
        bpy.context.collection.objects.link(obj_lash)
        sub = obj_lash.modifiers.new("Subdivision", 'SUBSURF')
        sub.levels = 1
        assign_mat(obj_lash, "ToonLash")
        
        # Eyebrow
        bm_brow = bmesh.new()
        brow_pos = eye_pos + Vector((0, -0.005, 0.115))
        for k in range(7):
            t = k / 6.0
            bx = (t - 0.5) * 0.072
            bz = 0.014 * math.sin(t * math.pi) - 0.006 * t
            bm_brow.verts.new(brow_pos + Vector((bx, 0, bz)))
            bm_brow.verts.new(brow_pos + Vector((bx, 0, bz + 0.010)))
        bm_brow.verts.ensure_lookup_table()
        for k in range(6):
            bm_brow.faces.new([
                bm_brow.verts[k * 2],
                bm_brow.verts[k * 2 + 1],
                bm_brow.verts[(k + 1) * 2 + 1],
                bm_brow.verts[(k + 1) * 2]
            ])
        mesh_brow = bpy.data.meshes.new(f"{prefix}_Brow")
        bm_brow.to_mesh(mesh_brow)
        bm_brow.free()
        obj_brow = bpy.data.objects.new(mesh_brow.name, mesh_brow)
        bpy.context.collection.objects.link(obj_brow)
        assign_mat(obj_brow, "ToonHair")

    # Nose, Mouth, Blush
    bm_nose = bmesh.new()
    num_s = 8
    r_base = 0.010
    n_base = Vector((0.0, -0.420, 1.18))
    n_tip = Vector((0.0, -0.442, 1.17))
    b_verts = []
    for s in range(num_s):
        ang = 2 * math.pi * s / num_s
        b_verts.append(bm_nose.verts.new(n_base + Vector((r_base * math.cos(ang), 0, r_base * math.sin(ang)))))
    v_tip = bm_nose.verts.new(n_tip)
    for s in range(num_s):
        s_next = (s + 1) % num_s
        bm_nose.faces.new([b_verts[s], b_verts[s_next], v_tip])
    mesh_n = bpy.data.meshes.new("Fern_Nose")
    bm_nose.to_mesh(mesh_n)
    bm_nose.free()
    obj_n = bpy.data.objects.new("Fern_Nose", mesh_n)
    bpy.context.collection.objects.link(obj_n)
    assign_mat(obj_n, "ToonSkin")

    bm_m = bmesh.new()
    m_pos = Vector((0.0, -0.412, 1.09))
    for k in range(7):
        t = k / 6.0
        mx = (t - 0.5) * 0.038
        mz = -0.006 * math.sin(t * math.pi)
        bm_m.verts.new(m_pos + Vector((mx, 0, mz)))
        bm_m.verts.new(m_pos + Vector((mx, 0, mz + 0.010)))
    bm_m.verts.ensure_lookup_table()
    for k in range(6):
        bm_m.faces.new([
            bm_m.verts[k * 2],
            bm_m.verts[k * 2 + 1],
            bm_m.verts[(k + 1) * 2 + 1],
            bm_m.verts[(k + 1) * 2]
        ])
    mesh_m = bpy.data.meshes.new("Fern_Mouth")
    bm_m.to_mesh(mesh_m)
    bm_m.free()
    obj_m = bpy.data.objects.new("Fern_Mouth", mesh_m)
    bpy.context.collection.objects.link(obj_m)
    assign_mat(obj_m, "ToonMouth")

    for sign in [-1, 1]:
        blush_pos = Vector((sign * 0.19, -0.435, 1.16))
        rot = Euler((math.radians(110), -sign * math.radians(12), 0))
        make_disc(f"Fern_Blush_{'L' if sign < 0 else 'R'}", blush_pos, 0.040, (1.30, 0.70), rot, "ToonBlush", 14)

    # 7. Fern's Flowing Purple Hair
    bm_hb = bmesh.new()
    num_lat, num_lon = 12, 20
    center_hair = Vector((0.0, -0.16, 1.32))
    grid = []
    for i in range(num_lat):
        lat = 0.5 * math.pi * i / (num_lat - 1)
        z_norm = math.cos(lat)
        r_layer = math.sin(lat)
        rx, ry, rz = 0.31, 0.30, 0.28
        z = center_hair.z + z_norm * rz
        row = []
        for j in range(num_lon):
            lon = 2 * math.pi * j / num_lon
            x = center_hair.x + math.sin(lon) * rx * r_layer
            y = center_hair.y + math.cos(lon) * ry * r_layer
            row.append(bm_hb.verts.new(Vector((x, y, z))))
        grid.append(row)
    for i in range(num_lat - 1):
        for j in range(num_lon):
            j_next = (j + 1) % num_lon
            bm_hb.faces.new([grid[i][j], grid[i][j_next], grid[i+1][j_next], grid[i+1][j]])
    mesh_hb = bpy.data.meshes.new("Fern_HairBase")
    bm_hb.to_mesh(mesh_hb)
    bm_hb.free()
    obj_hb = bpy.data.objects.new(mesh_hb.name, mesh_hb)
    bpy.context.collection.objects.link(obj_hb)
    sub = obj_hb.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = 2
    for p in mesh_hb.polygons:
        p.use_smooth = True
    assign_mat(obj_hb, "ToonHair")

    bm_bg = bmesh.new()
    num_strands = 11
    for s in range(num_strands):
        t = (s / (num_strands - 1) - 0.5) * 2.0
        root_x = t * 0.25
        root_y = -0.22 - math.cos(t * math.pi * 0.45) * 0.22
        root_z = 1.50 - abs(t) * 0.03
        gap = 0.012 if t > 0 else (-0.012 if t < 0 else 0)
        tip_x = root_x * 1.04 + gap
        tip_y = -0.450
        tip_z = 1.35 + 0.015 * math.sin(s * 3.5)
        if abs(t) > 0.75:
            tip_z = 1.28
            tip_y = -0.435
        w_root = 0.026
        w_tip = 0.005 if abs(t) < 0.8 else 0.014
        v_rt_l = bm_bg.verts.new(Vector((root_x - w_root, root_y, root_z)))
        v_rt_r = bm_bg.verts.new(Vector((root_x + w_root, root_y, root_z)))
        mid_x = (root_x + tip_x) * 0.5
        mid_y = (root_y + tip_y) * 0.5 - 0.02
        mid_z = (root_z + tip_z) * 0.5 + 0.01
        v_mid_l = bm_bg.verts.new(Vector((mid_x - w_root * 0.8, mid_y, mid_z)))
        v_mid_r = bm_bg.verts.new(Vector((mid_x + w_root * 0.8, mid_y, mid_z)))
        v_tip_l = bm_bg.verts.new(Vector((tip_x - w_tip, tip_y, tip_z)))
        v_tip_r = bm_bg.verts.new(Vector((tip_x + w_tip, tip_y, tip_z)))
        bm_bg.faces.new([v_rt_l, v_rt_r, v_mid_r, v_mid_l])
        bm_bg.faces.new([v_mid_l, v_mid_r, v_tip_r, v_tip_l])
    mesh_bg = bpy.data.meshes.new("Fern_Bangs")
    bm_bg.to_mesh(mesh_bg)
    bm_bg.free()
    obj_bg = bpy.data.objects.new(mesh_bg.name, mesh_bg)
    bpy.context.collection.objects.link(obj_bg)
    sol = obj_bg.modifiers.new("Solidify", 'SOLIDIFY')
    sol.thickness = 0.010
    sub = obj_bg.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = 1
    for p in mesh_bg.polygons:
        p.use_smooth = True
    assign_mat(obj_bg, "ToonHair")

    for sign in [-1, 1]:
        bm_sl = bmesh.new()
        path = [
            Vector((sign * 0.26, -0.32, 1.44)),
            Vector((sign * 0.30, -0.38, 1.28)),
            Vector((sign * 0.28, -0.34, 1.10)),
            Vector((sign * 0.24, -0.28, 0.90)),
            Vector((sign * 0.19, -0.24, 0.72)),
            Vector((sign * 0.14, -0.20, 0.55)),
        ]
        widths = [0.038, 0.042, 0.038, 0.030, 0.020, 0.006]
        prev_pair = []
        for i, pt in enumerate(path):
            w = widths[i]
            v1 = bm_sl.verts.new(pt + Vector((-w * 0.5, -0.01, 0)))
            v2 = bm_sl.verts.new(pt + Vector((w * 0.5, 0.01, 0)))
            if prev_pair:
                bm_sl.faces.new([prev_pair[0], prev_pair[1], v2, v1])
            prev_pair = [v1, v2]
        mesh_sl = bpy.data.meshes.new(f"Fern_Sidelock_{'L' if sign < 0 else 'R'}")
        bm_sl.to_mesh(mesh_sl)
        bm_sl.free()
        obj_sl = bpy.data.objects.new(mesh_sl.name, mesh_sl)
        bpy.context.collection.objects.link(obj_sl)
        sol = obj_sl.modifiers.new("Solidify", 'SOLIDIFY')
        sol.thickness = 0.012
        sub = obj_sl.modifiers.new("Subdivision", 'SUBSURF')
        sub.levels = 1
        for p in mesh_sl.polygons:
            p.use_smooth = True
        assign_mat(obj_sl, "ToonHair")

    bm_bh = bmesh.new()
    num_strands, num_steps = 18, 16
    for s in range(num_strands):
        u = (s / (num_strands - 1) - 0.5) * 2.0
        for step in range(num_steps):
            v_frac = step / (num_steps - 1)
            z = 1.45 * (1.0 - v_frac) + 0.02
            spread = 0.38 + 0.65 * (v_frac ** 1.3)
            x = u * spread + 0.04 * math.sin(v_frac * 3.5 + u * 2.5)
            y = 0.05 + 0.68 * v_frac + 0.05 * math.sin(v_frac * 3.14)
            bm_bh.verts.new(Vector((x, y, z)))
    bm_bh.verts.ensure_lookup_table()
    for s in range(num_strands - 1):
        for step in range(num_steps - 1):
            i1 = s * num_steps + step
            i2 = s * num_steps + (step + 1)
            i3 = (s + 1) * num_steps + (step + 1)
            i4 = (s + 1) * num_steps + step
            bm_bh.faces.new([
                bm_bh.verts[i1],
                bm_bh.verts[i2],
                bm_bh.verts[i3],
                bm_bh.verts[i4]
            ])
    mesh_bh = bpy.data.meshes.new("Fern_BackHair")
    bm_bh.to_mesh(mesh_bh)
    bm_bh.free()
    obj_bh = bpy.data.objects.new(mesh_bh.name, mesh_bh)
    bpy.context.collection.objects.link(obj_bh)
    sol = obj_bh.modifiers.new("Solidify", 'SOLIDIFY')
    sol.thickness = 0.022
    sub = obj_bh.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = 2
    for p in mesh_bh.polygons:
        p.use_smooth = True
    assign_mat(obj_bh, "ToonHair")

    # Angel Ring Highlight
    bm_hl = bmesh.new()
    num_pts = 16
    for i in range(num_pts):
        ang = math.pi * (0.15 + 0.70 * i / (num_pts - 1))
        x = 0.30 * math.cos(ang)
        y = -0.18 - 0.28 * math.sin(ang)
        z = 1.42 + 0.012 * math.sin(i * 0.9)
        bm_hl.verts.new(Vector((x, y, z)))
        bm_hl.verts.new(Vector((x * 0.97, y * 0.97, z + 0.025)))
    bm_hl.verts.ensure_lookup_table()
    for i in range(num_pts - 1):
        bm_hl.faces.new([
            bm_hl.verts[i * 2],
            bm_hl.verts[i * 2 + 1],
            bm_hl.verts[(i + 1) * 2 + 1],
            bm_hl.verts[(i + 1) * 2]
        ])
    mesh_hl = bpy.data.meshes.new("Fern_HairHighlight")
    bm_hl.to_mesh(mesh_hl)
    bm_hl.free()
    obj_hl = bpy.data.objects.new(mesh_hl.name, mesh_hl)
    bpy.context.collection.objects.link(obj_hl)
    assign_mat(obj_hl, "ToonHairHL")

    # Ground Contact Shadow
    bm_sh = bmesh.new()
    num_s = 24
    rx_sh, ry_sh = 0.72, 0.55
    for s in range(num_s):
        ang = 2 * math.pi * s / num_s
        bm_sh.verts.new(Vector((rx_sh * math.cos(ang), -0.22 + ry_sh * math.sin(ang), 0.003)))
    bm_sh.faces.new(bm_sh.verts)
    mesh_sh = bpy.data.meshes.new("Fern_GroundShadow")
    bm_sh.to_mesh(mesh_sh)
    bm_sh.free()
    obj_sh = bpy.data.objects.new("Fern_GroundShadow", mesh_sh)
    bpy.context.collection.objects.link(obj_sh)
    mat_sh = bpy.data.materials.new("GroundShadowMat")
    mat_sh.use_nodes = True
    bsdf_sh = next(n for n in mat_sh.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf_sh.inputs['Base Color'].default_value = (0.86, 0.84, 0.84, 1.0)
    bsdf_sh.inputs['Roughness'].default_value = 1.0
    obj_sh.data.materials.append(mat_sh)

    # Coat Seam
    bm_crease = bmesh.new()
    num_cr = 10
    for i in range(num_cr):
        t = i / (num_cr - 1)
        z = 0.82 * (1.0 - t) + 0.05
        y = -0.32 - t * 0.10
        w = 0.012
        bm_crease.verts.new(Vector((-w, y, z)))
        bm_crease.verts.new(Vector((0.0, y - 0.015, z)))
        bm_crease.verts.new(Vector((w, y, z)))
    bm_crease.verts.ensure_lookup_table()
    for i in range(num_cr - 1):
        bm_crease.faces.new([
            bm_crease.verts[i * 3],
            bm_crease.verts[i * 3 + 1],
            bm_crease.verts[(i + 1) * 3 + 1],
            bm_crease.verts[(i + 1) * 3]
        ])
        bm_crease.faces.new([
            bm_crease.verts[i * 3 + 1],
            bm_crease.verts[i * 3 + 2],
            bm_crease.verts[(i + 1) * 3 + 2],
            bm_crease.verts[(i + 1) * 3 + 1]
        ])
    mesh_cr = bpy.data.meshes.new("Fern_CoatSeam")
    bm_crease.to_mesh(mesh_cr)
    bm_crease.free()
    obj_cr = bpy.data.objects.new("Fern_CoatSeam", mesh_cr)
    bpy.context.collection.objects.link(obj_cr)
    sub = obj_cr.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = 1
    for p in mesh_cr.polygons:
        p.use_smooth = True
    assign_mat(obj_cr, "ToonCoat")

def main():
    setup_scene()
    create_toon_materials()
    build_character()
    print("Generation complete!")

if __name__ == "__main__":
    main()

"""Baseline build for a3d-03-blender-sonic.
Run: blender -b --python examples/baseline_sonic_build.py
"""
import math

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def material(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    m.diffuse_color = (*rgb, 1.0)
    return m


BLUE = material("SonicBlue", (0.05, 0.2, 0.9))
RED = material("ShoeRed", (0.9, 0.05, 0.05))
WHITE = material("EyeWhite", (0.95, 0.95, 0.9))
PEACH = material("Peach", (0.95, 0.75, 0.55))


def sphere(name, location, radius, mat, scale=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
    o = bpy.context.active_object
    o.name = name
    if scale:
        o.scale = scale
    o.data.materials.append(mat)
    return o


def cyl(name, location, radius, depth, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        location=location, rotation=rotation)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    return o


def cone(name, location, radius, depth, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(radius1=radius, radius2=0.0, depth=depth,
                                    location=location, rotation=rotation)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    return o


# +Y is front (eyes), -Y is back (quills)
sphere("Head", (0, 0, 2.2), 0.85, BLUE)
sphere("Body", (0, 0, 1.15), 0.55, BLUE, scale=(1, 1, 1.15))

# 6 quills sweeping back from the head
for i in range(6):
    z = 2.55 - 0.28 * i
    cone(f"Quill.{i + 1}", (0, -1.05 - 0.12 * (i % 2), z), 0.22, 1.0,
         BLUE, rotation=(math.radians(100 + 8 * i), 0, 0))

# eyes on the front
sphere("Eye.1", (-0.3, 0.72, 2.4), 0.22, WHITE, scale=(0.7, 0.5, 1.2))
sphere("Eye.2", (0.3, 0.72, 2.4), 0.22, WHITE, scale=(0.7, 0.5, 1.2))

# arms and legs
cyl("Arm.1", (-0.75, 0, 1.3), 0.1, 0.8, PEACH, rotation=(0, math.radians(35), 0))
cyl("Arm.2", (0.75, 0, 1.3), 0.1, 0.8, PEACH, rotation=(0, math.radians(-35), 0))
cyl("Leg.1", (-0.28, 0, 0.45), 0.11, 0.7, BLUE)
cyl("Leg.2", (0.28, 0, 0.45), 0.11, 0.7, BLUE)

# red shoes
sphere("Shoe.1", (-0.28, 0.12, 0.08), 0.24, RED, scale=(0.9, 1.5, 0.7))
sphere("Shoe.2", (0.28, 0.12, 0.08), 0.24, RED, scale=(0.9, 1.5, 0.7))

# camera + light (front view)
bpy.ops.object.camera_add(location=(2.6, 5.5, 2.4))
cam = bpy.context.active_object
scene.camera = cam
track = cam.constraints.new(type="TRACK_TO")
bpy.ops.object.empty_add(location=(0, 0, 1.5))
track.target = bpy.context.active_object
bpy.ops.object.light_add(type="SUN", location=(3, 6, 6))
bpy.context.active_object.rotation_euler = (math.radians(-40), math.radians(20), 0)

scene.render.filepath = "//sonic.png"
scene.render.resolution_x = 800
scene.render.resolution_y = 600
bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath("//sonic.blend"))
bpy.ops.render.render(write_still=True)
print("built and rendered sonic")

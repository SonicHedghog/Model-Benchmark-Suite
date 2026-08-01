"""Baseline build for a3d-02-blender-eiffel.
Run: blender -b --python examples/baseline_eiffel_build.py
"""
import math

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def cyl_between(name, p1, p2, radius):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=d.length,
                                        location=(p1 + p2) / 2)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = d.to_track_quat("Z", "Y")
    return obj


def box(name, location, size_xyz):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = Vector(size_xyz) / 2
    return obj


# 4 legs: base corners of a 4x4 square rising to a 1x1 square at z=4
n = 0
for sx in (-1, 1):
    for sy in (-1, 1):
        n += 1
        cyl_between(f"Leg.{n}", (2 * sx, 2 * sy, 0), (0.5 * sx, 0.5 * sy, 4), 0.18)

# platforms: lower big, upper small
box("Platform.1", (0, 0, 2.0), (3.2, 3.2, 0.15))
box("Platform.2", (0, 0, 4.0), (1.4, 1.4, 0.12))

# upper tower: tapering cone from the second platform to near the top
bpy.ops.mesh.primitive_cone_add(radius1=0.7, radius2=0.15, depth=5.0,
                                location=(0, 0, 6.5))
bpy.context.active_object.name = "Tower"

# spire
bpy.ops.mesh.primitive_cone_add(radius1=0.12, radius2=0.0, depth=1.0,
                                location=(0, 0, 9.5))
bpy.context.active_object.name = "Spire"

# camera + light
bpy.ops.object.camera_add(location=(14, -20, 8))
cam = bpy.context.active_object
scene.camera = cam
track = cam.constraints.new(type="TRACK_TO")
bpy.ops.object.empty_add(location=(0, 0, 4.5))
track.target = bpy.context.active_object
bpy.ops.object.light_add(type="SUN", location=(5, -5, 12))

scene.render.filepath = "//eiffel_tower.png"
scene.render.resolution_x = 800
scene.render.resolution_y = 600
bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath("//eiffel_tower.blend"))
bpy.ops.render.render(write_still=True)
print("built and rendered eiffel tower")

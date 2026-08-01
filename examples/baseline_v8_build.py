"""Baseline build for a3d-01-blender-v8: constructs a V8 engine scene headlessly.
Run: blender -b --python baseline_v8_build.py
"""
import math

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

BANK_TILT = math.radians(45)
BORE_SPACING = 1.4
CRANK_LEN = 6.0
CRANK_Z = 0.0
PISTON_DIST = 2.2  # distance from crank axis to piston center along bank axis


def add_cyl(name, radius, depth, location, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    return obj


# crankshaft along Y
add_cyl("Crankshaft", 0.25, CRANK_LEN, (0, 0, CRANK_Z), (math.pi / 2, 0, 0))

# crank throws
for i in range(4):
    y = -2.1 + i * BORE_SPACING
    ang = i * math.pi / 2
    add_cyl(f"Throw.{i + 1}", 0.18, 0.5,
            (0.45 * math.cos(ang), y, CRANK_Z + 0.45 * math.sin(ang)),
            (math.pi / 2, 0, 0))

# two banks of 4 pistons + rods, 90-degree V
n = 0
for side in (-1, 1):
    tilt = side * BANK_TILT
    for i in range(4):
        n += 1
        y = -2.1 + i * BORE_SPACING
        px = side * PISTON_DIST * math.sin(BANK_TILT)
        pz = CRANK_Z + PISTON_DIST * math.cos(BANK_TILT)
        add_cyl(f"Piston.{n}", 0.45, 0.8, (px, y, pz), (0, tilt, 0))
        rx = side * (PISTON_DIST / 2) * math.sin(BANK_TILT)
        rz = CRANK_Z + (PISTON_DIST / 2) * math.cos(BANK_TILT)
        add_cyl(f"Rod.{n}", 0.12, PISTON_DIST - 0.8, (rx, y, rz), (0, tilt, 0))

# camera + light for the render
bpy.ops.object.camera_add(location=(2.5, -10, 5))
cam = bpy.context.active_object
scene.camera = cam
track = cam.constraints.new(type="TRACK_TO")
bpy.ops.object.empty_add(location=(0, 0, 0.8))
track.target = bpy.context.active_object
bpy.ops.object.light_add(type="SUN", location=(4, -4, 8))

scene.render.filepath = "//v8_engine.png"
scene.render.resolution_x = 800
scene.render.resolution_y = 600
bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath("//v8_engine.blend"))
bpy.ops.render.render(write_still=True)
print("built and rendered v8 engine")

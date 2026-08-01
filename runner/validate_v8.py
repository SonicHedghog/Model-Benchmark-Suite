"""Validate a V8 engine scene built for item a3d-01-blender-v8.

Run inside Blender:  blender -b v8_engine.blend --python runner/validate_v8.py
Prints "V8_SCORE: <points>/10"; >= 8 points passes.
"""
import math
import re

import bpy
from mathutils import Vector

points = 0
notes = []


def log(pts, msg):
    global points
    points += pts
    notes.append(f"[{'+' + str(pts) if pts else ' 0'}] {msg}")


objs = list(bpy.data.objects)
pistons = [o for o in objs if re.match(r"(?i)piston\b|piston\.", o.name)]
rods = [o for o in objs if re.match(r"(?i)rod\b|rod\.", o.name)]
throws = [o for o in objs if re.match(r"(?i)throw\b|throw\.", o.name)]
cranks = [o for o in objs if re.match(r"(?i)crankshaft", o.name)]

# 1-2: piston count
log(2 if len(pistons) == 8 else 0, f"8 pistons named Piston.* (found {len(pistons)})")

# 3-4: two banks of 4 forming a ~90 degree V
if len(pistons) == 8:
    left = [p for p in pistons if p.location.x < 0]
    right = [p for p in pistons if p.location.x > 0]
    banks_ok = len(left) == 4 and len(right) == 4
    log(1 if banks_ok else 0, f"two banks of 4 across crank axis ({len(left)}/{len(right)})")

    def tilt_deg(o):
        z_axis = o.matrix_world.to_3x3() @ Vector((0, 0, 1))
        return math.degrees(z_axis.angle(Vector((0, 0, 1))))

    tilts = [tilt_deg(p) for p in pistons]
    tilt_ok = all(30 <= t <= 60 for t in tilts)
    log(1 if tilt_ok else 0,
        f"pistons tilted ~45 deg from vertical (tilts {[round(t) for t in tilts]})")
else:
    log(0, "bank checks skipped (wrong piston count)")
    log(0, "tilt check skipped")

# 5-6: crankshaft exists, elongated along Y, below pistons
if cranks:
    c = cranks[0]
    corners = [c.matrix_world @ Vector(b) for b in c.bound_box]
    dims = Vector((max(v.x for v in corners) - min(v.x for v in corners),
                   max(v.y for v in corners) - min(v.y for v in corners),
                   max(v.z for v in corners) - min(v.z for v in corners)))
    elongated = dims.y > dims.x and dims.y > dims.z
    below = not pistons or c.location.z < min(p.location.z for p in pistons)
    log(1, "crankshaft object present")
    log(1 if (elongated and below) else 0,
        f"crankshaft elongated along Y and below pistons (dims {tuple(round(d,2) for d in dims)})")
else:
    log(0, "no Crankshaft object")
    log(0, "crankshaft geometry check skipped")

# 7: crank throws
log(1 if len(throws) >= 4 else 0, f">=4 crank throws (found {len(throws)})")

# 8: rods
log(1 if len(rods) == 8 else 0, f"8 connecting rods (found {len(rods)})")

# 9: pistons evenly spaced along Y within each bank
if len(pistons) == 8:
    def spacing_ok(bank):
        ys = sorted(p.location.y for p in bank)
        gaps = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
        return gaps and max(gaps) - min(gaps) < 0.25 * max(gaps)
    left = [p for p in pistons if p.location.x < 0]
    right = [p for p in pistons if p.location.x > 0]
    ok = len(left) == 4 and len(right) == 4 and spacing_ok(left) and spacing_ok(right)
    log(1 if ok else 0, "pistons evenly spaced along Y within each bank")
else:
    log(0, "spacing check skipped")

# 10: total scene sanity — all named parts are meshes with geometry
named = pistons + rods + throws + cranks
geo_ok = named and all(o.type == "MESH" and len(o.data.vertices) >= 8 for o in named)
log(1 if geo_ok else 0, "all named parts are real meshes")

print("\n".join(notes))
print(f"V8_SCORE: {points}/10")

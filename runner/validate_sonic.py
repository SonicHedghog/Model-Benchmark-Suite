"""Validate the Sonic scene for item a3d-03-blender-sonic.

Run inside Blender:  blender -b sonic.blend --python runner/validate_sonic.py
Prints "SONIC_SCORE: <points>/10"; >= 8 points passes.
"""
import re

import bpy
from mathutils import Vector

points = 0
notes = []


def log(pts, msg):
    global points
    points += pts
    notes.append(f"[{'+' + str(pts) if pts else ' 0'}] {msg}")


def base_color(o):
    for slot in o.material_slots:
        m = slot.material
        if m is None:
            continue
        if m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    c = n.inputs["Base Color"].default_value
                    return c[0], c[1], c[2]
        return tuple(m.diffuse_color[:3])
    return None


def is_red(c):
    return c is not None and c[0] > 0.5 and c[1] < 0.35 and c[2] < 0.35


def is_blue(c):
    return c is not None and c[2] > 0.5 and c[0] < 0.35


objs = [o for o in bpy.data.objects if o.type == "MESH"]


def named(pat):
    return [o for o in objs if re.match(pat, o.name)]


heads = named(r"(?i)head")
bodies = named(r"(?i)body")
quills = named(r"(?i)quill")
eyes = named(r"(?i)eye\b|eye\.")
arms = named(r"(?i)arm\b|arm\.")
legs = named(r"(?i)leg\b|leg\.")
shoes = named(r"(?i)shoe\b|shoe\.")

# 1-2: head above smaller body
if heads and bodies:
    log(1, "Head and Body meshes present")
    h, b = heads[0], bodies[0]
    hv = max(h.dimensions)
    bv = max(b.dimensions)
    log(1 if h.location.z > b.location.z else 0, "head sits above body")
else:
    log(0, f"Head ({len(heads)}) and Body ({len(bodies)}) required")
    log(0, "head/body arrangement check skipped")

# 3-4: >=5 quills behind/above head center, pointing backward (-Y or +Y consistently)
if len(quills) >= 5:
    log(1, f">=5 quills (found {len(quills)})")
    if heads:
        hc = heads[0].location
        behind = [q for q in quills if abs(q.location.y - hc.y) > 0.1]
        same_side = len({q.location.y > hc.y for q in behind}) == 1 if behind else False
        log(1 if len(behind) >= 5 and same_side else 0,
            "quills all offset to the same side (back) of the head")
    else:
        log(0, "quill placement skipped (no head)")
else:
    log(0, f"need >=5 Quill.* meshes (found {len(quills)})")
    log(0, "quill placement skipped")

# 5: two eyes on the same side (front), opposite the quills
if len(eyes) == 2 and heads:
    hc = heads[0].location
    front_side = {e.location.y > hc.y for e in eyes}
    ok = len(front_side) == 1
    if ok and quills:
        q_side = quills[0].location.y > hc.y
        ok = front_side.pop() != q_side
    log(1 if ok else 0, "2 eyes on the front of the head (opposite the quills)")
else:
    log(0, f"need Eye.1/Eye.2 on the head (found {len(eyes)})")

# 6: limbs
log(1 if len(arms) == 2 and len(legs) == 2 else 0,
    f"2 arms and 2 legs (found {len(arms)} arms, {len(legs)} legs)")

# 7: two shoes at the bottom
if len(shoes) == 2:
    min_z = min(o.location.z for o in objs)
    ok = all(s.location.z <= min_z + 0.5 for s in shoes)
    log(1 if ok else 0, "2 shoes at the bottom of the figure")
else:
    log(0, f"need Shoe.1/Shoe.2 (found {len(shoes)})")

# 8: shoes are red
log(1 if len(shoes) == 2 and all(is_red(base_color(s)) for s in shoes) else 0,
    f"shoes have a red material ({[base_color(s) for s in shoes]})")

# 9: head/body/quills are blue
blue_parts = heads + bodies + quills
log(1 if blue_parts and all(is_blue(base_color(o)) for o in blue_parts) else 0,
    "head, body, and quills have a blue material")

# 10: all named parts are real meshes
named_all = heads + bodies + quills + eyes + arms + legs + shoes
geo_ok = named_all and all(len(o.data.vertices) >= 4 for o in named_all)
log(1 if geo_ok else 0, "all named parts are real meshes")

print("\n".join(notes))
print(f"SONIC_SCORE: {points}/10")

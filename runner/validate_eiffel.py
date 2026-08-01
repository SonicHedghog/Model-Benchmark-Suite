"""Validate the Eiffel Tower scene for item a3d-02-blender-eiffel.

Run inside Blender:  blender -b eiffel_tower.blend --python runner/validate_eiffel.py
Prints "EIFFEL_SCORE: <points>/10"; >= 8 points passes.
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


def world_bbox(objs):
    corners = [o.matrix_world @ Vector(b) for o in objs for b in o.bound_box]
    lo = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
    hi = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
    return lo, hi


objs = [o for o in bpy.data.objects if o.type == "MESH"]
legs = [o for o in objs if re.match(r"(?i)leg\b|leg\.", o.name)]
platforms = [o for o in objs if re.match(r"(?i)platform", o.name)]
towers = [o for o in objs if re.match(r"(?i)tower", o.name)]
spires = [o for o in objs if re.match(r"(?i)spire", o.name)]

# 1-2: four legs
log(2 if len(legs) == 4 else 0, f"4 legs named Leg.* (found {len(legs)})")

# 3: legs at corners of a square footprint (one per XY quadrant)
if len(legs) == 4:
    def base_xy(o):
        corners = [o.matrix_world @ Vector(b) for b in o.bound_box]
        low = min(corners, key=lambda v: v.z)
        return low.x, low.y
    quads = {(x > 0, y > 0) for x, y in map(base_xy, legs)}
    log(1 if len(quads) == 4 else 0, f"legs occupy 4 quadrants around origin ({len(quads)})")

    # 4: legs lean inward: top-of-leg XY spread much smaller than base spread
    def spread(zs):
        pts = []
        for o in legs:
            cs = [o.matrix_world @ Vector(b) for b in o.bound_box]
            pick = min(cs, key=lambda v: v.z) if zs == "base" else max(cs, key=lambda v: v.z)
            pts.append(pick)
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        return max(max(xs) - min(xs), max(ys) - min(ys))
    lean_ok = spread("top") < 0.6 * spread("base")
    log(1 if lean_ok else 0,
        f"legs lean inward (top spread {spread('top'):.2f} vs base {spread('base'):.2f})")
else:
    log(0, "quadrant check skipped")
    log(0, "lean check skipped")

# 5-6: platforms at different heights, higher one smaller
if len(platforms) >= 2:
    log(1, f">=2 platforms (found {len(platforms)})")
    ps = sorted(platforms, key=lambda o: o.location.z)
    lo_p, hi_p = ps[0], ps[-1]

    def footprint(o):
        lo, hi = world_bbox([o])
        return (hi.x - lo.x) * (hi.y - lo.y)
    ok = hi_p.location.z > lo_p.location.z and footprint(hi_p) < footprint(lo_p)
    log(1 if ok else 0, "higher platform is smaller than lower platform")
else:
    log(0, f"need >=2 Platform.* meshes (found {len(platforms)})")
    log(0, "platform size check skipped")

# 7: tower section and spire present, spire at the very top
if towers and spires:
    _, hi_all = world_bbox(objs)
    _, hi_spire = world_bbox(spires)
    log(1 if hi_spire.z >= hi_all.z - 1e-3 else 0, "Spire is the topmost mesh")
else:
    log(0, f"Tower ({len(towers)}) and Spire ({len(spires)}) meshes required")

# 8: proportions — height >= 2x base width
lo, hi = world_bbox(objs)
height = hi.z - lo.z
base_w = max(hi.x - lo.x, hi.y - lo.y)
log(1 if height >= 2 * base_w else 0,
    f"height {height:.2f} >= 2x base width {base_w:.2f}")

# 9: taper — width of top third well under half the base width
top_pts = []
bot_pts = []
for o in objs:
    for b in o.bound_box:
        v = o.matrix_world @ Vector(b)
        (top_pts if v.z > lo.z + 2 * height / 3 else bot_pts).append(v)
if top_pts and bot_pts:
    def width(pts):
        return max(max(p.x for p in pts) - min(p.x for p in pts),
                   max(p.y for p in pts) - min(p.y for p in pts))
    log(1 if width(top_pts) < 0.5 * width(bot_pts) else 0,
        f"tapering silhouette (top third {width(top_pts):.2f} vs base {width(bot_pts):.2f})")
else:
    log(0, "taper check skipped (no geometry in top third)")

# 10: all named parts are real meshes
named = legs + platforms + towers + spires
geo_ok = named and all(len(o.data.vertices) >= 4 for o in named)
log(1 if geo_ok else 0, "all named parts are real meshes")

print("\n".join(notes))
print(f"EIFFEL_SCORE: {points}/10")

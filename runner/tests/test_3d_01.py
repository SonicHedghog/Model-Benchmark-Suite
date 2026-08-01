from solution import make_cube_obj


def parse_obj(text):
    verts, faces = [], []
    for line in text.splitlines():
        p = line.split()
        if not p:
            continue
        if p[0] == "v":
            verts.append(tuple(float(x) for x in p[1:4]))
        elif p[0] == "f":
            faces.append(tuple(int(t.split("/")[0]) for t in p[1:]))
    return verts, faces


verts, faces = parse_obj(make_cube_obj(2.0))
assert len(verts) == 8, f"expected 8 vertices, got {len(verts)}"
assert len(faces) == 12, f"expected 12 faces, got {len(faces)}"
assert all(len(f) == 3 for f in faces), "faces must be triangles"
# all coordinates at +/- size/2
for v in verts:
    assert all(abs(abs(c) - 1.0) < 1e-6 for c in v), f"bad vertex {v}"
# 8 distinct corners
assert len({tuple(round(c, 6) for c in v) for v in verts}) == 8
# valid indices and every vertex used
idx = {i for f in faces for i in f}
assert idx == set(range(1, 9)), f"face indices {sorted(idx)}"
# each edge of a closed triangulated surface is shared by exactly 2 faces
from collections import Counter
edges = Counter()
for a, b, c in faces:
    for e in ((a, b), (b, c), (c, a)):
        edges[tuple(sorted(e))] += 1
assert all(n == 2 for n in edges.values()), "mesh is not watertight"
assert len(edges) == 18
print("OK")

from solution import make_pyramid_obj


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


verts, faces = parse_obj(make_pyramid_obj(2.0, 3.0))
assert len(verts) == 5, f"expected 5 vertices, got {len(verts)}"
assert len(faces) == 6, f"expected 6 faces, got {len(faces)}"
assert all(len(f) == 3 for f in faces)
apex = [v for v in verts if abs(v[2] - 3.0) < 1e-6]
assert len(apex) == 1 and abs(apex[0][0]) < 1e-6 and abs(apex[0][1]) < 1e-6, "apex must be (0,0,height)"
base = [v for v in verts if abs(v[2]) < 1e-6]
assert len(base) == 4, "4 base vertices in z=0 plane"
for v in base:
    assert abs(abs(v[0]) - 1.0) < 1e-6 and abs(abs(v[1]) - 1.0) < 1e-6, f"bad base vertex {v}"
from collections import Counter
edges = Counter()
for a, b, c in faces:
    for e in ((a, b), (b, c), (c, a)):
        edges[tuple(sorted(e))] += 1
assert all(n == 2 for n in edges.values()), "mesh is not watertight"
print("OK")

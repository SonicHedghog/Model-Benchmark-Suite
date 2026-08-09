"""Grade a generated 3D model against a reference point cloud.

Usage:  python3 runner/compare_mesh.py <candidate.obj> <reference_points.npz>

Both shapes are normalized (bbox-centered, scaled to unit max extent, Z-up).
The candidate is tested at 8 rotations about Z plus X-mirror to remove
orientation ambiguity; the best symmetric Chamfer distance is mapped to a
score out of 10 (printed as "SHAPE_SCORE: N/10"). >= 7 passes.

Requires: pip install trimesh numpy scipy
"""
import sys

import numpy as np
import trimesh
from scipy.spatial import cKDTree

N_SAMPLES = 15000
# chamfer -> score calibration: cd <= GOOD gives 10, cd >= BAD gives 0
GOOD, BAD = 0.01, 0.08


def normalize(pts):
    lo, hi = pts.min(0), pts.max(0)
    pts = pts - (lo + hi) / 2
    return pts / max((hi - lo).max(), 1e-12)


def chamfer(a, b, tree_b=None):
    tree_a = cKDTree(a)
    tree_b = tree_b or cKDTree(b)
    d1, _ = tree_b.query(a, k=1)
    d2, _ = tree_a.query(b, k=1)
    return (d1.mean() + d2.mean()) / 2


def main():
    cand_path, ref_path = sys.argv[1], sys.argv[2]
    ref = normalize(np.load(ref_path)["points"].astype(np.float64))
    ref_tree = cKDTree(ref)

    mesh = trimesh.load(cand_path, force="mesh")
    if hasattr(mesh, "area") and mesh.area > 0 and len(mesh.faces) > 0:
        pts = mesh.sample(N_SAMPLES)
    else:
        pts = np.asarray(mesh.vertices, dtype=np.float64)
    if len(pts) < 10:
        print("candidate mesh has too little geometry")
        print("SHAPE_SCORE: 0/10")
        return

    # accept either Z-up or Y-up candidate exports
    orientations = [pts, (pts[:, [0, 2, 1]] * np.array([1, -1, 1]))]
    best = np.inf
    for base in orientations:
        for mirror in (1, -1):
            for k in range(8):
                th = k * np.pi / 4
                rot = np.array([[np.cos(th), -np.sin(th), 0],
                                [np.sin(th), np.cos(th), 0],
                                [0, 0, 1]])
                p = normalize((base * np.array([mirror, 1, 1])) @ rot.T)
                best = min(best, chamfer(p, ref, ref_tree))

    frac = (BAD - best) / (BAD - GOOD)
    score = int(round(10 * min(1.0, max(0.0, frac))))
    print(f"chamfer distance (normalized): {best:.4f}")
    print(f"SHAPE_SCORE: {score}/10")


if __name__ == "__main__":
    main()

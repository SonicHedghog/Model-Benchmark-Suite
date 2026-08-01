#!/usr/bin/env python3
"""Print a side-by-side comparison table of result JSON files."""
import json
import sys

CATEGORIES = ["documents", "visual", "coding", "science_math", "other_modalities"]


def main():
    runs = []
    for path in sys.argv[1:]:
        with open(path) as f:
            runs.append(json.load(f))
    if not runs:
        print("usage: compare.py results/*.json")
        return
    name_w = max(len(r["model"]) for r in runs) + 2
    header = "model".ljust(name_w) + "".join(c.ljust(18) for c in CATEGORIES) + "overall"
    print(header)
    print("-" * len(header))
    for r in runs:
        row = r["model"].ljust(name_w)
        for c in CATEGORIES:
            cat = r["categories"].get(c)
            row += (str(cat["score"]) if cat and cat["score"] is not None else "-").ljust(18)
        row += str(r.get("overall", "-"))
        print(row)


if __name__ == "__main__":
    main()

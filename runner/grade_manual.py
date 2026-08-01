#!/usr/bin/env python3
"""Score a pre-recorded answers file (offline grading, no API calls).

Usage:
  python3 runner/grade_manual.py results/devin-baseline-answers.json \
      --out results/devin-baseline.json

Answers file format:
  {"model": "...", "answers": {"<item-id>": "<answer text>", ...},
   "manual_rubric_scores": {"<item-id>": 0|1|2}}
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_suite import CATEGORIES, ROOT, score_item  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("answers_file")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with open(args.answers_file) as f:
        data = json.load(f)
    answers = data["answers"]
    manual = data.get("manual_rubric_scores", {})

    results = {"model": data.get("model", "unknown"), "base_url": "offline", "categories": {}}
    for cat in CATEGORIES:
        with open(os.path.join(ROOT, "prompts", f"{cat}.json")) as f:
            suite = json.load(f)
        cat_items = []
        for item in suite["items"]:
            ans = answers.get(item["id"])
            if ans is None:
                cat_items.append({"id": item["id"], "answer": None,
                                  "score": 0.0, "note": "no answer"})
                continue
            if item["scoring"]["type"] == "rubric":
                if item["id"] in manual:
                    score, note = manual[item["id"]] / 2.0, "manual rubric"
                else:
                    score, note = None, "manual grading required"
            elif item["scoring"]["type"] == "agentic":
                agentic = data.get("manual_agentic_scores", {})
                if item["id"] in agentic and agentic[item["id"]] is not None:
                    score, note = float(agentic[item["id"]]), "validator score (0-1)"
                else:
                    score, note = None, f"run agentically, validate with {item['scoring']['validator']}"
            else:
                score, note = score_item(argparse.Namespace(judge_model=None), item, ans)
            cat_items.append({"id": item["id"], "answer": ans,
                              "score": score, "note": note})
        scored = [i["score"] for i in cat_items if i["score"] is not None]
        results["categories"][cat] = {
            "items": cat_items,
            "score": round(sum(scored) / len(scored), 3) if scored else None,
            "ungraded": sum(1 for i in cat_items if i["score"] is None),
        }
    graded = [c["score"] for c in results["categories"].values() if c["score"] is not None]
    results["overall"] = round(sum(graded) / len(graded), 3) if graded else None
    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)
    for k, v in results["categories"].items():
        print(k, v["score"])
    print("overall:", results["overall"])


if __name__ == "__main__":
    main()

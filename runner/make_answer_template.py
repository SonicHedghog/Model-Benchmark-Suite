#!/usr/bin/env python3
"""Emit an answers-file skeleton for agent-mode runs (e.g. a Devin session
answering the prompts itself, or a human copy-pasting prompts into any chat UI).

Usage:
  python3 runner/make_answer_template.py --model "my-model" --out answers.json

Fill in each empty "answers" value (image/audio items list the asset path to
open), then grade offline:

  python3 runner/grade_manual.py answers.json --out results/my-model.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_suite import CATEGORIES, ROOT  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    template = {"model": args.model, "answers": {}, "manual_rubric_scores": {},
                "_prompts": {}}
    for cat in CATEGORIES:
        with open(os.path.join(ROOT, "prompts", f"{cat}.json")) as f:
            suite = json.load(f)
        for item in suite["items"]:
            template["answers"][item["id"]] = ""
            meta = {"prompt": item["prompt"]}
            if item.get("image"):
                meta["image"] = item["image"]
            if item.get("audio"):
                meta["audio"] = item["audio"]
            if item["scoring"]["type"] == "rubric":
                meta["rubric"] = item["scoring"]["rubric"]
                template["manual_rubric_scores"][item["id"]] = None
            template["_prompts"][item["id"]] = meta
    with open(args.out, "w") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    print("template written to", args.out)


if __name__ == "__main__":
    main()

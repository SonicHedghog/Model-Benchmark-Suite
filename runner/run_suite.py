#!/usr/bin/env python3
"""Run the benchmark suite against any OpenAI-compatible chat endpoint.

Only uses the Python standard library (urllib), so it works without pip installs.

Examples:
  python3 runner/run_suite.py --base-url http://localhost:11434/v1 --model llama3.1:8b \
      --out results/llama3.1-8b.json
  python3 runner/run_suite.py --base-url https://api.openai.com/v1 --model gpt-4o-mini \
      --api-key $OPENAI_API_KEY --out results/gpt-4o-mini.json
"""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CATEGORIES = ["documents", "visual", "coding", "science_math", "logic", "three_d", "agentic_3d", "other_modalities"]


def chat(base_url, api_key, model, messages, temperature=0.0, timeout=300):
    body = {"model": model, "messages": messages, "temperature": temperature}
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 **({"Authorization": f"Bearer {api_key}"} if api_key else {})},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.load(r)
    return data["choices"][0]["message"]["content"]


def build_messages(item):
    parts = [{"type": "text", "text": item["prompt"]}]
    if item.get("image"):
        with open(os.path.join(ROOT, item["image"]), "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        parts.append({"type": "image_url",
                      "image_url": {"url": f"data:image/png;base64,{b64}"}})
    if item.get("audio"):
        with open(os.path.join(ROOT, item["audio"]), "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        parts.append({"type": "input_audio",
                      "input_audio": {"data": b64, "format": "wav"}})
    if len(parts) == 1:
        return [{"role": "user", "content": item["prompt"]}]
    return [{"role": "user", "content": parts}]


def norm(s):
    return re.sub(r"\s+", " ", s.strip().lower())


def last_number(s):
    nums = re.findall(r"-?\d[\d,]*\.?\d*", s.replace(",", ""))
    return float(nums[-1]) if nums else None


def extract_code(answer):
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", answer, re.S)
    return blocks[-1] if blocks else answer


def run_code_tests(answer, test_file):
    code = extract_code(answer)
    with tempfile.TemporaryDirectory() as td:
        with open(os.path.join(td, "solution.py"), "w") as f:
            f.write(code)
        try:
            env = {**os.environ, "PYTHONPATH": td}
            p = subprocess.run([sys.executable, os.path.join(HERE, "tests", test_file)],
                               cwd=td, env=env, capture_output=True, text=True, timeout=30)
            return (1.0, "OK") if p.returncode == 0 else (0.0, (p.stderr or p.stdout)[-500:])
        except subprocess.TimeoutExpired:
            return 0.0, "timeout"


def judge_rubric(args, item, answer):
    if not args.judge_model:
        return None, "manual grading required"
    prompt = (f"Grade this answer 0, 1, or 2 against the rubric. Reply with the digit only.\n"
              f"RUBRIC: {item['scoring']['rubric']}\n\nQUESTION:\n{item['prompt']}\n\nANSWER:\n{answer}")
    out = chat(args.judge_base_url or args.base_url, args.judge_api_key or args.api_key,
               args.judge_model, [{"role": "user", "content": prompt}])
    m = re.search(r"[012]", out)
    return (int(m.group()) / 2.0 if m else 0.0), f"judge said: {out.strip()[:100]}"


def score_item(args, item, answer):
    s = item["scoring"]
    t = s["type"]
    if t == "numeric":
        n = last_number(answer)
        ok = n is not None and abs(n - s["expected"]) <= s.get("tolerance", 0)
        return (1.0 if ok else 0.0), f"parsed={n}"
    if t == "exact":
        return (1.0 if norm(answer) == norm(s["expected"]) else 0.0), ""
    if t == "contains_all":
        missing = [e for e in s["expected"] if norm(e) not in norm(answer)]
        return (1.0 if not missing else 0.0), f"missing={missing}"
    if t == "regex":
        return (1.0 if re.search(s["expected"], answer, re.I) else 0.0), ""
    if t == "contains_any":
        return (1.0 if any(norm(e) in norm(answer) for e in s["expected"]) else 0.0), ""
    if t == "code_tests":
        return run_code_tests(answer, s["test_file"])
    if t == "rubric":
        return judge_rubric(args, item, answer)
    if t == "agentic":
        return None, f"agentic item — run via an agent, then validate with {s['validator']}"
    raise ValueError(t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", ""))
    ap.add_argument("--judge-base-url")
    ap.add_argument("--judge-model")
    ap.add_argument("--judge-api-key")
    ap.add_argument("--categories", default=",".join(CATEGORIES))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    results = {"model": args.model, "base_url": args.base_url, "categories": {}}
    for cat in args.categories.split(","):
        with open(os.path.join(ROOT, "prompts", f"{cat}.json")) as f:
            suite = json.load(f)
        cat_items = []
        for item in suite["items"]:
            print(f"[{item['id']}] ...", flush=True)
            try:
                answer = chat(args.base_url, args.api_key, args.model, build_messages(item))
                score, note = score_item(args, item, answer)
            except Exception as e:  # e.g. modality unsupported
                answer, score, note = None, 0.0, f"error/unsupported_modality: {e}"
            cat_items.append({"id": item["id"], "answer": answer,
                              "score": score, "note": note})
            print(f"  score={score} {note}")
        scored = [i["score"] for i in cat_items if i["score"] is not None]
        results["categories"][cat] = {
            "items": cat_items,
            "score": round(sum(scored) / len(scored), 3) if scored else None,
            "ungraded": sum(1 for i in cat_items if i["score"] is None),
        }
    graded = [c["score"] for c in results["categories"].values() if c["score"] is not None]
    results["overall"] = round(sum(graded) / len(graded), 3) if graded else None
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps({k: v["score"] for k, v in results["categories"].items()}, indent=2))
    print("overall:", results["overall"], "->", args.out)


if __name__ == "__main__":
    main()

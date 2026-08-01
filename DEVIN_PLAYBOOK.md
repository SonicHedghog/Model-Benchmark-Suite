# Playbook: Run the Model Benchmark Suite via Devin

Give a Devin session this repo plus one of the procedures below. Results land in
`results/<model>.json`; compare runs with `python3 runner/compare.py results/*.json`.

## Overview

Benchmark a model on 47 prompts across documents, visual, coding, science/math,
logic, 3D, agentic 3D (Blender), and other modalities, then commit the graded
results to this repo.

## Procedure A — Benchmark a model behind an API

Use when the model is reachable via an OpenAI-compatible endpoint (Ollama,
LM Studio, llama.cpp server, vLLM, OpenAI, OpenRouter...). Provide Devin the
base URL, model name, and an API key secret if needed.

1. Clone this repo and run `python3 runner/make_assets.py` if `assets/` is missing.
2. Run:
   ```bash
   python3 runner/run_suite.py --base-url <BASE_URL> --model <MODEL> \
       --api-key $API_KEY --out results/<MODEL>.json
   ```
3. Grade any `rubric` items left ungraded: read the item's `rubric` in
   `prompts/*.json`, judge the recorded answer 0/1/2, and fold the score in
   (or pass `--judge-model`/`--judge-base-url` to auto-judge).
4. Print `python3 runner/compare.py results/*.json` and commit the new results
   file on a branch; open a PR.

Note for local models on the user's machine: Devin's VM cannot reach your
localhost. Expose the endpoint with a tunnel (e.g. `ngrok http 11434` or
`cloudflared tunnel --url http://localhost:11434`) and give Devin the public URL.

## Procedure B — Devin (or any agent) takes the test itself

Use to benchmark the agent rather than an API.

1. Generate a template:
   ```bash
   python3 runner/make_answer_template.py --model "devin-<date>" --out my-answers.json
   ```
2. Answer every item in `_prompts` honestly, WITHOUT looking at `prompts/*.json`
   scoring fields, the tests in `runner/tests/`, or existing results files.
   For items with an `image`/`audio` key, open the asset file and answer from it.
   Write each answer into `answers`.
3. Self-grade the two rubric items per their rubric (0/1/2) into
   `manual_rubric_scores` (or have the user grade them).
4. Grade and save:
   ```bash
   python3 runner/grade_manual.py my-answers.json --out results/<model>.json
   python3 runner/compare.py results/*.json
   ```
5. For the agentic item `a3d-01-blender-v8`: install Blender (`sudo apt-get install -y blender`),
   build the V8 engine scene per the prompt (Blender MCP server or `blender -b --python`),
   validate with `blender -b v8_engine.blend --python runner/validate_v8.py`, and record
   score/10 in `manual_agentic_scores`. If Blender/tool access is unavailable, leave it
   ungraded and note why.
6. Commit the results file on a branch and open a PR (do not commit `my-answers.json`).

## Forbidden Actions

- Never peek at `scoring` blocks, `runner/tests/`, or prior `results/*.json`
  before answering in Procedure B.
- Do not edit prompts, tests, or expected answers to improve a score.

## Specification / Advice

- Temperature 0 is used by the runner for reproducibility.
- Items whose modality the model rejects (image/audio) score 0 and are noted
  `unsupported_modality` — report them separately in the PR description.

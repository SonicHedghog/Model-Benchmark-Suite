# Local Model Benchmark Suite

A compact, self-contained suite of 49 prompts for evaluating LLMs across 8 categories:

| Category | File | # Items | Modality |
|---|---|---|---|
| Documents | `prompts/documents.json` | 6 | text |
| Visual | `prompts/visual.json` | 6 | image + text |
| Coding | `prompts/coding.json` | 7 | text (auto-graded by unit tests) |
| Science & Math | `prompts/science_math.json` | 7 | text |
| Logic | `prompts/logic.json` | 7 | text |
| 3D Visualization & Creation | `prompts/three_d.json` | 7 | text + image (mesh generation auto-validated by geometry checks) |
| Agentic 3D | `prompts/agentic_3d.json` | 3 | agentic (Blender MCP or headless Blender) |
| Other Modalities | `prompts/other_modalities.json` | 6 | audio / structured data / ASCII / base64 |

## Scoring

Each item has a `scoring` block:
- `exact` — normalized string equality with `expected`
- `regex` — answer must match the regex (case-insensitive)
- `contains_all` / `contains_any` — answer must contain (all/any of) the listed substrings (case-insensitive)
- `numeric` — parsed number within `tolerance` of `expected`
- `code_tests` — extract the code block from the answer, run the paired test file in `runner/tests/`
- `rubric` — 0–2 human/judge-graded against `rubric` criteria
- `agentic` — the model (as an agent) performs a task with external tools; graded by the item's validator scripts. The three Blender items (`a3d-01` V8 engine, `a3d-02` Eiffel Tower, `a3d-03` Classic Sonic) are built via the Blender MCP server or `blender -b --python`, then scored with a structural validator run inside Blender (`runner/validate_v8.py`, `runner/validate_eiffel.py`, `runner/validate_sonic.py` — each out of 10). The Eiffel and Sonic items are ADDITIONALLY scored on shape against real reference models (`runner/compare_mesh.py <export.obj> assets/ref3d/<ref>_points.npz` — normalized Chamfer distance vs point clouds sampled from a CC-BY Poly Pizza Eiffel Tower and a low-poly Classic Sonic; see `assets/ref3d/ATTRIBUTION.md`); their final score = (structure + shape) / 20. Record scores (0–1) in `manual_agentic_scores`. Skipped (left ungraded) by the API runner — requires an agent with tool access, Blender (`apt install blender`), and `pip install trimesh scipy numpy` for the shape comparison.

Score per item is 0 or 1 (rubric items: score/2). Category score = mean. Overall = mean of category scores.

## Running

Against any OpenAI-compatible endpoint (Ollama, LM Studio, llama.cpp server, vLLM, OpenAI, etc.):

```bash
python3 runner/run_suite.py \
  --base-url http://localhost:11434/v1 \
  --model llama3.1:8b \
  --out results/llama3.1-8b.json
```

- Vision items send the image as a base64 `image_url` part; if the model rejects images the item is scored 0 and marked `unsupported_modality`.
- Audio items send base64 WAV via `input_audio`; same fallback.
- `--api-key` (or `OPENAI_API_KEY` env) for hosted endpoints.
- `--judge-base-url/--judge-model` optionally auto-grades `rubric` items with a judge model; otherwise rubric items are left for manual grading (`runner/grade_manual.py`).

Compare runs:

```bash
python3 runner/compare.py results/*.json
```

## Running through Devin

See `DEVIN_PLAYBOOK.md`: point a Devin session at this repo to benchmark either
an API-reachable model (Procedure A) or the agent itself (Procedure B, via
`runner/make_answer_template.py` + `runner/grade_manual.py`).

## Baseline

`results/devin-baseline.json` contains Devin's own answers/scores for comparison.

## Assets

Images and audio in `assets/` are generated deterministically by `runner/make_assets.py` (matplotlib/PIL/wave). Re-run it to regenerate.

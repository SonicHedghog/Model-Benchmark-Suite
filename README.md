# Local Model Benchmark Suite

A compact, self-contained suite of 46 prompts for evaluating LLMs across 7 categories:

| Category | File | # Items | Modality |
|---|---|---|---|
| Documents | `prompts/documents.json` | 6 | text |
| Visual | `prompts/visual.json` | 6 | image + text |
| Coding | `prompts/coding.json` | 7 | text (auto-graded by unit tests) |
| Science & Math | `prompts/science_math.json` | 7 | text |
| Logic | `prompts/logic.json` | 7 | text |
| 3D Visualization & Creation | `prompts/three_d.json` | 7 | text + image (mesh generation auto-validated by geometry checks) |
| Other Modalities | `prompts/other_modalities.json` | 6 | audio / structured data / ASCII / base64 |

## Scoring

Each item has a `scoring` block:
- `exact` — normalized string equality with `expected`
- `regex` — answer must match the regex (case-insensitive)
- `contains_all` / `contains_any` — answer must contain (all/any of) the listed substrings (case-insensitive)
- `numeric` — parsed number within `tolerance` of `expected`
- `code_tests` — extract the code block from the answer, run the paired test file in `runner/tests/`
- `rubric` — 0–2 human/judge-graded against `rubric` criteria

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

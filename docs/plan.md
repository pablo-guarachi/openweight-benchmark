# Plan — openweight-benchmark

Created: 2026-10-20 · Status: **Phase 2 completed 2026-10-21** → conclusions in [conclusions-track-a.md](conclusions-track-a.md), numbers in `results/SUMMARY.md`. Next: Phase 3 (rented GPUs). Ollama upgraded 0.21 → 0.40.7.

## Goal
Test open-weight models and their real capabilities, to understand **which model is needed for which task**
and therefore **which hardware is needed** to run it. Two tracks with the **same test set**, so the results are comparable:

| Track | Where | Models |
|---|---|---|
| **A — Local** | PC: RTX 3060 12GB VRAM, 16GB RAM, i7-8700K | Up to ~14B quantised (fully in VRAM) |
| **B — Rented GPUs** | RunPod / Vast.ai / similar, by the hour | 27B → 120B+ and large MoE, concurrency tests |

## Capabilities to test (common suite)
Decisions 2026-10-20: languages **IT + EN + ES** · images **scanned documents + charts/tables** · documents **including long ones (30-100 pages)** · grading: **Claude reads and grades with a 1-5 rubric, the author reviews the grades**.

| # | Capability | What it measures | Evaluation |
|---|---|---|---|
| 1 | Speed | generation tok/s, time to first token, short and long prompts, 1 vs N users | Automatic |
| 2 | Conversation | multi-turn dialogue: context memory, consistency, natural tone | 1-5 rubric |
| 3 | Document analysis | questions on the document, data extraction (dates, amounts, names), correct source; 1-10 pages and 30-100 pages | Automatic (expected answers) + rubric |
| 4 | Summaries | faithfulness, completeness, no inventions, required length | 1-5 rubric |
| 5 | Hallucinations | questions with no answer in the text, non-existent facts, "I don't know" when needed, wrong refusals | Automatic + rubric |
| 6 | Images | photographed/scanned documents (invoices, forms, contracts) and charts/tables: text reading, data extraction, description | Automatic (expected values) + rubric |
| 7 | Complex writing | reports, formal emails, proposals, long structured texts with constraints | 1-5 rubric |
| 8 | Multilingual | same tasks in IT/EN/ES, translation, answers in the question's language | 1-5 rubric per language |
| 9 | Tool calling + JSON | picks the right function with the right arguments; JSON output valid against a schema | Automatic |
| 10 | Reasoning + code | multi-step problems, calculations, simple scripts, SQL | Automatic (exact answer / tests) |

Technical metrics for every test: tokens/s · time to first token · VRAM/RAM used · maximum useful context.
Note: capability 6 excludes text-only models (gpt-oss, Llama 3.1, Mistral Nemo); for them the cell stays "n/a".

## Phase 0 — Setup
- [x] Project folder
- [x] Up-to-date research: open-weight models relevant in October 2026 → [model-research-2026-10.md](model-research-2026-10.md)
- [x] Models stay on C: (D: is a spinning disk, loading too slow). Clean-up with `ollama rm` after each group of tests
- [x] Python environment (`.venv`: openai, pyyaml, httpx)
- [x] Runner `scripts/run.py` tested on `qwen3.5:9b` with `benchmark/smoke.yaml` (1 and 3 users)

### Operating rules (from the 2026-10-20 trial run)
- **Before every local test: close other GPU-heavy apps (a dictation app and the browser).** They take ~4 GB of VRAM; with them open the 9B ended up 27% on CPU → 19 tok/s instead of 45. The script records `vram_before_mb`: it must be < 1000.
- **Thinking off by default** (`reasoning_effort: none`, works on Ollama and vLLM). `--think` to measure the cost/benefit of reasoning.
- **Ollama serves 1 request at a time** by default: with 3 users the third waits ~4 s. For the local concurrency test set `OLLAMA_NUM_PARALLEL` in Ollama's environment (Windows user variable + restart). The reliable concurrency figure remains the Track B one with vLLM.
- Reference: `qwen3.5:9b` on RTX 3060 = **~45 tok/s**, 8.9 GB peak VRAM, context 8192.

## Phase 1 — Test suite
- [x] Suite: 86 tests in `benchmark/01..10-*.yaml` (IT/EN/ES), expected answers from facts.yaml
- [x] Test material → `corpus/` (facts.yaml = ground truth; 11 short IT/EN/ES documents, a long ~30k-token manual with 8 needles, 5 images). See `corpus/README.md`
- [x] Automatic grading rules (`check:`) + tests to grade by hand (`grade: true`)
- [x] Runner script: OpenAI-compatible endpoint, N users, tok/s, TTFT, VRAM → `scripts/run.py`
- [x] `scripts/evaluate.py` (automatic checks + review sheet) · `scripts/report.py` (SUMMARY.md) · `scripts/run_all.sh` (Track A batch)
- [x] Output in `results/local/<model>/`, manual grades in `results/scores/<model>.yaml`, summary in `results/SUMMARY.md`

## Phase 2 — Track A (local) — COMPLETED 2026-10-21
10 models × 86 tests (+ speed at 4 users + thinking on/off on 2 models). Manual grades in `results/scores/`.
- [x] qwen3.5:9b · qwen3.5:4b · gemma4:12b · gemma4:26b (MoE, offload) · gemma4:e4b · gemma4:e2b · llama3.1:8b · mistral-nemo · gpt-oss:20b (offload, think-level low)
- [x] Offload: gemma4:26b holds up (29-36 tok/s, 3.8B active); mistral-nemo at 30k ctx collapses to 1.7 tok/s
- [x] Thinking on/off: not worth it (qwen 9B: 43→31 correct, 5→30 s per answer)
- [ ] Not done: Q4 vs Q8 quantisation comparison; QLoRA fine-tuning (postponed: no use case required it)

## Phase 3 — Track B (rented GPUs)
- [ ] Budget rule: no spend without an explicit go-ahead; estimate hours × price per hour before each session
- [ ] Models: qwen3.8:27b, qwen3.6:35b-a3b, gemma4:31b, gemma4:26b (full VRAM), mistral-small 24B; then gpt-oss:120b / qwen3.5:122b on 96 GB
- [ ] Key question: do the 27-35B models fix the tier's errors (relative dates, leave, conversations with invented promises) or do they remain "system" errors?
- [ ] Same suite via vLLM
- [ ] Concurrency test: 1 / 5 / 10 / 25 simultaneous users
- [ ] VRAM tiers to try: 24-32GB / 48GB / 80-96GB

## Phase 4 — Conclusions
- [ ] Map capability → minimum model that satisfies it
- [ ] Map model → minimum hardware (with simultaneous users)

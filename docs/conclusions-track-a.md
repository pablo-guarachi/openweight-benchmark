# Conclusions — Track A (local, RTX 3060 12 GB)

Date: 2026-10-21 · Suite: 86 tests (`benchmark/`), Rossi Impianti corpus (`corpus/`) · Full numbers: [results/SUMMARY.md](../results/SUMMARY.md) · Grades and notes per test: `results/scores/*.yaml`

## In one line
**On a 12 GB card, Qwen 3.5 9B and Gemma 4 12B are already usable for a business assistant working on documents (97% and 94% of automatic checks, grade 4.3/5); the 2024 models (Llama 3.1, Mistral Nemo) are not. The bottleneck is not quality but concurrency: with 4 users at once the first word arrives after 17 s.**

## Ranking (10 models)

| Rank | Model | Auto | Grade | VRAM | tok/s | Verdict |
|---|---|---|---|---|---|---|
| 1 | **qwen3.5:9b** | 97% | 4.3 | 8.2 GB | 52 | The most reliable on documents, hallucinations, JSON, images. Weak in "operator" conversations: promises invented interventions and timings |
| 2 | **gemma4:12b** | 94% | 4.3 | 9.7 GB | 46 | Excellent writing and multilingual. Serious flaw: with an Italian system prompt it answers in Italian even to English questions |
| 3 | **gemma4:26b** (MoE, 3.8B active) | 94% | 4.3 | 11.6 GB* | 29–36 | Same quality as the 12B while running half on CPU. On a 16–24 GB GPU it would be the fastest in this tier |
| 4 | qwen3.5:4b | 88% | 3.9 | 5.8 GB | 76 | Surprising: reads images, handles JSON and tools. Loses on calculations and long writing |
| 5 | gpt-oss:20b (think low) | 85% | 3.8 | 10.8 GB* | 40 | Excellent summaries and structured writing (5/5). But **confidently invents concrete details**: technician names, ticket numbers, URLs, phone numbers, shops. Always reasons (ignores `think=false`): at the default level 15 empty answers out of 76; with `low` it works. Does not fit in 12 GB |
| 6 | mistral-nemo 12B | 85% | 3.8 | 10.5 GB | 43 | Natural, concise Italian. But invents facts, ignores "answer in Spanish", weak tool calling, **collapses to 1.7 tok/s with 30k tokens of context** |
| 7 | gemma4:e4b (4.5B) | 83% | 3.8 | 5.8 GB | 102–122 | Very fast, reads sharp images. Errors on figures (IBAN, sums from a chart); one unjustified refusal |
| 8 | gemma4:e2b (2.3B) | 78% | 3.5 | 5.0 GB | 121 | Text OK for simple tasks; **cannot read images** ("table of numbers"); switches to French mid-answer |
| 9 | llama3.1:8b | 74% | 3.2 | 10.2 GB | 60 | 2024 generation: invents names and places, refuses a harmless rewrite, tool calls with swapped arguments |
| – | gemma4:latest (E4B, 6-month-old blob) | 77% | 3.6 | 5.5 GB | 74 | Old blob without vision: row to ignore, replaced by gemma4:e4b |

\* partly on CPU (the model does not fit in VRAM)

## What each tier can do (task → minimum model map)

| Task | Minimum model that does it well locally | Notes |
|---|---|---|
| Questions on short documents (1–10 pages), data extraction, citing the source | qwen3.5:4b | All 9B+ are at 100% |
| "I don't know" when the fact is missing, correcting false premises | qwen3.5:9b / gemma4:12b | The 4B models manage it but with less confidence; the 2B models confuse entities (Idrotec/Valvex) |
| Long documents (30k tokens, needle in a haystack) | qwen3.5:9b, gemma4:12b/26b | 100% on the needles. Cost: 17–34 s before the first word on the 3060. Mistral Nemo unusable beyond ~16k |
| Faithful summaries | qwen3.5:9b, gemma4:12b/26b, gpt-oss:20b (5/5) | Grade 4–5. The small models omit things (RIDDOR, penalty) |
| Reading images: invoices, forms, rating plates, charts | qwen3.5:9b (10/10), gemma4:12b (10/10), qwen3.5:4b (10/10) | gemma4:26b gets one IBAN digit wrong; e4b gets sums wrong; e2b cannot read |
| Structured JSON, classification with enums | qwen3.5:4b and up | 8/9 for all Qwen/Gemma; Nemo and Llama fail |
| Tool calling (choice of function + arguments) | qwen3.5:9b, gemma4:12b | See "common errors": everyone gets relative dates wrong |
| Business writing IT/EN/ES | gemma4:12b (4.0), qwen3.5:9b (4.3) | Gemma tends to give 3 versions when you ask for one |
| Multilingual, translation | gemma4:12b, qwen3.5:9b (4.6) | Gemma: high quality but unstable answer language |
| Customer-service operator conversation | **none is ready without guardrails** | All (except gemma4:26b and gemma4:e4b/latest) promise engineers "within the hour", refunds, replacement chillers |
| Calculations and dates | gemma4:26b / qwen3.5:9b (reasoning 88–100%) | but see below |

## Errors common to (almost) all models — to be solved by the system, not the model

1. **Relative dates**: "Thursday of this week" given "today is Monday 20 October" → 10 models out of 10 get it wrong (22, 23, 25, 29 October, or ask for the date). **In the product: the backend always passes absolute dates and a calendar; the model must not compute days.** (Note added later: the test premise itself is wrong — 20 October 2026 is a Tuesday — so answers of 22 October are defensible; see `docs/failure-modes.md` and the README.)
2. **45 days from 15 June = 30 July**: almost all say 29 July or 10/30 August. Same rule: date arithmetic outside the model (a `calcola_data` tool).
3. **Answer language**: with an Italian system prompt, Gemma 4 (all sizes), Qwen 4B, Llama and gpt-oss answer English questions in Italian. Qwen 9B and Nemo do not. **In the product: system prompt in the user's language, or an explicit per-request instruction ("Answer in English").**
4. **Promises and invented details in conversations**: without an explicit list of what the assistant can and cannot do, the models play the human operator ("I have sent an engineer"); gpt-oss goes as far as inventing ticket numbers, apps and URLs. **In the product: a system prompt with the limits of action + real tools (crea_ticket) instead of phrases.**
5. **Leave (5-day carry-over, 25+5−9 = 21)**: only qwen3.5:9b gets there. Multi-step reasoning on rules: a real limit of the ≤12B tier.
6. **"Three options instead of one"** (Gemma): fixed with "answer with a single version" in the prompt.

## Thinking (explicit reasoning): not worth it locally

| Model | Correct off → on | Mean time per answer |
|---|---|---|
| qwen3.5:9b | 43/44 → **31/44** | 4.9 s → **30.5 s** (14 empty answers: the reasoning exhausts 3000 tokens) |
| gemma4:12b | 40/44 → 38/44 | 4.5 s → 11.6 s |

For business tasks on documents, thinking **improves nothing and costs 2.5–6× in time**. Keep it off by default (`reasoning_effort: none` / `think: false`), on only for specific reasoning tasks. gpt-oss always reasons: at the default level it exhausts the budget (39/68 correct, 15 empty answers), with `low` it reaches 58/68.

## Speed and hardware: what the 3060 says

- **1 user**: 9–12B at 46–52 tok/s = fluid experience (faster than reading). 4B at 76–120 tok/s.
- **Context reading**: 1,100–1,800 tokens/s on the 9–12B models. A 10-page contract (~10k tokens) = 6–10 s of waiting before the first word; the 30k manual = 17–34 s. **Long documents need RAG (retrieving only the relevant passages), not the whole document in the prompt.**
- **4 users at once**: Ollama serves one request at a time → mean TTFT 10–18 s, server throughput 27–47 tok/s in total. More users need (a) `OLLAMA_NUM_PARALLEL` or vLLM and (b) VRAM for each user's context cache: the real constraint for a small multi-user setup.
- **CPU offload**: gemma4:26b MoE holds up (29–36 tok/s) because it has 3.8B active; dense mistral-nemo 12B with 30k context collapses to 1.7 tok/s. **MoE models are the key to cheap hardware.**
- **Shared VRAM**: a browser and a dictation app took 4 GB and halved the speed. On a dedicated server the problem does not exist; on an office PC it does.

## Implications for Track B

1. To test on rented GPUs (24–32 GB): **qwen3.8:27b**, **qwen3.6:35b-a3b**, **gemma4:31b**, **gemma4:26b fully in VRAM**, mistral-small 24B. Key question: do the 27–35B models fix the tier's weaknesses (leave, dates, conversations) or do they remain "system" errors?
2. Concurrency with vLLM: 1/5/10/25 users on the same speed tests, to size the hardware for 5–10 concurrent users.
3. Hypothesis to verify: for 2–3 concurrent users the minimum is a 16–24 GB GPU + gemma4:26b or qwen3.5:9b + RAG + tools for dates/calendar. Not a 12 GB card: with 4 users it already queues.
4. For images (invoices, forms) the 9–12B models are enough: no need to go up in size for OCR.

## Method and limits
- Grader: Claude (1–5 grades with a fixed rubric), one run per test, temperature 0.2, 8k context (40k for the long tests), thinking off, Ollama 0.40.7, default Q4_K_M quantisation.
- Documents are passed whole in the prompt (no retrieval): this measures the model's capability, not a RAG system's.
- The automatic checks are strings/regexes: a model that answers correctly in a language other than the expected one can be marked "failed" (counted as a defect deliberately, because in the product it is one).
- The "gemma4:latest" test was run on a 6-month-old blob without vision: kept to document the incident, not for the ranking.

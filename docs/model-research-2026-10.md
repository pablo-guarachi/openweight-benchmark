# Research — relevant open-weight models (October 2026)

Date: 2026-10-20. Primary sources: official Ollama pages (tags, sizes, context) + model cards reported on HN.
Benchmark numbers come from blogs and threads: indicative, not truth. **Our suite exists precisely to replace them with our own measurements.**

## Landscape by family

| Family | Local sizes | Notes |
|---|---|---|
| **Qwen 3.5** (Feb-Mar 2026) | 0.8B, 2B, 4B, 9B, 27B dense · 35B-A3B, 122B-A10B MoE · 397B-A17B | Apache 2.0, 256K context, text+images. The small ones are considered the strongest in their class (tool use, RAG) |
| **Qwen 3.6** (Apr 2026) | 27B dense, 35B-A3B | Improvements in agentic coding and thinking |
| **Qwen 3.8** (Aug 2026) | 27B dense · Flash-Next 125B-A6B (not on Ollama at the moment) | Thinking on by default, can be disabled per request |
| **Gemma 4** (Apr 2026; 12B June) | E2B, E4B, 12B, 26B-A4B MoE, 31B dense | Google, 128K/256K context, multimodal (E-series also audio). Reports of tool calling being less reliable than Qwen |
| **gpt-oss** (OpenAI) | 20B (14GB), 120B (65GB) | Apache 2.0, 128K, reasoning. 120B = reference for its tier in Track B |
| **Mistral** | Nemo 12B, Small 3.2 24B · Medium 3.5 128B · Large 4 1.05T-A52B | Small 3.2: good tool calling, European (useful for Italian?). Large 4 out of reach |
| **Llama** (Meta) | 3.1 8B, 3.3 70B, 4 Scout 109B-A17B, 4 Maverick | Broad ecosystem but non-Apache licence; quality overtaken by Qwen/Gemma in recent comparisons |
| **GLM 5.x / MiniMax M3 / Kimi K3 / DeepSeek V4** | 400B-2.8T | Open frontier, but they need clusters: outside our target hardware range |

## Reported numbers (model cards via HN, not ours)

| Model | MMLU-Pro | GPQA | LiveCodeBench | TAU2 (tool) | MMMLU (multiling.) |
|---|---|---|---|---|---|
| Gemma 4 31B | 85.2 | 84.3 | 80.0 | 76.9 | 88.4 |
| Gemma 4 26B-A4B | 82.6 | 82.3 | 77.1 | 68.2 | 86.3 |
| Gemma 4 E4B | 69.4 | 58.6 | 52.0 | 42.2 | 76.6 |
| Qwen 3.5 27B | 86.1 | 85.5 | 80.7 | 79.0 | 85.9 |
| Qwen 3.5 35B-A3B | 85.3 | 84.2 | 74.6 | 81.2 | 85.2 |
| Qwen 3.5 122B-A10B | 86.7 | 86.6 | 78.9 | 79.5 | 86.7 |
| gpt-oss-120B | 80.8 | 80.1 | 82.7 | – | 78.2 |

Reading: **the 27-35B tier is already close to the 120B models** on benchmarks. If our suite confirms it, a 32-48GB VRAM tier covers almost everything; the 120B is needed only for high concurrency or special cases.

Speed reported on an RTX 4090 24GB, Q4: Gemma 4 26B-A4B ~150 tok/s · Qwen 3.5 35B-A3B ~100 tok/s · Gemma 4 31B ~5 tok/s (does not fit in VRAM → collapse). Confirms that **MoE models are the key to cheap hardware**.

## Candidates — Track A (RTX 3060 12GB)

Constraint: ≤ ~10 GB for the model in Q4, to leave room for the context.

| Model | Ollama tag | Download | Why |
|---|---|---|---|
| Qwen 3.5 9B | `qwen3.5:9b` | 6.6-7.6GB | Already pulled. Main candidate of the tier |
| Qwen 3.5 4B | `qwen3.5:4b` | 3.3-4GB | Low end: how much does it lose? |
| Gemma 4 12B | `gemma4:12b` | 7.7-8GB | Direct rival of the 9B, 256K context |
| Gemma 4 E4B | `gemma4:e4b` | 6.6-9.5GB | Already pulled (`latest`). Audio+images |
| Gemma 4 E2B | `gemma4:e2b` | 4.6-7.5GB | Already pulled. Low reference |
| Llama 3.1 8B | `llama3.1:8b` | 4.9GB | Already pulled. "Old generation" reference |
| Mistral Nemo 12B | `mistral-nemo` | 7GB | European, to be checked on Italian |
| gpt-oss 20B | `gpt-oss:20b` | 14GB | WARNING: does not fit: offload test (how much speed drops) |
| Gemma 4 26B-A4B | `gemma4:26b` | 16-19GB | WARNING: does not fit: MoE with offload, maybe acceptable thanks to 3.8B active |

To drop from the tests: `llama3:latest` (superseded), `medgemma:4b` (specialist, out of scope).

## Candidates — Track B (rented GPUs, vLLM)

| VRAM tier | Models | Typical GPU | Reported rental price |
|---|---|---|---|
| 24-32GB | Qwen 3.8 27B, Qwen 3.6 35B-A3B, Gemma 4 26B-A4B, Gemma 4 31B, Mistral Small 3.2 24B | RTX 5090 32GB | ~$0.7-1.2/h (RunPod), ~$0.6-0.9/h (Vast) |
| 80-96GB | gpt-oss 120B, Qwen 3.5 122B-A10B, Llama 4 Scout, Mistral Medium 3.5 (tight) | RTX Pro 6000 96GB · H100 80GB | Pro 6000 ~$2.5/h · H100 ~$2.5-4/h |
| Concurrency | the best of the 27-35B tier with 1/5/10/25 users | RTX 5090 then Pro 6000 | as above |

Spend estimate for Track B: ~10 h on a 5090 + ~6 h on 96GB ≈ **$30-40 in total**. To be confirmed before each session.

## Choices to make
- Qwen 3.5 vs 3.6 vs 3.8 at 27B: same size, three versions. In Track B try all three on a subset of the suite, then keep the best.
- Italian: no source measures it. It will be a distinctive point of our suite.

## Sources
- Ollama: [gemma4](https://ollama.com/library/gemma4) · [qwen3.5](https://ollama.com/library/qwen3.5) · [qwen3.6](https://ollama.com/library/qwen3.6) · [qwen3.8](https://ollama.com/library/qwen3.8) · [gpt-oss](https://ollama.com/library/gpt-oss)
- [HN: consolidated Gemma 4 vs Qwen 3.5 table](https://news.ycombinator.com/item?id=47616761)
- [betterclaw: Gemma 4 vs Qwen 3.5/3.6/3.8](https://www.betterclaw.io/blog/gemma-4-vs-qwen-3-5) (updated 2026-09-29)
- [bentoml: open-source LLMs 2026](https://www.bentoml.com/blog/navigating-the-world-of-open-source-large-language-models) · [morphllm](https://www.morphllm.com/best-open-source-llm) · [digitalapplied: self-hosting guide](https://www.digitalapplied.com/blog/self-hosting-open-weight-llms-2026-deployment-decision-guide)
- GPU prices: [gpuperhour.com](https://gpuperhour.com/) · [guptadeepak: 7 providers](https://guptadeepak.com/tools/top-7-gpu-cloud-ai-compute-providers-2026/) · [spheron: RunPod vs Vast](https://www.spheron.network/blog/runpod-vs-vastai-2026/)

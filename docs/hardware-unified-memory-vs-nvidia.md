# Hardware: unified memory (AMD Strix Halo / Mac) vs NVIDIA GPUs

Date: 2026-10-22 · Origin: evaluation of an AMD Ryzen AI Halo offer (192 GB, $7,299) and UK alternatives (Framework Desktop 64/128 GB £1,959/£3,449, Minisforum MS-S1 MAX 128 GB £3,399, GMKtec EVO-X2). Prices not verified by us.

## The rule that decides everything: memory bandwidth, not GB
Generation speed for one user ≈ memory bandwidth ÷ GB read per token (active weights). Consistent with our measurement: RTX 3060 (360 GB/s) → qwen3.5:9b Q4 at 52 tok/s.

| Hardware | Bandwidth | 27B dense Q4 (~17 GB) | MoE 35B-A3B / Gemma 26B-A4B |
|---|---|---|---|
| RTX 3060 12 GB (measured) | 360 GB/s | does not fit | 29–36 tok/s (half on CPU) |
| Ryzen AI Max+ 395/495 (Strix Halo) | ~256 GB/s | ~12–15 tok/s | ~40–60 tok/s |
| Mac Studio M3 Ultra | ~820 GB/s | ~40 tok/s | 100+ tok/s |
| RTX 5090 32 GB | 1,800 GB/s | ~60–80 tok/s | ~150 tok/s |
| RTX Pro 6000 96 GB | 1,800 GB/s | ~60–80 tok/s + cache for many users; the 120B MoE models fit | |

Estimates from bandwidth; to be verified in Track B.

## The second, ignored number: context reading (prefill)
It depends on compute, not memory. Measured on the 3060: 1,100–1,800 tokens/s → 6–10 s for a 10-page contract, 17–34 s for 30k tokens. The Strix Halo iGPU has less compute than a 3060: with RAG on long documents the waits double. This is the main weakness of unified memory for a "documents" assistant.

## Conclusions
- Unified memory = running huge models (70B–120B MoE) for **one** user. Not for 5–10 simultaneous requests with long documents.
- For a **personal lab**: an RTX 5090 32 GB (or a used 3090 24 GB) beats Strix Halo on everything except the >70B models. Strix Halo 128 GB only if you want the 120B models at home (gpt-oss-120b ~30 tok/s reported). vLLM on ROCm/Strix Halo is immature; llama.cpp is OK.
- "50 employees ≠ 50 simultaneous requests": typically 2–5, with peaks. Measured: 4 users queued on Ollama/3060 = 17 s to the first word.
- **No purchase before Track B** (a rented RTX 5090 session, ~$10): it gives tokens per request, latency at N users, real prefill.

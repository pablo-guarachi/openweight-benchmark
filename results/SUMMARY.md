# Results — Track A (local, RTX 3060 12GB)

Auto = % of tests with automatic checks passed · Grade = mean manual grade 1-5 (rubric in evaluate.py) · n/a = not applicable

| Model | conversation | documents | summaries | hallucinations | images | writing | multilingual | tools | reasoning | **Auto total** | **Mean grade** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma4_12b | 100% · 4.2 | 89% · 2.5 | 100% · 4.5 | 100% · 4.3 | 100% · 5.0 | 83% · 4.0 | 100% · 4.6 | 89% · 4.0 | 88% · 4.0 | **94%** (73/78) | **4.3** (n=41) |
| gemma4_26b | 100% · 4.3 | 100% · 4.5 | 100% · 4.5 | 100% · 4.0 | 80% · 5.0 | 83% · 3.7 | 100% · 4.4 | 89% · 4.0 | 88% · 5.0 | **94%** (73/78) | **4.3** (n=41) |
| gemma4_e2b | 100% · 4.0 | 89% · 4.5 | 100% · 3.8 | 89% · 3.4 | 10% · 1.0 | 100% · 4.2 | 88% · 3.6 | 89% · 5.0 | 62% · 2.0 | **78%** (61/78) | **3.5** (n=41) |
| gemma4_e4b | 100% · 4.2 | 89% · 4.0 | 100% · 4.0 | 89% · 3.6 | 70% · 3.8 | 67% · 3.0 | 88% · 4.0 | 89% · 5.0 | 62% · 5.0 | **83%** (65/78) | **3.8** (n=41) |
| gemma4_latest | 100% · 4.2 | 83% · 5.0 | 100% · 3.8 | 89% · 3.4 | 10% · 1.0 | 83% · 3.7 | 88% · 3.9 | 89% · 5.0 | 75% · 4.0 | **77%** (60/78) | **3.6** (n=41) |
| gpt-oss_20b | 100% · 3.0 | 72% · 4.0 | 100% · 5.0 | 78% · 4.0 | n/a | 100% · 3.5 | 88% · 3.8 | 89% · 4.0 | 88% · 2.0 | **85%** (58/68) | **3.8** (n=37) |
| llama3.1_8b | 100% · 3.3 | 67% · 2.5 | 100% · 3.3 | 89% · 4.0 | n/a | 67% · 3.3 | 75% · 3.0 | 67% · 1.0 | 50% · 2.0 | **74%** (50/68) | **3.2** (n=37) |
| mistral-nemo | 75% · 3.5 | 89% · 3.5 | 100% · 3.5 | 89% · 4.6 | n/a | 83% · 3.7 | 88% · 4.1 | 67% · 2.0 | 88% · 2.0 | **85%** (58/68) | **3.8** (n=37) |
| qwen3.5_4b | 100% · 3.7 | 83% · 5.0 | 100% · 3.7 | 100% · 3.9 | 100% · 4.8 | 67% · 3.2 | 88% · 4.1 | 89% · 4.0 | 75% · 2.0 | **88%** (69/78) | **3.9** (n=41) |
| qwen3.5_9b | 75% · 3.2 | 100% · 5.0 | 100% · 4.0 | 100% · 4.4 | 100% · 5.0 | 100% · 4.3 | 100% · 4.6 | 89% · 5.0 | 100% · 4.0 | **97%** (76/78) | **4.3** (n=41) |

## Speed

TTFT = time to first token, excluding model load time. Prompt tok/s = context reading speed (measured on ~10k uncached tokens). 4 users = 6 requests sent together with 4 in parallel: Ollama queues them, so the mean TTFT grows.

| Model | Peak VRAM | tok/s (1 user) | TTFT short | prompt tok/s | TTFT 10k tokens | tok/s @30k ctx | 4 users: tok/s/user · mean TTFT · server tok/s |
|---|---|---|---|---|---|---|---|
| gemma4_12b | 9.7 GB | 46.1 | 0.11 s | 1113 | 9.6 s | 45.9 | 52.2 · 18.06 s · 27.4 |
| gemma4_26b | 11.6 GB | 28.7 | 0.38 s | 569 | 18.7 s | 36.4 | 28.3 · 34.28 s · 13.5 |
| gemma4_e2b | 5.0 GB | 121.3 | 0.05 s | 4457 | 2.4 s | 101.1 | 124.0 · 6.62 s · 63.6 |
| gemma4_e4b | 5.8 GB | 102.0 | 0.05 s | 2497 | 4.3 s | 115.5 | 97.3 · 10.08 s · 47.6 |
| gemma4_latest | 5.5 GB | 74.1 | 0.06 s | 2477 | 4.3 s | 62.2 | 73.2 · 12.01 s · 42.6 |
| gpt-oss_20b | 10.8 GB | 39.2 | 0.70 s | 1286 | 8.8 s | 32.0 | 39.8 · 23.86 s · 22.6 |
| llama3.1_8b | 10.2 GB | 59.7 | 0.05 s | 1764 | 7.0 s | 33.4 | 59.0 · 12.06 s · 37.3 |
| mistral-nemo | 10.5 GB | 43.2 | 0.05 s | 1322 | 8.6 s | 1.7 | 43.2 · 16.21 s · 27.9 |
| qwen3.5_4b | 5.8 GB | 76.4 | 0.11 s | 2964 | 3.4 s | 63.8 | 75.9 · 9.94 s · 47.3 |
| qwen3.5_9b | 8.2 GB | 51.5 | 0.12 s | 1820 | 5.6 s | 45.0 | 50.8 · 16.79 s · 31.9 |

## Thinking on vs off (documents, hallucinations, reasoning, tools)

| Model | Auto off | Auto on | mean generated tokens off → on | mean time per answer off → on |
|---|---|---|---|---|
| gemma4_12b | 40/44 | 38/44 | 108 → 562 | 4.5 s → 11.6 s |
| qwen3.5_9b | 43/44 | 31/44 | 167 → 1448 | 4.9 s → 30.5 s |

## Failed tests (automatic checks)

- **gemma4_12b** (5): doc-quotation-total, doc-estrazione-tabella, wr-faq-generate, tool-pianifica-data, rag-ferie
- **gemma4_26b** (5): img-fattura-iban, img-rapporto-descrizione, wr-faq-generate, tool-pianifica-data, rag-ferie
- **gemma4_e2b** (17): doc-email-ricambio, doc-incident-riddor, hal-entita-confusa, img-fattura-campi, img-fattura-iban, img-rapporto-campi, img-rapporto-descrizione, img-grafico-massimo, img-grafico-tendenza, img-tabella-confronto, img-targhetta-seriale, img-targhetta-potenza, ml-en-su-it, tool-pianifica-data, rag-date-consegna, rag-ferie, rag-python
- **gemma4_e4b** (13): doc-quotation-total, doc-handbook-carryover, hal-data-inventata, img-fattura-iban, img-rapporto-descrizione, img-grafico-tendenza, wr-propuesta-es, wr-faq-generate, ml-en-su-it, tool-pianifica-data, rag-penale-3gg, rag-date-consegna, rag-ferie
- **gemma4_latest** (18): doc-quotation-total, doc-handbook-carryover, long-32k-multi, hal-data-inventata, img-fattura-campi, img-fattura-iban, img-rapporto-campi, img-rapporto-descrizione, img-grafico-massimo, img-grafico-tendenza, img-tabella-confronto, img-targhetta-seriale, img-targhetta-potenza, wr-faq-generate, ml-en-su-it, tool-pianifica-data, rag-date-consegna, rag-ferie
- **gpt-oss_20b** (10): doc-quotation-total, doc-incident-riddor, doc-handbook-carryover, doc-es-pagos, long-32k-multi, hal-premessa-falsa, hal-data-inventata, ml-en-su-it, tool-pianifica-data, rag-ferie
- **llama3.1_8b** (18): doc-quotation-total, doc-quotation-warranty, doc-incident-riddor, doc-handbook-carryover, doc-es-pagos, doc-estrazione-tabella, hal-data-inventata, wr-riscrittura-tono, wr-vincoli-formali, ml-en-su-it, ml-istruzione-lingua, tool-pianifica-data, tool-nessuno-necessario, tool-ambiguo-chiede, rag-penale-3gg, rag-deposit-uk, rag-date-consegna, rag-ferie
- **mistral-nemo** (10): conv-memoria-it, doc-multi-persona, long-32k-multi, hal-entita-confusa, wr-vincoli-formali, ml-istruzione-lingua, tool-pianifica-data, json-contratto, json-lista-decisioni, rag-date-consegna
- **qwen3.5_4b** (9): doc-quotation-total, doc-incident-riddor, doc-handbook-carryover, wr-faq-generate, wr-vincoli-formali, ml-en-su-it, tool-pianifica-data, rag-date-consegna, rag-ferie
- **qwen3.5_9b** (2): conv-support-es, tool-pianifica-data

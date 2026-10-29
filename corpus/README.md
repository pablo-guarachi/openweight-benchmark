# Test corpus — Rossi Impianti Srl (fictional company)

The material the models have to draw on. **`facts.yaml` is the ground truth**: every document and image is derived from it, and the suite's expected answers are checked against it.

The documents are test data and stay in their original language (Italian, English, Spanish). All companies, people, addresses, phone numbers and identifiers are invented. UK addresses use "Example" street names and no postcode; the UK phone number `+44 116 496 0123` is in Ofcom's range reserved for drama.

## Documents (`docs/`)
| File | Language | Type | Words |
|---|---|---|---|
| it-contratto-manutenzione-2026-114.md | IT | maintenance contract | ~460 |
| it-procedura-PR07-sicurezza.md | IT | internal safety procedure | ~465 |
| it-verbale-riunione-2026-09-03.md | IT | meeting minutes | ~370 |
| it-email-ritardo-bianchi.md | IT | email thread (complaint) | ~445 |
| it-listino-2026.md | IT/EN | price list | ~300 |
| it-faq-clienti.md | IT | customer FAQ | ~300 |
| it-manuale-operativo.md | IT | **long document**: 36 sections, ~19,800 words (~30k tokens), 8 planted "needle" facts | 19,788 |
| en-quotation-Q-UK-2026-031.md | EN | quotation | ~410 |
| en-incident-report-2026-07-14.md | EN | incident report | ~385 |
| en-uk-handbook-leave.md | EN | staff handbook (leave) | ~370 |
| es-contrato-ES-2026-07.md | ES | supply contract | ~400 |
| es-correo-soler-entrega.md | ES | email thread (delivery) | ~400 |

The documents are **consistent with each other** (same people, dates, amounts), which allows questions that combine several sources (e.g. "how much is the penalty for the September delay?" needs the contract + the email thread).

## Images (`images/`)
| File | Type | Difficulty |
|---|---|---|
| fattura-FT-2026-0087-scansione.png | scanned invoice, rotated, with noise | reading fields and amounts |
| rapporto-intervento-2026-09-24.png | filled-in form (fields in a different typeface) | matching label ↔ value |
| grafico-interventi-2026.png | bar chart with values | reading values, maximum, sum |
| tabella-listino-2026.png | two-currency table | comparison, empty cells |
| targhetta-RX-16-AIR.png | tilted rating plate, small text | OCR of codes and units |

Expected values: the `immagini` section of `facts.yaml`.

## Regenerating
`python scripts/build_corpus.py` regenerates the manual and the images (fixed seed: identical output). The short documents are hand-written.

## Revision note
The stored results were produced on an earlier revision of this corpus. Since then two UK
addresses were anonymised (a real business park and street name with real-looking Leicester
postcodes were replaced by "Example" names without a postcode). No fact that a test checks was
changed; see the README, "Limitations".

"""Aggregate the stored results into results/SUMMARY.md.

For each model it takes, for each test id, the latest available result (1-user run, thinking off),
applies the automatic checks, reads the manual grades from results/scores/<model>.yaml (if any)
and adds speed (1 and 4 users) and the thinking on/off comparison. No model is called.

Usage: python scripts/report.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate import category, evaluate  # noqa: E402

RES = ROOT / "results" / "local"
SCORES = ROOT / "results" / "scores"
CATS = ["01-speed", "02-conversation", "03-documents", "04-summaries", "05-hallucinations",
        "06-images", "07-writing", "08-multilingual", "09-tools", "10-reasoning"]
SHORT = {c: c[3:] for c in CATS}


def load_runs(model_dir):
    runs = []
    for f in sorted(model_dir.glob("*.json")):
        if ".eval" in f.name:
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        for r in d["results"]:
            r["category"] = category(r["category"])  # old runs store the Italian category ids
        runs.append((f.name, d["summary"], d["results"]))
    return runs


def latest_results(runs, users=1, think=False):
    best = {}
    for name, s, results in runs:
        st = s["think"]
        if isinstance(st, str):  # "level:low" = normal mode for models that always reason
            st = False
        if s["users"] != users or st != think:
            continue
        for r in results:
            best[r["id"]] = r  # files are in chronological order: the latest wins
    return best


def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "–"


def main():
    models = {}
    for d in sorted(RES.iterdir()):
        if d.is_dir():
            runs = load_runs(d)
            if runs:
                models[d.name] = runs
    manual = {}
    for f in SCORES.glob("*.yaml") if SCORES.exists() else []:
        manual[f.stem] = yaml.safe_load(f.read_text(encoding="utf-8")) or {}

    lines = ["# Results — Track A (local, RTX 3060 12GB)\n",
             "Auto = % of tests with automatic checks passed · Grade = mean manual grade 1-5 (rubric in evaluate.py) · n/a = not applicable\n"]

    # --- quality table by category
    header = "| Model | " + " | ".join(SHORT[c] for c in CATS if c != "01-speed") + " | **Auto total** | **Mean grade** |"
    lines += [header, "|" + "---|" * (len(CATS) + 2)]
    detail = {}
    for m, runs in models.items():
        res = latest_results(runs)
        by_cat = defaultdict(lambda: [0, 0])
        grades = defaultdict(list)
        tot = [0, 0]
        for tid, r in res.items():
            passed, _ = evaluate(r)
            if passed is not None:
                by_cat[r["category"]][1] += 1
                tot[1] += 1
                if passed:
                    by_cat[r["category"]][0] += 1
                    tot[0] += 1
            g = manual.get(m, {}).get(tid)
            if isinstance(g, (int, float)):
                grades[r["category"]].append(g)
        cells = []
        for c in CATS:
            if c == "01-speed":
                continue
            a = by_cat.get(c)
            g = grades.get(c)
            cell = pct(*a) if a else "n/a"
            if g:
                cell += f" · {sum(g) / len(g):.1f}"
            cells.append(cell)
        allg = [x for v in grades.values() for x in v]
        gcell = f"**{sum(allg) / len(allg):.1f}** (n={len(allg)})" if allg else "–"
        lines.append(f"| {m} | " + " | ".join(cells) + f" | **{pct(*tot)}** ({tot[0]}/{tot[1]}) | {gcell} |")
        detail[m] = (res, by_cat, grades)

    # --- speed
    # TTFT excluding model load time (load_s, Ollama only); prompt tok/s measured on vel-doc-12k
    # (the first long prompt in the suite, so no prefix cache).
    lines += ["\n## Speed\n",
              "TTFT = time to first token, excluding model load time. Prompt tok/s = context reading speed (measured on ~10k uncached tokens). "
              "4 users = 6 requests sent together with 4 in parallel: Ollama queues them, so the mean TTFT grows.\n",
              "| Model | Peak VRAM | tok/s (1 user) | TTFT short | prompt tok/s | TTFT 10k tokens | tok/s @30k ctx | 4 users: tok/s/user · mean TTFT · server tok/s |",
              "|---|---|---|---|---|---|---|---|"]
    for m, runs in models.items():
        res = latest_results(runs)
        vel = [r for r in res.values() if r["category"] == "01-speed" and r.get("tok_s")]
        short = [r for r in vel if r["id"] in ("vel-short-it", "vel-short-en") and r.get("ttft_s") is not None]
        if not vel or not short:
            lines.append(f"| {m} | – |")
            continue
        net = lambda r: max(0.0, (r["ttft_s"] or 0) - (r.get("load_s") or 0))
        doc12 = res.get("vel-doc-12k", {})
        long32 = res.get("long-32k-legionella", {})
        peak = max((s["vram_peak_mb"] for _, s, _ in runs if s["users"] == 1), default=0)
        p12 = f"{doc12['in_tokens'] / net(doc12):.0f}" if doc12.get("in_tokens") and net(doc12) > 0 else "–"
        u4 = [s for _, s, _ in runs if s["users"] == 4]
        u4c = f"{u4[-1]['avg_tok_s']} · {u4[-1]['avg_ttft_s']} s · {u4[-1]['server_tok_s']}" if u4 else "–"
        lines.append(f"| {m} | {peak / 1024:.1f} GB | {sum(r['tok_s'] for r in vel) / len(vel):.1f} | "
                     f"{min(net(r) for r in short):.2f} s | {p12} | {net(doc12):.1f} s | {long32.get('tok_s', '–')} | {u4c} |")

    # --- thinking on/off
    lines += ["\n## Thinking on vs off (documents, hallucinations, reasoning, tools)\n",
              "| Model | Auto off | Auto on | mean generated tokens off → on | mean time per answer off → on |", "|---|---|---|---|---|"]
    for m, runs in models.items():
        off, on = latest_results(runs, think=False), latest_results(runs, think=True)
        if not on:
            continue
        ids = [i for i in on if i in off and (on[i].get("check"))]
        po = sum(1 for i in ids if evaluate(off[i])[0])
        pn = sum(1 for i in ids if evaluate(on[i])[0])
        to = sum(off[i].get("out_tokens") or 0 for i in ids) / len(ids)
        tn = sum(on[i].get("out_tokens") or 0 for i in ids) / len(ids)
        so = sum(off[i].get("total_s") or 0 for i in ids) / len(ids)
        sn = sum(on[i].get("total_s") or 0 for i in ids) / len(ids)
        lines.append(f"| {m} | {po}/{len(ids)} | {pn}/{len(ids)} | {to:.0f} → {tn:.0f} | {so:.1f} s → {sn:.1f} s |")

    # --- failures per test (which tests trip up which model)
    lines += ["\n## Failed tests (automatic checks)\n"]
    for m, (res, _, _) in detail.items():
        fails = [tid for tid, r in res.items() if evaluate(r)[0] is False]
        lines.append(f"- **{m}** ({len(fails)}): " + ", ".join(fails))

    (ROOT / "results" / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

"""Build the README / site charts from the result files already on disk.

Reads only: results/local/<model>/*.json (raw runs), results/scores/<model>.yaml (manual 1-5
grades) and the automatic checks in scripts/evaluate.py. Nothing is re-run or re-scored; the
aggregation mirrors scripts/report.py, so the numbers match results/SUMMARY.md.

Outputs (each chart in a light and a dark variant, PNG + SVG):
  docs/charts/quality-by-model-{light,dark}.{png,svg}
  docs/charts/speed-by-model-{light,dark}.{png,svg}
  docs/charts/quality-vs-vram-{light,dark}.{png,svg}
  docs/charts/data.json          the aggregated numbers behind the charts
  site/charts/*                  copy of the above for the static results page
  site/data.js                   same data as a JS global (works from file:// too)

Usage: .venv/Scripts/python scripts/make_charts.py
"""
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate import evaluate  # noqa: E402
from report import latest_results, load_runs  # noqa: E402

RES = ROOT / "results" / "local"
SCORES = ROOT / "results" / "scores"
OUT = ROOT / "docs" / "charts"
SITE = ROOT / "site"

# gemma4:latest was a stale 6-month-old blob without vision; the write-up excludes it from the ranking.
EXCLUDE = {"gemma4_latest"}
# Models whose weights did not fit in 12 GB VRAM and ran partly on CPU.
OFFLOAD = {"gemma4_26b", "gpt-oss_20b"}
# The two models the write-up calls usable on a 12 GB card.
USABLE = {"qwen3.5_9b", "gemma4_12b"}

LABEL = {
    "qwen3.5_9b": "Qwen 3.5 9B", "qwen3.5_4b": "Qwen 3.5 4B", "gemma4_12b": "Gemma 4 12B",
    "gemma4_26b": "Gemma 4 26B (MoE)", "gemma4_e4b": "Gemma 4 E4B", "gemma4_e2b": "Gemma 4 E2B",
    "gpt-oss_20b": "gpt-oss 20B", "mistral-nemo": "Mistral Nemo 12B", "llama3.1_8b": "Llama 3.1 8B",
    "gemma4_latest": "Gemma 4 (stale blob)",
}

# Validated with the dataviz skill's validate_palette.js (accent + second slot, both modes).
THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#898781", grid="#e1e0d9",
                  axis="#c3c2b7", accent="#2a78d6", second="#eb6834", rest="#c3c2b7"),
    "dark": dict(surface="#1a1a19", ink="#f0efec", ink2="#c3c2b7", muted="#898781", grid="#2c2c2a",
                 axis="#383835", accent="#3987e5", second="#d95926", rest="#5f5e5a"),
}
FONT = ["Segoe UI", "DejaVu Sans"]


def collect():
    manual = {f.stem: yaml.safe_load(f.read_text(encoding="utf-8")) or {} for f in SCORES.glob("*.yaml")}
    rows = []
    for d in sorted(RES.iterdir()):
        if not d.is_dir():
            continue
        runs = load_runs(d)
        if not runs:
            continue
        m = d.name
        res = latest_results(runs)
        passed = total = 0
        grades = []
        by_cat = defaultdict(lambda: [0, 0])
        for tid, r in res.items():
            ok, _ = evaluate(r)
            if ok is not None:
                total += 1
                by_cat[r["category"]][1] += 1
                if ok:
                    passed += 1
                    by_cat[r["category"]][0] += 1
            g = manual.get(m, {}).get(tid)
            if isinstance(g, (int, float)):
                grades.append(g)
        vel = [r for r in res.values() if r["category"] == "01-speed" and r.get("tok_s")]
        peak = max((s["vram_peak_mb"] for _, s, _ in runs if s["users"] == 1), default=0)
        u4 = [s for _, s, _ in runs if s["users"] == 4]
        rows.append({
            "id": m,
            "label": LABEL.get(m, m),
            "auto_passed": passed,
            "auto_total": total,
            "auto_pct": round(100 * passed / total, 1) if total else None,
            "grade_mean": round(sum(grades) / len(grades), 2) if grades else None,
            "grade_n": len(grades),
            "tok_s_1user": round(sum(r["tok_s"] for r in vel) / len(vel), 1) if vel else None,
            "vram_peak_gb": round(peak / 1024, 1),
            "ttft_4users_s": u4[-1]["avg_ttft_s"] if u4 else None,
            "offload": m in OFFLOAD,
            "usable": m in USABLE,
            "excluded": m in EXCLUDE,
            "by_category": {c[3:]: {"passed": a, "total": b} for c, (a, b) in sorted(by_cat.items())},
        })
    return rows


def style(ax, fig, t, xgrid=True):
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(t["axis"])
    ax.tick_params(colors=t["muted"], labelsize=9, length=0)
    ax.grid(axis="x" if xgrid else "both", color=t["grid"], linewidth=0.8)
    ax.set_axisbelow(True)


def title(fig, t, main, sub):
    fig.text(0.02, 0.96, main, color=t["ink"], fontsize=13, fontweight="semibold", va="top")
    fig.text(0.02, 0.905, sub, color=t["ink2"], fontsize=9.5, va="top")


def hbar(rows, key, fmt, main, sub, xlabel, xmax, t):
    rows = sorted(rows, key=lambda r: r[key])
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
    style(ax, fig, t)
    y = range(len(rows))
    colors = [t["accent"] if r["usable"] else t["rest"] for r in rows]
    ax.barh(list(y), [r[key] for r in rows], height=0.55, color=colors)
    ax.set_yticks(list(y), [r["label"] for r in rows])
    for lbl, r in zip(ax.get_yticklabels(), rows):
        lbl.set_color(t["ink"] if r["usable"] else t["ink2"])
        lbl.set_fontsize(9.5)
    for i, r in enumerate(rows):
        ax.text(r[key] + xmax * 0.012, i, fmt(r), va="center", fontsize=9,
                color=t["ink"] if r["usable"] else t["ink2"])
    ax.set_xlim(0, xmax)
    ax.set_xlabel(xlabel, color=t["muted"], fontsize=9)
    fig.subplots_adjust(left=0.22, right=0.97, top=0.82, bottom=0.13)
    title(fig, t, main, sub)
    return fig


def scatter(rows, t):
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=150)
    style(ax, fig, t, xgrid=False)
    ax.axvline(12, color=t["axis"], linewidth=1)
    ax.text(11.92, 98.6, "12 GB card limit", color=t["muted"], fontsize=8.5, va="bottom", ha="right")
    fit = [r for r in rows if not r["offload"]]
    off = [r for r in rows if r["offload"]]
    ax.scatter([r["vram_peak_gb"] for r in fit], [r["auto_pct"] for r in fit], s=70, color=t["accent"],
               edgecolors=t["surface"], linewidths=2, zorder=3, label="Fits in VRAM")
    ax.scatter([r["vram_peak_gb"] for r in off], [r["auto_pct"] for r in off], s=70, marker="D",
               color=t["second"], edgecolors=t["surface"], linewidths=2, zorder=3,
               label="Partly offloaded to CPU")
    nudge = {"gemma4_12b": (-0.15, 0.9, "right"), "gemma4_26b": (0, -2.0, "center"), "gpt-oss_20b": (-0.15, -1.6, "right"),
             "mistral-nemo": (-0.15, 1.0, "right"), "llama3.1_8b": (0.15, -1.6), "qwen3.5_9b": (0.15, 0.9),
             "qwen3.5_4b": (0.15, 0.9), "gemma4_e4b": (0.15, -1.6), "gemma4_e2b": (0.15, -1.6)}
    for r in rows:
        dx, dy, *ha = nudge.get(r["id"], (0.15, 0.9))
        ax.text(r["vram_peak_gb"] + dx, r["auto_pct"] + dy, r["label"], fontsize=8.5,
                color=t["ink"] if r["usable"] else t["ink2"], ha=ha[0] if ha else "left")
    ax.set_xlim(4, 13)
    ax.set_ylim(72, 100)
    ax.set_xlabel("Peak VRAM (GB)", color=t["muted"], fontsize=9)
    ax.set_ylabel("Automatic checks passed (%)", color=t["muted"], fontsize=9)
    leg = ax.legend(loc="lower left", frameon=False, fontsize=8.5)
    for txt in leg.get_texts():
        txt.set_color(t["ink2"])
    fig.subplots_adjust(left=0.1, right=0.97, top=0.82, bottom=0.12)
    title(fig, t, "Bigger is not automatically better",
          "Accuracy vs. peak VRAM on an RTX 3060 12 GB. Peak GPU memory; offloaded models also use system RAM.")
    return fig


def save(fig, name, mode):
    for ext in ("png", "svg"):
        fig.savefig(OUT / f"{name}-{mode}.{ext}", facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    plt.rcParams["font.family"] = FONT
    plt.rcParams["svg.fonttype"] = "none"  # keep text as text in the SVG
    OUT.mkdir(parents=True, exist_ok=True)
    rows = collect()
    ranked = [r for r in rows if not r["excluded"]]
    for mode, t in THEMES.items():
        save(hbar(ranked, "auto_pct",
                  lambda r: f"{r['auto_pct']:.0f}%  ·  {r['grade_mean']:.1f}/5",
                  "Two local models are good enough",
                  "Share of automatic checks passed, with the mean manual grade (1–5). Blue = usable.",
                  "Automatic checks passed (%)  ·  text-only models skip the 10 image checks", 112, t),
             "quality-by-model", mode)
        save(hbar(ranked, "tok_s_1user", lambda r: f"{r['tok_s_1user']:.0f} tok/s",
                  "Fast enough for one user",
                  "Generation speed, one user, RTX 3060 12 GB (Ollama, Q4_K_M). Concurrency, not speed, is the limit.",
                  "Output tokens per second (mean of the speed suite)", 140, t),
             "speed-by-model", mode)
        save(scatter(ranked, t), "quality-vs-vram", mode)
    data = {"source": "results/local + results/scores (aggregated like scripts/report.py)", "models": rows}
    (OUT / "data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    (SITE / "charts").mkdir(parents=True, exist_ok=True)
    for f in OUT.iterdir():
        shutil.copy2(f, SITE / "charts" / f.name)
    (SITE / "data.js").write_text("window.BENCH = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    for r in rows:
        print(f"{r['id']:14} auto {r['auto_passed']}/{r['auto_total']} ({r['auto_pct']}%)  grade {r['grade_mean']} "
              f"(n={r['grade_n']})  {r['tok_s_1user']} tok/s  {r['vram_peak_gb']} GB")


if __name__ == "__main__":
    main()

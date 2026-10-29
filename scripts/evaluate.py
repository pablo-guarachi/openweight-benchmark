"""Automatic evaluation of the results + review sheet for the manually graded ("grade") tests.

Usage:
  python scripts/evaluate.py results/local/qwen3.5_9b/<file>.json      # one file
  python scripts/evaluate.py results/local/qwen3.5_9b                  # every run file in the folder

For each run file it writes, next to it: <file>.eval.json (result per test) and <file>.review.md
(the tests to grade by hand). Only stored outputs are read; no model is called.

Supported `check` rules (all case-insensitive on the normalised text):
  contains_any / contains_any_2, contains_all, not_contains, regex / regex_2 / regex_3, not_regex,
  bullets (exact number of bullet points), max_words, min_words, lang (it|en|es, heuristic),
  json_equals {key: value}, json_array_min N, json_items {id: {key: value}},
  tool {name, args_contain {k: substring}}, no_tool, tool_not <name>

Category names: the suite files were renamed to English (benchmark/03-documents.yaml, ...). Runs
recorded before the rename store the original Italian category ids (e.g. "03-documenti"); they are
mapped with LEGACY_CATEGORIES so old and new runs aggregate together. Test ids keep their original
Italian identifiers.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# Original (Italian) category ids stored in runs recorded before the suite files were renamed.
LEGACY_CATEGORIES = {
    "01-velocita": "01-speed", "02-conversazione": "02-conversation", "03-documenti": "03-documents",
    "04-riassunto": "04-summaries", "05-allucinazioni": "05-hallucinations", "06-immagini": "06-images",
    "07-scrittura": "07-writing", "08-multilingua": "08-multilingual", "09-tools": "09-tools",
    "10-ragionamento": "10-reasoning",
    # smoke.yaml
    "conversazione": "conversation", "riassunto": "summary", "allucinazioni": "hallucinations",
}


def category(name):
    """Current (English) category id for a category stored in a run file."""
    return LEGACY_CATEGORIES.get(name, name)


def current_tests():
    """id -> test, read from the current benchmark files (so fixes to checks and grader notes also
    apply to past runs)."""
    import yaml
    out = {}
    for f in (ROOT / "benchmark").glob("*.yaml"):
        for t in yaml.safe_load(f.read_text(encoding="utf-8")).get("tests", []):
            out[t["id"]] = t
    return out


TESTS = current_tests()
CHECKS = {k: t.get("check") for k, t in TESTS.items()}

STOP = {
    "it": {"il", "la", "di", "che", "è", "non", "per", "una", "sono", "del", "della", "con", "gli", "le", "nel", "anche"},
    "en": {"the", "and", "is", "of", "to", "in", "that", "for", "with", "are", "not", "this", "be", "on", "it", "as"},
    "es": {"el", "la", "de", "que", "y", "en", "los", "las", "es", "por", "una", "con", "para", "del", "se", "no"},
}


def norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s).replace("$", "")  # inline LaTeX produced by Gemma models
    s = re.sub("[‐-―−]", "-", s)  # unicode dashes (gpt-oss uses U+2011) -> "-"
    s = re.sub("[   ]", " ", s)  # thin / non-breaking spaces -> space
    s = re.sub(r"(\d)\s+%", r"\1%", s)  # "2 %" -> "2%"
    return re.sub(r"\s+", " ", s).strip().casefold()


def detect_lang(text):
    words = re.findall(r"[a-záéíóúàèìòùñ]+", (text or "").casefold())
    scores = {k: sum(1 for w in words if w in v) for k, v in STOP.items()}
    return max(scores, key=scores.get) if any(scores.values()) else None


def extract_json(text):
    t = (text or "").strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1).strip()
    for start, end in (("{", "}"), ("[", "]")):
        i, j = t.find(start), t.rfind(end)
        if i != -1 and j > i:
            try:
                return json.loads(t[i:j + 1])
            except Exception:
                continue
    return None


def num_eq(a, b):
    try:
        return abs(float(a) - float(b)) < 1e-6
    except Exception:
        return norm(str(a)) == norm(str(b))


def count_bullets(text):
    return sum(1 for line in (text or "").splitlines() if re.match(r"^\s*([-*•]|\d+[.)])\s+", line))


def evaluate(r):
    """Return (passed: bool|None, failed_rules: list). None = the test has no automatic check."""
    chk = CHECKS.get(r["id"], r.get("check")) or {}
    if not chk:
        return None, []
    if r.get("error"):
        return False, ["error"]
    txt = norm(r.get("response"))
    raw = r.get("response") or ""
    failed = []
    for rule, val in chk.items():
        base = re.sub(r"_\d$", "", rule)
        ok = True
        if base == "contains_any":
            ok = any(norm(v) in txt for v in val)
        elif base == "contains_all":
            ok = all(norm(v) in txt for v in val)
        elif base == "not_contains":
            ok = not any(norm(v) in txt for v in val)
        elif base == "regex":
            ok = re.search(val, raw) is not None
        elif base == "not_regex":
            ok = re.search(val, raw) is None
        elif base == "bullets":
            ok = count_bullets(raw) == val
        elif base == "max_words":
            ok = len(raw.split()) <= val
        elif base == "min_words":
            ok = len(raw.split()) >= val
        elif base == "lang":
            ok = detect_lang(raw) == val
        elif base == "json_equals":
            j = extract_json(raw)
            ok = isinstance(j, dict) and all(k in j and num_eq(j[k], v) for k, v in val.items())
        elif base == "json_array_min":
            j = extract_json(raw)
            ok = isinstance(j, list) and len(j) >= val
        elif base == "json_items":
            j = extract_json(raw)
            ok = isinstance(j, list)
            if ok:
                by_id = {}
                for it in j:
                    if isinstance(it, dict) and "id" in it:
                        by_id[str(it["id"])] = it
                for i, exp in val.items():
                    it = by_id.get(str(i))
                    if not it or not all(norm(str(it.get(k))) == norm(str(v)) for k, v in exp.items()):
                        ok = False
        elif base == "tool":
            calls = r.get("tool_calls") or []
            ok = False
            for c in calls:
                if c["name"] != val["name"]:
                    continue
                args = c.get("arguments") or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {}
                if all(norm(str(v)) in norm(str(args.get(k, ""))) for k, v in (val.get("args_contain") or {}).items()):
                    ok = True
        elif base == "no_tool":
            ok = not (r.get("tool_calls"))
        elif base == "tool_not":
            ok = not any(c["name"] == val for c in (r.get("tool_calls") or []))
        if not ok:
            failed.append(rule)
    return not failed, failed


def process(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for r in data["results"]:
        passed, failed = evaluate(r)
        rows.append({"id": r["id"], "category": category(r["category"]), "passed": passed, "failed": failed,
                     "grade": bool(r.get("grade")), "error": bool(r.get("error")),
                     "tok_s": r.get("tok_s"), "ttft_s": r.get("ttft_s"), "in_tokens": r.get("in_tokens")})
    checked = [x for x in rows if x["passed"] is not None]
    summary = {"model": data["summary"]["model"], "file": path.name,
               "auto_pass": sum(1 for x in checked if x["passed"]), "auto_total": len(checked),
               "errors": sum(1 for x in rows if x["error"])}
    by_cat = {}
    for x in checked:
        c = by_cat.setdefault(x["category"], [0, 0])
        c[1] += 1
        c[0] += 1 if x["passed"] else 0
    summary["by_category"] = {k: f"{v[0]}/{v[1]}" for k, v in by_cat.items()}
    path.with_suffix(".eval.json").write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")

    # review sheet for the tests graded by hand
    lines = [f"# Manual review — {summary['model']} — {path.name}\n",
             "Rubric 1-5: 5 = perfect; 4 = correct with minor flaws; 3 = usable after correction; 2 = substantive errors; 1 = unusable or invented.\n"]
    for r in data["results"]:
        if not r.get("grade"):
            continue
        passed, failed = evaluate(r)
        auto = "n/a" if passed is None else ("PASS" if passed else f"FAIL {failed}")
        lines.append(f"\n## {r['id']}  [{category(r['category'])}/{r['lang']}]  auto={auto}\n")
        lines.append(f"**Expected:** {TESTS.get(r['id'], {}).get('expected', r.get('expected'))}\n")
        if r.get("tool_calls"):
            lines.append(f"**Tool calls:** `{json.dumps(r['tool_calls'], ensure_ascii=False)}`\n")
        lines.append("**Response:**\n\n```\n" + (r.get("response") or r.get("error") or "").strip() + "\n```\n")
    path.with_suffix(".review.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    for x in rows:
        if x["passed"] is False:
            print(f"  FAIL {x['id']:<28} {x['failed']}")
    return summary


if __name__ == "__main__":
    target = Path(sys.argv[1])
    files = [target] if target.is_file() else sorted(p for p in target.glob("*.json") if ".eval" not in p.name)
    for f in files:
        process(f)

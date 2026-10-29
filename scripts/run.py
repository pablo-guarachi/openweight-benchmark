"""Benchmark suite runner.

Sends the tests in one or more YAML files to a model, with N simultaneous users, and stores the
response + metrics. Two backends:
  - ollama  : native API (per-test context size, images, tools, precise timings)  [Track A, local]
  - openai  : OpenAI-compatible endpoint, e.g. vLLM                               [Track B, rented GPUs]

Usage:
  python scripts/run.py --model qwen3.5:9b --suite benchmark/03-documents.yaml
  python scripts/run.py --model qwen3.5:9b --suite benchmark/01-speed.yaml --users 4
  python scripts/run.py --model qwen3.5:9b --suite all --skip-vision
  python scripts/run.py --model Qwen3.8-27B --backend openai --base-url http://1.2.3.4:8000/v1 --tag rented

Test fields (YAML):
  id, category, lang, prompt | messages, system, doc (path or {path, sections:[a,b]}),
  image (path), tools (OpenAI format), ctx (num_ctx), max_tokens, temperature,
  expected (note for the grader), check (automatic rules, see evaluate.py), grade (bool)

The test data (prompts, documents, the default system prompt below) is in Italian, English and
Spanish on purpose and is sent to the model verbatim.
"""
import argparse
import asyncio
import base64
import json
import re
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"

# Default system prompt for document tests. Part of the test data: kept in Italian (translation:
# "You are a company assistant. Answer only from the documents provided. If the requested information
# is not in the documents, say so clearly without inventing. Answer in the language of the question.")
DOC_SYSTEM = ("Sei un assistente aziendale. Rispondi basandoti esclusivamente sui documenti forniti. "
              "Se l'informazione richiesta non è presente nei documenti, dillo chiaramente senza inventare. "
              "Rispondi nella stessa lingua della domanda.")


# --------------------------------------------------------------------------- helpers
class VramSampler:
    def __init__(self):
        self.max_mb = 0
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._loop, daemon=True)

    @staticmethod
    def read_mb():
        try:
            out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                 capture_output=True, text=True, timeout=5).stdout.strip()
            return int(out.splitlines()[0])
        except Exception:
            return 0

    def _loop(self):
        while not self._stop.is_set():
            self.max_mb = max(self.max_mb, self.read_mb())
            time.sleep(0.5)

    def __enter__(self):
        self._t.start()
        return self

    def __exit__(self, *_):
        self._stop.set()
        self._t.join(timeout=2)


def load_doc(spec):
    """spec: 'docs/x.md' or {path: 'docs/x.md', sections: [a, b]} (sections '## N.' a..b inclusive)."""
    if isinstance(spec, str):
        spec = {"path": spec}
    text = (CORPUS / spec["path"]).read_text(encoding="utf-8")
    if "sections" in spec:
        a, b = spec["sections"]
        parts = re.split(r"(?m)^(?=## \d+\. )", text)
        head = parts[0].split("## Indice")[0]
        keep = [p for p in parts[1:] if a <= int(re.match(r"## (\d+)\.", p).group(1)) <= b]
        text = head + "".join(keep)
    return text


def build_messages(test):
    msgs = []
    system = test.get("system")
    if test.get("doc") and not system:
        system = DOC_SYSTEM
    if system:
        msgs.append({"role": "system", "content": system})
    doc_block = ""
    if test.get("doc"):
        docs = test["doc"] if isinstance(test["doc"], list) else [test["doc"]]
        blocks = []
        for d in docs:
            name = d if isinstance(d, str) else d["path"]
            # the <documento> wrapper is part of the prompt (test data), kept as recorded
            blocks.append(f"<documento nome=\"{Path(name).name}\">\n{load_doc(d)}\n</documento>")
        doc_block = "\n\n".join(blocks) + "\n\n"
    if "messages" in test:
        turns = [dict(m) for m in test["messages"]]
        turns[-1]["content"] = doc_block + turns[-1]["content"]  # documents attached to the last turn
        msgs += turns
        return msgs
    m = {"role": "user", "content": doc_block + test["prompt"]}
    if test.get("image"):
        m["_image"] = (CORPUS / test["image"]).read_bytes()
    msgs.append(m)
    return msgs


# --------------------------------------------------------------------------- Ollama backend (native API)
async def call_ollama(client, base, model, test, msgs, max_tokens, think):
    payload_msgs = []
    for m in msgs:
        mm = {"role": m["role"], "content": m["content"]}
        if "_image" in m:
            mm["images"] = [base64.b64encode(m["_image"]).decode()]
        payload_msgs.append(mm)
    body = {
        "model": model, "messages": payload_msgs,
        # gpt-oss ignores think=false and always reasons; it accepts a level "low|medium|high" instead
        "think": think if isinstance(think, str) else bool(think),
        "options": {"num_predict": max_tokens, "temperature": test.get("temperature", 0.2),
                    "num_ctx": test.get("ctx", 8192)},
        "stream": not test.get("tools"),
    }
    if test.get("tools"):
        body["tools"] = test["tools"]
    t0 = time.perf_counter()
    ttft = None
    text, reasoning, tool_calls, final = [], [], [], {}
    if body["stream"]:
        async with client.stream("POST", f"{base}/api/chat", json=body, timeout=None) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line.strip():
                    continue
                ch = json.loads(line)
                msg = ch.get("message", {})
                if msg.get("thinking"):
                    reasoning.append(msg["thinking"])
                if msg.get("content"):
                    if ttft is None:
                        ttft = time.perf_counter() - t0
                    text.append(msg["content"])
                if ch.get("done"):
                    final = ch
    else:
        r = await client.post(f"{base}/api/chat", json=body, timeout=None)
        r.raise_for_status()
        final = r.json()
        msg = final.get("message", {})
        text.append(msg.get("content") or "")
        if msg.get("thinking"):
            reasoning.append(msg["thinking"])
        for tc in msg.get("tool_calls") or []:
            tool_calls.append({"name": tc["function"]["name"], "arguments": tc["function"].get("arguments")})
        ttft = time.perf_counter() - t0
    total = time.perf_counter() - t0
    ev, evd = final.get("eval_count"), final.get("eval_duration")
    pe, ped = final.get("prompt_eval_count"), final.get("prompt_eval_duration")
    return {
        "response": "".join(text), "reasoning": "".join(reasoning) or None, "tool_calls": tool_calls or None,
        "ttft_s": round(ttft, 3) if ttft is not None else None, "total_s": round(total, 3),
        "in_tokens": pe, "out_tokens": ev,
        "tok_s": round(ev / (evd / 1e9), 1) if ev and evd else None,
        "prompt_tok_s": round(pe / (ped / 1e9), 1) if pe and ped else None,
        "load_s": round(final.get("load_duration", 0) / 1e9, 2),
    }


# --------------------------------------------------------------------------- OpenAI-compatible backend (vLLM)
async def call_openai(client, base, model, test, msgs, max_tokens, think):
    payload_msgs = []
    for m in msgs:
        if "_image" in m:
            b64 = base64.b64encode(m["_image"]).decode()
            payload_msgs.append({"role": m["role"], "content": [
                {"type": "text", "text": m["content"]},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]})
        else:
            payload_msgs.append({"role": m["role"], "content": m["content"]})
    body = {"model": model, "messages": payload_msgs, "max_tokens": max_tokens,
            "temperature": test.get("temperature", 0.2), "stream": not test.get("tools"),
            "stream_options": {"include_usage": True}}
    if not think:
        body["reasoning_effort"] = "none"
    if test.get("tools"):
        body["tools"] = test["tools"]
        body.pop("stream_options")
    t0 = time.perf_counter()
    ttft = None
    text, reasoning, tool_calls, usage = [], [], [], {}
    if body["stream"]:
        async with client.stream("POST", f"{base}/chat/completions", json=body, timeout=None) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line.startswith("data:") or "[DONE]" in line:
                    continue
                ch = json.loads(line[5:])
                if ch.get("usage"):
                    usage = ch["usage"]
                for c in ch.get("choices") or []:
                    d = c.get("delta", {})
                    if d.get("reasoning"):
                        reasoning.append(d["reasoning"])
                    if d.get("content"):
                        if ttft is None:
                            ttft = time.perf_counter() - t0
                        text.append(d["content"])
    else:
        r = await client.post(f"{base}/chat/completions", json=body, timeout=None)
        r.raise_for_status()
        d = r.json()
        usage = d.get("usage") or {}
        msg = d["choices"][0]["message"]
        text.append(msg.get("content") or "")
        for tc in msg.get("tool_calls") or []:
            args = tc["function"].get("arguments")
            try:
                args = json.loads(args) if isinstance(args, str) else args
            except Exception:
                pass
            tool_calls.append({"name": tc["function"]["name"], "arguments": args})
        ttft = time.perf_counter() - t0
    total = time.perf_counter() - t0
    out = usage.get("completion_tokens")
    gen = total - (ttft or 0)
    return {
        "response": "".join(text), "reasoning": "".join(reasoning) or None, "tool_calls": tool_calls or None,
        "ttft_s": round(ttft, 3) if ttft is not None else None, "total_s": round(total, 3),
        "in_tokens": usage.get("prompt_tokens"), "out_tokens": out,
        "tok_s": round(out / gen, 1) if out and gen > 0 else None, "prompt_tok_s": None, "load_s": None,
    }


# --------------------------------------------------------------------------- orchestration
async def run_one(client, args, test, sem):
    msgs = build_messages(test)
    call = call_ollama if args.backend == "ollama" else call_openai
    async with sem:
        try:
            r = await call(client, args.base_url, args.model, test, msgs, test.get("max_tokens", args.max_tokens), args.think)
            r["error"] = None
        except Exception as e:
            r = {"response": "", "reasoning": None, "tool_calls": None, "ttft_s": None, "total_s": None,
                 "in_tokens": None, "out_tokens": None, "tok_s": None, "prompt_tok_s": None, "load_s": None,
                 "error": repr(e)[:500]}
    base = {k: test.get(k) for k in ("id", "category", "lang", "expected", "check", "grade", "ctx")}
    base["vision"] = bool(test.get("image"))
    return {**base, **r}


def load_suites(spec):
    files = sorted((ROOT / "benchmark").glob("*.yaml")) if spec == "all" else [Path(p) for p in spec.split(",")]
    files = [f for f in files if f.stem != "smoke"] if spec == "all" else files
    tests = []
    for f in files:
        for t in yaml.safe_load(f.read_text(encoding="utf-8"))["tests"]:
            t.setdefault("category", f.stem)
            tests.append(t)
    return tests, [f.stem for f in files]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--suite", required=True, help="YAML file (several allowed, comma-separated) or 'all'")
    ap.add_argument("--backend", choices=["ollama", "openai"], default="ollama")
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--users", type=int, default=1)
    ap.add_argument("--max-tokens", type=int, default=800)
    ap.add_argument("--tag", default="local")
    ap.add_argument("--think", action="store_true")
    ap.add_argument("--think-level", choices=["low", "medium", "high"], default=None,
                    help="reasoning level, for models that always reason (gpt-oss)")
    ap.add_argument("--skip-vision", action="store_true", help="skip the image tests (text-only models)")
    ap.add_argument("--only", default=None, help="run only the tests whose id contains this string")
    args = ap.parse_args()
    if args.think_level:
        args.think = args.think_level
    if args.base_url is None:
        args.base_url = "http://localhost:11434" if args.backend == "ollama" else "http://localhost:8000/v1"

    tests, names = load_suites(args.suite)
    if args.skip_vision:
        tests = [t for t in tests if not t.get("image")]
    if args.only:
        tests = [t for t in tests if args.only in t["id"]]
    sem = asyncio.Semaphore(args.users)

    vram_before = VramSampler.read_mb()
    t0 = time.perf_counter()
    async with httpx.AsyncClient() as client:
        with VramSampler() as vram:
            results = await asyncio.gather(*(run_one(client, args, t, sem) for t in tests))
    wall = time.perf_counter() - t0

    ok = [r for r in results if r["tok_s"] and r["ttft_s"] is not None]
    summary = {
        "model": args.model, "tag": args.tag, "backend": args.backend, "users": args.users, "think": args.think if isinstance(args.think, bool) else f"level:{args.think}",
        "suites": names, "n": len(results), "errors": sum(1 for r in results if r["error"]),
        "wall_s": round(wall, 1),
        "avg_ttft_s": round(sum(r["ttft_s"] for r in ok) / len(ok), 2) if ok else None,
        "avg_tok_s": round(sum(r["tok_s"] for r in ok) / len(ok), 1) if ok else None,
        "server_tok_s": round(sum(r["out_tokens"] for r in ok) / wall, 1) if ok else None,
        "vram_before_mb": vram_before, "vram_peak_mb": vram.max_mb,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    out_dir = ROOT / "results" / args.tag / args.model.replace(":", "_").replace("/", "_")
    out_dir.mkdir(parents=True, exist_ok=True)
    suite_name = "all" if args.suite == "all" else "+".join(names)
    name = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_{suite_name}_u{args.users}{('_think' if args.think is True else '_think-' + args.think) if args.think else ''}"
    (out_dir / f"{name}.json").write_text(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    for r in results:
        flag = "ERR" if r["error"] else ""
        print(f"  {r['id']:<28} ttft={r['ttft_s']} tok/s={r['tok_s']} in={r['in_tokens']} out={r['out_tokens']} {flag}")
    print(f"-> {out_dir / name}.json")


if __name__ == "__main__":
    asyncio.run(main())

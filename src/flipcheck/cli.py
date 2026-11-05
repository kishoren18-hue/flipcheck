"""flipcheck questions.jsonl --backend openai --model gpt-4o-mini --html report.html"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .backends import make_backend
from .cache import CachedBackend
from .core import run
from .report import to_html


def load_items(path: str) -> list[dict]:
    items = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    for i, it in enumerate(items):
        if "question" not in it:
            raise SystemExit(f"line {i + 1}: missing 'question'")
        it.setdefault("id", f"q{i + 1}")
    return items


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="flipcheck",
                                 description="Measure how often a model's answer changes when only the wording changes.")
    ap.add_argument("questions", help="JSONL with question (and optional id, answer)")
    ap.add_argument("--backend", choices=["openai", "anthropic", "command"], required=True)
    ap.add_argument("--model", help="model name (openai/anthropic backends)")
    ap.add_argument("--base-url", help="OpenAI-compatible base URL (default api.openai.com/v1)")
    ap.add_argument("--cmd", help="shell command for the command backend, e.g. 'ollama run llama3.1'")
    ap.add_argument("--variants", type=int, default=8, help="rewordings per question (max 12)")
    ap.add_argument("--answer-type", choices=["free", "number", "yesno", "choice"], default="free")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--html", help="write an HTML report here")
    ap.add_argument("--jsonl", help="write per-question results here")
    ap.add_argument("--max-flip-rate", type=float, help="exit 1 if the flip rate exceeds this (for CI)")
    ap.add_argument("--samples", type=int, default=1,
                    help="ask each wording this many times (use with --temperature > 0) to separate "
                         "sampling noise from wording sensitivity")
    ap.add_argument("--llm-paraphrases", type=int, default=0,
                    help="also have the model write this many extra rewordings per question")
    ap.add_argument("--cache", default=".flipcheck_cache.jsonl",
                    help="reply cache for resuming and re-analysis (default .flipcheck_cache.jsonl)")
    ap.add_argument("--no-cache", action="store_true", help="always call the model")
    a = ap.parse_args(argv)
    if a.samples > 1 and a.temperature == 0:
        print("note: --samples > 1 at temperature 0 will usually return identical samples", file=sys.stderr)

    backend = make_backend(a.backend, a.model, a.base_url, a.cmd, a.temperature)
    cached = None
    if not a.no_cache:
        cached = CachedBackend(backend, a.cache, namespace=f"{backend!r}|t={a.temperature}")
        backend = cached
    items = load_items(a.questions)
    results, s = run(items, backend, a.variants, a.answer_type, a.workers,
                     progress=lambda i, n: print(f"\r{i}/{n}", end="", file=sys.stderr),
                     samples=a.samples, n_llm_paraphrases=a.llm_paraphrases)
    print(file=sys.stderr)
    if cached:
        print(f"cache: {cached.hits} reused, {cached.misses} new calls ({a.cache})", file=sys.stderr)
    for k, v in s.__dict__.items():
        print(f"{k:<22} {v if not isinstance(v, float) else round(v, 3)}")
    if a.jsonl:
        with open(a.jsonl, "w") as f:
            for r in results:
                f.write(json.dumps(r.as_dict()) + "\n")
    if a.html:
        Path(a.html).write_text(to_html(results, s, repr(backend), f"temperature={a.temperature}, samples per wording={a.samples}"))
        print(f"report: {a.html}", file=sys.stderr)
    if a.max_flip_rate is not None and s.flip_rate > a.max_flip_rate:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

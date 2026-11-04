"""flipcheck questions.jsonl --backend openai --model gpt-4o-mini --html report.html"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .backends import make_backend
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
    a = ap.parse_args(argv)

    backend = make_backend(a.backend, a.model, a.base_url, a.cmd, a.temperature)
    items = load_items(a.questions)
    results, s = run(items, backend, a.variants, a.answer_type, a.workers,
                     progress=lambda i, n: print(f"\r{i}/{n}", end="", file=sys.stderr))
    print(file=sys.stderr)
    for k, v in s.__dict__.items():
        print(f"{k:<22} {v if not isinstance(v, float) else round(v, 3)}")
    if a.jsonl:
        with open(a.jsonl, "w") as f:
            for r in results:
                f.write(json.dumps(r.as_dict()) + "\n")
    if a.html:
        Path(a.html).write_text(to_html(results, s, repr(backend), f"temperature={a.temperature}"))
        print(f"report: {a.html}", file=sys.stderr)
    if a.max_flip_rate is not None and s.flip_rate > a.max_flip_rate:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build the public leaderboard: every model answers every question under 10 rewordings.

    GEMINI_API_KEY=... python scripts/build_leaderboard.py --models gemini-3.5-flash-lite,gemini-3.8-flash

Models from different companies can be ranked side by side: names starting with
"gemini" use GEMINI_API_KEY (a free Google AI Studio key works) and names starting
with "claude" use ANTHROPIC_API_KEY. Models without a key are skipped.

Free-tier keys have per-minute and per-day limits. Every reply is cached, so if a
run stops at a limit, run it again later and it continues where it left off.

Writes src/data/leaderboard.json, which the website reads at build time. Run it
from the "Update leaderboard" GitHub Action so results are versioned in git and
anyone can audit exactly what was asked and answered.
"""

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

from flipcheck import evaluate_question, summarize
from flipcheck.backends import Anthropic, Gemini
from flipcheck.cache import CachedBackend

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODELS = "gemini-3.5-flash-lite,gemini-3.8-flash,claude-haiku-5-5"


def backend_for(model: str):
    """(backend, cache namespace, workers) for a model name, or None if its key is missing."""
    if model.startswith("gemini") and os.environ.get("GEMINI_API_KEY"):
        return Gemini(model, temperature=0.0, max_tokens=1024, timeout=60), f"gemini:{model}:t0", 2
    if model.startswith("claude") and os.environ.get("ANTHROPIC_API_KEY"):
        return Anthropic(model, temperature=0.0, max_tokens=300, timeout=60), f"anthropic:{model}:t0", 5
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=os.environ.get("AI_MODELS", DEFAULT_MODELS))
    ap.add_argument("--questions", default=str(ROOT / "data" / "questions.jsonl"))
    ap.add_argument("--variants", type=int, default=10)
    ap.add_argument("--out", default=str(ROOT / "src" / "data" / "leaderboard.json"))
    ap.add_argument("--cache", default=str(ROOT / ".leaderboard_cache.jsonl"))
    a = ap.parse_args()

    items = [json.loads(line) for line in Path(a.questions).read_text().splitlines() if line.strip()]
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    board = []
    for model in models:
        made = backend_for(model)
        if made is None:
            print(f"[{model}] skipped: no API key for this provider", file=sys.stderr)
            continue
        raw, namespace, workers = made
        backend = CachedBackend(raw, a.cache, namespace=namespace)
        results = []
        for i, it in enumerate(items, 1):
            print(f"[{model}] {i}/{len(items)} {it['id']}", file=sys.stderr)
            try:
                results.append(evaluate_question(it, backend, a.variants, it.get("type", "free"), workers=workers))
            except RuntimeError as e:
                print(f"  skipped: {e}", file=sys.stderr)
        if len(results) < len(items):
            print(f"[{model}] incomplete ({len(results)}/{len(items)}); not added. Re-run later to finish from the cache.",
                  file=sys.stderr)
            continue
        s = summarize(results)
        board.append({
            "model": model,
            "summary": s.__dict__,
            "questions": [
                {"id": r.id, "question": r.question, "gold": r.gold, "answers": r.answers, "majority": r.majority,
                 "agreement": r.agreement, "flipped": r.flipped, "majority_correct": r.majority_correct,
                 "original_correct": r.original_correct}
                for r in results
            ],
        })
        print(f"[{model}] flip rate {s.flip_rate:.0%}, accuracy {s.accuracy_original:.0%} -> every wording "
              f"{s.accuracy_worst_case:.0%}; cache {backend.hits} reused / {backend.misses} new", file=sys.stderr)

    if not board:
        print("no model finished; set GEMINI_API_KEY and/or ANTHROPIC_API_KEY", file=sys.stderr)
        return 2
    out = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "n_questions": len(items),
        "n_variants": a.variants,
        "temperature": 0.0,
        "models": board,
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {a.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build the public leaderboard: every model answers every question under 10 rewordings.

    ANTHROPIC_API_KEY=... python scripts/build_leaderboard.py --models claude-haiku-5-5,claude-sonnet-5-5

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
from flipcheck.backends import Anthropic
from flipcheck.cache import CachedBackend

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=os.environ.get("CLAUDE_MODELS", "claude-haiku-5-5,claude-sonnet-5-5"))
    ap.add_argument("--questions", default=str(ROOT / "data" / "questions.jsonl"))
    ap.add_argument("--variants", type=int, default=10)
    ap.add_argument("--out", default=str(ROOT / "src" / "data" / "leaderboard.json"))
    ap.add_argument("--cache", default=str(ROOT / ".leaderboard_cache.jsonl"))
    a = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set", file=sys.stderr)
        return 2
    items = [json.loads(line) for line in Path(a.questions).read_text().splitlines() if line.strip()]
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    board = []
    for model in models:
        backend = CachedBackend(Anthropic(model, temperature=0.0, max_tokens=300, timeout=60), a.cache,
                                namespace=f"anthropic:{model}:t0")
        results = []
        for i, it in enumerate(items, 1):
            print(f"[{model}] {i}/{len(items)} {it['id']}", file=sys.stderr)
            try:
                results.append(evaluate_question(it, backend, a.variants, it.get("type", "free"), workers=5))
            except RuntimeError as e:
                print(f"  skipped: {e}", file=sys.stderr)
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

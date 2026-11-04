"""Run every question under several rewordings and measure how often the answer flips."""

from __future__ import annotations

import math
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field

from .normalize import ANSWER_INSTRUCTIONS, NORMALIZERS
from .paraphrase import rule_paraphrases


@dataclass
class QuestionResult:
    id: str
    question: str
    gold: str | None
    variants: list[str]
    replies: list[str] = field(repr=False)
    answers: list[str | None]
    majority: str | None
    agreement: float          # share of parseable answers equal to the majority
    flipped: bool             # any parseable answer differs from the majority
    entropy: float            # bits, over parseable answers
    n_distinct: int
    unparsed: int
    majority_correct: bool | None
    original_correct: bool | None

    def as_dict(self):
        return asdict(self)


@dataclass
class Summary:
    n_questions: int
    n_variants: int
    flip_rate: float
    mean_agreement: float
    mean_entropy: float
    unparsed_rate: float
    accuracy_original: float | None
    accuracy_majority: float | None
    accuracy_worst_case: float | None   # correct under every variant
    stability_auroc: float | None       # does agreement predict correctness?


def _entropy(counts: Counter) -> float:
    n = sum(counts.values())
    return -sum(c / n * math.log2(c / n) for c in counts.values()) if n else 0.0


def _auroc(scores, labels):
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    if not pos or not neg:
        return None
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def evaluate_question(item: dict, backend, n_variants: int = 8, answer_type: str = "free",
                      extra_variants: list[str] | None = None, workers: int = 4) -> QuestionResult:
    norm = NORMALIZERS[answer_type]
    instr = ANSWER_INSTRUCTIONS[answer_type]
    variants = rule_paraphrases(item["question"], n_variants, instr)
    variants += [f"{v}\n\n{instr}" for v in (extra_variants or [])]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        replies = list(ex.map(backend, variants))
    answers = [norm(r) for r in replies]
    parsed = [a for a in answers if a not in (None, "")]
    counts = Counter(parsed)
    majority = counts.most_common(1)[0][0] if counts else None
    gold = item.get("answer")
    gold_n = norm(f"Answer: {gold}") if gold is not None else None
    return QuestionResult(
        id=str(item.get("id", "")), question=item["question"], gold=gold, variants=variants,
        replies=replies, answers=answers, majority=majority,
        agreement=counts[majority] / len(parsed) if parsed else 0.0,
        flipped=len(counts) > 1, entropy=_entropy(counts), n_distinct=len(counts),
        unparsed=len(answers) - len(parsed),
        majority_correct=(majority == gold_n) if gold_n is not None else None,
        original_correct=(answers[0] == gold_n) if gold_n is not None else None,
    )


def run(items: list[dict], backend, n_variants: int = 8, answer_type: str = "free",
        workers: int = 4, progress=None) -> tuple[list[QuestionResult], Summary]:
    results = []
    for i, it in enumerate(items):
        results.append(evaluate_question(it, backend, n_variants, answer_type, workers=workers))
        if progress:
            progress(i + 1, len(items))
    return results, summarize(results)


def summarize(results: list[QuestionResult]) -> Summary:
    n = len(results)
    graded = [r for r in results if r.majority_correct is not None]
    total_answers = sum(len(r.answers) for r in results)
    worst = None
    if graded:
        worst = sum(bool(r.majority_correct) and not r.flipped and r.unparsed == 0 for r in graded) / len(graded)
    return Summary(
        n_questions=n,
        n_variants=len(results[0].variants) if results else 0,
        flip_rate=sum(r.flipped for r in results) / n if n else 0.0,
        mean_agreement=sum(r.agreement for r in results) / n if n else 0.0,
        mean_entropy=sum(r.entropy for r in results) / n if n else 0.0,
        unparsed_rate=sum(r.unparsed for r in results) / total_answers if total_answers else 0.0,
        accuracy_original=sum(bool(r.original_correct) for r in graded) / len(graded) if graded else None,
        accuracy_majority=sum(bool(r.majority_correct) for r in graded) / len(graded) if graded else None,
        accuracy_worst_case=worst,
        stability_auroc=_auroc([r.agreement for r in graded], [r.majority_correct for r in graded]) if graded else None,
    )

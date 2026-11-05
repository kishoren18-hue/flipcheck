"""Run every question under several rewordings and measure how often the answer flips.

With `samples > 1`, each rewording is asked several times (use temperature > 0).
That separates two sources of instability that a single run mixes together:

* sampling noise: the same wording gives different answers on repeated tries
* wording sensitivity: different wordings settle on different answers

Per-wording answers are then the majority over that wording's samples, so the
flip rate measures wording sensitivity with sampling noise averaged out.
"""

from __future__ import annotations

import math
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field

from .cache import call
from .normalize import ANSWER_INSTRUCTIONS, NORMALIZERS
from .paraphrase import llm_paraphrases, rule_paraphrases


@dataclass
class QuestionResult:
    id: str
    question: str
    gold: str | None
    variants: list[str]
    replies: list[str] = field(repr=False)
    answers: list[str | None]           # one per wording (majority over samples)
    majority: str | None
    agreement: float                    # share of parseable wording-answers equal to the majority
    flipped: bool                       # any parseable wording-answer differs from the majority
    entropy: float                      # bits, over parseable wording-answers
    n_distinct: int
    unparsed: int
    majority_correct: bool | None
    original_correct: bool | None
    samples: int = 1
    sample_answers: list[list[str | None]] = field(default_factory=list, repr=False)
    within_agreement: float | None = None   # mean share of a wording's samples agreeing with that wording's majority

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
    n_samples: int = 1
    sampling_flip_rate: float | None = None   # questions where some wording disagreed with itself
    mean_within_agreement: float | None = None


def _entropy(counts: Counter) -> float:
    n = sum(counts.values())
    return -sum(c / n * math.log2(c / n) for c in counts.values()) if n else 0.0


def _auroc(scores, labels):
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    if not pos or not neg:
        return None
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def _majority(answers):
    parsed = [a for a in answers if a not in (None, "")]
    if not parsed:
        return None, 0.0
    a, c = Counter(parsed).most_common(1)[0]
    return a, c / len(parsed)


def evaluate_question(item: dict, backend, n_variants: int = 8, answer_type: str = "free",
                      extra_variants: list[str] | None = None, workers: int = 4,
                      samples: int = 1) -> QuestionResult:
    if samples < 1:
        raise ValueError("samples must be >= 1")
    norm = NORMALIZERS[answer_type]
    instr = ANSWER_INSTRUCTIONS[answer_type]
    variants = rule_paraphrases(item["question"], n_variants, instr)
    variants += [f"{v}\n\n{instr}" for v in (extra_variants or [])]
    jobs = [(v, s) for v in variants for s in range(samples)]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        flat = list(ex.map(lambda job: call(backend, job[0], job[1]), jobs))
    replies_by_variant = [flat[i * samples:(i + 1) * samples] for i in range(len(variants))]
    sample_answers = [[norm(r) for r in rs] for rs in replies_by_variant]

    answers, within = [], []
    for sa in sample_answers:
        maj, share = _majority(sa)
        answers.append(maj)
        if samples > 1 and maj is not None:
            within.append(share)

    parsed = [a for a in answers if a not in (None, "")]
    counts = Counter(parsed)
    majority = counts.most_common(1)[0][0] if counts else None
    gold = item.get("answer")
    gold_n = norm(f"Answer: {gold}") if gold is not None else None
    return QuestionResult(
        id=str(item.get("id", "")), question=item["question"], gold=gold, variants=variants,
        replies=[rs[0] for rs in replies_by_variant], answers=answers, majority=majority,
        agreement=counts[majority] / len(parsed) if parsed else 0.0,
        flipped=len(counts) > 1, entropy=_entropy(counts), n_distinct=len(counts),
        unparsed=len(answers) - len(parsed),
        majority_correct=(majority == gold_n) if gold_n is not None else None,
        original_correct=(answers[0] == gold_n) if gold_n is not None else None,
        samples=samples, sample_answers=sample_answers,
        within_agreement=(sum(within) / len(within)) if within else None,
    )


def run(items: list[dict], backend, n_variants: int = 8, answer_type: str = "free",
        workers: int = 4, progress=None, samples: int = 1,
        n_llm_paraphrases: int = 0) -> tuple[list[QuestionResult], Summary]:
    """Evaluate every item. n_llm_paraphrases > 0 also asks the model itself to
    write that many extra rewordings per question (spot-check them for meaning)."""
    results = []
    for i, it in enumerate(items):
        extra = llm_paraphrases(it["question"], backend, n_llm_paraphrases) if n_llm_paraphrases else None
        results.append(evaluate_question(it, backend, n_variants, answer_type, extra, workers, samples))
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
    n_samples = results[0].samples if results else 1
    sampled = [r for r in results if r.within_agreement is not None]
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
        n_samples=n_samples,
        sampling_flip_rate=(sum(r.within_agreement < 1.0 for r in sampled) / len(sampled)) if sampled else None,
        mean_within_agreement=(sum(r.within_agreement for r in sampled) / len(sampled)) if sampled else None,
    )

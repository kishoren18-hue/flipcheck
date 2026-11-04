"""Meaning-preserving rewordings of a question.

The rule-based set only changes surface form (framing, politeness, casing,
punctuation, answer-format request), never content, so any change in a model's
answer across variants is instability, not a different question. LLM-written
paraphrases can be added with `llm_paraphrases`, but they should be spot-checked
because a paraphrasing model can change meaning.
"""

from __future__ import annotations

import re

TEMPLATES = [
    "{q}",
    "Question: {q}",
    "{q} Answer concisely.",
    "Please answer the following question.\n\n{q}",
    "I'm trying to figure something out. {q}",
    "Quick question: {q}",
    "{q_lower}",
    "Answer this: {q_nopunct}",
    "Here is a question for you.\n{q}\nGive your answer.",
    "{q} Think carefully, then give a short final answer.",
    "Could you help me with this? {q}",
    "Q: {q}\nA:",
]


def _fields(q: str) -> dict:
    q = q.strip()
    return {
        "q": q,
        "q_lower": q[:1].lower() + q[1:],
        "q_nopunct": re.sub(r"[?.!]+$", "", q),
    }


def rule_paraphrases(question: str, n: int = 8, answer_instruction: str = "") -> list[str]:
    """Return n deterministic variants (the first is always the original question)."""
    f = _fields(question)
    out = []
    for t in TEMPLATES[:max(1, min(n, len(TEMPLATES)))]:
        v = t.format(**f)
        if answer_instruction:
            v = f"{v}\n\n{answer_instruction}"
        out.append(v)
    return out


PARAPHRASE_PROMPT = """Rewrite the question below in {n} different ways. Each rewrite must ask exactly the same thing and have exactly the same correct answer. Change wording and sentence structure only; do not add, remove or hint at information.

Question: {q}

Return one rewrite per line, no numbering, nothing else."""


def llm_paraphrases(question: str, backend, n: int = 5) -> list[str]:
    """Ask a model for paraphrases. Returns at most n non-empty, de-duplicated lines."""
    text = backend(PARAPHRASE_PROMPT.format(n=n, q=question))
    seen, out = set(), []
    for line in text.splitlines():
        line = re.sub(r"^\s*(?:\d+[.)]|[-*])\s*", "", line).strip()
        if line and line.lower() not in seen:
            seen.add(line.lower())
            out.append(line)
    return out[:n]

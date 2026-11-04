"""Reduce free-text model replies to comparable answers."""

from __future__ import annotations

import re

_NUM_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}
_FINAL = re.compile(r"(?:final answer|answer)\s*(?:is|:)\s*(.+)", re.I)


def final_segment(reply: str) -> str:
    """Prefer text after an explicit 'Answer:' marker, else the last non-empty line."""
    reply = (reply or "").strip()
    matches = _FINAL.findall(reply)
    if matches:
        return matches[-1].strip()
    lines = [ln.strip() for ln in reply.splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def norm_free(reply: str) -> str:
    s = final_segment(reply).lower()
    s = re.sub(r"\*\*|__|`", "", s)
    s = re.sub(r"[^\w\s.-]", " ", s)
    s = re.sub(r"\b(?:the|a|an)\b", " ", s)
    s = re.sub(r"\.$", "", s.strip())
    return re.sub(r"\s+", " ", s).strip()


def norm_number(reply: str) -> str | None:
    s = final_segment(reply).lower().replace(",", "")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if m:
        v = float(m.group(0))
        return f"{v:g}"
    for w, v in _NUM_WORDS.items():
        if re.search(rf"\b{w}\b", s):
            return str(v)
    return None


def norm_yesno(reply: str) -> str | None:
    s = final_segment(reply).lower()
    yes = re.search(r"\b(?:yes|true|correct)\b", s)
    no = re.search(r"\b(?:no|false|incorrect|not)\b", s)
    if yes and not no:
        return "yes"
    if no and not yes:
        return "no"
    if yes and no:
        return "yes" if yes.start() < no.start() else "no"
    return None


def norm_choice(reply: str, letters: str = "ABCDE") -> str | None:
    s = final_segment(reply)
    m = re.search(rf"\(?\b([{letters}])\b\)?", s)
    if m:
        return m.group(1).upper()
    m = re.search(rf"\b([{letters.lower()}])\)", s)
    return m.group(1).upper() if m else None


NORMALIZERS = {"free": norm_free, "number": norm_number, "yesno": norm_yesno, "choice": norm_choice}

ANSWER_INSTRUCTIONS = {
    "free": "End your reply with a line of the form 'Answer: <short answer>'.",
    "number": "End your reply with a line of the form 'Answer: <number>'.",
    "yesno": "End your reply with 'Answer: yes' or 'Answer: no'.",
    "choice": "End your reply with 'Answer: <letter>'.",
}

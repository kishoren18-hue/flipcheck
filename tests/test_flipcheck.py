import json
import sys

import pytest

from flipcheck import Command, evaluate_question, rule_paraphrases, run
from flipcheck.cli import main
from flipcheck.normalize import norm_choice, norm_free, norm_number, norm_yesno
from flipcheck.report import to_html


def test_paraphrases_keep_question_and_are_distinct():
    vs = rule_paraphrases("What is the capital of France?", n=12)
    assert vs[0] == "What is the capital of France?"
    assert len(set(vs)) == len(vs) == 12
    assert all("capital of France" in v or "capital of france" in v.lower() for v in vs)


def test_normalizers():
    assert norm_free("Reasoning...\nAnswer: **The Amazon.**") == "amazon"
    assert norm_number("I think the answer is: 1,024 items") == "1024"
    assert norm_number("Answer: four") == "4"
    assert norm_yesno("Answer: No, that does not follow.") == "no"
    assert norm_yesno("Answer: True") == "yes"
    assert norm_choice("The best option is (C).") == "C"


def test_stable_model_never_flips():
    item = {"id": "a", "question": "What is 2+2?", "answer": "4"}
    r = evaluate_question(item, lambda p: "Answer: 4", n_variants=8, answer_type="number")
    assert not r.flipped and r.agreement == 1.0 and r.majority_correct


def test_brittle_model_flips():
    item = {"id": "a", "question": "What is 2+2?", "answer": "4"}
    model = lambda p: "Answer: 5" if p.startswith("Quick") else "Answer: 4"  # noqa: E731
    r = evaluate_question(item, model, n_variants=8, answer_type="number")
    assert r.flipped and r.n_distinct == 2 and r.majority == "4"
    assert r.agreement == pytest.approx(7 / 8)


def test_summary_and_stability_auroc():
    items = [{"id": str(i), "question": f"Q{i}?", "answer": "x"} for i in range(6)]

    def model(p):
        import re
        i = int(re.search(r"\bQ(\d)", p, re.I).group(1))
        if i < 3:
            return "Answer: x"  # stable and right
        return "Answer: y" if len(p) % 2 else "Answer: z"  # unstable and wrong

    results, s = run(items, model, n_variants=6, workers=1)
    assert s.accuracy_majority == pytest.approx(0.5)
    assert s.stability_auroc == pytest.approx(1.0)
    assert s.accuracy_worst_case == pytest.approx(0.5)
    html = to_html(results, s, "test")
    assert "flipcheck report" in html and "Flip rate" in html


def test_command_backend_roundtrip():
    b = Command(f"{sys.executable} -c \"import sys; sys.stdin.read(); print('Answer: 42')\"")
    assert b("anything").strip() == "Answer: 42"


def test_cli_with_command_backend(tmp_path):
    q = tmp_path / "q.jsonl"
    q.write_text(json.dumps({"question": "What is 6 times 7?", "answer": "42"}) + "\n")
    out = tmp_path / "r.html"
    cmd = f"{sys.executable} -c \"import sys; sys.stdin.read(); print('Answer: 42')\""
    assert main([str(q), "--backend", "command", "--cmd", cmd, "--variants", "4", "--answer-type", "number",
                 "--html", str(out), "--max-flip-rate", "0"]) == 0
    assert out.exists()

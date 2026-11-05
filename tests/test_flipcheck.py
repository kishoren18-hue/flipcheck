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
                 "--html", str(out), "--max-flip-rate", "0", "--cache", str(tmp_path / "c.jsonl")]) == 0
    assert out.exists()


def test_cache_resumes_without_new_calls(tmp_path):
    from flipcheck import CachedBackend

    calls = []

    def model(p):
        calls.append(p)
        return "Answer: 4"

    item = {"id": "a", "question": "What is 2+2?", "answer": "4"}
    c1 = CachedBackend(model, tmp_path / "c.jsonl", namespace="m")
    evaluate_question(item, c1, n_variants=5, answer_type="number", workers=1)
    assert len(calls) == 5 and c1.misses == 5
    c2 = CachedBackend(model, tmp_path / "c.jsonl", namespace="m")  # fresh process, same file
    evaluate_question(item, c2, n_variants=5, answer_type="number", workers=1)
    assert len(calls) == 5 and c2.hits == 5
    # a truncated last line (interrupted run) is tolerated
    with open(tmp_path / "c.jsonl", "a") as f:
        f.write('{"k": "abc", "r": ')
    CachedBackend(model, tmp_path / "c.jsonl", namespace="m")


def test_samples_separate_sampling_noise_from_wording():
    import itertools

    counter = itertools.count()

    def noisy_but_wording_blind(p):
        # every wording gets the same answer distribution: 2 of 3 samples say 4
        return "Answer: 5" if next(counter) % 3 == 2 else "Answer: 4"

    item = {"id": "a", "question": "What is 2+2?", "answer": "4"}
    r = evaluate_question(item, noisy_but_wording_blind, n_variants=6, answer_type="number", workers=1, samples=3)
    assert not r.flipped                     # wording-level majorities all agree
    assert r.within_agreement == pytest.approx(2 / 3)
    from flipcheck.core import summarize
    s = summarize([r])
    assert s.sampling_flip_rate == 1.0 and s.flip_rate == 0.0 and s.n_samples == 3


def test_llm_paraphrases_are_added():
    def model(p):
        if p.startswith("Rewrite the question"):
            return "1. What do you get when adding 2 and 2?\n2. 2 plus 2 equals what?"
        return "Answer: 4"

    results, s = run([{"question": "What is 2+2?", "answer": "4"}], model, n_variants=3,
                     answer_type="number", workers=1, n_llm_paraphrases=2)
    assert s.n_variants == 5 and not results[0].flipped


def test_gemini_backend_builds_request_and_skips_thoughts(monkeypatch):
    from flipcheck import backends

    seen = {}

    def fake_post(url, body, headers, timeout, retries=3, backoff=1.0):
        seen.update(url=url, body=body, headers=headers)
        return {"candidates": [{"content": {"parts": [
            {"text": "thinking...", "thought": True}, {"text": "Canberra"}]}}]}

    monkeypatch.setattr(backends, "_post", fake_post)
    g = backends.from_spec("gemini:gemini-3.5-flash-lite", api_key="k")
    assert g("What is the capital of Australia?") == "Canberra"
    assert seen["url"].endswith("/models/gemini-3.5-flash-lite:generateContent")
    assert seen["headers"] == {"x-goog-api-key": "k"}
    assert seen["body"]["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "low"}
    assert seen["body"]["contents"][0]["parts"][0]["text"].startswith("What is")


def test_gemini_text_reports_blocked_prompt():
    from flipcheck.backends import gemini_text

    with pytest.raises(RuntimeError, match="SAFETY"):
        gemini_text({"promptFeedback": {"blockReason": "SAFETY"}})


def test_from_spec_rejects_bad_specs():
    from flipcheck.backends import Anthropic, from_spec

    assert isinstance(from_spec("anthropic:claude-haiku-5-5", api_key="k"), Anthropic)
    for bad in ["gemini", "nope:model", "gemini:"]:
        with pytest.raises(ValueError):
            from_spec(bad)

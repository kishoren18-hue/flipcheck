"""Backend tests with fake Supabase and a fake model. Run from web/: python -m pytest api -q"""

import importlib.util
import sys
from pathlib import Path

from fastapi.testclient import TestClient

spec = importlib.util.spec_from_file_location("fc_api", Path(__file__).with_name("index.py"))
api = importlib.util.module_from_spec(spec)
sys.modules["fc_api"] = api
spec.loader.exec_module(api)
client = TestClient(api.app)

Q = {"question": "What is 17 multiplied by 23?", "answer": "391", "answer_type": "number", "model": "claude-haiku-5-5"}


class FakeResp:
    def __init__(self, status, payload):
        self.status_code, self._p = status, payload

    def json(self):
        return self._p


def fake_supabase(monkeypatch, status=200, payload=True):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, headers, json):
            assert url.endswith("/rpc/fc_take_quota")
            return FakeResp(status, payload)

    monkeypatch.setattr(api.httpx, "AsyncClient", FakeClient)


def fake_model(monkeypatch, fn):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setattr(api, "make_backend", lambda model: fn)


def test_health_lists_only_models_with_keys(monkeypatch):
    monkeypatch.setenv("AI_MODELS", "gemini-a, claude-b ,other")
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    h = client.get("/api/py/health").json()
    assert h["models"] == ["gemini-a"] and h["ai"] is True
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    assert client.get("/api/py/health").json()["models"] == ["gemini-a", "claude-b"]


def test_health_without_keys(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    h = client.get("/api/py/health").json()
    assert h["models"] == [] and h["ai"] is False


def test_backend_by_provider(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    assert isinstance(api.make_backend("gemini-3.5-flash-lite"), api.Gemini)
    assert isinstance(api.make_backend("claude-haiku-5-5"), api.Anthropic)


def test_run_requires_sign_in(monkeypatch):
    fake_model(monkeypatch, lambda p: "Answer: 391")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    assert client.post("/api/py/run", json=Q).status_code == 401


def test_run_rejects_unknown_model(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    r = client.post("/api/py/run", json={**Q, "model": "gpt-5"}, headers={"Authorization": "Bearer t"})
    assert r.status_code == 422


def test_run_rejects_links():
    r = client.post("/api/py/run", json={**Q, "question": "Summarize https://example.com please"})
    assert r.status_code == 422


def test_stable_model(monkeypatch):
    fake_supabase(monkeypatch)
    fake_model(monkeypatch, lambda p: "Let me compute.\nAnswer: 391")
    r = client.post("/api/py/run", json=Q, headers={"Authorization": "Bearer t"})
    assert r.status_code == 200
    b = r.json()
    assert b["flipped"] is False and b["agreement"] == 1.0 and b["majority_correct"] is True
    assert len(b["variants"]) == 8
    assert all("Answer:" not in v["prompt"] for v in b["variants"])  # instruction stripped for display


def test_brittle_model(monkeypatch):
    fake_supabase(monkeypatch)
    fake_model(monkeypatch, lambda p: "Answer: 381" if p.startswith("Quick") else "Answer: 391")
    b = client.post("/api/py/run", json=Q, headers={"Authorization": "Bearer t"}).json()
    assert b["flipped"] is True and b["n_distinct"] == 2 and b["majority"] == "391"


def test_quota(monkeypatch):
    fake_supabase(monkeypatch, payload=False)
    fake_model(monkeypatch, lambda p: "Answer: 391")
    assert client.post("/api/py/run", json=Q, headers={"Authorization": "Bearer t"}).status_code == 429


def test_upstream_error_is_friendly(monkeypatch):
    fake_supabase(monkeypatch)

    def boom(p):
        raise RuntimeError("HTTP 529 from https://api.anthropic.com/v1/messages")

    fake_model(monkeypatch, boom)
    r = client.post("/api/py/run", json=Q, headers={"Authorization": "Bearer t"})
    assert r.status_code == 429 and "busy" in r.json()["detail"]

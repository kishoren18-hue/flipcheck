"""Model backends. A backend is any callable: prompt (str) -> reply (str).

Only the standard library is used, so flipcheck installs anywhere.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
import urllib.error
import urllib.request


def _post(url: str, body: dict, headers: dict, timeout: int, retries: int = 3, backoff: float = 1.0) -> dict:
    data = json.dumps(body).encode()
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529) and attempt < retries - 1:
                time.sleep(backoff * 2 ** attempt)
                continue
            raise RuntimeError(f"HTTP {e.code} from {url}: {e.read()[:300]!r}") from None
    raise RuntimeError("unreachable")


class OpenAICompatible:
    """OpenAI, OpenRouter, Together, vLLM, Ollama (/v1), LM Studio..."""

    def __init__(self, model: str, base_url: str = "https://api.openai.com/v1", api_key: str | None = None,
                 temperature: float = 0.0, max_tokens: int = 512, timeout: int = 120):
        self.model, self.base_url = model, base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("API_KEY", "none")
        self.temperature, self.max_tokens, self.timeout = temperature, max_tokens, timeout

    def __call__(self, prompt: str) -> str:
        r = _post(f"{self.base_url}/chat/completions",
                  {"model": self.model, "temperature": self.temperature, "max_tokens": self.max_tokens,
                   "messages": [{"role": "user", "content": prompt}]},
                  {"Authorization": f"Bearer {self.api_key}"}, self.timeout)
        return r["choices"][0]["message"]["content"] or ""

    def __repr__(self):
        return f"OpenAICompatible({self.model})"


class Anthropic:
    """Anthropic Messages API."""

    def __init__(self, model: str, api_key: str | None = None, temperature: float = 0.0,
                 max_tokens: int = 512, timeout: int = 120):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.temperature, self.max_tokens, self.timeout = temperature, max_tokens, timeout

    def __call__(self, prompt: str) -> str:
        r = _post("https://api.anthropic.com/v1/messages",
                  {"model": self.model, "max_tokens": self.max_tokens, "temperature": self.temperature,
                   "messages": [{"role": "user", "content": prompt}]},
                  {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}, self.timeout)
        return "".join(b.get("text", "") for b in r.get("content", []))

    def __repr__(self):
        return f"Anthropic({self.model})"


class Gemini:
    """Google Gemini API (generateContent). Works with free-tier keys from Google AI Studio.

    Gemini 3 models always think a little; `thinking_level` keeps that short. Thinking
    tokens count against `max_tokens`, so leave headroom. Free-tier keys have low
    per-minute limits, so 429s are retried with a longer backoff.
    """

    BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, model: str, api_key: str | None = None, temperature: float = 0.0,
                 max_tokens: int = 1024, timeout: int = 120, thinking_level: str | None = "low"):
        self.model = model.removeprefix("models/")
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
        self.temperature, self.max_tokens, self.timeout = temperature, max_tokens, timeout
        self.thinking_level = thinking_level

    def __call__(self, prompt: str) -> str:
        config: dict = {"temperature": self.temperature, "maxOutputTokens": self.max_tokens}
        if self.thinking_level:
            config["thinkingConfig"] = {"thinkingLevel": self.thinking_level}
        r = _post(f"{self.BASE}/{self.model}:generateContent",
                  {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": config},
                  {"x-goog-api-key": self.api_key}, self.timeout, retries=5, backoff=4.0)
        return gemini_text(r)

    def __repr__(self):
        return f"Gemini({self.model})"


def gemini_text(response: dict) -> str:
    """Answer text from a generateContent response, skipping thought parts."""
    candidates = response.get("candidates") or []
    if not candidates:
        reason = (response.get("promptFeedback") or {}).get("blockReason", "no candidates")
        raise RuntimeError(f"Gemini returned no answer ({reason})")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    return "".join(p.get("text", "") for p in parts if not p.get("thought"))


class Command:
    """Any shell command that reads the prompt on stdin and prints a reply, e.g.
    `ollama run llama3.1` or `llm -m some-model`."""

    def __init__(self, cmd: str, timeout: int = 300):
        self.argv, self.timeout = shlex.split(cmd), timeout

    def __call__(self, prompt: str) -> str:
        p = subprocess.run(self.argv, input=prompt, capture_output=True, text=True, timeout=self.timeout)
        if p.returncode:
            raise RuntimeError(f"command failed ({p.returncode}): {p.stderr[:300]}")
        return p.stdout

    def __repr__(self):
        return f"Command({' '.join(self.argv)})"


def make_backend(kind: str, model: str | None = None, base_url: str | None = None, cmd: str | None = None,
                 temperature: float = 0.0):
    if kind == "openai":
        return OpenAICompatible(model, base_url or "https://api.openai.com/v1", temperature=temperature)
    if kind == "anthropic":
        return Anthropic(model, temperature=temperature)
    if kind == "gemini":
        return Gemini(model, temperature=temperature)
    if kind == "command":
        return Command(cmd)
    raise ValueError(f"unknown backend {kind!r}")


PROVIDERS = ("gemini", "anthropic", "openai")


def from_spec(spec: str, temperature: float = 0.0, **kw):
    """Build a backend from "provider:model", e.g. "gemini:gemini-3.5-flash-lite"."""
    provider, sep, model = spec.partition(":")
    if not sep or provider not in PROVIDERS or not model:
        raise ValueError(f"model spec must look like 'gemini:<model>' or 'anthropic:<model>', got {spec!r}")
    if provider == "gemini":
        return Gemini(model, temperature=temperature, **kw)
    if provider == "anthropic":
        return Anthropic(model, temperature=temperature, **kw)
    return OpenAICompatible(model, temperature=temperature, **kw)

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


def _post(url: str, body: dict, headers: dict, timeout: int, retries: int = 3) -> dict:
    data = json.dumps(body).encode()
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529) and attempt < retries - 1:
                time.sleep(2 ** attempt)
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
    if kind == "command":
        return Command(cmd)
    raise ValueError(f"unknown backend {kind!r}")

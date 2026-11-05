"""On-disk response cache so long runs can be resumed and re-analyzed for free.

Each reply is stored once, keyed by the backend's identity, the exact prompt
and the sample index. Re-running the same command reads from the cache, so an
interrupted run picks up where it stopped and changing the report costs no
extra API calls.
"""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path


class CachedBackend:
    def __init__(self, backend, path: str | Path, namespace: str | None = None):
        self.backend = backend
        self.path = Path(path)
        self.namespace = namespace or repr(backend)
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()
        self._store: dict[str, str] = {}
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    try:
                        row = json.loads(line)
                        self._store[row["k"]] = row["r"]
                    except (json.JSONDecodeError, KeyError):
                        continue  # tolerate a truncated last line from an interrupted run

    def _key(self, prompt: str, sample: int) -> str:
        return hashlib.sha256(f"{self.namespace}\x00{sample}\x00{prompt}".encode()).hexdigest()

    def sample(self, prompt: str, i: int = 0) -> str:
        k = self._key(prompt, i)
        with self._lock:
            if k in self._store:
                self.hits += 1
                return self._store[k]
        reply = self.backend(prompt)
        with self._lock:
            self.misses += 1
            self._store[k] = reply
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a") as f:
                f.write(json.dumps({"k": k, "r": reply}) + "\n")
        return reply

    def __call__(self, prompt: str) -> str:
        return self.sample(prompt, 0)

    def __repr__(self):
        return repr(self.backend)


def call(backend, prompt: str, i: int) -> str:
    """Ask for sample i of a prompt; plain backends just get called again."""
    if hasattr(backend, "sample"):
        return backend.sample(prompt, i)
    return backend(prompt)

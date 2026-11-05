"""flipcheck API (FastAPI, deployed as a Vercel Python function).

Routes
  GET  /api/py/health   which models are enabled and whether AI is configured
  POST /api/py/run      ask one question under several rewordings (signed-in users, daily quota)
"""

import os
import re
from typing import Literal

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from flipcheck import evaluate_question, summarize
from flipcheck.backends import Anthropic, Gemini

DAILY_LIMIT = 15
# Gemini models work with a free Google AI Studio key. Claude models are listed too,
# but only offered when ANTHROPIC_API_KEY is set.
DEFAULT_MODELS = "gemini-3.5-flash-lite,gemini-3.8-flash,claude-haiku-5-5"
KEY_FOR = {"gemini": "GEMINI_API_KEY", "claude": "ANTHROPIC_API_KEY"}


def provider(model: str) -> str | None:
    return next((p for p in KEY_FOR if model.startswith(p)), None)


def enabled_models() -> list[str]:
    """Configured models whose provider has an API key on this deployment."""
    configured = [m.strip() for m in os.environ.get("AI_MODELS", DEFAULT_MODELS).split(",") if m.strip()]
    return [m for m in configured if provider(m) and os.environ.get(KEY_FOR[provider(m)])]


app = FastAPI(title="flipcheck API", version="0.2.0", docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")


class RunIn(BaseModel):
    question: str = Field(min_length=8, max_length=600)
    answer: str | None = Field(default=None, max_length=120)
    answer_type: Literal["free", "number", "yesno", "choice"] = "free"
    model: str
    variants: int = Field(default=8, ge=4, le=12)

    @field_validator("question")
    @classmethod
    def no_links_or_code(cls, v: str) -> str:
        if re.search(r"https?://|```", v):
            raise ValueError("Questions can't contain links or code blocks.")
        return v.strip()


@app.get("/api/py/health")
def health():
    return {
        "ok": True,
        "ai": bool(enabled_models()),
        "accounts": bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_ANON_KEY")),
        "models": enabled_models(),
        "daily_limit": DAILY_LIMIT,
    }


async def take_quota(authorization: str | None) -> None:
    url, anon = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_ANON_KEY")
    if not (url and anon):
        raise HTTPException(503, "Accounts aren't configured on this deployment.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Sign in to run live checks.")
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{url}/rest/v1/rpc/fc_take_quota",
            headers={"apikey": anon, "Authorization": authorization, "Content-Type": "application/json"},
            json={},
        )
    if r.status_code in (401, 403):
        raise HTTPException(401, "Your session has expired. Sign in again.")
    if r.status_code != 200:
        raise HTTPException(502, "Couldn't check your usage limit. Try again shortly.")
    if r.json() is not True:
        raise HTTPException(429, f"Daily limit reached ({DAILY_LIMIT} live checks per day). Try again tomorrow.")


def make_backend(model: str):
    p = provider(model)
    key = os.environ.get(KEY_FOR[p]) if p else None
    if not key:
        raise HTTPException(503, "Live checks aren't configured on this deployment yet.")
    if p == "gemini":
        return Gemini(model, api_key=key, temperature=0.0, max_tokens=1024, timeout=40)
    return Anthropic(model, api_key=key, temperature=0.0, max_tokens=300, timeout=40)


@app.post("/api/py/run")
async def run(body: RunIn, authorization: str | None = Header(default=None)):
    models = enabled_models()
    if not models:
        raise HTTPException(503, "Live checks aren't configured on this deployment yet.")
    if body.model not in models:
        raise HTTPException(422, f"Model not available. Choose one of: {', '.join(models)}.")
    backend = make_backend(body.model)
    await take_quota(authorization)
    item = {"id": "live", "question": body.question, "answer": body.answer or None}
    try:
        # Free-tier Gemini keys have low per-minute limits, so send fewer requests at once.
        workers = 4 if provider(body.model) == "gemini" else body.variants
        r = evaluate_question(item, backend, n_variants=body.variants, answer_type=body.answer_type, workers=workers)
    except RuntimeError as e:
        msg = str(e)
        if "429" in msg or "529" in msg:
            raise HTTPException(429, "The AI service is busy. Try again in a minute.") from None
        raise HTTPException(502, "The AI service returned an error. Try again.") from None
    s = summarize([r])
    return {
        "model": body.model,
        "question": r.question,
        "gold": r.gold,
        "answer_type": body.answer_type,
        "majority": r.majority,
        "agreement": r.agreement,
        "flipped": r.flipped,
        "n_distinct": r.n_distinct,
        "majority_correct": r.majority_correct,
        "original_correct": r.original_correct,
        "variants": [
            {"prompt": v.rsplit("\n\n", 1)[0], "answer": a, "reply": (rep or "")[:400]}
            for v, a, rep in zip(r.variants, r.answers, r.replies)
        ],
        "unparsed": r.unparsed,
        "entropy": s.mean_entropy,
    }

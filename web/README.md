# flipcheck web app

A public **model stability leaderboard** and a **live tester**, built on the [flipcheck](../README.md) library.

* **Leaderboard:** every model answers 40 questions under 10 meaning-preserving rewordings. Models are ranked by accuracy under *every* wording, not just the usual one, with the gap shown next to each model. Every number comes from `src/data/leaderboard.json`, which a GitHub Action produces and commits, so the results are versioned and auditable.
* **Try a question:** signed-in users run any question live against a Gemini or Claude model under 4–12 rewordings, see each wording's answer color-coded, and save or share the result.
* **Cross-vendor:** models from different companies are ranked on the same questions and rewordings. Gemini works with a free Google AI Studio key; Claude models appear when an Anthropic key is added.

## Architecture

```
Next.js 15 · React 19 · TypeScript · Tailwind ── leaderboard page reads leaderboard.json at build time
   │
   ├── POST /api/py/run ──► FastAPI (Python, Vercel function) ──► flipcheck library ──► Gemini or Claude API
   │                           └──► Supabase RPC fc_take_quota (per-user daily limit)
   └── saved checks ──► Supabase Postgres (row-level security) + Supabase Auth

GitHub Action "update leaderboard" (manual) ──► scripts/build_leaderboard.py ──► commits leaderboard.json ──► redeploy
```

The live tester and the leaderboard use the same Python library and the same model backends (`flipcheck.backends.Gemini` and `Anthropic`), so the website can't drift from the open-source tool.

### Security model

* Saved checks are private unless the owner makes them public; row-level security enforces it, and `supabase/tests/rls_test.sql` verifies it in CI.
* Live checks require sign-in and are limited per user per day through a `security definer` function.
* Only models listed in `AI_MODELS` whose provider has a key can be called; questions can't include links or code blocks.
* API keys are server-side environment variables only.
* Free-tier Gemini requests may be used by Google to improve its models and read by human reviewers. The app says so next to the form, and the questions are trivia, not personal data.

## Run locally

```bash
cd web
npm install
pip install -e .. fastapi httpx uvicorn
cp .env.example .env.local
npm run dev        # Next.js on :3000, FastAPI on :8000
```

## Update the leaderboard

Add `GEMINI_API_KEY` (free from Google AI Studio) and optionally `ANTHROPIC_API_KEY` as repository secrets, then **Actions → update leaderboard → Run workflow**. Or locally:

```bash
GEMINI_API_KEY=... npm run leaderboard -- --models gemini-3.5-flash-lite,gemini-3.8-flash
```

Replies are cached in `.leaderboard_cache.jsonl` (and between Action runs), so if a free-tier daily limit stops a run, running it again later finishes from where it stopped. A model only appears on the board once all 40 questions are done.

## Tests

```bash
npm test && npm run test:api && npm run lint && npm run typecheck && npm run build
```

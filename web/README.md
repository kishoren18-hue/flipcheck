# flipcheck web app

A public **model stability leaderboard** and a **live tester**, built on the [flipcheck](../README.md) library.

* **Leaderboard:** every model answers 40 questions under 10 meaning-preserving rewordings. Models are ranked by accuracy under *every* wording, not just the usual one, with the gap shown next to each model. Every number comes from `src/data/leaderboard.json`, which a GitHub Action produces and commits, so the results are versioned and auditable.
* **Try a question:** signed-in users run any question live against a Claude model under 4–12 rewordings, see each wording's answer color-coded, and save or share the result.

## Architecture

```
Next.js 15 · React 19 · TypeScript · Tailwind ── leaderboard page reads leaderboard.json at build time
   │
   ├── POST /api/py/run ──► FastAPI (Python, Vercel function) ──► flipcheck library ──► Claude API
   │                           └──► Supabase RPC fc_take_quota (per-user daily limit)
   └── saved checks ──► Supabase Postgres (row-level security) + Supabase Auth

GitHub Action "update leaderboard" (manual) ──► scripts/build_leaderboard.py ──► commits leaderboard.json ──► redeploy
```

The live tester and the leaderboard use the same Python library and the same Anthropic backend, so the website can't drift from the open-source tool.

### Security model

* Saved checks are private unless the owner makes them public; row-level security enforces it, and `supabase/tests/rls_test.sql` verifies it in CI.
* Live checks require sign-in and are limited per user per day through a `security definer` function.
* Only models listed in `CLAUDE_MODELS` can be called; questions can't include links or code blocks.
* The Anthropic key is a server-side environment variable only.

## Run locally

```bash
cd web
npm install
pip install -e .. fastapi httpx uvicorn
cp .env.example .env.local
npm run dev        # Next.js on :3000, FastAPI on :8000
```

## Update the leaderboard

Add `ANTHROPIC_API_KEY` as a repository secret, then **Actions → update leaderboard → Run workflow**. Or locally:

```bash
ANTHROPIC_API_KEY=... npm run leaderboard -- --models claude-haiku-5-5,claude-sonnet-5-5
```

Replies are cached in `.leaderboard_cache.jsonl`, so reruns only pay for new questions or models.

## Tests

```bash
npm test && npm run test:api && npm run lint && npm run typecheck && npm run build
```

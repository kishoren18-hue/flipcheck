import { Card } from "@/components/ui";

export const metadata = { title: "Method" };

const REWORDINGS = [
  "What is 17 multiplied by 23?",
  "Question: What is 17 multiplied by 23?",
  "Quick question: What is 17 multiplied by 23?",
  "what is 17 multiplied by 23?",
  "Could you help me with this? What is 17 multiplied by 23?",
  "Q: What is 17 multiplied by 23? A:",
];

export default function About() {
  return (
    <main className="mx-auto max-w-3xl space-y-10 px-4 py-10">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Method</h1>
        <p className="mt-3 text-lg text-muted">
          The rewordings change surface form only (framing, politeness, casing, punctuation), never content. So if the answer
          changes, the only explanation is instability.
        </p>
      </div>
      <Card>
        <h2 className="mb-3 font-semibold">Example rewordings</h2>
        <ul className="space-y-1.5 font-mono text-sm">
          {REWORDINGS.map((r) => (
            <li key={r} className="rounded bg-surface-2 px-3 py-1.5">
              {r}
            </li>
          ))}
        </ul>
      </Card>
      <section className="space-y-3 text-muted">
        <h2 className="text-xl font-semibold text-ink">Metrics</h2>
        <p><b className="text-ink">Flip rate</b>: share of questions whose answer changed under at least one rewording.</p>
        <p><b className="text-ink">Accuracy, every wording</b>: a question counts only if all rewordings got the right answer. This is the number the leaderboard ranks by.</p>
        <p><b className="text-ink">Stability → correctness</b>: the AUROC of agreement as a predictor of being right. Above 0.5 means consistency is a usable confidence signal, even for models that don&apos;t expose probabilities.</p>
      </section>
      <section className="space-y-3 text-muted">
        <h2 className="text-xl font-semibold text-ink">Reproducibility</h2>
        <p>
          The leaderboard is produced by a GitHub Action running the open-source <code className="text-ink">flipcheck</code> Python
          library at temperature 0. Every question, every rewording and every parsed answer is committed to the repository in{" "}
          <code className="text-ink">web/src/data/leaderboard.json</code>.
        </p>
      </section>
      <section>
        <h2 className="mb-3 text-xl font-semibold">Architecture</h2>
        <Card className="overflow-x-auto font-mono text-[13px] leading-6">
          <pre>{`Next.js 15 (TypeScript, Tailwind) ── leaderboard page reads leaderboard.json
   │
   ├─ POST /api/py/run ──► FastAPI (Python) ──► flipcheck library ──► Gemini / Claude API
   │                            └─► Supabase RPC: per-user daily quota
   └─ save / share checks ──► Supabase Postgres (row-level security) + Auth

GitHub Action (manual) ──► scripts/build_leaderboard.py ──► commits leaderboard.json`}</pre>
        </Card>
      </section>
    </main>
  );
}

import { AnswerChips } from "@/components/answer-chips";
import { Badge, ButtonLink, Card } from "@/components/ui";
import { fragileQuestions, leaderboard, pct, ranked } from "@/lib/leaderboard";

export default function LeaderboardPage() {
  const lb = leaderboard;
  const models = ranked(lb);
  const fragile = fragileQuestions(lb);

  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <div className="max-w-3xl">
        <p className="mb-3 text-sm font-medium text-accent">Model stability leaderboard</p>
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          Ask the same question ten ways. Does the answer change?
        </h1>
        <p className="mt-4 text-lg text-muted">
          Benchmarks ask each question once, in one phrasing. Here every model answers {lb.n_questions} questions under{" "}
          {lb.n_variants} meaning-preserving rewordings (&quot;Quick question:&quot;, a lowercase version, a polite version…). A
          model that changes its answer when only the wording changes doesn&apos;t really know it.
        </p>
      </div>

      {models.length === 0 ? (
        <Card className="mt-10 border-dashed text-center">
          <h2 className="font-semibold">The first leaderboard run hasn&apos;t happened yet</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-muted">
            Results are produced by a GitHub Action and committed to the repository, so every number is reproducible. Until the
            first run, you can test any question live.
          </p>
          <ButtonLink href="/try" className="mt-4">
            Try a question
          </ButtonLink>
        </Card>
      ) : (
        <>
          <section className="mt-10" aria-labelledby="board-h">
            <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
              <h2 id="board-h" className="text-xl font-semibold">
                Results
              </h2>
              <p className="text-xs text-muted">
                Updated {lb.generated_at ? new Date(lb.generated_at).toLocaleDateString("en-US", { dateStyle: "medium" }) : "–"} ·
                temperature {lb.temperature} · data in{" "}
                <a className="underline" href="https://github.com/kishoren18-hue/flipcheck/blob/main/web/src/data/leaderboard.json">
                  leaderboard.json
                </a>
              </p>
            </div>
            <div className="overflow-x-auto rounded-xl border border-line bg-surface">
              <table className="w-full min-w-[640px] text-sm">
                <thead className="border-b border-line text-left text-xs uppercase tracking-wide text-muted">
                  <tr>
                    <th className="px-4 py-3">#</th>
                    <th className="px-4 py-3">Model</th>
                    <th className="px-4 py-3">Accuracy, usual wording</th>
                    <th className="px-4 py-3">Accuracy, every wording</th>
                    <th className="px-4 py-3">Flip rate</th>
                    <th className="px-4 py-3" title="Does agreement across rewordings predict a correct answer? 0.5 = no signal">
                      Stability → correctness
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {models.map((m, i) => {
                    const s = m.summary;
                    const gap = (s.accuracy_original ?? 0) - (s.accuracy_worst_case ?? 0);
                    return (
                      <tr key={m.model}>
                        <td className="px-4 py-3 font-mono text-muted">{i + 1}</td>
                        <td className="px-4 py-3 font-mono font-medium">{m.model}</td>
                        <td className="px-4 py-3 tabular-nums">{pct(s.accuracy_original)}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2 tabular-nums">
                            <span className="font-semibold">{pct(s.accuracy_worst_case)}</span>
                            {gap > 0.005 && <Badge tone="danger">−{Math.round(gap * 100)} pts</Badge>}
                          </div>
                          <div className="mt-1.5 h-1.5 w-40 overflow-hidden rounded-full bg-surface-2">
                            <div className="h-full bg-accent" style={{ width: pct(s.accuracy_worst_case) }} />
                          </div>
                        </td>
                        <td className="px-4 py-3 tabular-nums">{pct(s.flip_rate)}</td>
                        <td className="px-4 py-3 tabular-nums">{s.stability_auroc == null ? "–" : s.stability_auroc.toFixed(2)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="mt-2 text-xs text-muted">
              Ranked by accuracy under every wording: a question only counts if the model answered it correctly in all{" "}
              {lb.n_variants} phrasings.
            </p>
          </section>

          <section className="mt-12" aria-labelledby="fragile-h">
            <h2 id="fragile-h" className="text-xl font-semibold">
              Questions that made models flip
            </h2>
            <p className="mt-1 text-sm text-muted">Each square is one rewording; a second color means the answer changed.</p>
            {fragile.length === 0 ? (
              <p className="mt-4 text-sm text-muted">No model changed its answer on any question.</p>
            ) : (
              <ul className="mt-4 divide-y divide-line overflow-hidden rounded-xl border border-line bg-surface">
                {fragile.map((row) => (
                  <li key={row.id} className="grid gap-3 px-4 py-4 md:grid-cols-[1fr_auto]">
                    <div>
                      <p className="font-medium">{row.question}</p>
                      <p className="mt-0.5 text-xs text-muted">
                        Correct answer: <span className="font-mono">{row.gold}</span>
                      </p>
                    </div>
                    <div className="space-y-2">
                      {row.per.map((q, i) =>
                        q ? (
                          <div key={lb.models[i].model} className="flex items-start gap-3">
                            <span className="w-36 shrink-0 truncate pt-0.5 font-mono text-xs text-muted">{lb.models[i].model}</span>
                            <AnswerChips answers={q.answers} size={12} />
                          </div>
                        ) : null,
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}

      <Card className="mt-12 flex flex-wrap items-center justify-between gap-4 bg-accent-soft">
        <div>
          <h2 className="font-semibold">Have a question you think breaks a model?</h2>
          <p className="text-sm text-muted">Run it live under up to 12 rewordings and share the result.</p>
        </div>
        <ButtonLink href="/try">Try a question</ButtonLink>
      </Card>
    </main>
  );
}

"use client";

import { useState } from "react";

import { AnswerChips, colorMap } from "./answer-chips";
import { Badge, Stat } from "./ui";

export type RunResult = {
  model: string;
  question: string;
  gold: string | null;
  majority: string | null;
  agreement: number;
  flipped: boolean;
  n_distinct: number;
  majority_correct: boolean | null;
  original_correct: boolean | null;
  unparsed: number;
  variants: { prompt: string; answer: string | null; reply: string }[];
};

export function CheckResult({ r }: { r: RunResult }) {
  const [open, setOpen] = useState<number | null>(null);
  const answers = r.variants.map((v) => v.answer);
  const colors = colorMap(answers);
  const verdict = !r.flipped
    ? { tone: "ok" as const, text: "Stable: every rewording got the same answer" }
    : { tone: "danger" as const, text: `Flipped: ${r.n_distinct} different answers across ${r.variants.length} rewordings` };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <Badge tone={verdict.tone} className="px-3 py-1 text-sm">
          {verdict.text}
        </Badge>
        <span className="font-mono text-xs text-muted">{r.model}</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Stat label="Agreement" value={`${Math.round(r.agreement * 100)}%`} hint="rewordings matching the most common answer" />
        <Stat label="Most common answer" value={r.majority ?? "–"} hint={r.gold ? `expected: ${r.gold}` : "no expected answer given"} />
        <Stat
          label="Correct?"
          value={r.majority_correct == null ? "–" : r.majority_correct ? "Yes" : "No"}
          hint={r.original_correct == null ? undefined : `original wording: ${r.original_correct ? "correct" : "wrong"}`}
        />
      </div>
      <AnswerChips answers={answers} size={22} />
      <ul className="divide-y divide-line overflow-hidden rounded-xl border border-line bg-surface">
        {r.variants.map((v, i) => (
          <li key={i}>
            <button className="flex w-full items-start gap-3 px-4 py-3 text-left text-sm hover:bg-surface-2" onClick={() => setOpen(open === i ? null : i)} aria-expanded={open === i}>
              <span
                className="mt-1 inline-block h-3 w-3 shrink-0 rounded-sm"
                style={{ background: v.answer ? colors.get(v.answer) : "transparent", border: v.answer ? "none" : "1.5px dashed var(--muted)" }}
              />
              <span className="min-w-0 flex-1 whitespace-pre-wrap">{v.prompt}</span>
              <span className="shrink-0 font-mono font-medium">{v.answer ?? "?"}</span>
            </button>
            {open === i && (
              <pre className="mx-4 mb-3 whitespace-pre-wrap rounded-lg bg-surface-2 p-3 font-mono text-xs text-muted">{v.reply || "(empty reply)"}</pre>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

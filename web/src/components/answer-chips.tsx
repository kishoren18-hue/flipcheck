const PALETTE = ["#4f46e5", "#d9822b", "#0f9488", "#c0397a", "#7a5cc7", "#8a8f2a"];

/** One colored square per rewording; same color = same answer. */
export function colorMap(answers: (string | null)[]): Map<string, string> {
  const m = new Map<string, string>();
  for (const a of answers) if (a && !m.has(a)) m.set(a, PALETTE[m.size % PALETTE.length]);
  return m;
}

export function AnswerChips({ answers, size = 14, legend = true }: { answers: (string | null)[]; size?: number; legend?: boolean }) {
  const colors = colorMap(answers);
  return (
    <div>
      <div className="flex flex-wrap gap-[3px]" role="img" aria-label={`Answers per rewording: ${answers.map((a) => a ?? "unreadable").join(", ")}`}>
        {answers.map((a, i) => (
          <span
            key={i}
            title={a ?? "no answer found"}
            className="rounded-[3px]"
            style={{
              width: size,
              height: size,
              background: a ? colors.get(a) : "transparent",
              border: a ? "none" : "1.5px dashed var(--muted)",
            }}
          />
        ))}
      </div>
      {legend && colors.size > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted">
          {[...colors].map(([a, c]) => (
            <span key={a} className="inline-flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-sm" style={{ background: c }} />
              <span className="font-mono">{a}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

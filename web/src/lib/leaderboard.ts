import raw from "@/data/leaderboard.json";

export type LbQuestion = {
  id: string;
  question: string;
  gold: string | null;
  answers: (string | null)[];
  majority: string | null;
  agreement: number;
  flipped: boolean;
  majority_correct: boolean | null;
  original_correct: boolean | null;
};

export type LbModel = {
  model: string;
  summary: {
    n_questions: number;
    flip_rate: number;
    mean_agreement: number;
    accuracy_original: number | null;
    accuracy_majority: number | null;
    accuracy_worst_case: number | null;
    stability_auroc: number | null;
    unparsed_rate: number;
  };
  questions: LbQuestion[];
};

export type Leaderboard = {
  generated_at: string | null;
  n_questions: number;
  n_variants: number;
  temperature: number;
  models: LbModel[];
};

export const leaderboard = raw as Leaderboard;

/** Models ranked by accuracy under every wording, then by lower flip rate. */
export function ranked(lb: Leaderboard): LbModel[] {
  return [...lb.models].sort(
    (a, b) =>
      (b.summary.accuracy_worst_case ?? 0) - (a.summary.accuracy_worst_case ?? 0) ||
      a.summary.flip_rate - b.summary.flip_rate,
  );
}

/** Questions where at least one model flipped, most unstable first. */
export function fragileQuestions(lb: Leaderboard, limit = 12) {
  const ids = lb.models[0]?.questions.map((q) => q.id) ?? [];
  const rows = ids.map((id) => {
    const per = lb.models.map((m) => m.questions.find((q) => q.id === id));
    const meanAgreement = per.reduce((s, q) => s + (q?.agreement ?? 1), 0) / Math.max(per.length, 1);
    return { id, question: per[0]?.question ?? "", gold: per[0]?.gold ?? null, per, meanAgreement };
  });
  return rows.filter((r) => r.per.some((q) => q?.flipped)).sort((a, b) => a.meanAgreement - b.meanAgreement).slice(0, limit);
}

export const pct = (v: number | null | undefined) => (v == null ? "–" : `${Math.round(v * 100)}%`);

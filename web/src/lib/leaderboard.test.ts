import { describe, expect, it } from "vitest";

import { colorMap } from "@/components/answer-chips";

import { fragileQuestions, type Leaderboard, ranked } from "./leaderboard";

const q = (id: string, agreement: number, flipped: boolean) => ({
  id,
  question: id,
  gold: "1",
  answers: [],
  majority: "1",
  agreement,
  flipped,
  majority_correct: true,
  original_correct: true,
});

const model = (name: string, worst: number, flip: number, qs: ReturnType<typeof q>[]) => ({
  model: name,
  summary: {
    n_questions: qs.length,
    flip_rate: flip,
    mean_agreement: 0.9,
    accuracy_original: 0.9,
    accuracy_majority: 0.9,
    accuracy_worst_case: worst,
    stability_auroc: 0.7,
    unparsed_rate: 0,
  },
  questions: qs,
});

const lb: Leaderboard = {
  generated_at: "2026-11-05T00:00:00Z",
  n_questions: 2,
  n_variants: 10,
  temperature: 0,
  models: [
    model("a", 0.6, 0.3, [q("q1", 0.6, true), q("q2", 1, false)]),
    model("b", 0.8, 0.1, [q("q1", 0.9, true), q("q2", 1, false)]),
  ],
};

describe("leaderboard", () => {
  it("ranks by accuracy under every wording", () => {
    expect(ranked(lb).map((m) => m.model)).toEqual(["b", "a"]);
  });

  it("lists only questions that flipped, least stable first", () => {
    const f = fragileQuestions(lb);
    expect(f.map((r) => r.id)).toEqual(["q1"]);
    expect(f[0].meanAgreement).toBeCloseTo(0.75);
  });

  it("assigns one color per distinct answer", () => {
    const m = colorMap(["4", "5", "4", null]);
    expect(m.size).toBe(2);
    expect(m.get("4")).not.toBe(m.get("5"));
  });
});

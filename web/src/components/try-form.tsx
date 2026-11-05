"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getBrowserClient } from "@/lib/supabase/client";

import { CheckResult, type RunResult } from "./check-result";
import { Alert, Button, Card, Input, Label, Textarea } from "./ui";

const EXAMPLES = [
  { q: "How many letters r are in the word strawberry?", a: "3", t: "number" },
  { q: "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How many cents does the ball cost?", a: "5", t: "number" },
  { q: "Tom has 3 sisters. Each of his sisters has 1 brother. How many brothers does Tom have?", a: "0", t: "number" },
  { q: "Is Reno, Nevada farther west than Los Angeles, California?", a: "yes", t: "yesno" },
] as const;

type Health = { ai: boolean; accounts: boolean; models: string[]; daily_limit: number } | null;

export function TryForm({ signedIn }: { signedIn: boolean }) {
  const router = useRouter();
  const [health, setHealth] = useState<Health>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [type, setType] = useState<"free" | "number" | "yesno" | "choice">("number");
  const [model, setModel] = useState("");
  const [variants, setVariants] = useState(8);
  const [result, setResult] = useState<RunResult | null>(null);
  const [busy, setBusy] = useState<"" | "run" | "save">("");
  const [error, setError] = useState("");
  const [isPublic, setIsPublic] = useState(true);

  useEffect(() => {
    fetch("/api/py/health")
      .then((r) => (r.ok ? r.json() : null))
      .then((h: Health) => {
        setHealth(h);
        if (h?.models?.length) setModel(h.models[0]);
      })
      .catch(() => setHealth(null));
  }, []);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    setBusy("run");
    setError("");
    setResult(null);
    try {
      const { data } = (await getBrowserClient()?.auth.getSession()) ?? { data: { session: null } };
      const token = data.session?.access_token;
      if (!token) throw new Error("Sign in to run live checks.");
      const res = await fetch("/api/py/run", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ question, answer: answer.trim() || null, answer_type: type, model, variants }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(Array.isArray(body.detail) ? body.detail[0]?.msg ?? "Check your input." : body.detail ?? `Request failed (${res.status}).`);
      setResult(body);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy("");
    }
  }

  async function save() {
    if (!result) return;
    setBusy("save");
    const { data, error: err } = await getBrowserClient()!
      .from("fc_checks")
      .insert({ question: result.question, model: result.model, agreement: result.agreement, flipped: result.flipped, result, is_public: isPublic })
      .select("id")
      .single();
    setBusy("");
    if (err) return setError(`Couldn't save: ${err.message}`);
    router.push(`/c/${data.id}`);
  }

  const disabled = !signedIn || !health?.ai;

  return (
    <div className="space-y-8">
      <Card>
        <form onSubmit={run} className="space-y-5">
          <div>
            <div className="mb-1.5 flex items-center justify-between">
              <Label htmlFor="q" className="mb-0">
                Question
              </Label>
              <div className="flex flex-wrap gap-1">
                {EXAMPLES.map((x, i) => (
                  <button
                    key={i}
                    type="button"
                    className="rounded-md border border-line px-2 py-0.5 text-xs text-muted hover:bg-surface-2 hover:text-ink"
                    onClick={() => {
                      setQuestion(x.q);
                      setAnswer(x.a);
                      setType(x.t);
                    }}
                  >
                    Example {i + 1}
                  </button>
                ))}
              </div>
            </div>
            <Textarea id="q" rows={3} required minLength={8} maxLength={600} value={question} onChange={(e) => setQuestion(e.target.value)} className="font-sans" placeholder="A question with one short, checkable answer…" />
          </div>
          <div className="grid gap-4 sm:grid-cols-4">
            <div>
              <Label htmlFor="a">Expected answer (optional)</Label>
              <Input id="a" value={answer} maxLength={120} onChange={(e) => setAnswer(e.target.value)} placeholder="e.g. 3" />
            </div>
            <div>
              <Label htmlFor="t">Answer type</Label>
              <select id="t" value={type} onChange={(e) => setType(e.target.value as typeof type)} className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm">
                <option value="number">Number</option>
                <option value="yesno">Yes / no</option>
                <option value="choice">Multiple choice letter</option>
                <option value="free">Short text</option>
              </select>
            </div>
            <div>
              <Label htmlFor="m">Model</Label>
              <select id="m" value={model} onChange={(e) => setModel(e.target.value)} className="w-full rounded-lg border border-line bg-surface px-3 py-2 font-mono text-sm">
                {(health?.models ?? []).map((m) => (
                  <option key={m}>{m}</option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="v">Rewordings: {variants}</Label>
              <input id="v" type="range" min={4} max={12} value={variants} onChange={(e) => setVariants(+e.target.value)} className="mt-3 w-full accent-[var(--accent)]" />
            </div>
          </div>
          {health && !health.ai && <Alert tone="warn">Live checks aren&apos;t enabled on this deployment yet.</Alert>}
          {!signedIn && (
            <Alert>
              <Link href="/login?next=/try" className="font-medium text-accent underline">
                Sign in
              </Link>{" "}
              to run live checks (free, {health?.daily_limit ?? 15} per day).
            </Alert>
          )}
          <div className="flex items-center gap-3">
            <Button type="submit" disabled={disabled || question.trim().length < 8} loading={busy === "run"}>
              {busy === "run" ? `Asking ${variants} ways…` : "Run check"}
            </Button>
            <span className="text-xs text-muted">Temperature 0, so differences come from wording, not randomness.</span>
          </div>
        </form>
      </Card>

      {error && (
        <Alert tone="danger" title="Something went wrong">
          {error}
        </Alert>
      )}

      {result && (
        <section className="space-y-4">
          <CheckResult r={result} />
          <Card className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={isPublic} onChange={(e) => setIsPublic(e.target.checked)} />
              Anyone with the link can view
            </label>
            <Button onClick={save} loading={busy === "save"} className="ml-auto">
              Save and get a link
            </Button>
          </Card>
        </section>
      )}
    </div>
  );
}

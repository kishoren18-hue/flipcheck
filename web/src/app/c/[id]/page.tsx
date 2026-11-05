import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { CheckResult, type RunResult } from "@/components/check-result";
import { DeleteCheck } from "@/components/delete-check";
import { getServerClient, getUser } from "@/lib/supabase/server";

type Row = { id: string; user_id: string; question: string; result: RunResult; is_public: boolean; created_at: string };

async function load(id: string): Promise<Row | null> {
  if (!/^[0-9a-f-]{36}$/i.test(id)) return null;
  const supabase = await getServerClient();
  if (!supabase) return null;
  const { data } = await supabase.from("fc_checks").select("id,user_id,question,result,is_public,created_at").eq("id", id).maybeSingle();
  return data as Row | null;
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const r = await load((await params).id);
  return { title: r ? r.question.slice(0, 60) : "Check", robots: { index: false } };
}

export default async function CheckPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [row, user] = await Promise.all([load(id), getUser()]);
  if (!row) notFound();
  const isOwner = user?.id === row.user_id;
  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      <Link href={isOwner ? "/checks" : "/"} className="text-sm text-muted hover:text-ink">
        ← {isOwner ? "My checks" : "Leaderboard"}
      </Link>
      <div className="mb-8 mt-3 flex flex-wrap items-start gap-4">
        <h1 className="min-w-0 flex-1 text-2xl font-semibold tracking-tight">{row.question}</h1>
        {isOwner && <DeleteCheck id={row.id} />}
      </div>
      <CheckResult r={row.result} />
      <p className="mt-6 text-xs text-muted">
        Checked {new Date(row.created_at).toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" })}.{" "}
        <Link href="/try" className="underline">
          Try your own question
        </Link>
      </p>
    </main>
  );
}

import Link from "next/link";
import { redirect } from "next/navigation";

import { Badge, ButtonLink } from "@/components/ui";
import { supabaseConfigured } from "@/lib/supabase/env";
import { getServerClient, getUser } from "@/lib/supabase/server";

export const metadata = { title: "My checks" };
export const dynamic = "force-dynamic";

type Row = { id: string; question: string; model: string; agreement: number; flipped: boolean; is_public: boolean; created_at: string };

export default async function ChecksPage() {
  if (!supabaseConfigured) redirect("/login");
  const user = await getUser();
  if (!user) redirect("/login?next=/checks");
  const supabase = (await getServerClient())!;
  const { data, error } = await supabase
    .from("fc_checks")
    .select("id,question,model,agreement,flipped,is_public,created_at")
    .eq("user_id", user.id)
    .order("created_at", { ascending: false })
    .limit(100);
  const rows = (data ?? []) as Row[];

  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">My checks</h1>
        <ButtonLink href="/try">New check</ButtonLink>
      </div>
      {error && <p className="text-sm text-danger">Couldn&apos;t load checks: {error.message}</p>}
      {rows.length === 0 && !error ? (
        <div className="rounded-xl border border-dashed border-line p-10 text-center text-muted">No saved checks yet.</div>
      ) : (
        <ul className="divide-y divide-line overflow-hidden rounded-xl border border-line bg-surface">
          {rows.map((r) => (
            <li key={r.id}>
              <Link href={`/c/${r.id}`} className="flex flex-wrap items-center gap-3 px-4 py-3 hover:bg-surface-2">
                <span className="min-w-0 flex-1 truncate">{r.question}</span>
                <span className="font-mono text-xs text-muted">{r.model}</span>
                <Badge tone={r.flipped ? "danger" : "ok"}>{r.flipped ? "Flipped" : "Stable"} · {Math.round(r.agreement * 100)}%</Badge>
                {r.is_public && <Badge tone="accent">Public</Badge>}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

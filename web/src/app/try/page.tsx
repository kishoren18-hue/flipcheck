import { TryForm } from "@/components/try-form";
import { getUser } from "@/lib/supabase/server";

export const metadata = { title: "Try a question" };
export const dynamic = "force-dynamic";

export default async function TryPage() {
  const user = await getUser();
  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">Try a question</h1>
      <p className="mb-8 mt-2 text-muted">
        Your question is asked several ways at once. Same color everywhere means the model is stable; a second color means
        the wording alone changed its answer.
      </p>
      <TryForm signedIn={Boolean(user)} />
    </main>
  );
}

import { ButtonLink } from "@/components/ui";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-md px-4 py-24 text-center">
      <h1 className="text-2xl font-semibold">Not found</h1>
      <p className="mt-2 text-muted">This page or report doesn&apos;t exist, or it&apos;s private.</p>
      <ButtonLink href="/" className="mt-6">
        Go to note-drift
      </ButtonLink>
    </main>
  );
}

"use client";

import { Button } from "@/components/ui";

export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  return (
    <main className="mx-auto max-w-md px-4 py-24 text-center">
      <h1 className="text-2xl font-semibold">Something went wrong</h1>
      <p className="mt-2 text-muted">The page hit an unexpected error. Your data is safe.</p>
      <Button className="mt-6" onClick={reset}>
        Try again
      </Button>
    </main>
  );
}

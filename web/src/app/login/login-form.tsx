"use client";

import { useState } from "react";

import { Alert, Button, Input, Label } from "@/components/ui";
import { getBrowserClient } from "@/lib/supabase/client";

export function LoginForm({ next, linkError }: { next: string; linkError: boolean }) {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [message, setMessage] = useState("");
  const supabase = getBrowserClient();

  if (!supabase) {
    return (
      <Alert tone="warn" title="Accounts aren't set up yet" className="mt-6">
        This deployment has no database configured. Everything that doesn&apos;t need an account still works.
      </Alert>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setState("sending");
    const redirect = `${window.location.origin}/auth/callback?next=${encodeURIComponent(next)}`;
    const { error } = await supabase!.auth.signInWithOtp({ email, options: { emailRedirectTo: redirect } });
    if (error) {
      setState("error");
      setMessage(
        error.status === 429
          ? "Too many sign-in emails were sent recently. Please wait a few minutes and try again."
          : error.message,
      );
    } else {
      setState("sent");
    }
  }

  return (
    <div className="mt-6 space-y-4">
      {linkError && (
        <Alert tone="danger" title="That sign-in link didn't work">
          It may have expired or already been used. Request a new one below.
        </Alert>
      )}
      {state === "sent" ? (
        <Alert tone="ok" title="Check your email">
          We sent a sign-in link to <b>{email}</b>. Open it on this device.
        </Alert>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>
          {state === "error" && <Alert tone="danger">{message}</Alert>}
          <Button type="submit" loading={state === "sending"} className="w-full">
            Email me a sign-in link
          </Button>
        </form>
      )}
    </div>
  );
}

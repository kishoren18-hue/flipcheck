"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { getBrowserClient } from "@/lib/supabase/client";

import { Button } from "./ui";

export function SignOutButton() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  return (
    <Button
      variant="ghost"
      className="px-3 py-1.5"
      loading={busy}
      onClick={async () => {
        setBusy(true);
        await getBrowserClient()?.auth.signOut();
        router.push("/");
        router.refresh();
      }}
    >
      Sign out
    </Button>
  );
}

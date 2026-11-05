"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { getBrowserClient } from "@/lib/supabase/client";

import { Button } from "./ui";

export function DeleteCheck({ id }: { id: string }) {
  const router = useRouter();
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  return confirming ? (
    <Button
      variant="danger"
      loading={busy}
      onClick={async () => {
        setBusy(true);
        await getBrowserClient()?.from("fc_checks").delete().eq("id", id);
        router.push("/checks");
        router.refresh();
      }}
    >
      Confirm delete
    </Button>
  ) : (
    <Button variant="danger" onClick={() => setConfirming(true)}>
      Delete
    </Button>
  );
}

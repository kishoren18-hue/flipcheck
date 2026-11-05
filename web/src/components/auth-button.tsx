import { getUser } from "@/lib/supabase/server";
import { supabaseConfigured } from "@/lib/supabase/env";

import { ButtonLink } from "./ui";
import { SignOutButton } from "./sign-out-button";

export async function AuthButton() {
  if (!supabaseConfigured) return null;
  const user = await getUser();
  if (!user) {
    return (
      <ButtonLink href="/login" variant="secondary" className="px-3 py-1.5">
        Sign in
      </ButtonLink>
    );
  }
  return (
    <div className="flex items-center gap-2">
      <span className="hidden max-w-40 truncate text-sm text-muted sm:inline" title={user.email ?? ""}>
        {user.email}
      </span>
      <SignOutButton />
    </div>
  );
}

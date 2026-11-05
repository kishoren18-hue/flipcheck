import { createServerClient } from "@supabase/ssr";
import type { SupabaseClient, User } from "@supabase/supabase-js";
import { cookies } from "next/headers";

import { SUPABASE_ANON_KEY, SUPABASE_URL, supabaseConfigured } from "./env";

export async function getServerClient(): Promise<SupabaseClient | null> {
  if (!supabaseConfigured) return null;
  const store = await cookies();
  return createServerClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    cookies: {
      getAll: () => store.getAll(),
      setAll: (list) => {
        try {
          list.forEach(({ name, value, options }) => store.set(name, value, options));
        } catch {
          // called from a Server Component: the middleware refreshes the session instead
        }
      },
    },
  });
}

export async function getUser(): Promise<User | null> {
  const supabase = await getServerClient();
  if (!supabase) return null;
  const { data } = await supabase.auth.getUser();
  return data.user ?? null;
}

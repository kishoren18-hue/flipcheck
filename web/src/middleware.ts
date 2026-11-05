import { createServerClient } from "@supabase/ssr";
import { type NextRequest, NextResponse } from "next/server";

import { SUPABASE_ANON_KEY, SUPABASE_URL, supabaseConfigured } from "@/lib/supabase/env";

// Keeps the Supabase session cookie fresh on every navigation.
export async function middleware(request: NextRequest) {
  let response = NextResponse.next({ request });
  if (!supabaseConfigured) return response;

  const supabase = createServerClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (list) => {
        list.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        list.forEach(({ name, value, options }) => response.cookies.set(name, value, options));
      },
    },
  });
  await supabase.auth.getUser();
  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api/py|.*\\.(?:svg|png|jpg|jpeg|gif|webp|json)$).*)"],
};

import { LoginForm } from "./login-form";

export const metadata = { title: "Sign in" };

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; error?: string }>;
}) {
  const { next, error } = await searchParams;
  return (
    <main className="mx-auto w-full max-w-md px-4 py-16">
      <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
      <p className="mt-2 text-sm text-muted">
        We&apos;ll email you a one-time sign-in link. No password needed.
      </p>
      <LoginForm next={next ?? "/"} linkError={error === "link"} />
    </main>
  );
}

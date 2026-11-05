import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";
import type { Metadata } from "next";
import Link from "next/link";

import { AuthButton } from "@/components/auth-button";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "flipcheck: does the answer survive a reworded question?", template: "%s · flipcheck" },
  description:
    "A public leaderboard of how often language models change their answer when only the wording of a question changes, plus a live tester.",
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
};

const nav = [
  { href: "/", label: "Leaderboard" },
  { href: "/try", label: "Try a question" },
  { href: "/checks", label: "My checks" },
  { href: "/about", label: "Method" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="flex min-h-screen flex-col" style={{ ["--accent" as string]: "#4f46e5" }}>
        <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-2">
          Skip to content
        </a>
        <header className="sticky top-0 z-40 border-b border-line bg-bg/85 backdrop-blur">
          <div className="mx-auto flex h-14 max-w-6xl items-center gap-6 px-4">
            <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
              <span aria-hidden className="grid h-7 w-7 place-items-center rounded-md bg-accent font-mono text-sm text-accent-ink">
                ⇄
              </span>
              flipcheck
            </Link>
            <nav aria-label="Main" className="hidden gap-1 text-sm sm:flex">
              {nav.map((n) => (
                <Link key={n.href} href={n.href} className="rounded-md px-3 py-1.5 text-muted hover:bg-surface-2 hover:text-ink">
                  {n.label}
                </Link>
              ))}
            </nav>
            <div className="ml-auto">
              <AuthButton />
            </div>
          </div>
          <nav aria-label="Main mobile" className="flex gap-1 overflow-x-auto px-3 pb-2 text-sm sm:hidden">
            {nav.map((n) => (
              <Link key={n.href} href={n.href} className="shrink-0 rounded-md px-3 py-1 text-muted hover:bg-surface-2">
                {n.label}
              </Link>
            ))}
          </nav>
        </header>
        <div id="main" className="flex-1">
          {children}
        </div>
        <footer className="border-t border-line py-6 text-center text-xs text-muted">
          Open source:{" "}
          <a className="underline hover:text-ink" href="https://github.com/kishoren18-hue/flipcheck">
            github.com/kishoren18-hue/flipcheck
          </a>
        </footer>
      </body>
    </html>
  );
}

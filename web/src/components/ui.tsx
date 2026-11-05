import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";

export function cx(...parts: (string | false | null | undefined)[]) {
  return parts.filter(Boolean).join(" ");
}

type Variant = "primary" | "secondary" | "ghost" | "danger";

const variants: Record<Variant, string> = {
  primary: "bg-accent text-accent-ink hover:opacity-90 shadow-sm",
  secondary: "bg-surface text-ink border border-line hover:bg-surface-2",
  ghost: "text-ink hover:bg-surface-2",
  danger: "bg-surface text-danger border border-line hover:bg-danger-soft",
};

const base =
  "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50";

export function Button({
  variant = "primary",
  className,
  loading,
  children,
  ...props
}: ComponentProps<"button"> & { variant?: Variant; loading?: boolean }) {
  return (
    <button className={cx(base, variants[variant], className)} disabled={loading || props.disabled} {...props}>
      {loading && <Spinner />}
      {children}
    </button>
  );
}

export function ButtonLink({
  variant = "primary",
  className,
  ...props
}: ComponentProps<typeof Link> & { variant?: Variant }) {
  return <Link className={cx(base, variants[variant], className)} {...props} />;
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={cx("inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent", className)}
    />
  );
}

export function Card({ className, ...props }: ComponentProps<"div">) {
  return <div className={cx("rounded-xl border border-line bg-surface p-5", className)} {...props} />;
}

const tones = {
  neutral: "bg-surface-2 text-muted",
  accent: "bg-accent-soft text-accent",
  danger: "bg-danger-soft text-danger",
  warn: "bg-warn-soft text-warn",
  ok: "bg-ok-soft text-ok",
};

export function Badge({ tone = "neutral", className, ...props }: ComponentProps<"span"> & { tone?: keyof typeof tones }) {
  return (
    <span
      className={cx("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", tones[tone], className)}
      {...props}
    />
  );
}

export function Alert({
  tone = "neutral",
  title,
  children,
  className,
}: {
  tone?: "neutral" | "danger" | "warn" | "ok";
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  const bg = { neutral: "bg-info-soft", danger: "bg-danger-soft", warn: "bg-warn-soft", ok: "bg-ok-soft" }[tone];
  const ink = { neutral: "text-ink", danger: "text-danger", warn: "text-warn", ok: "text-ok" }[tone];
  return (
    <div role={tone === "danger" ? "alert" : "status"} className={cx("rounded-lg px-4 py-3 text-sm", bg, className)}>
      {title && <p className={cx("mb-0.5 font-semibold", ink)}>{title}</p>}
      <div className="text-ink/90">{children}</div>
    </div>
  );
}

const field =
  "w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink placeholder:text-muted/70 focus:border-accent focus:outline-none";

export function Input({ className, ...props }: ComponentProps<"input">) {
  return <input className={cx(field, className)} {...props} />;
}

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  return <textarea className={cx(field, "font-mono leading-relaxed", className)} {...props} />;
}

export function Label({ className, ...props }: ComponentProps<"label">) {
  return <label className={cx("mb-1.5 block text-sm font-medium text-ink", className)} {...props} />;
}

export function Stat({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <div className="font-mono text-2xl tabular-nums">{value}</div>
      <div className="mt-1 text-sm font-medium">{label}</div>
      {hint && <div className="mt-0.5 text-xs text-muted">{hint}</div>}
    </div>
  );
}

import Link from "next/link";
import type { Flag } from "@/lib/types";

export function Cite({ ids }: { ids: number[] }) {
  if (!ids.length) return null;
  return (
    <span className="ml-1 inline-flex flex-wrap gap-0.5 align-super text-[10px]">
      {ids.map((id) => (
        <Link
          key={id}
          href={`/evidence/${id}`}
          className="text-accent hover:underline"
          title={`Source evidence #${id}`}
        >
          [{id}]
        </Link>
      ))}
    </span>
  );
}

/** Prose with [n] citation tags turned into evidence links. */
export function CitedText({ text }: { text: string }) {
  const parts = text.split(/((?:\[\d+\])+)/);
  return (
    <>
      {parts.map((part, i) =>
        /^\[\d+\]/.test(part) ? (
          <Cite key={i} ids={[...part.matchAll(/\[(\d+)\]/g)].map((m) => Number(m[1]))} />
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </>
  );
}

export function pct(value: string | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${parseFloat(Number(value).toFixed(3))}%`;
}

export function Section({
  title,
  children,
  aside,
}: {
  title: string;
  children: React.ReactNode;
  aside?: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-line bg-surface">
      <div className="flex items-baseline justify-between gap-4 border-b border-line px-5 py-3">
        <h2 className="font-semibold">{title}</h2>
        {aside && <div className="text-xs text-muted">{aside}</div>}
      </div>
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-muted">{children}</p>;
}

export function FlagList({ flags }: { flags: Flag[] }) {
  if (!flags.length) return null;
  const seen = new Set<string>();
  const unique = flags.filter((f) => {
    const key = f.code + f.message;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  return (
    <ul className="space-y-1.5 text-sm">
      {unique.map((f) => (
        <li key={f.code + f.message} className="flex gap-2">
          <span
            className={`mt-1.5 size-1.5 shrink-0 rounded-full ${f.interpretation_required ? "bg-warn" : "bg-muted"}`}
            aria-hidden
          />
          <span>
            {f.message}
            {f.interpretation_required && (
              <span className="ml-1.5 rounded bg-warn-soft px-1.5 py-0.5 text-[11px] font-medium text-warn">
                needs professional review
              </span>
            )}
          </span>
        </li>
      ))}
    </ul>
  );
}

export function ScoreBar({ score }: { score: string | null }) {
  const n = score === null ? null : Number(score);
  const tone = n === null ? "bg-line" : n >= 70 ? "bg-good" : n >= 40 ? "bg-warn" : "bg-bad";
  return (
    <div className="h-2 w-full rounded-full bg-bg overflow-hidden" role="img" aria-label={`score ${score ?? "n/a"}`}>
      <div className={`h-full ${tone}`} style={{ width: `${n ?? 0}%` }} />
    </div>
  );
}

export function Badge({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "good" | "warn" | "bad" | "accent";
  children: React.ReactNode;
}) {
  const cls = {
    neutral: "bg-bg text-muted border-line",
    good: "bg-accent-soft text-good border-transparent",
    warn: "bg-warn-soft text-warn border-transparent",
    bad: "bg-bad-soft text-bad border-transparent",
    accent: "bg-accent-soft text-accent border-transparent",
  }[tone];
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${cls}`}>
      {children}
    </span>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-bad/30 bg-bad-soft px-5 py-4 text-sm text-bad">
      {message}
    </div>
  );
}

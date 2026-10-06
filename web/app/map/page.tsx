import type { Metadata } from "next";
import Link from "next/link";
import { Cite, ErrorNote, pct, Section } from "@/components/ui";
import { api, today } from "@/lib/api";
import type { CorporateTaxRow } from "@/lib/types";
import { BINS, binFor, FILL_OPACITY } from "./bins";
import { WorldMap } from "./world-map";

export const metadata: Metadata = { title: "Map" };

export default async function MapPage({ searchParams }: { searchParams: Promise<{ on?: string }> }) {
  const on = (await searchParams).on || today();
  let rows: CorporateTaxRow[];
  try {
    ({ jurisdictions: rows } = await api<{ jurisdictions: CorporateTaxRow[] }>(
      `/v1/browse/corporate-tax?on_date=${on}`,
    ));
  } catch {
    return <ErrorNote message="The data service is unavailable." />;
  }
  const ranked = [...rows].sort(
    (a, b) => (a.rate === null ? 1 : 0) - (b.rate === null ? 1 : 0) || Number(a.rate) - Number(b.rate) || a.name.localeCompare(b.name),
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Corporate tax map</h1>
          <p className="mt-2 text-muted">
            Headline corporate income tax rate for each jurisdiction we cover. Bracketed systems are
            coloured by their top rate. Grey countries are not covered yet.
          </p>
        </div>
        <form method="get" className="flex items-end gap-2 text-sm">
          <label>
            <span className="block text-xs text-muted">As of</span>
            <input type="date" name="on" defaultValue={on} className="rounded-lg border border-line bg-surface px-3 py-2" />
          </label>
          <button className="rounded-lg border border-line bg-surface px-3 py-2 hover:bg-bg">Show</button>
        </form>
      </div>

      <section className="rounded-xl border border-line bg-surface p-4">
        <WorldMap rows={rows} />
        <ul className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted">
          {BINS.map((b) => (
            <li key={b.label} className="flex items-center gap-1.5">
              <span
                className="inline-block size-3.5 rounded-sm border"
                style={{ borderColor: b.color, background: `color-mix(in srgb, ${b.color} ${FILL_OPACITY * 100}%, transparent)` }}
                aria-hidden
              />
              {b.label}
            </li>
          ))}
        </ul>
      </section>

      <Section title="Rates" aside={`valid on ${on} · lowest first`}>
        <ul className="grid gap-x-6 gap-y-1.5 text-sm sm:grid-cols-2 lg:grid-cols-3">
          {ranked.map((r) => {
            const bin = binFor(r.rate);
            return (
              <li key={r.code} className="flex items-center gap-2">
                <span
                  className="inline-block size-3 shrink-0 rounded-sm"
                  style={{ background: bin?.color ?? "var(--line)", opacity: 0.75 }}
                  aria-hidden
                />
                <Link href={`/jurisdictions/${r.code}`} className="hover:underline">
                  {r.name}
                </Link>
                <span className="ml-auto font-mono text-muted">
                  {r.rate === null
                    ? "not recorded"
                    : r.bracketed && r.min_rate !== null
                      ? `${pct(r.min_rate)}–${pct(r.rate)}`
                      : pct(r.rate)}
                  {r.citation !== null && <Cite ids={[r.citation]} />}
                </span>
              </li>
            );
          })}
        </ul>
      </Section>
    </div>
  );
}

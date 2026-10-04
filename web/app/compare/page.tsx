import type { Metadata } from "next";
import Link from "next/link";
import { Cite, ErrorNote, pct } from "@/components/ui";
import { api, today } from "@/lib/api";
import type { Jurisdiction, Overview } from "@/lib/types";

export const metadata: Metadata = { title: "Compare" };

type Cell = { text: string; cites: number[] };

function rule(o: Overview, taxType: string): Cell {
  const rules = o.domestic_rules.filter((r) => r.tax_type === taxType);
  if (!rules.length) return { text: "not recorded", cites: [] };
  const r = rules.find((x) => x.taxpayer_type === "company") ?? rules[0];
  const text = r.brackets.length
    ? r.brackets.map((b) => `${pct(b.rate)}${b.upper ? ` up to ${Number(b.upper).toLocaleString()}` : ""}`).join(", then ")
    : pct(r.rate);
  return { text, cites: [r.citation] };
}

const ROWS: [string, (o: Overview) => Cell][] = [
  ["Corporate income tax", (o) => rule(o, "CIT")],
  ["WHT on dividends", (o) => rule(o, "WHT_DIVIDEND")],
  ["WHT on interest", (o) => rule(o, "WHT_INTEREST")],
  ["WHT on royalties", (o) => rule(o, "WHT_ROYALTY")],
  [
    "Participation exemption",
    (o) =>
      o.holding_regime
        ? {
            text: `${pct(o.holding_regime.exempt_share_pct)} of dividends · ≥${pct(o.holding_regime.min_holding_pct)} for ${o.holding_regime.min_holding_period_months ?? "?"} months${o.holding_regime.min_subject_to_tax_rate ? ` · payer taxed ≥${pct(o.holding_regime.min_subject_to_tax_rate)}` : ""}`,
            cites: [o.holding_regime.citation],
          }
        : { text: "not recorded", cites: [] },
  ],
  [
    "List status",
    (o) =>
      o.lists.length
        ? { text: o.lists.map((l) => l.list_code).join(", "), cites: o.lists.map((l) => l.citation) }
        : { text: "none tracked", cites: [] },
  ],
  [
    "Treaties in force",
    (o) => {
      const inForce = o.treaties.filter((t) => t.in_force);
      return {
        text: inForce.length ? inForce.flatMap((t) => t.counterparties).join(", ") : "none recorded",
        cites: inForce.map((t) => t.citation),
      };
    },
  ],
  [
    "CFC rule (as parent)",
    (o) => (o.cfc_rule ? { text: o.cfc_rule.legal_ref, cites: [o.cfc_rule.citation] } : { text: "not recorded", cites: [] }),
  ],
];

export default async function ComparePage({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const sp = await searchParams;
  const on = sp.on || today();
  let jurisdictions: Jurisdiction[];
  try {
    ({ jurisdictions } = await api<{ jurisdictions: Jurisdiction[] }>("/v1/onboarding/questions"));
  } catch {
    return <ErrorNote message="The data service is unavailable." />;
  }
  const a = sp.a || jurisdictions[0]?.code;
  const b = sp.b || jurisdictions[1]?.code;
  const overviews = await Promise.all(
    [a, b].map((c) => (c ? api<Overview>(`/v1/browse/jurisdictions/${encodeURIComponent(c)}?on_date=${on}`).catch(() => null) : null)),
  );

  const select = (name: string, value: string | undefined) => (
    <select name={name} defaultValue={value} className="rounded-lg border border-line bg-surface px-3 py-2">
      {jurisdictions.map((j) => (
        <option key={j.code} value={j.code}>
          {j.name}
        </option>
      ))}
    </select>
  );

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold tracking-tight">Compare</h1>
      <form method="get" className="flex flex-wrap items-end gap-3 text-sm">
        {select("a", a)}
        <span className="pb-2 text-muted">vs</span>
        {select("b", b)}
        <input type="date" name="on" defaultValue={on} className="rounded-lg border border-line bg-surface px-3 py-2" />
        <button className="rounded-lg bg-accent px-4 py-2 font-medium text-white dark:text-black">Compare</button>
      </form>
      {overviews.some((o) => o === null) ? (
        <ErrorNote message="Could not load one of the jurisdictions." />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-line bg-surface">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line text-left">
                <th className="px-5 py-3 font-medium text-muted w-1/4">As of {on}</th>
                {overviews.map((o) => (
                  <th key={o!.code} className="px-5 py-3 font-semibold">
                    <Link href={`/jurisdictions/${o!.code}`} className="hover:underline">{o!.name}</Link>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {ROWS.map(([label, fn]) => (
                <tr key={label}>
                  <td className="px-5 py-3 text-muted">{label}</td>
                  {overviews.map((o) => {
                    const cell = fn(o!);
                    return (
                      <td key={o!.code} className="px-5 py-3">
                        {cell.text}
                        <Cite ids={cell.cites} />
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

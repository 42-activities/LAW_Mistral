import type { Metadata } from "next";
import Link from "next/link";
import { Badge, Cite, Empty, ErrorNote, pct, Section } from "@/components/ui";
import { notFound } from "next/navigation";
import { api, ApiError, today } from "@/lib/api";
import type { Overview, Period } from "@/lib/types";

type Props = {
  params: Promise<{ code: string }>;
  searchParams: Promise<{ on?: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return { title: (await params).code.toUpperCase() };
}

const TAX_LABEL: Record<string, string> = {
  CIT: "Corporate income tax",
  WHT_DIVIDEND: "Withholding — dividends",
  WHT_INTEREST: "Withholding — interest",
  WHT_ROYALTY: "Withholding — royalties",
};

function since(p: Period) {
  return p.to ? `${p.from} → ${p.to}` : `since ${p.from}`;
}

export default async function JurisdictionPage({ params, searchParams }: Props) {
  const { code } = await params;
  const on = (await searchParams).on || today();
  let o: Overview;
  try {
    o = await api<Overview>(`/v1/browse/jurisdictions/${encodeURIComponent(code)}?on_date=${on}`);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    return <ErrorNote message={e instanceof ApiError && e.status === 404 ? "Unknown jurisdiction." : "The data service is unavailable."} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-muted">
            <Link href="/jurisdictions" className="hover:underline">Jurisdictions</Link> / {o.code}
          </p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">{o.name}</h1>
        </div>
        <form method="get" className="flex items-end gap-2 text-sm">
          <label>
            <span className="block text-xs text-muted">As of</span>
            <input type="date" name="on" defaultValue={on} className="rounded-lg border border-line bg-surface px-3 py-2" />
          </label>
          <button className="rounded-lg border border-line bg-surface px-3 py-2 hover:bg-bg">Show</button>
        </form>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Section title="Domestic rules" aside={`valid on ${o.on_date}`}>
          {o.domestic_rules.length === 0 ? (
            <Empty>No domestic rules recorded for this date.</Empty>
          ) : (
            <table className="w-full text-sm">
              <tbody className="divide-y divide-line">
                {o.domestic_rules.map((r) => (
                  <tr key={r.tax_type + r.taxpayer_type}>
                    <td className="py-2 pr-4">
                      {TAX_LABEL[r.tax_type] ?? r.tax_type}
                      <span className="block text-xs text-muted">
                        {r.taxpayer_type === "any" ? "all recipients" : `${r.taxpayer_type} recipients`} · {since(r.valid)}
                      </span>
                    </td>
                    <td className="py-2 text-right font-mono whitespace-nowrap">
                      {r.brackets.length
                        ? r.brackets.map((b) => (
                            <span key={b.lower} className="block">
                              {pct(b.rate)} {b.upper ? `≤ ${Number(b.upper).toLocaleString()}` : `> ${Number(b.lower).toLocaleString()}`}
                            </span>
                          ))
                        : pct(r.rate)}
                      <Cite ids={[r.citation]} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {o.wht_exemptions.length > 0 && (
            <div className="mt-4 border-t border-line pt-3">
              <p className="text-xs font-medium uppercase tracking-wide text-muted">Withholding exemptions</p>
              <ul className="mt-2 space-y-1.5 text-sm">
                {o.wht_exemptions.map((e) => (
                  <li key={e.income_category + e.recipient_group}>
                    {e.income_category.toLowerCase()} to {e.recipient_group} companies: 0%
                    <span className="text-muted">
                      {" "}
                      ({[
                        e.min_holding_pct && `≥${pct(e.min_holding_pct)}`,
                        e.min_holding_months && `${e.min_holding_months} months`,
                      ]
                        .filter(Boolean)
                        .join(", ")}
                      ; {e.legal_ref})
                    </span>
                    <Cite ids={[e.citation]} />
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Section>

        <Section title="Participation exemption">
          {o.holding_regime ? (
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <dt className="text-muted">Dividends</dt>
              <dd>{o.holding_regime.dividends_exempt ? `${pct(o.holding_regime.exempt_share_pct)} exempt` : "not exempt"}</dd>
              <dt className="text-muted">Capital gains</dt>
              <dd>{o.holding_regime.capital_gains_exempt ? "exempt" : "not exempt"}</dd>
              <dt className="text-muted">Minimum holding</dt>
              <dd>{pct(o.holding_regime.min_holding_pct)}</dd>
              <dt className="text-muted">Minimum period</dt>
              <dd>{o.holding_regime.min_holding_period_months ?? "—"} months</dd>
              {o.holding_regime.min_subject_to_tax_rate && (
                <>
                  <dt className="text-muted">Subject-to-tax floor</dt>
                  <dd>{pct(o.holding_regime.min_subject_to_tax_rate)}</dd>
                </>
              )}
              <dt className="text-muted">Source</dt>
              <dd>
                {o.holding_regime.notes}
                <Cite ids={[o.holding_regime.citation]} />
              </dd>
            </dl>
          ) : (
            <Empty>No participation-exemption regime recorded.</Empty>
          )}
        </Section>

        <Section title="List status" aside={`on ${o.on_date}`}>
          {o.lists.length === 0 ? (
            <Empty>Not on any tracked list on this date.</Empty>
          ) : (
            <ul className="space-y-2 text-sm">
              {o.lists.map((l) => (
                <li key={l.list_code} className="flex items-center gap-2">
                  <Badge tone={l.family === "aml_cft" ? "bad" : "warn"}>{l.list_code}</Badge>
                  <span className="text-muted">{l.classification.replaceAll("_", " ")}</span>
                  <Cite ids={[l.citation]} />
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="Anti-abuse">
          <div className="space-y-3 text-sm">
            {o.cfc_rule ? (
              <p>
                <span className="font-medium">CFC rule ({o.cfc_rule.legal_ref}):</span> applies to entities
                controlled above {pct(o.cfc_rule.control_threshold_pct)} and taxed below{" "}
                {pct(o.cfc_rule.low_tax_relative_pct)} of the domestic tax. {o.cfc_rule.effect}
                <Cite ids={[o.cfc_rule.citation]} />
              </p>
            ) : (
              <Empty>No CFC rule recorded.</Empty>
            )}
            {o.substance_rules.length ? (
              o.substance_rules.map((s) => (
                <p key={s.regime}>
                  Substance ({s.regime}): {s.requirement_band} requirement <Cite ids={[s.citation]} />
                </p>
              ))
            ) : (
              <Empty>No substance rules recorded.</Empty>
            )}
          </div>
        </Section>
      </div>

      <Section title="Tax treaties">
        {o.treaties.length === 0 ? (
          <Empty>No treaties recorded.</Empty>
        ) : (
          <div className="space-y-5">
            {o.treaties.map((t) => (
              <div key={t.name}>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-medium">{t.name}</h3>
                  <Badge tone={t.in_force ? "good" : "neutral"}>{t.in_force ? "in force" : "not in force"}</Badge>
                  <Cite ids={[t.citation]} />
                </div>
                <p className="text-xs text-muted">
                  Signed {t.signature_date} · in force {t.entry_into_force_date ?? "date not recorded"} · with{" "}
                  {t.counterparties.map((c) => (
                    <Link key={c} href={`/jurisdictions/${c}`} className="hover:underline">{c}</Link>
                  ))}
                </p>
                <table className="mt-2 w-full text-sm">
                  <tbody className="divide-y divide-line">
                    {t.rates.map((r) => (
                      <tr key={r.income_category + (r.ownership_threshold ?? "")}>
                        <td className="py-1.5 pr-4">
                          {r.income_category.toLowerCase()} <span className="text-muted">({r.article})</span>
                          {r.ownership_threshold && (
                            <span className="block text-xs text-muted">
                              holding ≥{pct(r.ownership_threshold)}
                              {r.min_holding_days ? ` for ${r.min_holding_days} days` : ""}
                            </span>
                          )}
                        </td>
                        <td className="py-1.5 pr-4 text-muted">
                          {r.exclusive_residence_taxation ? "residence State only" : `capped at ${pct(r.max_rate)}`}
                          {r.beneficial_owner_required && " · beneficial owner"}
                          {r.relief_mechanism && ` · relief by ${r.relief_mechanism.replace("_", " ")}`}
                        </td>
                        <td className="py-1.5 text-right font-mono">
                          {r.exclusive_residence_taxation ? "0%" : pct(r.max_rate)}
                          <Cite ids={[r.citation]} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}

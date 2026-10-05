import type { Metadata } from "next";
import Link from "next/link";
import { Badge, Cite, CitedText, ErrorNote, FlagList, pct, ScoreBar } from "@/components/ui";
import { notFound } from "next/navigation";
import { api, ApiError, today } from "@/lib/api";
import {
  FACTOR_LABEL,
  type FactorName,
  type Flag,
  type Jurisdiction,
  type Profile,
  type Recommendation,
  type ScoreCard,
} from "@/lib/types";
import { requireUser } from "@/lib/session";
import { Reweight } from "./reweight";

export const metadata: Metadata = { title: "Recommendation" };

type Props = {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

const WEIGHT_PARAMS: [string, FactorName][] = [
  ["tax", "tax_efficiency"],
  ["compliance", "compliance"],
  ["treaty", "treaty_breadth"],
  ["substance", "substance_burden"],
];

const FLOW_LABEL: Record<string, string> = {
  DIVIDEND: "Dividends",
  ROYALTY: "Royalties",
  INTEREST: "Interest",
};

function one(v: string | string[] | undefined) {
  return Array.isArray(v) ? v[0] : v;
}

export default async function RecommendationPage({ params, searchParams }: Props) {
  const { id } = await params;
  await requireUser(`/analyze/${id}`);
  const sp = await searchParams;
  const onDate = one(sp.on) || today();
  const custom = WEIGHT_PARAMS.filter(([p]) => one(sp[p]) !== undefined);
  const weights = custom.length
    ? Object.fromEntries(WEIGHT_PARAMS.map(([p, f]) => [f, Number(one(sp[p]) ?? 0)]))
    : undefined;

  let profile: Profile, rec: Recommendation, jurisdictions: Jurisdiction[];
  try {
    [profile, rec, { jurisdictions }] = await Promise.all([
      api<Profile>(`/v1/profiles/${id}`),
      api<Recommendation>("/v1/analyze/holding-recommendation", {
        method: "POST",
        body: { profile_id: Number(id), on_date: onDate, weights, summarize: true },
      }),
      api<{ jurisdictions: Jurisdiction[] }>("/v1/onboarding/questions"),
    ]);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    const msg = e instanceof ApiError ? e.detail : "The analysis service is unavailable.";
    return <ErrorNote message={msg} />;
  }
  const name = Object.fromEntries(jurisdictions.map((j) => [j.code, j.name]));
  const a = profile.answers;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-muted">
            <Link href="/analyze" className="hover:underline">Analyses</Link> / #{id}
          </p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">Holding recommendation</h1>
          <p className="mt-2 text-sm text-muted">
            {a.flows.map((f) => FLOW_LABEL[f] ?? f).join(", ")} from{" "}
            {a.sources.map((s) => name[s] ?? s).join(", ")} · parent in {name[a.parent] ?? a.parent} ·
            substance capacity {profile.derived.substance_capacity}
          </p>
        </div>
        <div className="text-right text-xs text-muted">
          <p>Run #{rec.scoring_run_id} · data as of {rec.data_asof}</p>
          <p>Engine {rec.engine_version} · weights {rec.weight_set}</p>
        </div>
      </div>

      {rec.summary && <SummaryBlock summary={rec.summary} />}

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        <ol className="space-y-4">
          {rec.scorecards.map((c) => (
            <li key={c.jurisdiction}>
              <Card card={c} name={name[c.jurisdiction] ?? c.jurisdiction} />
            </li>
          ))}
        </ol>
        <aside className="lg:sticky lg:top-6 self-start rounded-xl border border-line bg-surface p-5">
          <h2 className="font-semibold">Weights</h2>
          <div className="mt-4">
            <Reweight weights={rec.weights} onDate={onDate} />
          </div>
        </aside>
      </div>
    </div>
  );
}

function SummaryBlock({ summary }: { summary: NonNullable<Recommendation["summary"]> }) {
  const ai = summary.status !== "template";
  return (
    <section className="rounded-xl border border-line bg-surface px-5 py-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold">
          {ai ? "AI-generated narration of the figures below" : "Summary of the figures below"}
        </h2>
        <span className="text-xs text-muted">
          {ai
            ? `${summary.model} · every number and citation checked against the engine output`
            : "fixed template, no AI" + (summary.note ? ` · ${summary.note}` : "")}
        </span>
      </div>
      <p className="mt-2 text-[15px] leading-relaxed">
        <CitedText text={summary.text} />
      </p>
    </section>
  );
}

function Card({ card, name }: { card: ScoreCard; name: string }) {
  const factorFlags: Flag[] = Object.values(card.factors).flatMap((f) => f.flags);
  const review = factorFlags.filter((f) => f.interpretation_required);
  const flows = Object.entries(
    card.flow_breakdown.reduce<Record<string, ScoreCard["flow_breakdown"]>>((acc, line) => {
      (acc[line.flow] ??= []).push(line);
      return acc;
    }, {}),
  );

  return (
    <article className="rounded-xl border border-line bg-surface">
      <header className="flex items-center gap-4 border-b border-line px-5 py-4">
        <span className="font-mono text-sm text-muted w-6">#{card.rank}</span>
        <div className="flex-1">
          <h2 className="text-lg font-semibold">
            <Link href={`/jurisdictions/${card.jurisdiction}`} className="hover:underline">{name}</Link>{" "}
            <span className="text-sm font-normal text-muted">{card.jurisdiction}</span>
          </h2>
          <div className="mt-1 flex flex-wrap gap-1.5">
            {!card.complete && <Badge tone="neutral">incomplete data</Badge>}
            {card.guardrail_flags.length > 0 && <Badge tone="bad">guardrail</Badge>}
            {review.length > 0 && <Badge tone="warn">{review.length} point{review.length > 1 ? "s" : ""} to review</Badge>}
          </div>
        </div>
        <div className="text-right">
          <div className="text-3xl font-semibold tabular-nums">{card.overall_score ?? "—"}</div>
          <div className="text-xs text-muted">of 100</div>
        </div>
      </header>

      <div className="px-5 py-4 space-y-4">
        {card.guardrail_flags.length > 0 && (
          <div className="rounded-lg bg-bad-soft px-4 py-3 text-sm text-bad">
            <FlagList flags={card.guardrail_flags} />
          </div>
        )}

        <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
          {(Object.keys(FACTOR_LABEL) as FactorName[]).map((f) => {
            const factor = card.factors[f];
            return (
              <div key={f}>
                <dt className="flex justify-between text-sm">
                  <span>
                    {FACTOR_LABEL[f]}
                    <span className="ml-1 text-xs text-muted">×{Math.round(Number(factor.weight) * 100)}%</span>
                  </span>
                  <span className="font-mono tabular-nums">{factor.score ?? "n/a"}</span>
                </dt>
                <dd className="mt-1.5">
                  <ScoreBar score={factor.score} />
                </dd>
              </div>
            );
          })}
        </dl>

        {flows.length > 0 && (
          <details className="group rounded-lg border border-line">
            <summary className="cursor-pointer list-none px-4 py-2.5 text-sm font-medium flex justify-between">
              Flow-by-flow computation
              <span className="text-muted group-open:rotate-90 transition-transform">›</span>
            </summary>
            <div className="overflow-x-auto border-t border-line">
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-muted">
                  <tr>
                    <th className="px-4 py-2 font-medium">Leg</th>
                    <th className="px-4 py-2 font-medium">Tax</th>
                    <th className="px-4 py-2 font-medium text-right">Rate</th>
                    <th className="px-4 py-2 font-medium text-right">Per 100</th>
                  </tr>
                </thead>
                {flows.map(([flow, lines]) => (
                  <tbody key={flow} className="border-t border-line">
                    <tr>
                      <td colSpan={4} className="px-4 pt-3 pb-1 text-xs font-medium uppercase tracking-wide text-muted">
                        {flow}
                      </td>
                    </tr>
                    {lines.map((l) => (
                      <tr key={l.leg}>
                        <td className="px-4 py-1.5">{l.leg}</td>
                        <td className="px-4 py-1.5 text-muted">{l.kind === "wht" ? "withholding" : "corporate tax"}</td>
                        <td className="px-4 py-1.5 text-right font-mono">
                          {pct(l.rate)}
                          <Cite ids={l.citations} />
                        </td>
                        <td className="px-4 py-1.5 text-right font-mono">{l.tax_per_100 ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                ))}
              </table>
            </div>
          </details>
        )}

        {factorFlags.length > 0 && (
          <details className="group rounded-lg border border-line">
            <summary className="cursor-pointer list-none px-4 py-2.5 text-sm font-medium flex justify-between">
              Assumptions, conditions and flags ({new Set(factorFlags.map((f) => f.code + f.message)).size})
              <span className="text-muted group-open:rotate-90 transition-transform">›</span>
            </summary>
            <div className="border-t border-line px-4 py-3 space-y-3">
              <FlagList flags={factorFlags} />
              <p className="text-xs text-muted">
                Factor sources: <Cite ids={card.citations} />
              </p>
            </div>
          </details>
        )}
      </div>
    </article>
  );
}

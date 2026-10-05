import type { Metadata } from "next";
import { ErrorNote } from "@/components/ui";
import { api } from "@/lib/api";
import Link from "next/link";
import { requireUser } from "@/lib/session";
import type { Jurisdiction, Profile, Question } from "@/lib/types";
import { Wizard } from "./wizard";

export const metadata: Metadata = { title: "New analysis" };

type PastProfile = Profile & { created_at: string };

export default async function AnalyzePage() {
  await requireUser("/analyze");
  let data: { questions: Question[]; jurisdictions: Jurisdiction[] };
  let past: PastProfile[];
  try {
    [data, past] = await Promise.all([
      api<{ questions: Question[]; jurisdictions: Jurisdiction[] }>("/v1/onboarding/questions"),
      api<PastProfile[]>("/v1/profiles?limit=10"),
    ]);
  } catch {
    return <ErrorNote message="The analysis service is unavailable. Try again in a moment." />;
  }
  return (
    <div className="max-w-3xl">
      <h1 className="text-3xl font-semibold tracking-tight">New analysis</h1>
      <p className="mt-2 text-muted">
        Three questions. The answers are mapped to a structured profile by fixed rules — nothing
        you tick is interpreted by a language model.
      </p>
      <div className="mt-8">
        <Wizard questions={data.questions} jurisdictions={data.jurisdictions} />
      </div>
      {past.length > 0 && (
        <section className="mt-12">
          <h2 className="font-semibold">Recent analyses in your organisation</h2>
          <ul className="mt-3 divide-y divide-line rounded-xl border border-line bg-surface text-sm">
            {past.map((p) => (
              <li key={p.id}>
                <Link href={`/analyze/${p.id}`} className="flex justify-between gap-4 px-4 py-3 hover:bg-bg">
                  <span>
                    #{p.id} · {p.answers.flows.join(", ").toLowerCase()} from {p.answers.sources.join(", ")} → parent{" "}
                    {p.answers.parent}
                  </span>
                  <span className="text-muted whitespace-nowrap">{p.created_at.slice(0, 10)}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

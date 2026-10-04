import type { Metadata } from "next";
import Link from "next/link";
import { ErrorNote } from "@/components/ui";
import { api } from "@/lib/api";
import type { Jurisdiction } from "@/lib/types";

export const metadata: Metadata = { title: "Jurisdictions" };

export default async function JurisdictionsPage() {
  let jurisdictions: Jurisdiction[];
  try {
    ({ jurisdictions } = await api<{ jurisdictions: Jurisdiction[] }>("/v1/onboarding/questions"));
  } catch {
    return <ErrorNote message="The data service is unavailable." />;
  }
  return (
    <div>
      <h1 className="text-3xl font-semibold tracking-tight">Jurisdictions</h1>
      <p className="mt-2 text-muted">Domestic rules, holding regimes, list status and treaties — as of any date.</p>
      <ul className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {jurisdictions.map((j) => (
          <li key={j.code}>
            <Link
              href={`/jurisdictions/${j.code}`}
              className="flex items-center justify-between rounded-xl border border-line bg-surface px-5 py-4 hover:border-muted"
            >
              <span className="font-medium">{j.name}</span>
              <span className="font-mono text-sm text-muted">{j.code}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

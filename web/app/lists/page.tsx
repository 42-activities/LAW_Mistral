import type { Metadata } from "next";
import Link from "next/link";
import { Badge, Cite, ErrorNote } from "@/components/ui";
import { api, today } from "@/lib/api";
import type { ListInfo } from "@/lib/types";

export const metadata: Metadata = { title: "Lists" };

export default async function ListsPage({ searchParams }: { searchParams: Promise<{ on?: string }> }) {
  const on = (await searchParams).on || today();
  let lists: ListInfo[];
  try {
    lists = await api<ListInfo[]>(`/v1/lists?on_date=${on}`);
  } catch {
    return <ErrorNote message="The data service is unavailable." />;
  }
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Lists</h1>
          <p className="mt-2 text-muted">
            Tax-governance and AML/CFT lists are kept apart: a FATF status is not an EU tax-list status.
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
      <div className="grid gap-4 md:grid-cols-2">
        {lists.map((l) => (
          <article key={l.code} className="rounded-xl border border-line bg-surface p-5">
            <div className="flex items-start justify-between gap-3">
              <h2 className="font-semibold">
                {l.name}
                <Cite ids={[l.citation]} />
              </h2>
              <Badge tone={l.family === "aml_cft" ? "bad" : "accent"}>{l.family === "aml_cft" ? "AML/CFT" : "tax governance"}</Badge>
            </div>
            <p className="mt-1 text-xs text-muted">
              {l.publisher}
              {l.update_cadence && ` · ${l.update_cadence}`}
            </p>
            {l.members.length === 0 ? (
              <p className="mt-3 text-sm text-muted">No tracked jurisdiction listed on {on}.</p>
            ) : (
              <ul className="mt-3 space-y-1 text-sm">
                {l.members.map((m) => (
                  <li key={m.jurisdiction}>
                    <Link href={`/jurisdictions/${m.jurisdiction}`} className="font-medium hover:underline">{m.jurisdiction}</Link>{" "}
                    <span className="text-muted">
                      {m.classification.replaceAll("_", " ")} · since {m.valid.from}
                    </span>
                    <Cite ids={[m.citation]} />
                  </li>
                ))}
              </ul>
            )}
          </article>
        ))}
      </div>
      <p className="text-xs text-muted">
        Only memberships verified for the jurisdictions currently covered are recorded — an empty list means
        “no tracked jurisdiction listed”, not “nobody listed”.
      </p>
    </div>
  );
}

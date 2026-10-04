import type { Metadata } from "next";
import { Badge, ErrorNote } from "@/components/ui";
import { notFound } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Evidence } from "@/lib/types";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return { title: `Evidence #${(await params).id}` };
}

export default async function EvidencePage({ params }: Props) {
  const { id } = await params;
  let ev: Evidence;
  try {
    ev = await api<Evidence>(`/v1/evidence/${Number(id)}`);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    return <ErrorNote message={e instanceof ApiError && e.status === 404 ? "No such evidence record." : "The data service is unavailable."} />;
  }
  const reviewed = ev.review_status === "human_verified";
  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <p className="text-sm text-muted">Source evidence #{ev.id}</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">{ev.document_title}</h1>
        <div className="mt-3 flex flex-wrap gap-2">
          <Badge tone={reviewed ? "good" : "warn"}>{reviewed ? "human verified" : ev.review_status}</Badge>
          {ev.article && <Badge>{ev.article}</Badge>}
          {ev.page && <Badge>page {ev.page}</Badge>}
        </div>
      </div>
      <blockquote className="rounded-xl border-l-4 border-accent bg-surface px-6 py-5 text-[15px] leading-relaxed">
        {ev.quoted_text}
      </blockquote>
      <dl className="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-2 text-sm">
        <dt className="text-muted">Document</dt>
        <dd className="break-all">
          <a href={ev.document_url} target="_blank" rel="noreferrer noopener" className="text-accent hover:underline">
            {ev.document_url}
          </a>
        </dd>
        <dt className="text-muted">Retrieved</dt>
        <dd>{ev.retrieved_at.slice(0, 10)}</dd>
      </dl>
      {!reviewed && (
        <p className="text-sm text-muted">
          This extract was checked against the source by software and has not yet been confirmed by a named
          reviewer. Verify it against the document before relying on it.
        </p>
      )}
    </div>
  );
}

import type { Metadata } from "next";
import { ErrorNote } from "@/components/ui";
import { api } from "@/lib/api";
import type { Jurisdiction, Question } from "@/lib/types";
import { Wizard } from "./wizard";

export const metadata: Metadata = { title: "New analysis" };

export default async function AnalyzePage() {
  let data: { questions: Question[]; jurisdictions: Jurisdiction[] };
  try {
    data = await api("/v1/onboarding/questions");
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
    </div>
  );
}

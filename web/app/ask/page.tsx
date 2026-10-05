import type { Metadata } from "next";
import { AskForm } from "./form";

export const metadata: Metadata = { title: "Ask" };

export default function AskPage() {
  return (
    <div className="max-w-3xl">
      <h1 className="text-3xl font-semibold tracking-tight">Ask a withholding question</h1>
      <p className="mt-2 text-muted">
        Plain-language questions about dividend, interest and royalty withholding between covered
        jurisdictions. The prose answer is rendered from the engine result, so every figure is sourced.
      </p>
      <div className="mt-8">
        <AskForm />
      </div>
    </div>
  );
}

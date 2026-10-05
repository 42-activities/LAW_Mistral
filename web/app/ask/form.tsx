"use client";

import { useActionState } from "react";
import { CitedText, FlagList, pct } from "@/components/ui";
import { askQuestion, type AskState } from "./actions";

const EXAMPLES = [
  "What withholding tax applies to dividends a French company pays to its UAE parent?",
  "Royalties from France to a UAE licensor — what is withheld and what is the final rate?",
  "Dividends paid from France to a Vanuatu company in June 2025?",
];

export function AskForm() {
  const [state, action, pending] = useActionState<AskState, FormData>(askQuestion, {
    question: "",
    data: null,
    error: null,
  });
  const r = state.data?.result;
  return (
    <div className="space-y-6">
      <form action={action} className="space-y-3">
        <textarea
          name="question"
          rows={3}
          defaultValue={state.question}
          placeholder={EXAMPLES[0]}
          className="w-full rounded-xl border border-line bg-surface px-4 py-3 text-[15px]"
        />
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={pending}
            className="rounded-lg bg-accent px-5 py-2.5 font-medium text-white dark:text-black disabled:opacity-40"
          >
            {pending ? "Working…" : "Ask"}
          </button>
          <span className="text-xs text-muted">
            The language model only turns your question into a query; the answer comes from the engine.
          </span>
        </div>
      </form>

      {!state.data && !state.error && (
        <ul className="space-y-1 text-sm text-muted">
          {EXAMPLES.map((e) => (
            <li key={e}>“{e}”</li>
          ))}
        </ul>
      )}
      {state.error && <p className="rounded-lg bg-bad-soft px-4 py-3 text-sm text-bad">{state.error}</p>}

      {state.data && r && (
        <section className="rounded-xl border border-line bg-surface">
          <div className="border-b border-line px-5 py-3 text-xs text-muted">
            Understood as: {state.data.query.income_category.toLowerCase()} paid from{" "}
            {state.data.query.source} to {state.data.query.recipient} on {state.data.query.on_date}
            {state.data.query.holding_pct && `, ${state.data.query.holding_pct}% holding`}
          </div>
          <div className="space-y-4 px-5 py-4">
            <p className="text-[15px] leading-relaxed">
              <CitedText text={state.data.answer} />
            </p>
            {r.complete && (
              <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4 text-sm">
                {[
                  ["Domestic rate", r.effective_domestic_rate],
                  ["Treaty cap", r.treaty_cap],
                  ["Withheld at payment", r.withheld_at_payment],
                  ["Final rate", r.final_rate],
                ].map(([label, v]) => (
                  <div key={label} className="rounded-lg bg-bg px-3 py-2">
                    <dt className="text-xs text-muted">{label}</dt>
                    <dd className="mt-0.5 font-mono text-lg">{pct(v)}</dd>
                  </div>
                ))}
              </dl>
            )}
            <FlagList flags={r.flags} />
          </div>
        </section>
      )}
    </div>
  );
}

"use client";

import { useActionState, useState } from "react";
import type { Jurisdiction, Option, Question } from "@/lib/types";
import { createProfile, type WizardState } from "./actions";

function Choice({
  name,
  option,
  type,
  checked,
  onChange,
}: {
  name: string;
  option: Option;
  type: "radio" | "checkbox";
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  const disabled = option.enabled === false;
  return (
    <label
      className={`flex items-start gap-3 rounded-lg border px-4 py-3 text-sm transition-colors ${
        disabled
          ? "cursor-not-allowed border-line opacity-50"
          : checked
            ? "cursor-pointer border-accent bg-accent-soft"
            : "cursor-pointer border-line bg-surface hover:border-muted"
      }`}
    >
      <input
        type={type}
        name={name}
        value={option.value}
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-0.5 accent-[var(--accent)]"
      />
      <span>
        <span className="font-medium">{option.label}</span>
        {option.hint && <span className="block text-muted">{option.hint}</span>}
      </span>
    </label>
  );
}

function Step({ n, question, children }: { n: number; question: Question; children: React.ReactNode }) {
  return (
    <fieldset className="rounded-xl border border-line bg-surface p-5">
      <legend className="sr-only">{question.text}</legend>
      <div className="flex gap-3">
        <span className="font-mono text-sm text-accent pt-0.5">0{n}</span>
        <div className="flex-1">
          <h2 className="font-semibold">{question.text}</h2>
          {question.help && <p className="mt-1 text-sm text-muted">{question.help}</p>}
          <div className="mt-4">{children}</div>
        </div>
      </div>
    </fieldset>
  );
}

export function Wizard({ questions, jurisdictions }: { questions: Question[]; jurisdictions: Jurisdiction[] }) {
  const [state, action, pending] = useActionState<WizardState, FormData>(createProfile, { error: null });
  const [single, setSingle] = useState<Record<string, string>>({});
  const [flows, setFlows] = useState<Set<string>>(new Set());
  const [sources, setSources] = useState<Set<string>>(new Set());
  const [parent, setParent] = useState("");

  const toggle = (set: Set<string>, value: string, on: boolean) => {
    const next = new Set(set);
    if (on) next.add(value);
    else next.delete(value);
    return next;
  };

  const pickSingle = (q: Question, value: string) => {
    setSingle((s) => ({ ...s, [q.code]: value }));
    // Activity proposes flows (spec §6): pre-tick, the user can still change them.
    const suggests = q.options.find((o) => o.value === value)?.suggests;
    if (suggests && flows.size === 0) setFlows(new Set(suggests));
  };

  const ready = questions.every((q) => q.kind !== "single" || single[q.code]) && flows.size > 0 && sources.size > 0 && parent;

  return (
    <form action={action} className="space-y-5">
      {questions.map((q, i) =>
        q.kind === "single" ? (
          <Step key={q.code} n={i + 1} question={q}>
            <div className="grid gap-2 sm:grid-cols-2">
              {q.options.map((o) => (
                <Choice
                  key={o.value}
                  name={q.code}
                  option={o}
                  type="radio"
                  checked={single[q.code] === o.value}
                  onChange={() => pickSingle(q, o.value)}
                />
              ))}
            </div>
          </Step>
        ) : (
          <Step key={q.code} n={i + 1} question={q}>
            <p className="text-xs font-medium uppercase tracking-wide text-muted">Income flows</p>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {q.options.map((o) => (
                <Choice
                  key={o.value}
                  name="flows"
                  option={o}
                  type="checkbox"
                  checked={flows.has(o.value)}
                  onChange={(on) => setFlows((f) => toggle(f, o.value, on))}
                />
              ))}
            </div>
            <p className="mt-5 text-xs font-medium uppercase tracking-wide text-muted">
              Where the income arises (paying companies resident in)
            </p>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {jurisdictions.map((j) => (
                <Choice
                  key={j.code}
                  name="sources"
                  option={{ value: j.code, label: j.name, hint: j.code }}
                  type="checkbox"
                  checked={sources.has(j.code)}
                  onChange={(on) => setSources((s) => toggle(s, j.code, on))}
                />
              ))}
            </div>
            <label className="mt-5 block">
              <span className="text-xs font-medium uppercase tracking-wide text-muted">Ultimate parent jurisdiction</span>
              <select
                name="parent"
                value={parent}
                onChange={(e) => setParent(e.target.value)}
                className="mt-2 block w-full rounded-lg border border-line bg-surface px-3 py-2.5 text-sm"
              >
                <option value="">Select…</option>
                {jurisdictions.map((j) => (
                  <option key={j.code} value={j.code}>
                    {j.name} ({j.code})
                  </option>
                ))}
              </select>
            </label>
          </Step>
        ),
      )}

      {state.error && (
        <p className="rounded-lg bg-bad-soft px-4 py-3 text-sm text-bad" role="alert">
          {state.error}
        </p>
      )}
      <div className="flex items-center gap-4">
        <button
          type="submit"
          disabled={!ready || pending}
          className="rounded-lg bg-accent px-5 py-2.5 font-medium text-white dark:text-black disabled:opacity-40"
        >
          {pending ? "Computing…" : "Rank holding jurisdictions"}
        </button>
        <span className="text-sm text-muted">Holding assumed 100% for 24 months; adjustable via the API.</span>
      </div>
    </form>
  );
}

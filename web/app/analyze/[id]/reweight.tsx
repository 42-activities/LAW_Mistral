"use client";

import { useState } from "react";
import { FACTOR_LABEL, type FactorName } from "@/lib/types";

const PARAM: Record<FactorName, string> = {
  tax_efficiency: "tax",
  compliance: "compliance",
  treaty_breadth: "treaty",
  substance_burden: "substance",
};

export function Reweight({ weights, onDate }: { weights: Record<FactorName, string>; onDate: string }) {
  const [values, setValues] = useState(() =>
    Object.fromEntries(
      Object.entries(weights).map(([k, v]) => [k, Math.round(Number(v) * 100)]),
    ) as Record<FactorName, number>,
  );
  const total = Object.values(values).reduce((a, b) => a + b, 0) || 1;

  return (
    <form method="get" className="space-y-4">
      {(Object.keys(PARAM) as FactorName[]).map((f) => (
        <label key={f} className="block text-sm">
          <span className="flex justify-between">
            <span>{FACTOR_LABEL[f]}</span>
            <span className="font-mono text-muted">{Math.round((values[f] / total) * 100)}%</span>
          </span>
          <input
            type="range"
            name={PARAM[f]}
            min={0}
            max={100}
            value={values[f]}
            onChange={(e) => setValues((v) => ({ ...v, [f]: Number(e.target.value) }))}
            className="mt-1 w-full accent-[var(--accent)]"
          />
        </label>
      ))}
      <label className="block text-sm">
        <span>Data as of</span>
        <input
          type="date"
          name="on"
          defaultValue={onDate}
          className="mt-1 block w-full rounded-lg border border-line bg-surface px-3 py-2"
        />
      </label>
      <div className="flex gap-2">
        <button type="submit" className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white dark:text-black">
          Re-rank
        </button>
        <a href="?" className="rounded-lg border border-line px-4 py-2 text-sm hover:bg-bg">
          Default weights
        </a>
      </div>
      <p className="text-xs text-muted">Weights are normalised to 100% and stored with the run.</p>
    </form>
  );
}

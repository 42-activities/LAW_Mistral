"use client";

import { useEffect, useRef, useState } from "react";
import type { CorporateTaxRow } from "@/lib/types";
import { binFor, FILL_OPACITY, HOVER_OPACITY } from "./bins";

type World = {
  width: number;
  height: number;
  countries: Record<string, { name: string; d: string; dot: [number, number] | null }>;
};

function rateText(r: CorporateTaxRow) {
  if (r.rate === null) return "not recorded";
  const top = `${parseFloat(r.rate)}%`;
  return r.bracketed && r.min_rate !== null ? `${parseFloat(r.min_rate)}–${top} (bracketed)` : top;
}

const LIST_LABEL: Record<string, string> = {
  EU_AML_HIGH_RISK: "EU AML high-risk",
  EU_TAX_ANNEX_I: "EU non-cooperative (Annex I)",
  EU_TAX_ANNEX_II: "EU Annex II",
  FATF_BLACK: "FATF call for action",
  FATF_GREY: "FATF grey list",
  FR_ETNC: "France ETNC",
  GLOBAL_FORUM_RATING: "Global Forum rating",
  NL_LOW_TAX: "Netherlands low-tax list",
};

const WHT_LABEL = { DIVIDEND: "dividends", INTEREST: "interest", ROYALTY: "royalties" } as const;

function range(v: { min: string; max: string }) {
  const lo = parseFloat(v.min);
  const hi = parseFloat(v.max);
  return lo === hi ? `${hi}%` : `${lo}–${hi}%`;
}

/** Short, data-only description of a jurisdiction's rules for the hover bubble. */
function Bubble({ row }: { row: CorporateTaxRow }) {
  const s = row.summary;
  const pe = s.participation_exemption;
  const wht = (Object.keys(WHT_LABEL) as (keyof typeof WHT_LABEL)[]).filter((k) => s.wht[k]);
  return (
    <div className="space-y-1">
      <div className="font-medium">
        {row.name} <span className="font-mono text-xs text-muted">{row.code}</span>
      </div>
      <div>Corporate tax: {rateText(row)}</div>
      <div className="text-muted">
        Withholding (domestic):{" "}
        {wht.length ? wht.map((k) => `${WHT_LABEL[k]} ${range(s.wht[k]!)}`).join(" · ") : "not recorded"}
      </div>
      <div className="text-muted">
        Participation exemption:{" "}
        {pe === null
          ? "not recorded"
          : pe.dividends || pe.capital_gains
            ? [
                [pe.dividends && "dividends", pe.capital_gains && "gains"].filter(Boolean).join(" and "),
                pe.min_holding_pct && `from ${parseFloat(pe.min_holding_pct)}% holding`,
                pe.exempt_share_pct && Number(pe.exempt_share_pct) < 100 && `${parseFloat(pe.exempt_share_pct)}% exempt`,
              ]
                .filter(Boolean)
                .join(", ")
            : "none"}
      </div>
      <div className="text-muted">Tax treaties in force: {s.treaties_in_force}</div>
      {s.lists.length > 0 && (
        <div className="text-warn">
          Listed: {s.lists.map((l) => LIST_LABEL[l.code] ?? l.code).join(", ")}
        </div>
      )}
    </div>
  );
}

export function WorldMap({ rows }: { rows: CorporateTaxRow[] }) {
  const [world, setWorld] = useState<World | null>(null);
  const [failed, setFailed] = useState(false);
  const [hover, setHover] = useState<{ code: string; x: number; y: number } | null>(null);
  const box = useRef<HTMLDivElement>(null);
  const byCode = new Map(rows.map((r) => [r.code, r]));

  useEffect(() => {
    fetch("/world.json")
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then(setWorld)
      .catch(() => setFailed(true));
  }, []);

  if (failed) return <p className="text-sm text-muted">The map outline could not be loaded.</p>;
  if (!world) return <div className="aspect-[1000/437] w-full animate-pulse rounded-lg bg-bg" />;

  const hovered = hover ? byCode.get(hover.code) : undefined;
  const entries = Object.entries(world.countries);
  const tracked = entries.filter(([c]) => byCode.has(c));

  return (
    <div ref={box} className="relative" onMouseLeave={() => setHover(null)}>
      <svg
        viewBox={`0 0 ${world.width} ${world.height}`}
        className="h-auto w-full"
        role="img"
        aria-label="World map of headline corporate income tax rates"
      >
        {entries
          .filter(([c]) => !byCode.has(c))
          .map(([c, g]) => (
            <path key={c} d={g.d} fill="var(--line)" fillOpacity={0.5} stroke="var(--surface)" strokeWidth={0.3} />
          ))}
        {tracked.map(([c, g]) => {
          const row = byCode.get(c)!;
          const bin = binFor(row.rate);
          const color = bin?.color ?? "var(--muted)";
          const on = hover?.code === c;
          const enter = (e: React.MouseEvent) => {
            const r = box.current?.getBoundingClientRect();
            if (r) setHover({ code: c, x: e.clientX - r.left, y: e.clientY - r.top });
          };
          return (
            <a key={c} href={`/jurisdictions/${c}`} aria-label={`${row.name}: ${rateText(row)}`} onMouseLeave={() => setHover(null)}>
              <path
                d={g.d}
                fill={color}
                fillOpacity={on ? HOVER_OPACITY : bin ? FILL_OPACITY : 0.08}
                stroke={color}
                strokeOpacity={0.9}
                strokeWidth={on ? 0.9 : 0.5}
                onMouseMove={enter}
              />
              {g.dot && (
                <circle
                  cx={g.dot[0]}
                  cy={g.dot[1]}
                  r={on ? 4.5 : 3.5}
                  fill={color}
                  fillOpacity={on ? 0.9 : 0.6}
                  stroke="var(--surface)"
                  strokeWidth={0.8}
                  onMouseMove={enter}
                />
              )}
            </a>
          );
        })}
      </svg>
      {hover && hovered && (
        <div
          className="pointer-events-none absolute z-10 w-72 max-w-[80vw] rounded-lg border border-line bg-surface px-3 py-2 text-xs leading-relaxed shadow-md"
          style={{
            ...(hover.x > (box.current?.clientWidth ?? 0) / 2
              ? { right: (box.current?.clientWidth ?? 0) - hover.x + 12 }
              : { left: hover.x + 12 }),
            ...(hover.y > (box.current?.clientHeight ?? 0) / 2
              ? { bottom: (box.current?.clientHeight ?? 0) - hover.y + 12 }
              : { top: hover.y + 12 }),
          }}
        >
          <Bubble row={hovered} />
        </div>
      )}
    </div>
  );
}

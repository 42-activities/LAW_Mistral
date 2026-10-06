"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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

type View = { x: number; y: number; w: number };

const MAX_ZOOM = 24;

// Quick views, as boxes in projected map units (see scripts/build_world.py).
const REGIONS: { label: string; box: [number, number, number, number] | null }[] = [
  { label: "World", box: null },
  { label: "Europe", box: [469, 16, 138, 102] },
  { label: "Middle East & North Africa", box: [450, 89, 227, 123] },
  { label: "Gulf", box: [588, 125, 77, 72] },
];

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

  const [view, setView] = useState<View | null>(null);
  const svg = useRef<SVGSVGElement>(null);
  const drag = useRef<{ id: number; x: number; y: number; moved: boolean } | null>(null);
  const pinch = useRef<Map<number, { x: number; y: number }>>(new Map());

  const W = world?.width ?? 1000;
  const H = world?.height ?? 437;
  const v = view ?? { x: 0, y: 0, w: W };
  const k = W / v.w;

  const clamp = useCallback(
    (n: View): View => {
      const w = Math.min(W, Math.max(W / MAX_ZOOM, n.w));
      const h = (w * H) / W;
      return { w, x: Math.min(W - w, Math.max(0, n.x)), y: Math.min(H - h, Math.max(0, n.y)) };
    },
    [W, H],
  );

  /** Zooms by `factor` keeping the map point under (fx, fy) — fractions of the frame — fixed. */
  const zoomAt = useCallback(
    (factor: number, fx = 0.5, fy = 0.5) =>
      setView((cur) => {
        const c = cur ?? { x: 0, y: 0, w: W };
        const w = Math.min(W, Math.max(W / MAX_ZOOM, c.w / factor));
        const px = c.x + fx * c.w;
        const py = c.y + (fy * c.w * H) / W;
        return clamp({ w, x: px - fx * w, y: py - (fy * w * H) / W });
      }),
    [W, H, clamp],
  );

  const fit = (b: [number, number, number, number] | null) => {
    if (!b) return setView(null);
    const [bx, by, bw, bh] = b;
    const w = Math.max(bw, (bh * W) / H) * 1.08;
    setView(clamp({ w, x: bx + bw / 2 - w / 2, y: by + bh / 2 - (w * H) / W / 2 }));
  };

  const frac = (clientX: number, clientY: number) => {
    const r = svg.current!.getBoundingClientRect();
    return [(clientX - r.left) / r.width, (clientY - r.top) / r.height] as const;
  };

  // Ctrl/⌘ + scroll and trackpad pinch zoom; a plain scroll still scrolls the page.
  useEffect(() => {
    const el = svg.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      if (!e.ctrlKey && !e.metaKey) return;
      e.preventDefault();
      const [fx, fy] = frac(e.clientX, e.clientY);
      zoomAt(Math.exp(-e.deltaY * 0.01), fx, fy);
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [world, zoomAt]);

  const onPointerDown = (e: React.PointerEvent) => {
    pinch.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    drag.current = { id: e.pointerId, x: e.clientX, y: e.clientY, moved: false };
  };
  const onPointerMove = (e: React.PointerEvent) => {
    const pts = pinch.current;
    if (pts.has(e.pointerId) && pts.size === 2) {
      const [a, b] = [...pts.values()];
      const before = Math.hypot(a.x - b.x, a.y - b.y);
      pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
      const [c, d] = [...pts.values()];
      const after = Math.hypot(c.x - d.x, c.y - d.y);
      const [fx, fy] = frac((c.x + d.x) / 2, (c.y + d.y) / 2);
      if (before > 0) zoomAt(after / before, fx, fy);
      if (drag.current) drag.current.moved = true;
      return;
    }
    const d = drag.current;
    if (!d || d.id !== e.pointerId || e.buttons === 0) return;
    const dx = e.clientX - d.x;
    const dy = e.clientY - d.y;
    if (!d.moved && Math.hypot(dx, dy) < 4) return;
    if (!d.moved) svg.current?.setPointerCapture(e.pointerId);
    d.moved = true;
    d.x = e.clientX;
    d.y = e.clientY;
    const scale = v.w / svg.current!.getBoundingClientRect().width;
    setHover(null);
    setView((cur) => {
      const c = cur ?? { x: 0, y: 0, w: W };
      return clamp({ ...c, x: c.x - dx * scale, y: c.y - dy * scale });
    });
  };
  const onPointerUp = (e: React.PointerEvent) => {
    pinch.current.delete(e.pointerId);
    // Keep `moved` until the click that follows, so a drag never opens a country.
    setTimeout(() => (drag.current = null), 0);
  };

  if (failed) return <p className="text-sm text-muted">The map outline could not be loaded.</p>;
  if (!world) return <div className="aspect-[1000/437] w-full animate-pulse rounded-lg bg-bg" />;

  const hovered = hover ? byCode.get(hover.code) : undefined;
  const entries = Object.entries(world.countries);
  const tracked = entries.filter(([c]) => byCode.has(c));

  return (
    <div ref={box} className="relative overflow-hidden rounded-lg" onMouseLeave={() => setHover(null)}>
      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
        {REGIONS.map((r) => (
          <button
            key={r.label}
            type="button"
            onClick={() => fit(r.box)}
            className="rounded-md border border-line px-2 py-1 text-muted hover:bg-bg hover:text-fg"
          >
            {r.label}
          </button>
        ))}
        <span className="ml-auto hidden text-muted sm:inline">Drag to pan · Ctrl/⌘ + scroll or pinch to zoom</span>
      </div>
      <div className="absolute right-2 top-11 z-10 flex flex-col overflow-hidden rounded-md border border-line bg-surface shadow-sm">
        <button type="button" aria-label="Zoom in" onClick={() => zoomAt(1.6)} disabled={k >= MAX_ZOOM}
          className="size-8 text-lg leading-none hover:bg-bg disabled:opacity-40">+</button>
        <button type="button" aria-label="Zoom out" onClick={() => zoomAt(1 / 1.6)} disabled={k <= 1}
          className="size-8 border-t border-line text-lg leading-none hover:bg-bg disabled:opacity-40">−</button>
        <button type="button" aria-label="Reset view" onClick={() => setView(null)} disabled={k <= 1}
          className="size-8 border-t border-line text-xs hover:bg-bg disabled:opacity-40">⟲</button>
      </div>
      <svg
        ref={svg}
        viewBox={`${v.x} ${v.y} ${v.w} ${(v.w * H) / W}`}
        className={`h-auto w-full select-none ${k > 1 ? "cursor-grab active:cursor-grabbing" : ""}`}
        style={{ touchAction: k > 1 ? "none" : "pan-y" }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onDoubleClick={(e) => {
          const [fx, fy] = frac(e.clientX, e.clientY);
          zoomAt(e.shiftKey ? 1 / 2 : 2, fx, fy);
        }}
        onClickCapture={(e) => {
          if (drag.current?.moved) e.preventDefault();
        }}
        role="img"
        aria-label="World map of headline corporate income tax rates"
      >
        {entries
          .filter(([c]) => !byCode.has(c))
          .map(([c, g]) => (
            <path key={c} d={g.d} fill="var(--line)" fillOpacity={0.5} stroke="var(--surface)" strokeWidth={0.4} vectorEffect="non-scaling-stroke" />
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
                strokeWidth={on ? 1.2 : 0.6}
                vectorEffect="non-scaling-stroke"
                onMouseMove={enter}
              />
              {g.dot && (
                <circle
                  cx={g.dot[0]}
                  cy={g.dot[1]}
                  r={(on ? 4.5 : 3.5) / Math.sqrt(k)}
                  fill={color}
                  fillOpacity={on ? 0.9 : 0.6}
                  stroke="var(--surface)"
                  strokeWidth={0.8}
                  vectorEffect="non-scaling-stroke"
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

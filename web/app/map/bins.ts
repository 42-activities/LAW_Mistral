// Corporate tax bands for the map; a band includes its lower bound (15% falls in "15–20%").
export const BINS = [
  { lo: 0, hi: 0, label: "0%", color: "#2563eb" },
  { lo: 0, hi: 10, label: "under 10%", color: "#0891b2" },
  { lo: 10, hi: 15, label: "10–15%", color: "#16a34a" },
  { lo: 15, hi: 20, label: "15–20%", color: "#84cc16" },
  { lo: 20, hi: 25, label: "20–25%", color: "#eab308" },
  { lo: 25, hi: 30, label: "25–30%", color: "#f97316" },
  { lo: 30, hi: Infinity, label: "30% and over", color: "#dc2626" },
];

// The map tints countries lightly: 80% transparent, stronger on hover.
export const FILL_OPACITY = 0.2;
export const HOVER_OPACITY = 0.55;

export function binFor(rate: string | null) {
  if (rate === null) return null;
  const r = Number(rate);
  if (r === 0) return BINS[0];
  return BINS.slice(1).find((b) => r >= b.lo && r < b.hi) ?? null;
}

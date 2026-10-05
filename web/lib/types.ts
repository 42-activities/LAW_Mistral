export type Flag = { code: string; message: string; interpretation_required: boolean };

export type Factor = {
  score: string | null;
  weight: string;
  citations: number[];
  flags: Flag[];
  detail: Record<string, string>;
};

export type FlowLine = {
  flow: string;
  leg: string;
  kind: "wht" | "cit";
  rate: string | null;
  tax_per_100: string | null;
  citations: number[];
};

export type ScoreCard = {
  jurisdiction: string;
  rank: number;
  overall_score: string | null;
  complete: boolean;
  weight_set: string;
  data_asof: string;
  engine_version: string;
  factors: Record<FactorName, Factor>;
  flow_breakdown: FlowLine[];
  guardrail_flags: Flag[];
  citations: number[];
};

export type FactorName = "tax_efficiency" | "compliance" | "treaty_breadth" | "substance_burden";

export const FACTOR_LABEL: Record<FactorName, string> = {
  tax_efficiency: "Tax efficiency",
  compliance: "Compliance standing",
  treaty_breadth: "Treaty network",
  substance_burden: "Substance burden",
};

export type Recommendation = {
  scoring_run_id: number;
  weight_set: string;
  weights: Record<FactorName, string>;
  engine_version: string;
  data_asof: string;
  scorecards: ScoreCard[];
  summary?: {
    text: string;
    status: "pass" | "repaired" | "template";
    model: string | null;
    citations: number[];
    note: string | null;
  };
};

export type Option = {
  value: string;
  label: string;
  hint?: string;
  enabled?: boolean;
  suggests?: string[];
};

export type Question = {
  code: string;
  text: string;
  help: string | null;
  kind: "single" | "flows";
  options: Option[];
};

export type Jurisdiction = { code: string; name: string };

export type Profile = {
  id: number;
  answers: { size: string; activity: string; flows: string[]; sources: string[]; parent: string };
  derived: {
    parent: string;
    substance_capacity: string;
    flows: { income_category: string; source: string }[];
  };
};

export type Period = { from: string | null; to: string | null };

export type Overview = {
  code: string;
  name: string;
  on_date: string;
  domestic_rules: {
    tax_type: string;
    income_category: string;
    taxpayer_type: string;
    rate: string | null;
    brackets: { lower: string; upper: string | null; rate: string }[];
    valid: Period;
    citation: number;
  }[];
  holding_regime: {
    dividends_exempt: boolean;
    capital_gains_exempt: boolean;
    min_holding_pct: string | null;
    min_holding_period_months: number | null;
    min_subject_to_tax_rate: string | null;
    exempt_share_pct: string;
    notes: string | null;
    valid: Period;
    citation: number;
  } | null;
  cfc_rule: {
    control_threshold_pct: string;
    low_tax_relative_pct: string;
    effect: string;
    legal_ref: string;
    citation: number;
  } | null;
  substance_rules: { regime: string; requirement_band: string; citation: number }[];
  lists: { list_code: string; family: string; classification: string; citation: number }[];
  treaties: {
    name: string;
    counterparties: string[];
    signature_date: string;
    entry_into_force_date: string | null;
    in_force: boolean;
    citation: number;
    rates: {
      income_category: string;
      article: string;
      max_rate: string | null;
      exclusive_residence_taxation: boolean;
      relief_mechanism: string | null;
      beneficial_owner_required: boolean;
      citation: number;
    }[];
  }[];
};

export type ListInfo = {
  code: string;
  name: string;
  family: string;
  publisher: string;
  update_cadence: string | null;
  citation: number;
  members: { jurisdiction: string; classification: string; valid: Period; citation: number }[];
};

export type Evidence = {
  id: number;
  document_title: string;
  document_url: string;
  retrieved_at: string;
  article: string | null;
  page: number | null;
  quoted_text: string;
  review_status: string;
};

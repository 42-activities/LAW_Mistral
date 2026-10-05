"use server";

import { api, ApiError } from "@/lib/api";

export type AskResult = {
  query: { source: string; recipient: string; income_category: string; holding_pct: string | null; on_date: string };
  result: {
    complete: boolean;
    domestic_rate: string | null;
    effective_domestic_rate: string | null;
    treaty_cap: string | null;
    withheld_at_payment: string | null;
    final_rate: string | null;
    treaty_name: string | null;
    citations: number[];
    flags: { code: string; message: string; interpretation_required: boolean }[];
  };
  answer: string;
};

export type AskState = { question: string; data: AskResult | null; error: string | null };

export async function askQuestion(_prev: AskState, form: FormData): Promise<AskState> {
  const question = String(form.get("question") ?? "").trim();
  if (question.length < 5) return { question, data: null, error: "Please write a full question." };
  try {
    const data = await api<AskResult>("/v1/ask", { method: "POST", body: { question } });
    return { question, data, error: null };
  } catch (e) {
    if (e instanceof ApiError && e.status === 503)
      return { question, data: null, error: "Natural-language questions are not enabled on this server yet." };
    return { question, data: null, error: e instanceof ApiError ? e.detail : "The service is unavailable." };
  }
}

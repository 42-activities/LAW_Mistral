"use server";

import { redirect } from "next/navigation";
import { api, ApiError } from "@/lib/api";

export type WizardState = { error: string | null };

export async function createProfile(_prev: WizardState, form: FormData): Promise<WizardState> {
  const answers = {
    size: form.get("size"),
    activity: form.get("activity"),
    flows: form.getAll("flows"),
    sources: form.getAll("sources"),
    parent: form.get("parent"),
  };
  let id: number;
  try {
    ({ id } = await api<{ id: number }>("/v1/profiles", { method: "POST", body: { answers } }));
  } catch (e) {
    return { error: e instanceof ApiError ? e.detail : "The analysis service is unavailable." };
  }
  redirect(`/analyze/${id}`);
}

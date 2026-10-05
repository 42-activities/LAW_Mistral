"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { api, ApiError, SESSION_COOKIE } from "@/lib/api";

export type FormState = { ok: string | null; error: string | null; secret?: string };

function fail(e: unknown): FormState {
  return { ok: null, error: e instanceof ApiError ? e.detail : "The service is unavailable." };
}

export async function changePassword(_p: FormState, form: FormData): Promise<FormState> {
  const next = String(form.get("new_password") ?? "");
  if (next !== form.get("repeat")) return { ok: null, error: "The new passwords do not match." };
  try {
    await api("/v1/auth/password", {
      method: "POST",
      body: { current_password: form.get("current_password"), new_password: next },
    });
  } catch (e) {
    return fail(e);
  }
  // Changing the password ends every session, including this one.
  (await cookies()).delete(SESSION_COOKIE);
  redirect("/login?next=/account");
}

export async function createUser(_p: FormState, form: FormData): Promise<FormState> {
  try {
    await api("/v1/admin/users", {
      method: "POST",
      body: {
        email: form.get("email"),
        name: form.get("name") || null,
        role: form.get("role"),
        password: form.get("password"),
      },
    });
  } catch (e) {
    return fail(e);
  }
  revalidatePath("/account");
  return { ok: `Created ${form.get("email")}. Share the initial password with them securely.`, error: null };
}

export async function updateUser(form: FormData): Promise<void> {
  const body: Record<string, unknown> = {};
  if (form.get("role")) body.role = form.get("role");
  if (form.get("active")) body.active = form.get("active") === "true";
  await api(`/v1/admin/users/${Number(form.get("id"))}`, { method: "PATCH", body }).catch(() => {});
  revalidatePath("/account");
}

export async function createKey(_p: FormState, form: FormData): Promise<FormState> {
  try {
    const key = await api<{ key: string; name: string }>("/v1/admin/api-keys", {
      method: "POST",
      body: { name: form.get("name"), role: form.get("role") },
    });
    revalidatePath("/account");
    return { ok: `Key “${key.name}” created. Copy it now — it is not shown again.`, error: null, secret: key.key };
  } catch (e) {
    return fail(e);
  }
}

export async function revokeKey(form: FormData): Promise<void> {
  await api(`/v1/admin/api-keys/${Number(form.get("id"))}`, { method: "DELETE" }).catch(() => {});
  revalidatePath("/account");
}

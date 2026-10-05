"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { api, ApiError, SESSION_COOKIE } from "@/lib/api";

export type LoginState = { error: string | null; email: string };

function safeNext(next: FormDataEntryValue | null): string {
  const n = typeof next === "string" ? next : "";
  return n.startsWith("/") && !n.startsWith("//") ? n : "/analyze";
}

export async function login(_prev: LoginState, form: FormData): Promise<LoginState> {
  const email = String(form.get("email") ?? "");
  let token: string, expires: string;
  try {
    ({ token, expires_at: expires } = await api<{ token: string; expires_at: string }>("/v1/auth/login", {
      method: "POST",
      body: { email, password: form.get("password") },
    }));
  } catch (e) {
    if (e instanceof ApiError && (e.status === 401 || e.status === 429 || e.status === 422))
      return { error: e.status === 422 ? "Enter your email and password." : e.detail, email };
    return { error: "Sign-in is unavailable right now.", email };
  }
  (await cookies()).set(SESSION_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    expires: new Date(expires),
  });
  redirect(safeNext(form.get("next")));
}

export async function logout(): Promise<void> {
  try {
    await api("/v1/auth/logout", { method: "POST" });
  } catch {}
  (await cookies()).delete(SESSION_COOKIE);
  redirect("/");
}

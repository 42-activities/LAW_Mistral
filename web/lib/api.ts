import { cookies } from "next/headers";

// Server-side only: neither the API key nor the session token is exposed to browser scripts.
const API_URL = process.env.API_URL ?? "http://app:8000";
export const SESSION_COOKIE = "mt_session";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(`API ${status}: ${detail}`);
  }
}

/** Calls the API as the signed-in user when there is a session, else as the site's viewer key. */
export async function api<T>(path: string, init?: { method?: string; body?: unknown }): Promise<T> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  const auth: Record<string, string> = token
    ? { Authorization: `Bearer ${token}` }
    : { "X-API-Key": process.env.API_KEY ?? "" };
  const res = await fetch(`${API_URL}${path}`, {
    method: init?.method ?? "GET",
    headers: { ...auth, "content-type": "application/json" },
    body: init?.body === undefined ? undefined : JSON.stringify(init.body),
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {}
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export function today(): string {
  return new Date().toISOString().slice(0, 10);
}

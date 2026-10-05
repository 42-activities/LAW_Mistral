import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { api, ApiError, SESSION_COOKIE } from "./api";

export type Me = {
  organisation: { id: number; name: string | null };
  role: "viewer" | "analyst" | "admin";
  user: { id: number; email: string; name: string | null; role: string } | null;
  plan: { code: string; name: string; analyses_per_day: number; analyses_per_minute: number; llm_calls_per_day: number };
};

/** The signed-in user, or null for anonymous visitors (who browse with the site's viewer key). */
export async function currentUser(): Promise<Me | null> {
  if (!(await cookies()).get(SESSION_COOKIE)) return null;
  try {
    const me = await api<Me>("/v1/auth/me");
    return me.user ? me : null;
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) return null;
    throw e;
  }
}

export async function requireUser(next: string): Promise<Me> {
  const me = await currentUser();
  if (!me) redirect(`/login?next=${encodeURIComponent(next)}`);
  return me;
}

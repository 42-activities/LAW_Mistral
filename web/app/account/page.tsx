import type { Metadata } from "next";
import { Badge, Section } from "@/components/ui";
import { api } from "@/lib/api";
import { requireUser } from "@/lib/session";
import { revokeKey, updateUser } from "./actions";
import { NewKeyForm, NewUserForm, PasswordForm } from "./forms";

export const metadata: Metadata = { title: "Account" };

type User = { id: number; email: string; name: string | null; role: string; active: boolean; last_login_at: string | null };
type Key = { id: number; name: string; role: string; active: boolean; created_at: string; last_used_at: string | null };
type Usage = { days: number; usage: Record<string, { events: number; units: number }> };
type Audit = { action: string; actor: string | null; target: string | null; created_at: string };

const USAGE_LABEL: Record<string, string> = {
  analysis: "Analyses",
  ask: "Questions",
  llm_call: "AI calls",
};

export default async function AccountPage() {
  const me = await requireUser("/account");
  const isAdmin = me.role === "admin";
  const [users, keys, usage, audit] = isAdmin
    ? await Promise.all([
        api<User[]>("/v1/admin/users"),
        api<Key[]>("/v1/admin/api-keys"),
        api<Usage>("/v1/admin/usage?days=30"),
        api<Audit[]>("/v1/admin/audit?limit=30"),
      ])
    : [[], [], null, []];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Account</h1>
        <p className="mt-2 text-muted">
          {me.user?.name ? `${me.user.name} · ` : ""}
          {me.user?.email} · {me.organisation.name} · <Badge tone="accent">{me.role}</Badge>
        </p>
      </div>

      <Section title="Plan and usage" aside={me.plan.name}>
        <div className="grid gap-3 sm:grid-cols-3 text-sm">
          <div className="rounded-lg bg-bg px-4 py-3">
            <div className="text-xs text-muted">Analyses</div>
            <div className="mt-1">{me.plan.analyses_per_day}/day · {me.plan.analyses_per_minute}/minute</div>
          </div>
          <div className="rounded-lg bg-bg px-4 py-3">
            <div className="text-xs text-muted">AI calls</div>
            <div className="mt-1">{me.plan.llm_calls_per_day}/day</div>
          </div>
          {usage && (
            <div className="rounded-lg bg-bg px-4 py-3">
              <div className="text-xs text-muted">Last {usage.days} days</div>
              <div className="mt-1">
                {Object.keys(usage.usage).length === 0
                  ? "no usage yet"
                  : Object.entries(usage.usage)
                      .map(([k, v]) => `${USAGE_LABEL[k] ?? k} ${v.events}${k === "llm_call" ? ` (${v.units.toLocaleString()} tokens)` : ""}`)
                      .join(" · ")}
              </div>
            </div>
          )}
        </div>
      </Section>

      <Section title="Password">
        <PasswordForm />
      </Section>

      {isAdmin && (
        <>
          <Section title="Users">
            <table className="w-full text-sm">
              <tbody className="divide-y divide-line">
                {users.map((u) => (
                  <tr key={u.id} className={u.active ? "" : "text-muted"}>
                    <td className="py-2 pr-4">
                      {u.name || u.email}
                      {u.name && <span className="block text-xs text-muted">{u.email}</span>}
                    </td>
                    <td className="py-2 pr-4">
                      <form action={updateUser} className="flex gap-2">
                        <input type="hidden" name="id" value={u.id} />
                        <select name="role" defaultValue={u.role} className="rounded-md border border-line bg-surface px-2 py-1">
                          <option value="viewer">viewer</option>
                          <option value="analyst">analyst</option>
                          <option value="admin">admin</option>
                        </select>
                        <button className="rounded-md border border-line px-2 py-1 hover:bg-bg">Save</button>
                      </form>
                    </td>
                    <td className="py-2 pr-4 text-xs text-muted">
                      {u.last_login_at ? `last sign-in ${u.last_login_at.slice(0, 10)}` : "never signed in"}
                    </td>
                    <td className="py-2 text-right">
                      <form action={updateUser}>
                        <input type="hidden" name="id" value={u.id} />
                        <input type="hidden" name="active" value={u.active ? "false" : "true"} />
                        <button className="rounded-md border border-line px-2 py-1 hover:bg-bg">
                          {u.active ? "Deactivate" : "Reactivate"}
                        </button>
                      </form>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-6 border-t border-line pt-5">
              <h3 className="mb-3 text-sm font-medium">Add a user</h3>
              <NewUserForm />
            </div>
          </Section>

          <Section title="API keys" aside="for scripts and integrations; see /docs">
            {keys.length > 0 && (
              <table className="mb-6 w-full text-sm">
                <tbody className="divide-y divide-line">
                  {keys.map((k) => (
                    <tr key={k.id} className={k.active ? "" : "text-muted line-through"}>
                      <td className="py-2 pr-4">{k.name}</td>
                      <td className="py-2 pr-4">{k.role}</td>
                      <td className="py-2 pr-4 text-xs text-muted">
                        {k.last_used_at ? `used ${k.last_used_at.slice(0, 10)}` : "never used"}
                      </td>
                      <td className="py-2 text-right">
                        {k.active && (
                          <form action={revokeKey}>
                            <input type="hidden" name="id" value={k.id} />
                            <button className="rounded-md border border-line px-2 py-1 text-bad hover:bg-bad-soft">Revoke</button>
                          </form>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <NewKeyForm />
          </Section>

          <Section title="Audit log" aside="latest 30 events">
            <table className="w-full text-sm">
              <tbody className="divide-y divide-line">
                {audit.map((a, i) => (
                  <tr key={i}>
                    <td className="py-1.5 pr-4 text-xs text-muted whitespace-nowrap">{a.created_at.slice(0, 16).replace("T", " ")}</td>
                    <td className="py-1.5 pr-4">{a.action.replaceAll("_", " ")}</td>
                    <td className="py-1.5 pr-4 text-muted">{a.target}</td>
                    <td className="py-1.5 text-muted">{a.actor}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Section>
        </>
      )}
    </div>
  );
}

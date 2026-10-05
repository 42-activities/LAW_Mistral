"use client";

import { useActionState } from "react";
import { changePassword, createKey, createUser, type FormState } from "./actions";

const input = "mt-1 block w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm";
const button = "rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white dark:text-black disabled:opacity-40";
const empty: FormState = { ok: null, error: null };

function Result({ state }: { state: FormState }) {
  return (
    <>
      {state.error && <p className="rounded-lg bg-bad-soft px-3 py-2 text-sm text-bad">{state.error}</p>}
      {state.ok && <p className="rounded-lg bg-accent-soft px-3 py-2 text-sm text-good">{state.ok}</p>}
      {state.secret && (
        <code className="block break-all rounded-lg border border-line bg-bg px-3 py-2 text-xs">{state.secret}</code>
      )}
    </>
  );
}

export function PasswordForm() {
  const [state, action, pending] = useActionState(changePassword, empty);
  return (
    <form action={action} className="grid gap-3 sm:grid-cols-3 items-end">
      <label className="text-sm">Current password<input name="current_password" type="password" autoComplete="current-password" required className={input} /></label>
      <label className="text-sm">New password (12+ characters)<input name="new_password" type="password" autoComplete="new-password" minLength={12} required className={input} /></label>
      <label className="text-sm">Repeat new password<input name="repeat" type="password" autoComplete="new-password" required className={input} /></label>
      <div className="sm:col-span-3 space-y-2">
        <Result state={state} />
        <button disabled={pending} className={button}>Change password</button>
        <p className="text-xs text-muted">You will be signed out everywhere and asked to sign in again.</p>
      </div>
    </form>
  );
}

function RoleSelect() {
  return (
    <select name="role" defaultValue="analyst" className={input}>
      <option value="viewer">Viewer — read only</option>
      <option value="analyst">Analyst — run analyses</option>
      <option value="admin">Admin — manage the organisation</option>
    </select>
  );
}

export function NewUserForm() {
  const [state, action, pending] = useActionState(createUser, empty);
  return (
    <form action={action} className="grid gap-3 sm:grid-cols-2 items-end">
      <label className="text-sm">Email<input name="email" type="email" required className={input} /></label>
      <label className="text-sm">Name<input name="name" className={input} /></label>
      <label className="text-sm">Role<RoleSelect /></label>
      <label className="text-sm">Initial password (12+ characters)<input name="password" type="text" minLength={12} required autoComplete="off" className={input} /></label>
      <div className="sm:col-span-2 space-y-2">
        <Result state={state} />
        <button disabled={pending} className={button}>Add user</button>
      </div>
    </form>
  );
}

export function NewKeyForm() {
  const [state, action, pending] = useActionState(createKey, empty);
  return (
    <form action={action} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] items-end">
      <label className="text-sm">Name<input name="name" required placeholder="e.g. reporting script" className={input} /></label>
      <label className="text-sm">Role<RoleSelect /></label>
      <button disabled={pending} className={button}>Create key</button>
      <div className="sm:col-span-3 space-y-2"><Result state={state} /></div>
    </form>
  );
}

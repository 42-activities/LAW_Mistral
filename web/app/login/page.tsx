import type { Metadata } from "next";
import { LoginForm } from "./form";

export const metadata: Metadata = { title: "Sign in" };

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ next?: string }> }) {
  const { next } = await searchParams;
  return (
    <div className="mx-auto max-w-sm pt-8">
      <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
      <p className="mt-2 text-sm text-muted">
        Analyses and questions are available to members of a subscribed organisation. Accounts are
        created by your organisation&apos;s admin.
      </p>
      <div className="mt-6 rounded-xl border border-line bg-surface p-6">
        <LoginForm next={next ?? "/analyze"} />
      </div>
    </div>
  );
}

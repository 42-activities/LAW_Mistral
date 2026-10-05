import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: { default: "MapTax — holding jurisdiction analysis", template: "%s · MapTax" },
  description:
    "Sourced, reproducible holding-jurisdiction recommendations for tax professionals. " +
    "Every figure cites its official source.",
};

const NAV = [
  { href: "/analyze", label: "Analyze" },
  { href: "/jurisdictions", label: "Jurisdictions" },
  { href: "/compare", label: "Compare" },
  { href: "/ask", label: "Ask" },
  { href: "/lists", label: "Lists" },
  { href: "/docs", label: "API" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen flex flex-col font-sans antialiased">
        <header className="border-b border-line bg-surface">
          <div className="mx-auto max-w-6xl px-4 h-14 flex items-center gap-6">
            <Link href="/" className="font-semibold tracking-tight flex items-center gap-2">
              <span className="inline-block size-6 rounded-md bg-accent" aria-hidden />
              MapTax
            </Link>
            <nav className="flex gap-1 text-sm overflow-x-auto">
              {NAV.map((n) => (
                <Link
                  key={n.href}
                  href={n.href}
                  className="px-2.5 py-1.5 rounded-md text-muted hover:text-fg hover:bg-bg whitespace-nowrap"
                >
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="flex-1 mx-auto w-full max-w-6xl px-4 py-8">{children}</main>
        <footer className="border-t border-line text-xs text-muted">
          <div className="mx-auto max-w-6xl px-4 py-6 space-y-1">
            <p>
              Informational working draft for tax professionals — not tax advice. Verify every
              figure against the cited official source before use.
            </p>
            <p>Figures marked “unreviewed” were checked against the source by software, not yet by a named reviewer.</p>
          </div>
        </footer>
      </body>
    </html>
  );
}

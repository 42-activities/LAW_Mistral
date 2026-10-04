import Link from "next/link";

const PILLARS = [
  {
    title: "Every figure is cited",
    body: "Rates, treaty caps, exemptions and list statuses each link to the official text they come from — article, quote and retrieval date.",
  },
  {
    title: "A deterministic engine",
    body: "Withholding, treaty relief, participation exemptions and CIT are computed by rules, not guessed. Same inputs, same data date, same result.",
  },
  {
    title: "Guardrails before scores",
    body: "FATF call-for-action jurisdictions and non-cooperative states for your counterparties are capped and flagged, whatever the tax saving.",
  },
];

const STEPS = [
  ["Describe the client", "Size, activity, income flows, where income arises and where the parent sits — three tickable questions."],
  ["Get ranked candidates", "Each holding jurisdiction gets a ScoreCard: tax efficiency, compliance standing, treaty network, substance burden."],
  ["Validate the working draft", "Open the flow-by-flow computation, follow each citation, re-weight the factors to your client's priorities."],
];

export default function Home() {
  return (
    <div className="space-y-16">
      <section className="pt-6 md:pt-12 max-w-3xl">
        <p className="text-sm font-medium text-accent">For tax professionals</p>
        <h1 className="mt-3 text-4xl md:text-5xl font-semibold tracking-tight leading-tight">
          Where should the holding sit? A sourced answer, leg by leg.
        </h1>
        <p className="mt-5 text-lg text-muted leading-relaxed">
          MapTax ranks candidate holding jurisdictions for a client&apos;s structure and shows
          the full tax computation behind each rank — domestic rate, treaty cap, amount withheld,
          exemption, onward distribution — with a citation on every number.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/analyze"
            className="rounded-lg bg-accent px-5 py-2.5 font-medium text-white dark:text-black hover:opacity-90"
          >
            Start an analysis
          </Link>
          <Link
            href="/jurisdictions"
            className="rounded-lg border border-line bg-surface px-5 py-2.5 font-medium hover:bg-bg"
          >
            Browse the data
          </Link>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {PILLARS.map((p) => (
          <div key={p.title} className="rounded-xl border border-line bg-surface p-5">
            <h2 className="font-semibold">{p.title}</h2>
            <p className="mt-2 text-sm text-muted leading-relaxed">{p.body}</p>
          </div>
        ))}
      </section>

      <section>
        <h2 className="text-xl font-semibold tracking-tight">How it works</h2>
        <ol className="mt-5 grid gap-4 md:grid-cols-3">
          {STEPS.map(([title, body], i) => (
            <li key={title} className="rounded-xl border border-line bg-surface p-5">
              <span className="text-sm font-mono text-accent">0{i + 1}</span>
              <h3 className="mt-1 font-semibold">{title}</h3>
              <p className="mt-2 text-sm text-muted leading-relaxed">{body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="rounded-xl border border-line bg-surface p-6 md:flex md:items-center md:justify-between gap-6">
        <div>
          <h2 className="font-semibold">Current coverage</h2>
          <p className="mt-1 text-sm text-muted max-w-2xl">
            The France–UAE corridor is modelled in depth (domestic withholding, CIT, participation
            exemptions, the 1989 treaty as amended, French CFC and ETNC rules, FATF / EU lists).
            Coverage is being extended to 50–70 jurisdictions; candidates without data are shown
            as incomplete, never guessed.
          </p>
        </div>
        <Link href="/lists" className="mt-4 md:mt-0 inline-block text-sm font-medium text-accent hover:underline whitespace-nowrap">
          See the lists tracked →
        </Link>
      </section>
    </div>
  );
}

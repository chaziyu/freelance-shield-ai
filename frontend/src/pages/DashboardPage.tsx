import { Link } from "react-router-dom";

export function DashboardPage() {
  return (
    <section className="grid gap-8 lg:grid-cols-[1.4fr_0.6fr] lg:items-start">
      <div>
        <p className="mb-3 text-sm font-medium uppercase tracking-[0.2em] text-cyan-300">
          Evidence-first workflow
        </p>
        <h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">
          Turn informal project chats into clear, reviewable records.
        </h1>
        <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-300">
          Milestone 1 provides the interface and health-check scaffold only.
          Project analysis, agreements, evidence, and agent traces are not
          connected yet.
        </p>
        <Link
          className="mt-8 inline-flex rounded-lg bg-cyan-300 px-5 py-3 font-semibold text-slate-950 hover:bg-cyan-200"
          to="/new-project"
        >
          Open new project
        </Link>
      </div>

      <aside className="rounded-2xl border border-amber-300/25 bg-amber-300/10 p-5 text-sm leading-6 text-amber-100">
        <h2 className="font-semibold">Safety boundary</h2>
        <p className="mt-2">
          Draft only — review and send manually. This product does not send
          messages, collect payment, or provide legal advice.
        </p>
      </aside>
    </section>
  );
}

interface PlaceholderPageProps {
  title: string;
}

export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <section className="rounded-2xl border border-dashed border-white/15 bg-white/5 p-8">
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-300">
        Placeholder route
      </p>
      <h1 className="mt-2 text-3xl font-semibold">{title}</h1>
      <p className="mt-3 text-slate-400">
        This workflow is intentionally deferred beyond Milestone 1.
      </p>
    </section>
  );
}

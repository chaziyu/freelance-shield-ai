import { platforms } from "../schema";

export function NewProjectPage() {
  return (
    <section>
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-300">
        New project
      </p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
        FreelanceShield AI
      </h1>
      <p className="mt-3 max-w-2xl text-slate-300">
        Draft only — review and send manually. Your chat stays unprocessed in
        this scaffold; agent analysis is not implemented yet.
      </p>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
        <form className="rounded-2xl border border-white/10 bg-white/5 p-5 sm:p-6">
          <label className="block font-medium" htmlFor="client-chat">
            Informal client chat
          </label>
          <textarea
            className="mt-2 min-h-48 w-full resize-y rounded-xl border border-white/15 bg-slate-900 p-4 text-slate-100 outline-none placeholder:text-slate-500 focus:border-cyan-300"
            id="client-chat"
            name="clientChat"
            placeholder="Paste synthetic demo chat here."
          />

          <label className="mt-5 block font-medium" htmlFor="platform">
            Source platform
          </label>
          <select
            className="mt-2 w-full rounded-xl border border-white/15 bg-slate-900 p-3 text-slate-100 outline-none focus:border-cyan-300"
            defaultValue="Instagram"
            id="platform"
            name="platform"
          >
            {platforms.map((platform) => (
              <option key={platform} value={platform}>
                {platform}
              </option>
            ))}
          </select>

          <button
            className="mt-6 w-full cursor-not-allowed rounded-xl bg-slate-700 px-4 py-3 font-semibold text-slate-400"
            disabled
            type="button"
          >
            Analyse Deal
          </button>
          <p className="mt-2 text-xs text-slate-500">
            Analysis becomes available when the agent workflow is implemented.
          </p>
        </form>

        <aside className="rounded-2xl border border-white/10 bg-white/5 p-5 sm:p-6">
          <h2 className="font-semibold">Agent trace</h2>
          <div className="mt-4 rounded-xl border border-dashed border-white/15 p-5 text-sm text-slate-400">
            No trace yet. Backend agent traces will appear here in a later
            milestone.
          </div>
        </aside>
      </div>
    </section>
  );
}

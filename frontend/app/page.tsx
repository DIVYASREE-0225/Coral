import Link from "next/link";
import { api } from "@/lib/api";
import { Database, FileText, ShieldCheck, TrendingUp, MessageCircle, Layers } from "lucide-react";

async function getWorkers() {
  try {
    return await api.workers();
  } catch {
    return [];
  }
}

const AGENTS = [
  { icon: Layers, name: "Platform Ingestion", desc: "Pulls earnings from Zomato, Swiggy, Ola, Uber, Urban Company into one ledger." },
  { icon: FileText, name: "Tax Filing", desc: "44AD presumptive calc, advance tax, ITR-4 pre-fill — one-click via Income Tax MCP." },
  { icon: ShieldCheck, name: "Income Proof", desc: "Bank-grade Digital Employment Certificate, signed and QR-verifiable." },
  { icon: TrendingUp, name: "Credit Score", desc: "Gig-native CIBIL-style score from consistency, tenure, growth." },
  { icon: MessageCircle, name: "Multilingual Voice", desc: "Telugu, Hindi, Tamil, Kannada — answered in 3 seconds via WhatsApp." },
  { icon: Database, name: "SQL Orchestrator", desc: "Cross-source SQL across all agents simultaneously — Coral's superpower." },
];

export default async function Home() {
  const workers = await getWorkers();

  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <header className="mb-14">
        <span className="chip bg-coral-900/40 text-coral-400 ring-1 ring-coral-700/40">
          🏆 The One Big Idea — Coral Multi-Agent
        </span>
        <h1 className="mt-4 text-5xl font-semibold tracking-tight">
          GigProof
        </h1>
        <p className="mt-2 text-xl text-coral-400">
          Financial Identity Agent for India&apos;s Invisible Workforce
        </p>
        <p className="mt-6 max-w-3xl text-white/70 leading-relaxed">
          1.2 crore Indian gig workers earn real money — but have no salary slip, no Form 16,
          no credit score, no auto-filed ITR. GigProof is a multi-agent system on Coral that
          ingests every platform&apos;s earning data, files ITR, generates a bank-grade income
          proof, and builds a credit identity — all from a single SQL query, in any language.
        </p>
      </header>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-14">
        {[
          ["1.2 Cr+", "gig workers in India"],
          ["0", "have a salary slip"],
          ["₹50K Cr+", "loans blocked, no proof"],
          ["31 Cr", "e-Shram registered"],
        ].map(([n, l]) => (
          <div key={l} className="card p-5">
            <div className="text-2xl font-semibold text-white">{n}</div>
            <div className="mt-1 text-sm text-white/60">{l}</div>
          </div>
        ))}
      </section>

      <section className="mb-14">
        <h2 className="text-xs font-semibold tracking-widest text-white/50 mb-4">
          DEMO WORKERS
        </h2>
        {workers.length === 0 ? (
          <div className="card p-6 text-white/60">
            Backend not running. Start it with{" "}
            <code className="text-coral-400 bg-ink-700 px-1.5 py-0.5 rounded">
              uvicorn main:app --reload --port 8000
            </code>{" "}
            in <code className="text-coral-400">backend/</code>.
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-3">
            {workers.map((w) => (
              <Link
                key={w.worker_id}
                href={`/worker/${w.worker_id}`}
                className="card p-5 hover:border-coral-600/40 hover:bg-ink-700/60 transition group"
              >
                <div className="flex items-center justify-between">
                  <div className="text-lg font-semibold">{w.name}</div>
                  <span className="text-xs text-white/40">{w.worker_id}</span>
                </div>
                <div className="mt-1 text-sm text-white/60">
                  {w.city} · {w.language}
                </div>
                <div className="mt-4 flex flex-wrap gap-1.5">
                  {w.platforms.split(",").map((p) => (
                    <span
                      key={p}
                      className="chip bg-coral-900/40 text-coral-400 capitalize"
                    >
                      {p}
                    </span>
                  ))}
                </div>
                <div className="mt-4 text-xs text-coral-400 group-hover:text-coral-100 transition">
                  Open dashboard →
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section className="mb-14">
        <h2 className="text-xs font-semibold tracking-widest text-white/50 mb-4">
          THE CORAL MULTI-AGENT ARCHITECTURE
        </h2>
        <div className="card divide-y divide-white/5">
          {AGENTS.map(({ icon: Icon, name, desc }) => (
            <div key={name} className="flex gap-4 p-5">
              <div className="rounded-lg bg-coral-900/40 p-2 h-fit">
                <Icon className="h-5 w-5 text-coral-400" />
              </div>
              <div>
                <div className="font-medium">{name}</div>
                <div className="text-sm text-white/60 mt-0.5">{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xs font-semibold tracking-widest text-white/50 mb-4">
          TRY THE ORCHESTRATOR
        </h2>
        <Link
          href="/sql"
          className="card p-6 flex items-center justify-between hover:border-coral-600/40 transition"
        >
          <div>
            <div className="font-medium">SQL Playground</div>
            <div className="text-sm text-white/60 mt-1">
              Run cross-source queries across all platforms in a single SQL statement.
            </div>
          </div>
          <Database className="h-6 w-6 text-coral-400" />
        </Link>
      </section>
    </main>
  );
}

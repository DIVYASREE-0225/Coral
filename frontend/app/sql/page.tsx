"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Play, Database } from "lucide-react";
import { api } from "@/lib/api";

export default function SqlPlayground() {
  const [examples, setExamples] = useState<{ name: string; sql: string }[]>([]);
  const [schemas, setSchemas] = useState<any[]>([]);
  const [sql, setSql] = useState<string>("");
  const [rows, setRows] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    api.examples().then((ex) => {
      setExamples(ex);
      if (ex[0]) setSql(ex[0].sql);
    });
    api.schemas().then(setSchemas);
  }, []);

  const run = async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await api.runSql(sql);
      setRows(res.rows);
    } catch (e: any) {
      setError(String(e.message ?? e));
      setRows([]);
    } finally {
      setRunning(false);
    }
  };

  const cols = rows[0] ? Object.keys(rows[0]) : [];

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-white/60 hover:text-coral-400 mb-6">
        <ArrowLeft className="h-4 w-4" /> Home
      </Link>

      <header className="mb-8">
        <h1 className="text-3xl font-semibold">SQL Orchestrator</h1>
        <p className="text-white/60 mt-1">
          One query. All sources. Zomato + Swiggy + Ola + Uber + Urban Company unified at query time —
          this is what no single-tool app can do.
        </p>
      </header>

      <div className="grid md:grid-cols-[260px_1fr] gap-5">
        <aside className="space-y-5">
          <div className="card p-4">
            <div className="text-xs font-semibold tracking-widest text-white/50 mb-3">EXAMPLES</div>
            <div className="space-y-1.5">
              {examples.map((e) => (
                <button
                  key={e.name}
                  onClick={() => setSql(e.sql)}
                  className="text-left text-sm text-white/80 hover:text-coral-400 block w-full"
                >
                  · {e.name}
                </button>
              ))}
            </div>
          </div>

          <div className="card p-4">
            <div className="text-xs font-semibold tracking-widest text-white/50 mb-3">TABLES</div>
            <div className="space-y-3">
              {schemas.map((t) => (
                <details key={t.name}>
                  <summary className="text-sm font-mono text-coral-400 cursor-pointer">
                    {t.name}
                  </summary>
                  <div className="mt-1 ml-3 text-xs font-mono text-white/50 space-y-0.5">
                    {t.columns.map((c: any) => (
                      <div key={c.name}>
                        {c.name}{" "}
                        <span className="text-white/30">{c.type}</span>
                      </div>
                    ))}
                  </div>
                </details>
              ))}
            </div>
          </div>
        </aside>

        <section>
          <div className="card p-4 mb-4">
            <textarea
              value={sql}
              onChange={(e) => setSql(e.target.value)}
              spellCheck={false}
              className="w-full h-56 bg-ink-900 rounded-lg border border-white/10 font-mono text-sm p-3 text-coral-100"
            />
            <div className="flex items-center justify-between mt-3">
              <div className="text-xs text-white/40">
                Read-only · runs against unified <code>income_ledger</code> view + native tables
              </div>
              <button
                onClick={run}
                disabled={running}
                className="inline-flex items-center gap-2 rounded-lg bg-coral-600 hover:bg-coral-500 px-4 py-2 text-sm font-medium disabled:opacity-50"
              >
                <Play className="h-4 w-4" />
                {running ? "Running…" : "Run query"}
              </button>
            </div>
          </div>

          <div className="card p-4">
            <div className="flex items-center gap-2 mb-3">
              <Database className="h-4 w-4 text-coral-400" />
              <div className="text-sm font-medium">
                Results {rows.length > 0 && <span className="text-white/40">· {rows.length} row{rows.length === 1 ? "" : "s"}</span>}
              </div>
            </div>
            {error ? (
              <div className="text-sm font-mono text-red-400 whitespace-pre-wrap">{error}</div>
            ) : rows.length === 0 ? (
              <div className="text-sm text-white/40">Run a query to see results.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-white/50 border-b border-white/10">
                      {cols.map((c) => (
                        <th key={c} className="py-2 pr-4 font-medium">{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r, i) => (
                      <tr key={i} className="border-b border-white/5 hover:bg-ink-700/40">
                        {cols.map((c) => (
                          <td key={c} className="py-2 pr-4 font-mono text-white/80">
                            {formatCell(r[c])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

function formatCell(v: any): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toFixed(2);
  return String(v);
}

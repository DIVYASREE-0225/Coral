"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Play, Database } from "lucide-react";
import { api } from "@/lib/api";

export default function SqlPlayground() {
  const [examples, setExamples] = useState<{ name: string; sql: string }[]>([]);
  const [schemas, setSchemas] = useState<any[]>([]);
  const [sql, setSql] = useState("");
  const [rows, setRows] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    api
      .examples()
      .then((ex) => {
        setExamples(ex || []);
        if (ex?.length) setSql(ex[0].sql);
      })
      .catch(() => setExamples([]));

    api.schemas().then(setSchemas).catch(() => setSchemas([]));
  }, []);

  const run = async () => {
    setRunning(true);
    setError(null);

    try {
      const res = await api.runSql(sql);
      setRows(res.rows || []);
    } catch (e: any) {
      setError(e.message || "Query failed");
      setRows([]);
    } finally {
      setRunning(false);
    }
  };

  const cols = rows?.[0] ? Object.keys(rows[0]) : [];

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <Link href="/" className="flex items-center gap-2 text-white/60 mb-6">
        <ArrowLeft className="h-4 w-4" /> Home
      </Link>

      <h1 className="text-3xl font-bold mb-6">SQL Orchestrator</h1>

      <div className="grid md:grid-cols-[260px_1fr] gap-6">
        <aside className="space-y-4">
          <div>
            <h2 className="text-sm text-white/50 mb-2">Examples</h2>
            {examples.map((e, i) => (
              <button
                key={i}
                onClick={() => setSql(e.sql)}
                className="block text-left text-sm text-coral-400 mb-1"
              >
                {e.name}
              </button>
            ))}
          </div>

          <div>
            <h2 className="text-sm text-white/50 mb-2">Tables</h2>
            {schemas.map((t, i) => (
              <details key={i}>
                <summary className="text-coral-400">{t.name}</summary>
                <div className="text-xs ml-3 text-white/60">
                  {t.columns?.map((c: any, j: number) => (
                    <div key={j}>
                      {c.name} ({c.type})
                    </div>
                  ))}
                </div>
              </details>
            ))}
          </div>
        </aside>

        <section>
          <textarea
            value={sql}
            onChange={(e) => setSql(e.target.value)}
            className="w-full h-52 bg-black border p-3 font-mono text-sm"
          />

          <button
            onClick={run}
            disabled={running}
            className="mt-3 bg-coral-600 px-4 py-2 rounded"
          >
            <Play className="inline h-4 w-4 mr-1" />
            {running ? "Running..." : "Run"}
          </button>

          <div className="mt-6">
            <div className="flex items-center gap-2 mb-2">
              <Database className="h-4 w-4" />
              Results
            </div>

            {error ? (
              <p className="text-red-400">{error}</p>
            ) : rows.length === 0 ? (
              <p className="text-white/40">No results</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr>
                    {cols.map((c) => (
                      <th key={c} className="text-left p-2">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => (
                    <tr key={i}>
                      {cols.map((c) => (
                        <td key={c} className="p-2">
                          {String(r[c])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
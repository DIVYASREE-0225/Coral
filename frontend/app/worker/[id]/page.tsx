
"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  ArrowLeft,
  Download,
  FileCheck2,
  Sparkles,
} from "lucide-react";

import { api, fmtINR } from "@/lib/api";

const PLATFORM_COLORS: Record<string, string> = {
  Zomato: "#ef4444",
  Swiggy: "#f97316",
  Ola: "#eab308",
  Uber: "#22c55e",
  UrbanCompany: "#a855f7",
};

export default function WorkerDashboard({
  params,
}: {
  params: { id: string };
}) {
  const [data, setData] = useState<any>(null);

  const [error, setError] = useState<string | null>(null);

  const [certPath, setCertPath] = useState<string | null>(null);

  const [generating, setGenerating] = useState(false);

  const [voice, setVoice] = useState<{
    q: string;
    lang: string;
    resp?: string;
  }>({
    q: "naa last month earnings enti?",
    lang: "te",
  });

  useEffect(() => {
    api
      .worker(params.id)
      .then((res) => {
        console.log("Worker Data:", res);
        setData(res);
      })
      .catch((e) => {
        console.error(e);
        setError(String(e));
      });
  }, [params.id]);

  const monthly = useMemo(() => {
    if (!data?.ingestion?.by_month) return [];

    const map = new Map<string, any>();

    for (const r of data.ingestion.by_month) {
      const key = r.month;

      if (!map.has(key)) {
        map.set(key, { month: key });
      }

      map.get(key)[r.platform] = Number(r.earnings);
    }

    return Array.from(map.values()).sort((a: any, b: any) =>
      a.month.localeCompare(b.month)
    );
  }, [data]);

  const platforms = useMemo(() => {
    const set = new Set<string>();

    monthly.forEach((m: any) => {
      Object.keys(m).forEach((k) => {
        if (k !== "month") {
          set.add(k);
        }
      });
    });

    return Array.from(set);
  }, [monthly]);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <Loading />;
  }

  const profile = data?.profile ?? {};

  const summary = data?.ingestion?.summary ?? {
    gross_annual: 0,
    total_payouts: 0,
    platforms: 0,
  };

  const credit = data?.credit ?? {
    score: 0,
    band: "N/A",
    verdict: "No data",
  };

  const itr = data?.tax?.itr4_prefill ?? {
    fy: "2025-26",
    gross_receipts: 0,
    presumed_income: 0,
    total_tax_liability: 0,
    tds_already_deducted: 0,
    tax_payable: 0,
    refund_due: 0,
    advance_tax_schedule: [],
  };

  const generateCertificate = async () => {
    try {
      setGenerating(true);

      const res = await api.certificate(params.id);

      console.log("Certificate:", res);

      setCertPath(res.certificate_filename);
    } catch (err) {
      console.error(err);
      alert("Certificate generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const askVoice = async () => {
    try {
      const res = await api.voice(
        params.id,
        voice.q,
        voice.lang
      );

      setVoice({
        ...voice,
        resp: res.response,
      });
    } catch (err) {
      console.error(err);

      setVoice({
        ...voice,
        resp: "Voice service unavailable",
      });
    }
  };

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">

      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-white/60 hover:text-coral-400 mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        All workers
      </Link>

      {/* HEADER */}

      <header className="mb-8">
        <div className="flex items-baseline justify-between flex-wrap gap-2">

          <div>
            <h1 className="text-3xl font-semibold">
              {profile?.name || "Unknown Worker"}
            </h1>

            <p className="text-white/60 mt-1">
              {profile?.city} · {profile?.language} · PAN {profile?.pan}
            </p>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {String(profile?.platforms || "")
              .split(",")
              .filter(Boolean)
              .map((p) => (
                <span
                  key={p}
                  className="chip bg-coral-900/40 text-coral-400 capitalize px-3 py-1 rounded"
                >
                  {p}
                </span>
              ))}
          </div>

        </div>
      </header>

      {/* STATS */}

      <section className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">

        <Stat
          label="Gross Annual"
          value={fmtINR(Number(summary.gross_annual || 0))}
        />

        <Stat
          label="Avg / Month"
          value={fmtINR(
            Number(summary.gross_annual || 0) /
              Math.max(monthly.length, 1)
          )}
        />

        <Stat
          label="Platforms"
          value={String(summary.platforms || 0)}
        />

        <Stat
          label="Payouts"
          value={String(summary.total_payouts || 0)}
        />

      </section>

      {/* CHART */}

      <section className="card p-5 mb-8 rounded-xl border border-white/10">

        <div className="flex items-center justify-between mb-4">
          <h2 className="font-medium">
            Unified Income Ledger
          </h2>

          <span className="text-xs text-white/40">
            via Coral SQL
          </span>
        </div>

        <div className="h-72">

          <ResponsiveContainer width="100%" height="100%">

            <BarChart data={monthly}>

              <CartesianGrid stroke="rgba(255,255,255,0.06)" />

              <XAxis
                dataKey="month"
                stroke="rgba(255,255,255,0.5)"
                fontSize={11}
              />

              <YAxis
                stroke="rgba(255,255,255,0.5)"
                fontSize={11}
              />

              <Tooltip
                formatter={(v: any) =>
                  fmtINR(Number(v))
                }
              />

              <Legend />

              {platforms.map((p) => (
                <Bar
                  key={p}
                  dataKey={p}
                  stackId="a"
                  fill={
                    PLATFORM_COLORS[p] || "#14b8a6"
                  }
                />
              ))}

            </BarChart>

          </ResponsiveContainer>

        </div>

      </section>

      {/* TAX + CREDIT */}

      <section className="grid md:grid-cols-2 gap-4 mb-8">

        {/* TAX */}

        <div className="card p-5 rounded-xl border border-white/10">

          <div className="flex items-center justify-between mb-3">
            <h2 className="font-medium">
              ITR-4 Pre-fill
            </h2>

            <span className="text-emerald-400 text-sm">
              Ready
            </span>
          </div>

          <dl className="space-y-2 text-sm">

            <Row
              k="Financial Year"
              v={itr.fy}
            />

            <Row
              k="Gross Receipts"
              v={fmtINR(itr.gross_receipts)}
            />

            <Row
              k="Presumed Income (6%)"
              v={fmtINR(itr.presumed_income)}
            />

            <Row
              k="Tax + 4% Cess"
              v={fmtINR(itr.total_tax_liability)}
            />

            <Row
              k="TDS Already Deducted"
              v={fmtINR(itr.tds_already_deducted)}
            />

            <Row
              k="Tax Payable"
              v={fmtINR(itr.tax_payable)}
              highlight
            />

          </dl>

        </div>

        {/* CREDIT */}

        <div className="card p-5 rounded-xl border border-white/10">

          <h2 className="font-medium mb-4">
            Credit Score
          </h2>

          <div className="text-5xl font-semibold text-coral-400">
            {credit.score}
          </div>

          <div className="text-sm text-white/60 mt-2">
            {credit.band} · {credit.verdict}
          </div>

        </div>

      </section>

      {/* CERTIFICATE */}

      <section className="card p-5 mb-8 rounded-xl border border-white/10">

        <div className="flex items-center justify-between mb-3">

          <h2 className="font-medium">
            Digital Income Certificate
          </h2>

          <span className="text-xs text-white/40">
            Bank-grade
          </span>

        </div>

        <div className="flex flex-wrap gap-3">

          <button
            onClick={generateCertificate}
            disabled={generating}
            className="inline-flex items-center gap-2 rounded-lg bg-coral-600 hover:bg-coral-500 disabled:opacity-50 px-4 py-2 text-sm font-medium transition"
          >
            <FileCheck2 className="h-4 w-4" />

            {generating
              ? "Generating..."
              : "Generate Certificate"}
          </button>

          {certPath && (
            <a
              href={`http://127.0.0.1:8000/certificate/file/${certPath}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-lg border border-coral-600/40 px-4 py-2 text-sm"
            >
              <Download className="h-4 w-4" />
              Download PDF
            </a>
          )}

        </div>

      </section>

      {/* VOICE */}

      <section className="card p-5 rounded-xl border border-white/10">

        <div className="flex items-center justify-between mb-3">

          <h2 className="font-medium">
            Multilingual Voice Agent
          </h2>

          <span className="text-xs text-coral-400">
            WhatsApp Style
          </span>

        </div>

        <div className="flex flex-col md:flex-row gap-2">

          <select
            value={voice.lang}
            onChange={(e) =>
              setVoice({
                ...voice,
                lang: e.target.value,
              })
            }
            className="rounded-lg bg-black border border-white/10 px-3 py-2"
          >
            <option value="en">English</option>
            <option value="te">Telugu</option>
            <option value="hi">Hindi</option>
            <option value="ta">Tamil</option>
            <option value="kn">Kannada</option>
          </select>

          <input
            value={voice.q}
            onChange={(e) =>
              setVoice({
                ...voice,
                q: e.target.value,
              })
            }
            className="flex-1 rounded-lg bg-black border border-white/10 px-3 py-2"
          />

          <button
            onClick={askVoice}
            className="inline-flex items-center gap-2 rounded-lg bg-coral-600 hover:bg-coral-500 px-4 py-2"
          >
            <Sparkles className="h-4 w-4" />
            Ask
          </button>

        </div>

        {voice.resp && (
          <div className="mt-4 rounded-lg border border-coral-700/40 bg-coral-900/20 p-4 text-sm">
            {voice.resp}
          </div>
        )}

      </section>

    </main>
  );
}

function Stat({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="card p-4 rounded-xl border border-white/10">
      <div className="text-xs text-white/50">
        {label}
      </div>

      <div className="text-xl font-semibold mt-1">
        {value}
      </div>
    </div>
  );
}

function Row({
  k,
  v,
  highlight,
}: {
  k: string;
  v: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex justify-between">
      <dt className="text-white/60">{k}</dt>

      <dd
        className={
          highlight
            ? "font-semibold text-coral-400"
            : "font-mono"
        }
      >
        {v}
      </dd>
    </div>
  );
}

function Loading() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-20 text-white/50">
      Loading worker data...
    </main>
  );
}

function ErrorState({
  message,
}: {
  message: string;
}) {
  return (
    <main className="mx-auto max-w-6xl px-6 py-20">
      <div className="font-medium text-red-400">
        Error
      </div>

      <div className="text-white/60 mt-2">
        {message}
      </div>
    </main>
  );
}


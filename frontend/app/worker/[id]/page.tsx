"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
} from "recharts";

import { ArrowLeft, Download, FileCheck2, Sparkles } from "lucide-react";
import { api, fmtINR } from "@/lib/api";

const PLATFORM_COLORS: Record<string, string> = {
  Zomato: "#ef4444",
  Swiggy: "#f97316",
  Ola: "#eab308",
  Uber: "#22c55e",
  UrbanCompany: "#a855f7",
};

export default function WorkerDashboard({ params }: { params: { id: string } }) {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [certPath, setCertPath] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  const [voice, setVoice] = useState({
    q: "naa last month earnings enti?",
    lang: "te",
    resp: "",
  });

  // ✅ FIX: safe fetch
  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.worker(params.id);
        setData(res);
      } catch (e: any) {
        setError(e.message || "Failed to load worker");
      }
    };

    load();
  }, [params.id]);

  // =========================
  // DATA TRANSFORMATION SAFE
  // =========================
  const monthly = useMemo(() => {
    if (!data?.ingestion?.by_month) return [];

    const map = new Map<string, any>();

    for (const r of data.ingestion.by_month) {
      const key = r.month;

      if (!map.has(key)) {
        map.set(key, { month: key });
      }

      map.get(key)[r.platform] = Number(r.earnings || 0);
    }

    return Array.from(map.values()).sort((a: any, b: any) =>
      a.month.localeCompare(b.month)
    );
  }, [data]);

  const platforms = useMemo(() => {
    const set = new Set<string>();
    monthly.forEach((m: any) => {
      Object.keys(m).forEach((k) => {
        if (k !== "month") set.add(k);
      });
    });
    return Array.from(set);
  }, [monthly]);

  // =========================
  // LOADING / ERROR STATES
  // =========================
  if (error) {
    return (
      <main className="p-10 text-red-400">
        Error: {error}
      </main>
    );
  }

  if (!data) {
    return (
      <main className="p-10 text-gray-400">
        Loading worker data...
      </main>
    );
  }

  const profile = data?.profile || {};
  const summary = data?.ingestion?.summary || {};
  const credit = data?.credit || {};
  const itr = data?.tax?.itr4_prefill || {};

  // =========================
  // API ACTIONS
  // =========================
  const generateCertificate = async () => {
    try {
      setGenerating(true);
      const res = await api.certificate(params.id);
      setCertPath(res?.certificate_filename || null);
    } catch {
      alert("Certificate generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const askVoice = async () => {
    try {
      const res = await api.voice(params.id, voice.q, voice.lang);
      setVoice((v) => ({ ...v, resp: res?.response || "" }));
    } catch {
      setVoice((v) => ({ ...v, resp: "Voice service unavailable" }));
    }
  };

  // =========================
  // UI
  // =========================
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">

      <Link href="/" className="text-sm text-gray-400 flex items-center gap-2 mb-6">
        <ArrowLeft size={16} />
        Back
      </Link>

      <h1 className="text-3xl font-bold">
        {profile.name || "Unknown Worker"}
      </h1>

      <p className="text-gray-400 mb-6">
        {profile.city} · {profile.language} · PAN {profile.pan}
      </p>

      {/* STATS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Stat label="Gross Annual" value={fmtINR(summary.gross_annual || 0)} />
        <Stat label="Platforms" value={summary.platforms || 0} />
        <Stat label="Payouts" value={summary.total_payouts || 0} />
        <Stat
          label="Avg / Month"
          value={fmtINR((summary.gross_annual || 0) / Math.max(monthly.length, 1))}
        />
      </div>

      {/* CHART */}
      <div className="h-72 mb-10">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={monthly}>
            <CartesianGrid />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            {platforms.map((p) => (
              <Bar
                key={p}
                dataKey={p}
                fill={PLATFORM_COLORS[p] || "#8884d8"}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* TAX */}
      <div className="mb-10">
        <h2 className="font-semibold mb-3">ITR-4</h2>

        <div className="space-y-2 text-sm">
          <div>Gross: {fmtINR(itr.gross_receipts || 0)}</div>
          <div>Tax: {fmtINR(itr.total_tax_liability || 0)}</div>
          <div className="text-green-500">
            Payable: {fmtINR(itr.tax_payable || 0)}
          </div>
        </div>
      </div>

      {/* CERTIFICATE */}
      <div className="mb-10">
        <button
          onClick={generateCertificate}
          disabled={generating}
          className="bg-blue-600 px-4 py-2 rounded"
        >
          {generating ? "Generating..." : "Generate Certificate"}
        </button>

        {certPath && (
          <a
            className="ml-4 text-blue-400 underline"
            href={`${process.env.NEXT_PUBLIC_API_BASE}/certificate/file/${certPath}`}
            target="_blank"
          >
            Download PDF
          </a>
        )}
      </div>

      {/* VOICE */}
      <div>
        <select
          value={voice.lang}
          onChange={(e) =>
            setVoice({ ...voice, lang: e.target.value })
          }
        >
          <option value="en">English</option>
          <option value="te">Telugu</option>
          <option value="hi">Hindi</option>
        </select>

        <input
          value={voice.q}
          onChange={(e) =>
            setVoice({ ...voice, q: e.target.value })
          }
        />

        <button onClick={askVoice}>Ask</button>

        {voice.resp && <p>{voice.resp}</p>}
      </div>

    </main>
  );
}

// =========================
// SMALL COMPONENT
// =========================
function Stat({ label, value }: any) {
  return (
    <div className="p-3 border rounded">
      <div className="text-gray-400 text-sm">{label}</div>
      <div className="font-bold">{value}</div>
    </div>
  );
}
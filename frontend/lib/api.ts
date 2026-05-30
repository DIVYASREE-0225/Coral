// Base API URL (PRODUCTION SAFE)
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

// Generic request handler
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`${res.status} - ${errorText}`);
  }

  return res.json() as Promise<T>;
}

/* ========================
   TYPES
======================== */

export type Worker = {
  worker_id: string;
  name: string;
  city: string;
  language: string;
  phone: string;
  pan: string;
  platforms: string;
};

/* ========================
   API METHODS
======================== */

export const api = {
  // Workers
  workers: () => request<Worker[]>("/workers"),
  worker: (id: string) => request<any>(`/worker/${id}`),

  // Income / Tax
  itr: (id: string) => request<any>(`/itr/${id}`),
  credit: (id: string) => request<any>(`/credit/${id}`),

  // Data ingestion
  ingestion: (id: string) => request<any>(`/ingestion/${id}`),

  // Certificate
  certificate: (id: string) =>
    request<any>(`/certificate/${id}`, {
      method: "POST",
    }),

  // Voice agent
  voice: (worker_id: string, question: string, lang: string) =>
    request<any>("/voice", {
      method: "POST",
      body: JSON.stringify({ worker_id, question, lang }),
    }),

  // SQL engine
  schemas: () => request<any[]>("/sql/schemas"),
  examples: () =>
    request<{ name: string; sql: string }[]>("/sql/examples"),

  runSql: (sql: string) =>
    request<{ rows: any[]; row_count: number }>("/sql/query", {
      method: "POST",
      body: JSON.stringify({ sql }),
    }),
};

/* ========================
   FORMATTER
======================== */

export const fmtINR = (n: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(n || 0);
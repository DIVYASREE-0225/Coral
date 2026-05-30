const DEFAULT_API =
  process.env.NEXT_PUBLIC_API_BASE || "https://coral-6j14.onrender.com";

export const API_BASE = DEFAULT_API;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "API Error");
  }

  return res.json() as Promise<T>;
}

export type Worker = {
  worker_id: string;
  name: string;
  city: string;
  language: string;
  phone: string;
  pan: string;
  platforms: string;
};

export const api = {
  workers: () => request<Worker[]>("/workers"),
  worker: (id: string) => request<any>(`/worker/${id}`),
  itr: (id: string) => request<any>(`/itr/${id}`),
  credit: (id: string) => request<any>(`/credit/${id}`),
  ingestion: (id: string) => request<any>(`/ingestion/${id}`),

  certificate: (id: string) =>
    request<any>(`/certificate/${id}`, {
      method: "POST",
    }),

  voice: (worker_id: string, question: string, lang: string) =>
    request<any>("/voice", {
      method: "POST",
      body: JSON.stringify({ worker_id, question, lang }),
    }),

  schemas: () => request<any[]>("/sql/schemas"),
  examples: () => request<any[]>("/sql/examples"),

  runSql: (sql: string) =>
    request<any>("/sql/query", {
      method: "POST",
      body: JSON.stringify({ sql }),
    }),
};

export const fmtINR = (n: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(n || 0);
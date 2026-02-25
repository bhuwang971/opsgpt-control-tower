import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";

type HealthPayload = {
  status: string;
  service: string;
  versions: Record<string, string>;
};

function LandingPage() {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-semibold text-slate-900">OpsGPT Control Tower</h1>
      <p className="mt-3 max-w-2xl text-slate-600">
        Local-first operations intelligence platform for airline, weather, and trade analytics.
      </p>
    </section>
  );
}

function HealthPage() {
  const [data, setData] = useState<HealthPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
    fetch(`${baseUrl}/health`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`health request failed (${response.status})`);
        }
        return (await response.json()) as HealthPayload;
      })
      .then((payload) => setData(payload))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "unknown error");
      });
  }, []);

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold text-slate-900">Backend Health</h2>
      {!data && !error && <p className="mt-3 text-slate-600">Loading...</p>}
      {error && <p className="mt-3 text-red-700">Error: {error}</p>}
      {data && (
        <pre className="mt-4 overflow-auto rounded-lg bg-slate-900 p-4 text-sm text-slate-100">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </section>
  );
}

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-50 to-slate-100">
      <div className="mx-auto max-w-5xl px-6 py-8">
        <nav className="mb-6 flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <Link to="/" className="font-medium text-brand-700 hover:text-brand-500">
            Home
          </Link>
          <Link to="/health" className="font-medium text-brand-700 hover:text-brand-500">
            Health
          </Link>
        </nav>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/health" element={<HealthPage />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;

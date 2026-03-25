import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";

type HealthPayload = {
  status: string;
  service: string;
  versions: Record<string, string>;
};

type KpiCard = {
  id: string;
  label: string;
  value: number;
  display: string;
  delta: number;
  status: "healthy" | "watch" | "risk";
};

type TrendPoint = {
  date: string;
  total_flights: number;
  on_time_rate: number;
  p50_arr_delay_minutes: number;
  p90_arr_delay_minutes: number;
  cancellation_rate: number;
  severe_delay_rate: number;
  reliability_score: number;
  volatility_index: number;
};

type CarrierRow = {
  carrier_code: string;
  total_flights: number;
  on_time_rate: number;
  avg_arr_delay_minutes: number;
  severe_delay_rate: number;
  cancellation_rate: number;
};

type TradeRow = {
  period: string;
  reporter_iso: string;
  trade_flow: string;
  shipment_count: number;
  total_trade_value_usd: number;
  avg_net_weight_kg: number;
};

type AlertRow = {
  severity: "high" | "medium" | "info";
  title: string;
  detail: string;
};

type ForecastPoint = {
  date: string;
  projected_on_time_rate: number;
  projected_reliability_score: number;
};

type SavedView = {
  id: string;
  name: string;
  description: string;
};

type ExportRow = {
  dataset: string;
  path: string;
};

type AssistantPayload = {
  mode: "retrieval" | "sql";
  answer: string;
  citations: Array<{ source: string; excerpt: string }>;
  sql: {
    statement: string;
    columns: string[];
    rows: Array<Array<string | number>>;
    audit_id: string;
  } | null;
};

type MemoPayload = {
  objective: string;
  diagnosis: {
    headline: string;
    latest_on_time_rate: string;
    latest_reliability_score: string;
    worst_carrier: string;
    worst_carrier_delay_minutes: number;
  };
  recommendations: Array<{ title: string; detail: string; tradeoff: string }>;
  memo_markdown: string;
  trace: Array<{ step: string; status: string; detail: string }>;
  evaluation: {
    score: number;
    max_score: number;
    rubric: Array<{ criterion: string; passed: boolean }>;
  };
};

type StreamStatusPayload = {
  generated_at: string;
  source: string;
  live_kpis: {
    on_time_rate: number;
    reliability_score: number;
    p90_arr_delay_minutes: number;
    volatility_index: number;
  };
  active_alerts: Array<{ severity: string; title: string; detail: string }>;
  event_log: Array<{ event_id: string; event_type: string; severity: string }>;
};

type ExperimentPayload = {
  toggle_name: string;
  title: string;
  description: string;
  design: {
    primary_metric: string;
    guardrail_metrics: string[];
    alpha: number;
    power_target: number;
    estimated_mde: number;
  };
  sample_size: number;
  window: {
    start_date: string;
    end_date: string;
  };
  variant_counts: {
    control: number;
    treatment: number;
  };
  primary_metric_result: {
    metric: string;
    control_rate: number;
    treatment_rate: number;
    absolute_lift: number;
    relative_lift: number;
    z_score: number;
    p_value: number;
    ci_95: [number, number];
    significant: boolean;
  };
  guardrails: Array<{
    metric: string;
    control_value: number;
    treatment_value: number;
    difference: number;
    status: string;
  }>;
  sequential_checks: Array<{
    checkpoint: string;
    sample_size: number;
    absolute_lift: number;
    p_value: number;
    decision: string;
  }>;
  segment_breakdown: Array<{
    carrier_code: string;
    control_rate: number;
    treatment_rate: number;
    absolute_lift: number;
    sample_size: number;
  }>;
  recommendation: {
    decision: string;
    rationale: string;
  };
};

type PortfolioPayload = {
  toggle_name: string;
  reward_metric: string;
  logged_rows: number;
  policies: Array<{
    policy_name: string;
    description: string;
    match_rate: number;
    estimated_reward_ips: number;
    estimated_reward_dm: number;
    estimated_reward_dr: number;
  }>;
  champion_policy: {
    policy_name: string;
    description: string;
    match_rate: number;
    estimated_reward_ips: number;
    estimated_reward_dm: number;
    estimated_reward_dr: number;
  };
  showcase_notes: string[];
};

type InterviewDashboardPayload = {
  generated_at: string;
  ml: {
    classification: Record<string, number>;
    regression: Record<string, number>;
    forecasting: Record<string, number>;
    model_cards: string;
  };
  rag: {
    summary: Record<string, number>;
    benchmark_cases: Array<{
      case_id: string;
      category: string;
      passed: boolean;
      hallucination_flag: boolean;
      citation_count: number;
    }>;
  };
  experimentation: {
    primary_metric: {
      absolute_lift: number;
      p_value: number;
      significant: boolean;
    };
    recommendation: {
      decision: string;
      rationale: string;
    };
    ope_champion: {
      policy_name: string;
      estimated_reward_dr: number;
    };
  };
  responsible_ai: {
    dataset_datasheet: {
      record_count: number;
      train_count: number;
      test_count: number;
      time_split: string;
      intended_use: string;
      limitations: string[];
    };
    fairness_slices: Array<{
      carrier_code: string;
      count: number;
      actual_positive_rate: number;
      predicted_positive_rate: number;
      mae: number;
      baseline_mae: number;
      mae_delta_vs_baseline: number;
    }>;
    privacy_governance_checklist: Array<{ control: string; status: string }>;
  };
  testing: {
    fast_backend_suite: { command: string; test_count: number };
    pipeline_backend_suite: { command: string; test_count: number };
    frontend_suite: { commands: string[] };
  };
  platform: {
    observability: string[];
    workflow_runtime: string;
    peft_sandbox: {
      recommended_for: string;
      status: string;
      experiments: Array<{
        name: string;
        method: string;
        rank: number;
        alpha: number;
      }>;
    };
  };
};

type ControlTowerPayload = {
  generated_at: string;
  kpis: KpiCard[];
  daily_trend: TrendPoint[];
  carrier_drilldown: CarrierRow[];
  trade_lens: TradeRow[];
  alerts: AlertRow[];
  forecast: {
    horizon_days: number;
    projected_on_time_rate: ForecastPoint[];
    baseline_metrics: {
      classification_pr_auc_proxy: number;
      regression_mae: number;
      forecast_rmse: number;
    };
  };
  saved_views: SavedView[];
  exports: ExportRow[];
};

function apiBaseUrl() {
  return import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
}

function formatDelta(value: number, suffix = "") {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}${suffix}`;
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function DashboardPage() {
  const [data, setData] = useState<ControlTowerPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<string>("network_watch");

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${apiBaseUrl()}/api/control-tower/overview`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`control tower request failed (${response.status})`);
        }
        return (await response.json()) as ControlTowerPayload;
      })
      .then((payload) => {
        setData(payload);
        setActiveView(payload.saved_views[0]?.id ?? "network_watch");
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        setError(err instanceof Error ? err.message : "unknown error");
      });
    return () => controller.abort();
  }, []);

  if (error) {
    return (
      <section className="panel-grid">
        <article className="panel panel-critical">
          <p className="eyebrow">Control Tower</p>
          <h1 className="panel-title">Dashboard unavailable</h1>
          <p className="panel-copy">{error}</p>
        </article>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="panel-grid">
        <article className="panel panel-loading">
          <p className="eyebrow">Control Tower</p>
          <h1 className="panel-title">Loading operations picture</h1>
          <p className="panel-copy">Hydrating KPIs, trend summaries, carrier drilldowns, and forecast baselines.</p>
        </article>
      </section>
    );
  }

  const activeLabel = data.saved_views.find((view) => view.id === activeView)?.name ?? "Network Watch";
  const topCarrier = data.carrier_drilldown[0];
  const riskCarrier = data.carrier_drilldown[data.carrier_drilldown.length - 1];

  return (
    <div className="dashboard-shell">
      <section className="hero-band">
        <div>
          <p className="eyebrow">OpsGPT Control Tower</p>
          <h1 className="hero-title">Operational clarity with KPIs, drift signals, and baseline forecasts in one room.</h1>
          <p className="hero-copy">
            The dashboard below is driven by the local DuckDB warehouse and the Cycle 3-4 analytical stack. Use the saved
            views to pivot between network reliability, carrier benchmarking, and trade context.
          </p>
        </div>
        <div className="hero-meta">
          <div className="meta-chip">
            <span className="meta-label">Active View</span>
            <strong>{activeLabel}</strong>
          </div>
          <div className="meta-chip">
            <span className="meta-label">Last Refresh</span>
            <strong>{new Date(data.generated_at).toLocaleString()}</strong>
          </div>
        </div>
      </section>

      <section className="view-strip">
        {data.saved_views.map((view) => (
          <button
            key={view.id}
            type="button"
            className={`view-pill ${activeView === view.id ? "view-pill-active" : ""}`}
            onClick={() => setActiveView(view.id)}
          >
            <span>{view.name}</span>
            <small>{view.description}</small>
          </button>
        ))}
      </section>

      <section className="kpi-grid">
        {data.kpis.map((kpi) => (
          <article key={kpi.id} className={`kpi-card kpi-${kpi.status}`}>
            <p className="kpi-label">{kpi.label}</p>
            <div className="kpi-row">
              <h2>{kpi.display}</h2>
              <span>{formatDelta(kpi.delta, kpi.id === "reliability_score" ? "" : "")}</span>
            </div>
          </article>
        ))}
      </section>

      <section className="panel-grid">
        <article className="panel panel-trend">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Trend Board</p>
              <h2 className="panel-title">Daily operations pulse</h2>
            </div>
            <p className="panel-copy">Track reliability, delay tail risk, and cancellation pressure over the observed window.</p>
          </div>
          <div className="trend-table">
            {data.daily_trend.map((point) => (
              <div key={point.date} className="trend-row">
                <div>
                  <strong>{point.date}</strong>
                  <span>{point.total_flights} flights</span>
                </div>
                <div>
                  <strong>{formatPercent(point.on_time_rate)}</strong>
                  <span>On-time</span>
                </div>
                <div>
                  <strong>{point.p90_arr_delay_minutes.toFixed(1)}m</strong>
                  <span>P90 delay</span>
                </div>
                <div>
                  <strong>{point.volatility_index.toFixed(1)}</strong>
                  <span>Volatility</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel panel-alerts">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Alert Feed</p>
              <h2 className="panel-title">What needs attention now</h2>
            </div>
          </div>
          <div className="alert-stack">
            {data.alerts.map((alert) => (
              <div key={`${alert.severity}-${alert.title}`} className={`alert-card alert-${alert.severity}`}>
                <strong>{alert.title}</strong>
                <p>{alert.detail}</p>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="panel-grid">
        <article className="panel panel-carriers">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Carrier Drilldown</p>
              <h2 className="panel-title">Who is absorbing the disruption load</h2>
            </div>
            <p className="panel-copy">
              Leader: {topCarrier.carrier_code} at {formatPercent(topCarrier.on_time_rate)} on-time. Risk tail:{" "}
              {riskCarrier.carrier_code} with {riskCarrier.avg_arr_delay_minutes.toFixed(1)} minute average delay.
            </p>
          </div>
          <div className="carrier-list">
            {data.carrier_drilldown.map((carrier) => (
              <div key={carrier.carrier_code} className="carrier-row">
                <div>
                  <strong>{carrier.carrier_code}</strong>
                  <span>{carrier.total_flights} flights</span>
                </div>
                <div>
                  <strong>{formatPercent(carrier.on_time_rate)}</strong>
                  <span>On-time</span>
                </div>
                <div>
                  <strong>{carrier.avg_arr_delay_minutes.toFixed(1)}m</strong>
                  <span>Avg delay</span>
                </div>
                <div>
                  <strong>{formatPercent(carrier.severe_delay_rate)}</strong>
                  <span>Severe delay</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel panel-forecast">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Baseline Forecast</p>
              <h2 className="panel-title">Five-day watchlist</h2>
            </div>
            <p className="panel-copy">
              Backed by the Cycle 4 benchmark pipeline. This is a planning baseline, not a production forecast.
            </p>
          </div>
          <div className="forecast-grid">
            {data.forecast.projected_on_time_rate.map((point) => (
              <div key={point.date} className="forecast-card">
                <span>{point.date}</span>
                <strong>{formatPercent(point.projected_on_time_rate)}</strong>
                <small>{point.projected_reliability_score.toFixed(1)} reliability</small>
              </div>
            ))}
          </div>
          <div className="metric-mini-grid">
            <div className="metric-mini">
              <span>Classification</span>
              <strong>{data.forecast.baseline_metrics.classification_pr_auc_proxy.toFixed(2)} PR-AUC proxy</strong>
            </div>
            <div className="metric-mini">
              <span>Regression</span>
              <strong>{data.forecast.baseline_metrics.regression_mae.toFixed(2)} MAE</strong>
            </div>
            <div className="metric-mini">
              <span>Forecast</span>
              <strong>{data.forecast.baseline_metrics.forecast_rmse.toFixed(2)} RMSE</strong>
            </div>
          </div>
        </article>
      </section>

      <section className="panel-grid">
        <article className="panel panel-trade">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Trade Context</p>
              <h2 className="panel-title">Monthly trade lens</h2>
            </div>
            <p className="panel-copy">Use trade volume context when explaining operational shifts in portfolio demos or interview walkthroughs.</p>
          </div>
          <div className="trade-list">
            {data.trade_lens.map((row) => (
              <div key={`${row.period}-${row.trade_flow}`} className="trade-row">
                <div>
                  <strong>{row.period}</strong>
                  <span>{row.trade_flow}</span>
                </div>
                <div>
                  <strong>${Math.round(row.total_trade_value_usd).toLocaleString()}</strong>
                  <span>Trade value</span>
                </div>
                <div>
                  <strong>{row.shipment_count}</strong>
                  <span>Shipments</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel panel-exports">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Exports</p>
              <h2 className="panel-title">Downloadable views</h2>
            </div>
          </div>
          <div className="export-list">
            {data.exports.map((item) => (
              <a
                key={item.dataset}
                className="export-link"
                href={`${apiBaseUrl()}${item.path}`}
                target="_blank"
                rel="noreferrer"
              >
                <strong>{item.dataset}</strong>
                <span>CSV export</span>
              </a>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}

function HealthPage() {
  const [data, setData] = useState<HealthPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${apiBaseUrl()}/health`)
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
    <section className="panel-grid">
      <article className="panel">
        <p className="eyebrow">Backend Health</p>
        <h2 className="panel-title">Service envelope</h2>
        {!data && !error && <p className="panel-copy">Loading service health...</p>}
        {error && <p className="panel-copy">{error}</p>}
        {data && (
          <pre className="health-block">
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </article>
    </section>
  );
}

function AssistantPage() {
  const [question, setQuestion] = useState("Show the latest daily reliability and on-time trend");
  const [data, setData] = useState<AssistantPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function submitQuestion() {
    setLoading(true);
    setError(null);
    fetch(`${apiBaseUrl()}/api/assistant/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`assistant request failed (${response.status})`);
        }
        return (await response.json()) as AssistantPayload;
      })
      .then((payload) => setData(payload))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "unknown error");
      })
      .finally(() => setLoading(false));
  }

  return (
    <div className="dashboard-shell">
      <section className="hero-band">
        <div>
          <p className="eyebrow">Grounded Assistant</p>
          <h1 className="hero-title">Ask for cited answers or safe SQL without leaving the control room.</h1>
          <p className="hero-copy">
            Questions that match allowlisted analytics intents run through guarded SQL with audit logging. Everything else
            falls back to local document retrieval with citations.
          </p>
        </div>
        <div className="hero-meta">
          <div className="meta-chip">
            <span className="meta-label">Prompt Policy</span>
            <strong>Cite-or-drop retrieval</strong>
          </div>
          <div className="meta-chip">
            <span className="meta-label">SQL Safety</span>
            <strong>Allowlist + LIMIT guardrails</strong>
          </div>
        </div>
      </section>

      <section className="panel-grid">
        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Query</p>
              <h2 className="panel-title">Ask the system</h2>
            </div>
          </div>
          <textarea
            className="assistant-input"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={5}
          />
          <div className="assistant-actions">
            <button type="button" className="action-button" onClick={submitQuestion} disabled={loading}>
              {loading ? "Running..." : "Run grounded query"}
            </button>
          </div>
          {error && <p className="panel-copy">{error}</p>}
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Answer</p>
              <h2 className="panel-title">Response</h2>
            </div>
          </div>
          {!data && <p className="panel-copy">Run a question to see cited retrieval output or guarded SQL results.</p>}
          {data && (
            <div className="assistant-result">
              <div className="meta-chip">
                <span className="meta-label">Mode</span>
                <strong>{data.mode}</strong>
              </div>
              <p>{data.answer}</p>
              {data.sql && (
                <div className="sql-block">
                  <code>{data.sql.statement}</code>
                  <small>Audit ID: {data.sql.audit_id}</small>
                </div>
              )}
            </div>
          )}
        </article>
      </section>

      {data && (
        <section className="panel-grid">
          <article className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Citations</p>
                <h2 className="panel-title">Grounding evidence</h2>
              </div>
            </div>
            <div className="alert-stack">
              {data.citations.map((citation) => (
                <div key={`${citation.source}-${citation.excerpt}`} className="alert-card alert-info">
                  <strong>{citation.source}</strong>
                  <p>{citation.excerpt}</p>
                </div>
              ))}
            </div>
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">SQL Result</p>
                <h2 className="panel-title">Tabular preview</h2>
              </div>
            </div>
            {!data.sql && <p className="panel-copy">No SQL was generated for this question.</p>}
            {data.sql && (
              <div className="table-wrap">
                <table className="result-table">
                  <thead>
                    <tr>
                      {data.sql.columns.map((column) => (
                        <th key={column}>{column}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.sql.rows.map((row, index) => (
                      <tr key={`${index}-${row[0]}`}>
                        {row.map((value, cellIndex) => (
                          <td key={`${index}-${cellIndex}`}>{String(value)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </article>
        </section>
      )}
    </div>
  );
}

function MemoPage() {
  const [objective, setObjective] = useState("Stabilize reliability before the next reporting cycle");
  const [data, setData] = useState<MemoPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function generateMemo() {
    setLoading(true);
    setError(null);
    fetch(`${apiBaseUrl()}/api/agent/decision-memo`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ objective }),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`decision memo request failed (${response.status})`);
        }
        return (await response.json()) as MemoPayload;
      })
      .then((payload) => setData(payload))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "unknown error");
      })
      .finally(() => setLoading(false));
  }

  return (
    <div className="dashboard-shell">
      <section className="hero-band">
        <div>
          <p className="eyebrow">Decision Workflow</p>
          <h1 className="hero-title">Generate an evidence-backed memo with stable traces and a visible rubric.</h1>
          <p className="hero-copy">
            This workflow calls the control tower and grounded assistant layers as tools, then assembles recommendations
            and trade-offs into a reproducible memo.
          </p>
        </div>
        <div className="hero-meta">
          <div className="meta-chip">
            <span className="meta-label">Flow</span>
            <strong>diagnose → evidence → recommend → memo</strong>
          </div>
          <div className="meta-chip">
            <span className="meta-label">Eval Harness</span>
            <strong>Memo rubric scoring</strong>
          </div>
        </div>
      </section>

      <section className="panel-grid">
        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Objective</p>
              <h2 className="panel-title">Decision memo prompt</h2>
            </div>
          </div>
          <textarea
            className="assistant-input"
            value={objective}
            onChange={(event) => setObjective(event.target.value)}
            rows={4}
          />
          <div className="assistant-actions">
            <button type="button" className="action-button" onClick={generateMemo} disabled={loading}>
              {loading ? "Generating..." : "Generate memo"}
            </button>
          </div>
          {error && <p className="panel-copy">{error}</p>}
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Summary</p>
              <h2 className="panel-title">Workflow result</h2>
            </div>
          </div>
          {!data && <p className="panel-copy">Run the workflow to see diagnosis, memo score, and trace details.</p>}
          {data && (
            <div className="assistant-result">
              <div className="metric-mini-grid">
                <div className="metric-mini">
                  <span>Diagnosis</span>
                  <strong>{data.diagnosis.headline}</strong>
                </div>
                <div className="metric-mini">
                  <span>Rubric Score</span>
                  <strong>
                    {data.evaluation.score}/{data.evaluation.max_score}
                  </strong>
                </div>
                <div className="metric-mini">
                  <span>Worst Carrier</span>
                  <strong>{data.diagnosis.worst_carrier}</strong>
                </div>
              </div>
              <pre className="health-block">{data.memo_markdown}</pre>
            </div>
          )}
        </article>
      </section>

      {data && (
        <section className="panel-grid">
          <article className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Trace</p>
                <h2 className="panel-title">Workflow steps</h2>
              </div>
            </div>
            <div className="alert-stack">
              {data.trace.map((step) => (
                <div key={step.step} className="alert-card alert-info">
                  <strong>{step.step}</strong>
                  <p>
                    {step.status}: {step.detail}
                  </p>
                </div>
              ))}
            </div>
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Rubric</p>
                <h2 className="panel-title">Memo quality checks</h2>
              </div>
            </div>
            <div className="alert-stack">
              {data.evaluation.rubric.map((item) => (
                <div key={item.criterion} className={`alert-card ${item.passed ? "alert-info" : "alert-medium"}`}>
                  <strong>{item.criterion}</strong>
                  <p>{item.passed ? "passed" : "needs attention"}</p>
                </div>
              ))}
            </div>
          </article>
        </section>
      )}
    </div>
  );
}

function LiveOpsPage() {
  const [data, setData] = useState<StreamStatusPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function loadStatus() {
    fetch(`${apiBaseUrl()}/api/stream/status`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`stream status request failed (${response.status})`);
        }
        return (await response.json()) as StreamStatusPayload;
      })
      .then((payload) => setData(payload))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "unknown error");
      });
  }

  function replayEvents() {
    setLoading(true);
    setError(null);
    fetch(`${apiBaseUrl()}/api/stream/replay`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`stream replay request failed (${response.status})`);
        }
        return (await response.json()) as StreamStatusPayload;
      })
      .then((payload) => setData(payload))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "unknown error");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadStatus();
  }, []);

  return (
    <div className="dashboard-shell">
      <section className="hero-band">
        <div>
          <p className="eyebrow">Live Ops Replay</p>
          <h1 className="hero-title">Replay near-real-time events and watch the alert surface react.</h1>
          <p className="hero-copy">
            This page drives the Cycle 8 local replay engine. It updates live KPIs, records replay metrics for Prometheus,
            and feeds Grafana-ready dashboard panels.
          </p>
        </div>
        <div className="hero-meta">
          <div className="meta-chip">
            <span className="meta-label">Replay Source</span>
            <strong>{data?.source ?? "loading"}</strong>
          </div>
          <div className="meta-chip">
            <span className="meta-label">Active Alerts</span>
            <strong>{data?.active_alerts.length ?? 0}</strong>
          </div>
        </div>
      </section>

      <section className="panel-grid">
        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Controls</p>
              <h2 className="panel-title">Replay events</h2>
            </div>
          </div>
          <div className="assistant-actions">
            <button type="button" className="action-button" onClick={replayEvents} disabled={loading}>
              {loading ? "Replaying..." : "Replay sample events"}
            </button>
          </div>
          {error && <p className="panel-copy">{error}</p>}
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Live KPIs</p>
              <h2 className="panel-title">Current replayed status</h2>
            </div>
          </div>
          {!data && <p className="panel-copy">Loading live replay status...</p>}
          {data && (
            <div className="metric-mini-grid">
              <div className="metric-mini">
                <span>On-time</span>
                <strong>{formatPercent(data.live_kpis.on_time_rate)}</strong>
              </div>
              <div className="metric-mini">
                <span>Reliability</span>
                <strong>{data.live_kpis.reliability_score.toFixed(1)}</strong>
              </div>
              <div className="metric-mini">
                <span>P90 Delay</span>
                <strong>{data.live_kpis.p90_arr_delay_minutes.toFixed(1)}m</strong>
              </div>
            </div>
          )}
        </article>
      </section>

      {data && (
        <section className="panel-grid">
          <article className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Alerts</p>
                <h2 className="panel-title">Triggered conditions</h2>
              </div>
            </div>
            <div className="alert-stack">
              {data.active_alerts.map((alert) => (
                <div key={`${alert.severity}-${alert.title}`} className={`alert-card alert-${alert.severity}`}>
                  <strong>{alert.title}</strong>
                  <p>{alert.detail}</p>
                </div>
              ))}
            </div>
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Replay Log</p>
                <h2 className="panel-title">Event stream</h2>
              </div>
            </div>
            <div className="alert-stack">
              {data.event_log.map((event) => (
                <div key={event.event_id} className="alert-card alert-info">
                  <strong>{event.event_type}</strong>
                  <p>
                    {event.event_id} · severity {event.severity}
                  </p>
                </div>
              ))}
            </div>
          </article>
        </section>
      )}
    </div>
  );
}

function ExperimentsPage() {
  const [data, setData] = useState<ExperimentPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function loadExperiment(showLoading: boolean) {
    if (showLoading) {
      setLoading(true);
      setError(null);
    }
    fetch(`${apiBaseUrl()}/api/experiments/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ toggle_name: "adaptive_turnaround_buffers" }),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`experiment analysis request failed (${response.status})`);
        }
        return (await response.json()) as ExperimentPayload;
      })
      .then((payload) => setData(payload))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "unknown error");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetch(`${apiBaseUrl()}/api/experiments/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ toggle_name: "adaptive_turnaround_buffers" }),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`experiment analysis request failed (${response.status})`);
        }
        return (await response.json()) as ExperimentPayload;
      })
      .then((payload) => setData(payload))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "unknown error");
      });
  }, []);

  return (
    <div className="dashboard-shell">
      <section className="hero-band">
        <div>
          <p className="eyebrow">Experimentation Module</p>
          <h1 className="hero-title">Read A/B outcomes, guardrails, and rollout posture from one analysis surface.</h1>
          <p className="hero-copy">
            Cycle 9 uses the local warehouse to build a deterministic experiment frame for a config toggle, then reports
            primary lift, guardrail behavior, and checkpoint-level sequential reads.
          </p>
        </div>
        <div className="hero-meta">
          <div className="meta-chip">
            <span className="meta-label">Default Toggle</span>
            <strong>{data?.toggle_name ?? "adaptive_turnaround_buffers"}</strong>
          </div>
          <div className="meta-chip">
            <span className="meta-label">Sample Size</span>
            <strong>{data?.sample_size ?? 0}</strong>
          </div>
        </div>
      </section>

      <section className="panel-grid">
        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Controls</p>
              <h2 className="panel-title">Run analysis</h2>
            </div>
          </div>
          <div className="assistant-actions">
            <button
              type="button"
              className="action-button"
              onClick={() => loadExperiment(true)}
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Re-run experiment analysis"}
            </button>
          </div>
          {error && <p className="panel-copy">{error}</p>}
          {data && (
            <div className="metric-mini-grid">
              <div className="metric-mini">
                <span>Window</span>
                <strong>
                  {data.window.start_date} to {data.window.end_date}
                </strong>
              </div>
              <div className="metric-mini">
                <span>Alpha / Power</span>
                <strong>
                  {data.design.alpha} / {data.design.power_target}
                </strong>
              </div>
              <div className="metric-mini">
                <span>Estimated MDE</span>
                <strong>{formatPercent(data.design.estimated_mde)}</strong>
              </div>
            </div>
          )}
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Primary Result</p>
              <h2 className="panel-title">On-time lift</h2>
            </div>
          </div>
          {!data && <p className="panel-copy">Loading experiment analysis...</p>}
          {data && (
            <div className="metric-mini-grid">
              <div className="metric-mini">
                <span>Control</span>
                <strong>{formatPercent(data.primary_metric_result.control_rate)}</strong>
              </div>
              <div className="metric-mini">
                <span>Treatment</span>
                <strong>{formatPercent(data.primary_metric_result.treatment_rate)}</strong>
              </div>
              <div className="metric-mini">
                <span>Absolute Lift</span>
                <strong>{formatPercent(data.primary_metric_result.absolute_lift)}</strong>
              </div>
              <div className="metric-mini">
                <span>p-value</span>
                <strong>{data.primary_metric_result.p_value.toFixed(4)}</strong>
              </div>
            </div>
          )}
        </article>
      </section>

      {data && (
        <>
          <section className="panel-grid">
            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">Guardrails</p>
                  <h2 className="panel-title">Secondary metrics</h2>
                </div>
              </div>
              <div className="alert-stack">
                {data.guardrails.map((item) => (
                  <div key={item.metric} className={`alert-card ${item.status === "pass" ? "alert-info" : "alert-medium"}`}>
                    <strong>{item.metric}</strong>
                    <p>
                      control {item.control_value.toFixed(4)} · treatment {item.treatment_value.toFixed(4)} · diff{" "}
                      {item.difference.toFixed(4)}
                    </p>
                  </div>
                ))}
              </div>
            </article>

            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">Recommendation</p>
                  <h2 className="panel-title">Rollout posture</h2>
                </div>
              </div>
              <div className="assistant-result">
                <div className="meta-chip">
                  <span className="meta-label">Decision</span>
                  <strong>{data.recommendation.decision}</strong>
                </div>
                <p>{data.recommendation.rationale}</p>
                <p className="panel-copy">
                  Variant split: control {data.variant_counts.control}, treatment {data.variant_counts.treatment}
                </p>
              </div>
            </article>
          </section>

          <section className="panel-grid">
            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">Sequential Checks</p>
                  <h2 className="panel-title">Checkpoint readout</h2>
                </div>
              </div>
              <div className="trend-table">
                {data.sequential_checks.map((check) => (
                  <div key={check.checkpoint} className="trend-row">
                    <div>
                      <strong>{check.checkpoint}</strong>
                      <span>{check.sample_size} rows</span>
                    </div>
                    <div>
                      <strong>{formatPercent(check.absolute_lift)}</strong>
                      <span>Lift</span>
                    </div>
                    <div>
                      <strong>{check.p_value.toFixed(4)}</strong>
                      <span>p-value</span>
                    </div>
                    <div>
                      <strong>{check.decision}</strong>
                      <span>Status</span>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">Carrier Slices</p>
                  <h2 className="panel-title">Segment view</h2>
                </div>
              </div>
              <div className="carrier-list">
                {data.segment_breakdown.slice(0, 5).map((segment) => (
                  <div key={segment.carrier_code} className="carrier-row">
                    <div>
                      <strong>{segment.carrier_code}</strong>
                      <span>{segment.sample_size} rows</span>
                    </div>
                    <div>
                      <strong>{formatPercent(segment.control_rate)}</strong>
                      <span>Control</span>
                    </div>
                    <div>
                      <strong>{formatPercent(segment.treatment_rate)}</strong>
                      <span>Treatment</span>
                    </div>
                    <div>
                      <strong>{formatPercent(segment.absolute_lift)}</strong>
                      <span>Lift</span>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </section>
        </>
      )}
    </div>
  );
}

function ShowcasePage() {
  const [data, setData] = useState<PortfolioPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function loadShowcase(showLoading: boolean) {
    if (showLoading) {
      setLoading(true);
      setError(null);
    }
    fetch(`${apiBaseUrl()}/api/portfolio/ope`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ toggle_name: "adaptive_turnaround_buffers" }),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`portfolio request failed (${response.status})`);
        }
        return (await response.json()) as PortfolioPayload;
      })
      .then((payload) => setData(payload))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "unknown error");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetch(`${apiBaseUrl()}/api/portfolio/ope`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ toggle_name: "adaptive_turnaround_buffers" }),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`portfolio request failed (${response.status})`);
        }
        return (await response.json()) as PortfolioPayload;
      })
      .then((payload) => setData(payload))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "unknown error");
      });
  }, []);

  return (
    <div className="dashboard-shell">
      <section className="hero-band">
        <div>
          <p className="eyebrow">Portfolio Showcase</p>
          <h1 className="hero-title">Close the loop with offline policy evaluation and a clear demo narrative.</h1>
          <p className="hero-copy">
            Cycle 10 adds a lightweight offline bandit layer on top of the experimentation frame so we can compare rollout
            policies before shipping them. This is the differentiator pass for interviews and demos.
          </p>
        </div>
        <div className="hero-meta">
          <div className="meta-chip">
            <span className="meta-label">Reward</span>
            <strong>{data?.reward_metric ?? "on_time_reward"}</strong>
          </div>
          <div className="meta-chip">
            <span className="meta-label">Logged Rows</span>
            <strong>{data?.logged_rows ?? 0}</strong>
          </div>
        </div>
      </section>

      <section className="panel-grid">
        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Controls</p>
              <h2 className="panel-title">Re-run portfolio analysis</h2>
            </div>
          </div>
          <div className="assistant-actions">
            <button type="button" className="action-button" onClick={() => loadShowcase(true)} disabled={loading}>
              {loading ? "Refreshing..." : "Refresh OPE analysis"}
            </button>
          </div>
          {error && <p className="panel-copy">{error}</p>}
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Champion Policy</p>
              <h2 className="panel-title">Best DR estimate</h2>
            </div>
          </div>
          {!data && <p className="panel-copy">Loading portfolio analysis...</p>}
          {data && (
            <div className="assistant-result">
              <div className="meta-chip">
                <span className="meta-label">Policy</span>
                <strong>{data.champion_policy.policy_name}</strong>
              </div>
              <p>{data.champion_policy.description}</p>
              <div className="metric-mini-grid">
                <div className="metric-mini">
                  <span>IPS</span>
                  <strong>{data.champion_policy.estimated_reward_ips.toFixed(4)}</strong>
                </div>
                <div className="metric-mini">
                  <span>DM</span>
                  <strong>{data.champion_policy.estimated_reward_dm.toFixed(4)}</strong>
                </div>
                <div className="metric-mini">
                  <span>DR</span>
                  <strong>{data.champion_policy.estimated_reward_dr.toFixed(4)}</strong>
                </div>
              </div>
            </div>
          )}
        </article>
      </section>

      {data && (
        <>
          <section className="panel-grid">
            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">Policy Table</p>
                  <h2 className="panel-title">Counterfactual estimates</h2>
                </div>
              </div>
              <div className="carrier-list">
                {data.policies.map((policy) => (
                  <div key={policy.policy_name} className="carrier-row">
                    <div>
                      <strong>{policy.policy_name}</strong>
                      <span>{policy.description}</span>
                    </div>
                    <div>
                      <strong>{policy.estimated_reward_ips.toFixed(4)}</strong>
                      <span>IPS</span>
                    </div>
                    <div>
                      <strong>{policy.estimated_reward_dm.toFixed(4)}</strong>
                      <span>DM</span>
                    </div>
                    <div>
                      <strong>{policy.estimated_reward_dr.toFixed(4)}</strong>
                      <span>DR</span>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">Showcase Notes</p>
                  <h2 className="panel-title">How to talk about it</h2>
                </div>
              </div>
              <div className="alert-stack">
                {data.showcase_notes.map((note) => (
                  <div key={note} className="alert-card alert-info">
                    <strong>Portfolio note</strong>
                    <p>{note}</p>
                  </div>
                ))}
              </div>
            </article>
          </section>
        </>
      )}
    </div>
  );
}

function InterviewDashboardPage() {
  const [data, setData] = useState<InterviewDashboardPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function loadDashboard(showLoading: boolean) {
    if (showLoading) {
      setLoading(true);
      setError(null);
    }
    fetch(`${apiBaseUrl()}/api/interview/dashboard`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`interview dashboard request failed (${response.status})`);
        }
        return (await response.json()) as InterviewDashboardPayload;
      })
      .then((payload) => setData(payload))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "unknown error");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetch(`${apiBaseUrl()}/api/interview/dashboard`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`interview dashboard request failed (${response.status})`);
        }
        return (await response.json()) as InterviewDashboardPayload;
      })
      .then((payload) => setData(payload))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "unknown error");
      });
  }, []);

  return (
    <div className="dashboard-shell">
      <section className="hero-band">
        <div>
          <p className="eyebrow">Interview Dashboard</p>
          <h1 className="hero-title">One place to show model quality, RAG safety, testing posture, and governance.</h1>
          <p className="hero-copy">
            This view aggregates the main interview-facing evidence: ML metrics, RAG evals, experiment/OPE outcomes,
            responsible-AI checks, and verification commands.
          </p>
        </div>
        <div className="hero-meta">
          <div className="meta-chip">
            <span className="meta-label">Workflow Runtime</span>
            <strong>{data?.platform.workflow_runtime ?? "loading"}</strong>
          </div>
          <div className="meta-chip">
            <span className="meta-label">Generated</span>
            <strong>{data ? new Date(data.generated_at).toLocaleString() : "loading"}</strong>
          </div>
        </div>
      </section>

      <section className="panel-grid">
        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Controls</p>
              <h2 className="panel-title">Refresh evidence</h2>
            </div>
          </div>
          <div className="assistant-actions">
            <button type="button" className="action-button" onClick={() => loadDashboard(true)} disabled={loading}>
              {loading ? "Refreshing..." : "Refresh dashboard"}
            </button>
          </div>
          {error && <p className="panel-copy">{error}</p>}
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Verification</p>
              <h2 className="panel-title">Test surfaces</h2>
            </div>
          </div>
          {!data && <p className="panel-copy">Loading interview dashboard...</p>}
          {data && (
            <div className="metric-mini-grid">
              <div className="metric-mini">
                <span>Fast Backend</span>
                <strong>{data.testing.fast_backend_suite.test_count} tests</strong>
              </div>
              <div className="metric-mini">
                <span>Pipeline Backend</span>
                <strong>{data.testing.pipeline_backend_suite.test_count} tests</strong>
              </div>
              <div className="metric-mini">
                <span>Frontend</span>
                <strong>{data.testing.frontend_suite.commands.length} commands</strong>
              </div>
            </div>
          )}
        </article>
      </section>

      {data && (
        <>
          <section className="panel-grid">
            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">ML Metrics</p>
                  <h2 className="panel-title">Accuracy and error baselines</h2>
                </div>
              </div>
              <div className="metric-mini-grid">
                <div className="metric-mini">
                  <span>Classification PR-AUC</span>
                  <strong>{data.ml.classification.pr_auc_proxy?.toFixed(3) ?? "n/a"}</strong>
                </div>
                <div className="metric-mini">
                  <span>Regression MAE</span>
                  <strong>{data.ml.regression.mae?.toFixed(3) ?? "n/a"}</strong>
                </div>
                <div className="metric-mini">
                  <span>Forecast RMSE</span>
                  <strong>{data.ml.forecasting.rmse?.toFixed(3) ?? "n/a"}</strong>
                </div>
              </div>
            </article>

            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">RAG Eval</p>
                  <h2 className="panel-title">Grounding and hallucination controls</h2>
                </div>
              </div>
              <div className="metric-mini-grid">
                <div className="metric-mini">
                  <span>Mode Accuracy</span>
                  <strong>{formatPercent(data.rag.summary.mode_accuracy ?? 0)}</strong>
                </div>
                <div className="metric-mini">
                  <span>Citation Coverage</span>
                  <strong>{formatPercent(data.rag.summary.citation_coverage ?? 0)}</strong>
                </div>
                <div className="metric-mini">
                  <span>Red-Team Pass</span>
                  <strong>{formatPercent(data.rag.summary.red_team_pass_rate ?? 0)}</strong>
                </div>
                <div className="metric-mini">
                  <span>Hallucination Proxy</span>
                  <strong>{formatPercent(data.rag.summary.hallucination_rate_proxy ?? 0)}</strong>
                </div>
              </div>
            </article>
          </section>

          <section className="panel-grid">
            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">RAG Cases</p>
                  <h2 className="panel-title">Benchmark and red-team cases</h2>
                </div>
              </div>
              <div className="alert-stack">
                {data.rag.benchmark_cases.map((item) => (
                  <div key={item.case_id} className={`alert-card ${item.passed ? "alert-info" : "alert-medium"}`}>
                    <strong>{item.case_id}</strong>
                    <p>
                      {item.category} - citations {item.citation_count} - hallucination flag{" "}
                      {item.hallucination_flag ? "on" : "off"}
                    </p>
                  </div>
                ))}
              </div>
            </article>

            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">Responsible AI</p>
                  <h2 className="panel-title">Datasheet, slices, governance</h2>
                </div>
              </div>
              <div className="metric-mini-grid">
                <div className="metric-mini">
                  <span>Dataset Rows</span>
                  <strong>{data.responsible_ai.dataset_datasheet.record_count}</strong>
                </div>
                <div className="metric-mini">
                  <span>Train/Test</span>
                  <strong>
                    {data.responsible_ai.dataset_datasheet.train_count}/{data.responsible_ai.dataset_datasheet.test_count}
                  </strong>
                </div>
                <div className="metric-mini">
                  <span>Time Split</span>
                  <strong>{data.responsible_ai.dataset_datasheet.time_split}</strong>
                </div>
              </div>
              <div className="alert-stack">
                {data.responsible_ai.privacy_governance_checklist.slice(0, 5).map((item) => (
                  <div key={item.control} className={`alert-card ${item.status === "implemented" ? "alert-info" : "alert-medium"}`}>
                    <strong>{item.control}</strong>
                    <p>{item.status}</p>
                  </div>
                ))}
              </div>
            </article>
          </section>

          <section className="panel-grid">
            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">Experimentation</p>
                  <h2 className="panel-title">Rollout evidence</h2>
                </div>
              </div>
              <div className="metric-mini-grid">
                <div className="metric-mini">
                  <span>Absolute Lift</span>
                  <strong>{formatPercent(data.experimentation.primary_metric.absolute_lift)}</strong>
                </div>
                <div className="metric-mini">
                  <span>p-value</span>
                  <strong>{data.experimentation.primary_metric.p_value.toFixed(4)}</strong>
                </div>
                <div className="metric-mini">
                  <span>OPE Champion</span>
                  <strong>{data.experimentation.ope_champion.policy_name}</strong>
                </div>
              </div>
              <p className="panel-copy">{data.experimentation.recommendation.rationale}</p>
            </article>

            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">Platform Depth</p>
                  <h2 className="panel-title">Monitoring and PEFT sandbox</h2>
                </div>
              </div>
              <div className="alert-stack">
                {data.platform.observability.map((item) => (
                  <div key={item} className="alert-card alert-info">
                    <strong>Observability</strong>
                    <p>{item}</p>
                  </div>
                ))}
                {data.platform.peft_sandbox.experiments.map((item) => (
                  <div key={item.name} className="alert-card alert-info">
                    <strong>{item.name}</strong>
                    <p>
                      {item.method} - rank {item.rank} - alpha {item.alpha}
                    </p>
                  </div>
                ))}
              </div>
            </article>
          </section>
        </>
      )}
    </div>
  );
}

function App() {
  return (
    <div className="app-frame">
      <div className="app-shell">
        <nav className="top-nav">
          <div>
            <p className="eyebrow">OpsGPT</p>
            <h1 className="nav-title">Control Tower</h1>
          </div>
          <div className="nav-links">
            <Link to="/">Dashboard</Link>
            <Link to="/assistant">Assistant</Link>
            <Link to="/memo">Memo</Link>
            <Link to="/live">Live Ops</Link>
            <Link to="/experiments">Experiments</Link>
            <Link to="/showcase">Showcase</Link>
            <Link to="/interview">Interview</Link>
            <Link to="/health">Health</Link>
          </div>
        </nav>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/assistant" element={<AssistantPage />} />
          <Route path="/memo" element={<MemoPage />} />
          <Route path="/live" element={<LiveOpsPage />} />
          <Route path="/experiments" element={<ExperimentsPage />} />
          <Route path="/showcase" element={<ShowcasePage />} />
          <Route path="/interview" element={<InterviewDashboardPage />} />
          <Route path="/health" element={<HealthPage />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;

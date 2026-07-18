import { useEffect, useState } from "react";
import { AlertTriangle, Bot, CheckCircle2, LoaderCircle, ShieldAlert, Sparkles } from "lucide-react";
import { Route, Routes, useLocation } from "react-router-dom";

import { Navigation } from "@/components/navigation";
import { ResultTable } from "@/components/result-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/input";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { askQuestion, fetchHealth, fetchHistory } from "@/lib/api";
import type { AskResponse, HealthResponse, HistoryItem, QueryMode } from "@/lib/types";

const starterPrompts = [
  "How many orders came from Mumbai last week?",
  "Which product category earns us the most revenue?",
  "What is the average order value for repeat customers?",
];

function App() {
  const location = useLocation();
  const [dark, setDark] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [question, setQuestion] = useState(starterPrompts[0]);
  const [mode, setMode] = useState<QueryMode>("trusted-llm");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const prefersDark = window.localStorage.getItem("talktodata-theme") === "dark";
    setDark(prefersDark);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    window.localStorage.setItem("talktodata-theme", dark ? "dark" : "light");
  }, [dark]);

  async function refresh() {
    try {
      const [healthPayload, historyPayload] = await Promise.all([fetchHealth(), fetchHistory()]);
      setHealth(healthPayload);
      setHistory(historyPayload);
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Unable to reach the backend.");
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const isDemo = params.get("demo") === "1";
    if (!isDemo || result || loading) {
      return;
    }

    setQuestion("Which product category earns us the most revenue?");
    setMode("trusted-llm");
    void (async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await askQuestion("Which product category earns us the most revenue?", "trusted-llm");
        setResult(response);
        await refresh();
      } catch (askError) {
        setError(askError instanceof Error ? askError.message : "The request failed.");
      } finally {
        setLoading(false);
      }
    })();
  }, [location.search, loading, result]);

  async function handleAsk() {
    setLoading(true);
    setError(null);
    try {
      const response = await askQuestion(question, mode);
      setResult(response);
      await refresh();
    } catch (askError) {
      setError(askError instanceof Error ? askError.message : "The request failed.");
    } finally {
      setLoading(false);
    }
  }

  const providerLabel = health?.provider?.name
    ? `${health.provider.name}${health.provider.model ? ` · ${health.provider.model}` : ""}`
    : "No provider detected";

  return (
    <div className="min-h-screen bg-sand bg-grid [background-size:28px_28px] text-ink transition dark:bg-slate-950 dark:text-white">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 rounded-[32px] border border-white/50 bg-gradient-to-br from-white via-white to-mist/80 p-6 shadow-panel dark:border-white/10 dark:from-slate-950 dark:via-slate-950 dark:to-slate-900">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-3">
              <Badge tone="warning" className="bg-signal/20 text-amber-900 dark:bg-signal/20 dark:text-signal">
                TalkToData
              </Badge>
              <div>
                <h1 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">
                  Ask your database in plain English.
                </h1>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
                  A guarded NL-to-SQL workspace for the MAIB case study. Compare rule-based translation, raw LLM output,
                  and production-style trust layers in one interface.
                </p>
              </div>
            </div>
            <div className="flex flex-col items-start gap-3 lg:items-end">
              <ThemeToggle dark={dark} onToggle={() => setDark((current) => !current)} />
              <Badge tone={health?.provider?.name ? "safe" : "blocked"}>{providerLabel}</Badge>
            </div>
          </div>
          <div className="mt-6">
            <Navigation />
          </div>
        </header>

        <Routes>
          <Route
            path="/"
            element={
              <DashboardPage
                error={error}
                health={health}
                history={history}
                loading={loading}
                mode={mode}
                question={question}
                result={result}
                setMode={setMode}
                setQuestion={setQuestion}
                onAsk={() => void handleAsk()}
              />
            }
          />
          <Route path="/history" element={<HistoryPage history={history} />} />
          <Route path="/guardrails" element={<GuardrailsPage health={health} result={result} />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </div>
    </div>
  );
}

interface DashboardPageProps {
  error: string | null;
  health: HealthResponse | null;
  history: HistoryItem[];
  loading: boolean;
  mode: QueryMode;
  question: string;
  result: AskResponse | null;
  setMode: (mode: QueryMode) => void;
  setQuestion: (question: string) => void;
  onAsk: () => void;
}

function DashboardPage({
  error,
  health,
  history,
  loading,
  mode,
  question,
  result,
  setMode,
  setQuestion,
  onAsk,
}: DashboardPageProps) {
  return (
    <div className="grid gap-6 lg:grid-cols-[1.4fr_0.9fr]">
      <div className="space-y-6">
        <Card className="overflow-hidden">
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <CardTitle>Question Workspace</CardTitle>
                <CardDescription>Ask in business language, then verify the SQL before you trust the result.</CardDescription>
              </div>
              <Badge tone="neutral">{health?.database_ready ? "SQLite ready" : "Loading DB"}</Badge>
            </div>

            <Textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask a business question..."
            />

            <div className="flex flex-wrap gap-2">
              {(["trusted-llm", "llm", "rule-based"] as QueryMode[]).map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setMode(value)}
                  className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                    mode === value
                      ? "bg-ink text-white"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-900 dark:text-slate-200"
                  }`}
                >
                  {value === "trusted-llm" ? "Phase C · Guarded" : value === "llm" ? "Phase B · Raw LLM" : "Phase A · Rules"}
                </button>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Button size="lg" onClick={onAsk} disabled={loading || question.trim().length < 3} className="gap-2">
                {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                Ask
              </Button>
              {starterPrompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => setQuestion(prompt)}
                  className="rounded-full border border-slate-200 bg-white/75 px-3 py-2 text-xs font-medium text-slate-600 transition hover:bg-white dark:border-slate-800 dark:bg-slate-900/60 dark:text-slate-300"
                >
                  {prompt}
                </button>
              ))}
            </div>

            {error ? (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-100">
                {error}
              </div>
            ) : null}
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle>Answer</CardTitle>
              <CardDescription>The result is only trustworthy when the SQL and explanation also make sense.</CardDescription>
            </div>
            <StatusBadge status={result?.status ?? "IDLE"} />
          </div>

          <div className="mt-5 space-y-5">
            <section className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Explanation</p>
              <p className="text-sm leading-7 text-slate-700 dark:text-slate-200">
                {result?.explanation ?? "Run a question to see the generated explanation here."}
              </p>
            </section>

            <section className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Generated SQL</p>
              <pre className="overflow-x-auto rounded-2xl bg-ink px-4 py-4 font-mono text-sm text-mist">
                <code>{result?.sql ?? "-- SQL will appear here after you ask a question"}</code>
              </pre>
            </section>

            <section className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Execution Result</p>
              <ResultTable answer={result?.answer ?? null} />
            </section>

            <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-900 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100">
              <div className="flex items-start gap-3">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <p>{result?.trust_note ?? "Trust note: keep a human in the loop by reviewing the SQL before acting on the answer."}</p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div className="space-y-6">
        <Card>
          <div className="flex items-center gap-3">
            <ShieldAlert className="h-5 w-5 text-ember" />
            <div>
              <CardTitle>Guardrail Status</CardTitle>
              <CardDescription>See whether the latest query passed safety and schema checks.</CardDescription>
            </div>
          </div>

          <div className="mt-5 space-y-4 text-sm">
            <GuardrailRow
              label="Safety"
              value={result?.guardrails?.read_only ? "Read-only" : result?.guardrails ? "Blocked" : "Waiting"}
            />
            <GuardrailRow
              label="Validation"
              value={result?.guardrails?.sqlite_validation?.ok ? "Schema validated" : result?.guardrails?.reason ?? "Waiting"}
            />
            <GuardrailRow
              label="Keywords"
              value={result?.guardrails?.dangerous_keywords?.length ? result.guardrails.dangerous_keywords.join(", ") : "None"}
            />
            <GuardrailRow
              label="Tables"
              value={result?.guardrails?.table_validation?.referenced_tables?.join(", ") || "Not checked yet"}
            />
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3">
            <Bot className="h-5 w-5 text-mint" />
            <div>
              <CardTitle>Recent History</CardTitle>
              <CardDescription>The last few questions help compare which mode behaves best.</CardDescription>
            </div>
          </div>

          <div className="mt-5 space-y-3">
            {history.length ? (
              history.slice(0, 4).map((item) => (
                <div
                  key={item.id}
                  className="rounded-2xl border border-slate-200 bg-white/70 p-4 dark:border-slate-800 dark:bg-slate-950/60"
                >
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <p className="text-sm font-medium">{item.question}</p>
                    <StatusBadge status={item.status} />
                  </div>
                  <p className="line-clamp-2 font-mono text-xs text-slate-500 dark:text-slate-400">{item.sql ?? "No SQL generated"}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500 dark:text-slate-400">No history yet. Ask the first question to populate this timeline.</p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

function HistoryPage({ history }: { history: HistoryItem[] }) {
  return (
    <Card>
      <div className="flex items-center justify-between gap-4">
        <div>
          <CardTitle>Query History</CardTitle>
          <CardDescription>Every question, SQL translation, and execution outcome in one audit trail.</CardDescription>
        </div>
        <Badge tone="neutral">{history.length} stored queries</Badge>
      </div>

      <div className="mt-6 space-y-4">
        {history.length ? (
          history.map((item) => (
            <div key={item.id} className="rounded-[24px] border border-slate-200 bg-white/70 p-5 dark:border-slate-800 dark:bg-slate-950/60">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <p className="font-medium">{item.question}</p>
                <div className="flex items-center gap-2">
                  <Badge tone="neutral">{item.mode}</Badge>
                  <StatusBadge status={item.status} />
                </div>
              </div>
              <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">{item.explanation}</p>
              <pre className="mt-4 overflow-x-auto rounded-2xl bg-ink px-4 py-4 font-mono text-xs text-mist">
                <code>{item.sql ?? "-- No SQL generated"}</code>
              </pre>
            </div>
          ))
        ) : (
          <div className="rounded-[24px] border border-dashed border-slate-300 bg-white/60 p-10 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-400">
            Query history will appear here after the backend receives its first question.
          </div>
        )}
      </div>
    </Card>
  );
}

function GuardrailsPage({ health, result }: { health: HealthResponse | null; result: AskResponse | null }) {
  const checks = [
    {
      label: "Read-only enforcement",
      detail: "Only SELECT or WITH queries should execute.",
      status: result?.guardrails?.read_only ? "PASS" : result?.guardrails ? "FAIL" : "WAITING",
    },
    {
      label: "Dangerous keyword blocklist",
      detail: "DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, and REPLACE are blocked.",
      status: result?.guardrails?.dangerous_keywords?.length ? "BLOCKED" : result?.guardrails ? "PASS" : "WAITING",
    },
    {
      label: "Schema validation",
      detail: result?.guardrails?.sqlite_validation?.message ?? "The backend validates that referenced tables and columns exist.",
      status: result?.guardrails?.sqlite_validation?.ok ? "PASS" : result?.guardrails ? "CHECK" : "WAITING",
    },
  ];

  return (
    <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <Card>
        <div className="flex items-center justify-between gap-4">
          <div>
            <CardTitle>Policy Summary</CardTitle>
            <CardDescription>Guardrails are what turn an impressive demo into a trustworthy workflow.</CardDescription>
          </div>
          <Badge tone={health?.provider?.name ? "safe" : "warning"}>{health?.provider?.name ? "Provider online" : "Provider pending"}</Badge>
        </div>

        <div className="mt-6 space-y-4">
          {checks.map((check) => (
            <div key={check.label} className="rounded-2xl border border-slate-200 bg-white/70 p-4 dark:border-slate-800 dark:bg-slate-950/60">
              <div className="flex items-center justify-between gap-3">
                <p className="font-medium">{check.label}</p>
                <Badge
                  tone={
                    check.status === "PASS"
                      ? "safe"
                      : check.status === "BLOCKED" || check.status === "FAIL"
                        ? "blocked"
                        : "warning"
                  }
                >
                  {check.status}
                </Badge>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{check.detail}</p>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <CardTitle>Latest Validation Details</CardTitle>
        <CardDescription>These are the exact fields the backend returns for the most recent guarded query.</CardDescription>

        <div className="mt-6 space-y-4">
          {result?.guardrails ? (
            <>
              <GuardrailRow label="Overall status" value={result.guardrails.status} />
              <GuardrailRow label="Reason" value={result.guardrails.reason} />
              <GuardrailRow
                label="Known tables"
                value={result.guardrails.table_validation?.referenced_tables?.join(", ") || "None"}
              />
              <GuardrailRow
                label="Unknown tables"
                value={result.guardrails.table_validation?.unknown_tables?.join(", ") || "None"}
              />
              <GuardrailRow
                label="Unknown columns"
                value={result.guardrails.column_validation?.unknown_columns?.join(", ") || "None"}
              />
              <GuardrailRow label="SQLite check" value={result.guardrails.sqlite_validation?.message ?? "Not available"} />
            </>
          ) : (
            <div className="rounded-[24px] border border-dashed border-slate-300 bg-white/60 p-10 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-400">
              Run a guarded query from the main screen to inspect its validation payload here.
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

function AboutPage() {
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <Card className="lg:col-span-1">
        <Badge tone="warning">NL-to-SQL</Badge>
        <CardTitle className="mt-4">Why this case study matters</CardTitle>
        <CardDescription className="mt-3">
          TalkToData is a compact version of the modern enterprise analytics pattern: natural language in, SQL out, with
          verification before action.
        </CardDescription>
      </Card>

      <Card className="lg:col-span-1">
        <Badge tone="safe">Machine Translation</Badge>
        <CardTitle className="mt-4">The translation relationship</CardTitle>
        <CardDescription className="mt-3">
          English is the source language, SQL is the target language, and the database schema acts like the grammar that the
          translation must obey.
        </CardDescription>
      </Card>

      <Card className="lg:col-span-1">
        <Badge tone="blocked">Guardrails</Badge>
        <CardTitle className="mt-4">Why guardrails exist</CardTitle>
        <CardDescription className="mt-3">
          A fluent SQL query can still be unfaithful to the question. TalkToData blocks unsafe SQL, validates schema usage,
          and always exposes the query for human review.
        </CardDescription>
      </Card>

      <Card className="lg:col-span-3">
        <CardTitle>What the user should trust</CardTitle>
        <CardDescription className="mt-3">
          The system is designed to support decisions, not replace judgment. The user should trust the workflow only when the
          answer, SQL, and explanation all align with the business question.
        </CardDescription>
      </Card>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "OK" || status === "SAFE") {
    return (
      <Badge tone="safe">
        <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
        {status}
      </Badge>
    );
  }
  if (status === "BLOCKED" || status === "ERROR") {
    return (
      <Badge tone="blocked">
        <ShieldAlert className="mr-1 h-3.5 w-3.5" />
        {status}
      </Badge>
    );
  }
  return <Badge tone="warning">{status}</Badge>;
}

function GuardrailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 rounded-2xl border border-slate-200 bg-white/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">{label}</p>
      <p className="text-sm leading-6 text-slate-700 dark:text-slate-200">{value}</p>
    </div>
  );
}

export default App;

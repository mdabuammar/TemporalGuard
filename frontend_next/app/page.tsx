"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, Loader2 } from "lucide-react";
import { Hero } from "@/components/Hero";
import { QuestionPanel } from "@/components/QuestionPanel";
import { ResultCard } from "@/components/ResultCard";
import { SettingsSummary } from "@/components/SettingsSummary";
import { Sidebar } from "@/components/Sidebar";
import { TabsPanel } from "@/components/TabsPanel";
import { analyzeTemporalGuard, getDefaultApiUrl } from "@/lib/api";
import { createDemoOutput } from "@/lib/demoData";
import type { AnalyzeRequest, DashboardState, TemporalGuardOutput } from "@/types/temporalguard";

const defaultState: DashboardState = {
  mode: "Demo Mode",
  llmProvider: "mock",
  searchProvider: "none",
  modelName: "openrouter/free",
  useOwnAnswer: true,
  apiUrl: getDefaultApiUrl(),
  reportType: "dashboard",
  maxSources: 3,
  showRawJson: false,
  showDebugDetails: false
};

export default function Page() {
  const [state, setState] = useState<DashboardState>(defaultState);
  const [question, setQuestion] = useState("What is the latest Python version?");
  const [answer, setAnswer] = useState("Python 3.11 is the latest version of Python.");
  const [output, setOutput] = useState<TemporalGuardOutput | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const payload = useMemo<AnalyzeRequest>(
    () => ({
      question,
      base_answer: state.useOwnAnswer ? answer || null : null,
      llm_provider: state.llmProvider,
      model_name: state.modelName || null,
      search_provider: state.searchProvider,
      report_type: state.reportType
    }),
    [answer, question, state.llmProvider, state.modelName, state.reportType, state.searchProvider, state.useOwnAnswer]
  );

  function updateState(next: Partial<DashboardState>) {
    setState((current) => ({ ...current, ...next }));
  }

  async function runAnalysis() {
    setError("");
    if (!question.trim()) {
      setError("Enter a question before running TemporalGuard.");
      return;
    }
    if (state.useOwnAnswer && !answer.trim()) {
      setError("Provide an answer, or turn off Use my own answer so the selected model can generate one.");
      return;
    }

    setIsLoading(true);
    try {
      if (state.mode === "Demo Mode") {
        await new Promise((resolve) => setTimeout(resolve, 420));
        setOutput(createDemoOutput(question, state.useOwnAnswer ? answer : undefined));
      } else {
        setOutput(await analyzeTemporalGuard(state.apiUrl, payload));
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "TemporalGuard could not complete the request.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="app-frame">
      <Sidebar
        state={state}
        onChange={updateState}
        onRun={runAnalysis}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen((value) => !value)}
        isLoading={isLoading}
      />

      <main className="min-w-0 flex-1 px-4 py-5 lg:px-8 lg:py-7">
        <div className="mx-auto flex max-w-[1180px] flex-col gap-6">
          <Hero />
          <SettingsSummary state={state} />
          <QuestionPanel
            question={question}
            answer={answer}
            state={state}
            isLoading={isLoading}
            onQuestionChange={setQuestion}
            onAnswerChange={setAnswer}
            onStateChange={updateState}
            onRun={runAnalysis}
          />

          {isLoading ? (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-3 rounded-[24px] border border-warm-border bg-white/70 p-5 text-warm-muted shadow-card"
            >
              <Loader2 className="animate-spin text-sage-700" size={20} aria-hidden="true" />
              TemporalGuard is checking the answer...
            </motion.div>
          ) : null}

          {error ? (
            <div className="flex gap-3 rounded-[24px] border border-red-200 bg-red-50 p-5 text-red-800 shadow-card">
              <AlertTriangle className="mt-1 shrink-0" size={19} aria-hidden="true" />
              <div>
                <h2 className="font-semibold">Request could not be completed</h2>
                <p className="mt-1 text-sm leading-6">{error}</p>
              </div>
            </div>
          ) : null}

          {output ? (
            <>
              <ResultCard output={output} />
              <TabsPanel output={output} state={state} />
            </>
          ) : (
            <section className="rounded-[28px] border border-dashed border-warm-border bg-white/42 p-8 text-center text-warm-muted">
              <h2 className="text-xl font-semibold text-warm-text">Ready to verify</h2>
              <p className="mt-2">Ask a question, choose an answer source, and run TemporalGuard.</p>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}

"use client";

import { motion } from "framer-motion";
import { AlertCircle, SendHorizonal } from "lucide-react";
import type { DashboardState } from "@/types/temporalguard";
import { demoQuestions } from "@/lib/demoData";

interface QuestionPanelProps {
  question: string;
  answer: string;
  state: DashboardState;
  isLoading: boolean;
  onQuestionChange: (value: string) => void;
  onAnswerChange: (value: string) => void;
  onStateChange: (next: Partial<DashboardState>) => void;
  onRun: () => void;
}

export function QuestionPanel({
  question,
  answer,
  state,
  isLoading,
  onQuestionChange,
  onAnswerChange,
  onStateChange,
  onRun
}: QuestionPanelProps) {
  return (
    <motion.section
      id="verify"
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.08, duration: 0.35 }}
      className="glass-card rounded-[28px] p-5 md:p-7"
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-[-0.02em] text-warm-text">Ask a question</h2>
          <p className="mt-1 text-sm text-warm-muted">Run TemporalGuard on time-sensitive answers, policies, releases, and factual claims.</p>
        </div>
        <select
          className="control max-w-full md:max-w-[260px]"
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          aria-label="Choose a demo question"
        >
          <option value={question}>{question || "Choose a demo question"}</option>
          {demoQuestions.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-6 space-y-5">
        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-warm-text">Question</span>
          <textarea
            className="control min-h-[132px] resize-y text-base leading-7"
            value={question}
            onChange={(event) => onQuestionChange(event.target.value)}
            placeholder="Ask a question that may depend on time, policy, releases, or recent evidence."
          />
        </label>

        <label className="flex cursor-pointer items-center justify-between rounded-[22px] border border-warm-border bg-white/65 px-4 py-3">
          <span>
            <span className="block font-semibold text-warm-text">Use my own answer</span>
            <span className="text-sm text-warm-muted">Provide a base answer for TemporalGuard to verify.</span>
          </span>
          <input
            type="checkbox"
            className="h-5 w-5 accent-sage-700"
            checked={state.useOwnAnswer}
            onChange={(event) => onStateChange({ useOwnAnswer: event.target.checked })}
          />
        </label>

        {state.useOwnAnswer ? (
          <label className="block">
            <span className="mb-2 block text-sm font-semibold text-warm-text">Your answer</span>
            <textarea
              className="control min-h-[122px] resize-y leading-7"
              value={answer}
              onChange={(event) => onAnswerChange(event.target.value)}
              placeholder="Paste or write the answer that TemporalGuard should check."
            />
          </label>
        ) : null}

        <div className="grid gap-3 md:grid-cols-3">
          <InfoLine>
            {state.useOwnAnswer
              ? "Model API will not be called because you provided an answer."
              : "The selected model will generate an answer before TemporalGuard checks it."}
          </InfoLine>
          {state.searchProvider === "none" ? (
            <InfoLine>No evidence provider selected. Fresh/current claims may receive low trust.</InfoLine>
          ) : (
            <InfoLine>Evidence provider: {state.searchProvider.toUpperCase()}.</InfoLine>
          )}
          <InfoLine>{state.mode === "Demo Mode" ? "Demo Mode runs without a backend." : "Backend requests go to FastAPI."}</InfoLine>
        </div>

        <button className="primary-button inline-flex w-full items-center justify-center gap-3 px-6 py-4 text-base font-semibold md:w-auto" onClick={onRun}>
          <SendHorizonal size={18} aria-hidden="true" />
          {isLoading ? "Checking answer..." : "Run TemporalGuard"}
        </button>
      </div>
    </motion.section>
  );
}

function InfoLine({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex gap-2 rounded-2xl border border-warm-border bg-white/62 px-4 py-3 text-sm leading-6 text-warm-muted">
      <AlertCircle className="mt-1 shrink-0 text-sage-700" size={16} aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}

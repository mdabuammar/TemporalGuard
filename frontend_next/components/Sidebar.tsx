"use client";

import { BarChart3, FileSearch, Menu, MessageSquareText, Settings, ShieldCheck, X } from "lucide-react";
import type { DashboardState, LlmProvider, ReportType, RunMode, SearchProvider } from "@/types/temporalguard";

interface SidebarProps {
  state: DashboardState;
  onChange: (next: Partial<DashboardState>) => void;
  onRun: () => void;
  isOpen: boolean;
  onToggle: () => void;
  isLoading: boolean;
}

const modes: RunMode[] = ["Demo Mode", "Local Pipeline", "Backend + Model API"];
const providers: { label: string; value: LlmProvider }[] = [
  { label: "Mock", value: "mock" },
  { label: "OpenRouter", value: "openrouter" },
  { label: "OpenAI", value: "openai" },
  { label: "Gemini", value: "gemini" },
  { label: "Anthropic", value: "anthropic" }
];
const searchProviders: { label: string; value: SearchProvider }[] = [
  { label: "None", value: "none" },
  { label: "Mock", value: "mock" },
  { label: "Tavily", value: "tavily" },
  { label: "Brave", value: "brave" }
];
const reportTypes: ReportType[] = ["dashboard", "technical", "debug"];

export function Sidebar({ state, onChange, onRun, isOpen, onToggle, isLoading }: SidebarProps) {
  return (
    <>
      <button
        className="fixed left-4 top-4 z-50 rounded-full border border-warm-border bg-cream-50 p-3 shadow-card lg:hidden"
        onClick={onToggle}
        aria-label={isOpen ? "Close settings" : "Open settings"}
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-[330px] transform overflow-y-auto border-r border-warm-border bg-[#f6f1e8]/95 px-5 py-5 shadow-card transition-transform duration-300 soft-scrollbar lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="rounded-[24px] border border-warm-border bg-white/60 p-5 shadow-card">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-sage-200 font-bold text-sage-700">TG</div>
          <h2 className="mt-4 text-2xl font-semibold tracking-[-0.03em] text-warm-text">TemporalGuard</h2>
          <p className="mt-1 text-sm text-warm-muted">AI answer reliability</p>
        </div>

        <nav className="mt-6 space-y-1" aria-label="TemporalGuard sections">
          {[
            ["Verify", ShieldCheck],
            ["Evidence", FileSearch],
            ["Claims", MessageSquareText],
            ["Settings", Settings]
          ].map(([label, Icon]) => (
            <a
              key={String(label)}
              href={`#${String(label).toLowerCase()}`}
              className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold text-warm-text transition hover:bg-white/70"
            >
              <Icon size={18} aria-hidden="true" />
              {String(label)}
            </a>
          ))}
        </nav>

        <div className="mt-6 space-y-5">
          <Field label="Mode">
            <select className="control" value={state.mode} onChange={(event) => onChange({ mode: event.target.value as RunMode })}>
              {modes.map((mode) => (
                <option key={mode}>{mode}</option>
              ))}
            </select>
          </Field>
          <Field label="Model provider">
            <select
              className="control"
              value={state.llmProvider}
              onChange={(event) => onChange({ llmProvider: event.target.value as LlmProvider })}
            >
              {providers.map((provider) => (
                <option key={provider.value} value={provider.value}>
                  {provider.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Evidence provider">
            <select
              className="control"
              value={state.searchProvider}
              onChange={(event) => onChange({ searchProvider: event.target.value as SearchProvider })}
            >
              {searchProviders.map((provider) => (
                <option key={provider.value} value={provider.value}>
                  {provider.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Model name">
            <input
              className="control"
              value={state.modelName}
              onChange={(event) => onChange({ modelName: event.target.value })}
              placeholder="openrouter/free"
            />
          </Field>

          <label className="flex cursor-pointer items-center justify-between rounded-2xl border border-warm-border bg-white/60 px-4 py-3">
            <span>
              <span className="block text-sm font-semibold text-warm-text">Use my own answer</span>
              <span className="block text-xs text-warm-muted">Skip model generation</span>
            </span>
            <input
              type="checkbox"
              className="h-5 w-5 accent-sage-700"
              checked={state.useOwnAnswer}
              onChange={(event) => onChange({ useOwnAnswer: event.target.checked })}
            />
          </label>

          <details className="rounded-[22px] border border-warm-border bg-white/60 p-4">
            <summary className="cursor-pointer text-sm font-semibold text-warm-text">Advanced settings</summary>
            <div className="mt-4 space-y-4">
              <Field label="API backend URL">
                <input className="control" value={state.apiUrl} onChange={(event) => onChange({ apiUrl: event.target.value })} />
              </Field>
              <Field label="Report type">
                <select
                  className="control"
                  value={state.reportType}
                  onChange={(event) => onChange({ reportType: event.target.value as ReportType })}
                >
                  {reportTypes.map((type) => (
                    <option key={type}>{type}</option>
                  ))}
                </select>
              </Field>
              <Field label="Max sources per claim">
                <input
                  className="control"
                  type="number"
                  min={1}
                  max={5}
                  value={state.maxSources}
                  onChange={(event) => onChange({ maxSources: Number(event.target.value) })}
                />
              </Field>
              <Toggle label="Show raw JSON" checked={state.showRawJson} onChange={(showRawJson) => onChange({ showRawJson })} />
              <Toggle
                label="Show debug details"
                checked={state.showDebugDetails}
                onChange={(showDebugDetails) => onChange({ showDebugDetails })}
              />
            </div>
          </details>

          <button className="primary-button flex w-full items-center justify-center gap-2 px-5 py-3 font-semibold" onClick={onRun} disabled={isLoading}>
            <BarChart3 size={18} aria-hidden="true" />
            {isLoading ? "Checking..." : "Run TemporalGuard"}
          </button>
          <p className="rounded-2xl bg-sage-100 px-4 py-3 text-xs leading-5 text-sage-700">
            API keys stay in backend environment variables. This frontend never asks for or displays secrets.
          </p>
        </div>
      </aside>
    </>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-semibold text-warm-text">{label}</span>
      {children}
    </label>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label className="flex items-center justify-between gap-3 text-sm text-warm-text">
      {label}
      <input className="h-5 w-5 accent-sage-700" type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
    </label>
  );
}

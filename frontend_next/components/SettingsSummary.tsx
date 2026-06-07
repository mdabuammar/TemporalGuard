import type { DashboardState } from "@/types/temporalguard";

export function SettingsSummary({ state }: { state: DashboardState }) {
  return (
    <details className="rounded-[24px] border border-warm-border bg-white/58 p-4 shadow-card">
      <summary className="cursor-pointer text-sm font-semibold text-warm-text">Settings summary</summary>
      <div className="mt-4 grid gap-3 text-sm text-warm-muted md:grid-cols-3">
        <Item label="Mode" value={state.mode} />
        <Item label="Model provider" value={state.llmProvider} />
        <Item label="Evidence provider" value={state.searchProvider} />
        <Item label="Model" value={state.modelName || "Default"} />
        <Item label="Backend" value={state.apiUrl} />
        <Item label="Answer source" value={state.useOwnAnswer ? "Provided answer" : "Generated answer"} />
      </div>
    </details>
  );
}

function Item({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-cream-50 px-4 py-3">
      <div className="text-xs font-semibold uppercase tracking-[0.12em] text-warm-muted">{label}</div>
      <div className="mt-1 break-words font-medium text-warm-text">{value}</div>
    </div>
  );
}

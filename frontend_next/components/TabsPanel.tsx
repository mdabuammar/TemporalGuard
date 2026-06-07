"use client";

import { useState } from "react";
import { Code2, Info } from "lucide-react";
import { getClaims, getEvidence, getOriginalAnswer, getSummary } from "@/lib/api";
import type { DashboardState, TemporalGuardOutput } from "@/types/temporalguard";
import { ClaimsTable } from "@/components/ClaimsTable";
import { EvidenceTable } from "@/components/EvidenceTable";

const tabs = ["Answer", "Evidence", "Claims", "Details"] as const;
type Tab = (typeof tabs)[number];

export function TabsPanel({ output, state }: { output: TemporalGuardOutput; state: DashboardState }) {
  const [active, setActive] = useState<Tab>("Answer");
  const summary = getSummary(output);
  const evidence = getEvidence(output);
  const claims = getClaims(output);

  return (
    <section className="rounded-[28px] border border-warm-border bg-cream-50/78 p-4 shadow-card md:p-5">
      <div className="flex flex-wrap gap-2 border-b border-warm-border pb-3">
        {tabs.map((tab) => (
          <button
            key={tab}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
              active === tab ? "bg-warm-text text-cream-50 shadow-card" : "bg-white/70 text-warm-muted hover:bg-white"
            }`}
            onClick={() => setActive(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="mt-5">
        {active === "Answer" ? (
          <div className="grid gap-4">
            <AnswerBlock title="Original answer" body={getOriginalAnswer(output) || "No original answer was provided."} />
            <AnswerBlock title="Final answer" body={summary.finalAnswer || "No final answer returned."} highlight />
            <div className="grid gap-4 md:grid-cols-2">
              <InfoCard
                title="Simple explanation"
                body={`TemporalGuard marked this answer as ${summary.badge.replaceAll("_", " ").toLowerCase()} with a ${Math.round(
                  summary.trustScore * 100
                )}% trust score.`}
              />
              <InfoCard
                title="What happened?"
                body="TemporalGuard checked the answer, extracted factual claims, compared claims with evidence, and generated a safety/risk label."
              />
            </div>
          </div>
        ) : null}

        {active === "Evidence" ? (
          <div id="evidence">
            <EvidenceTable items={evidence} />
          </div>
        ) : null}

        {active === "Claims" ? (
          <div id="claims">
            <ClaimsTable items={claims} />
          </div>
        ) : null}

        {active === "Details" ? (
          <div id="settings" className="grid gap-4">
            <InfoCard title="Pipeline status" body={`Mode: ${state.mode}. Provider: ${state.llmProvider}. Evidence: ${state.searchProvider}.`} />
            {Array.isArray(output.warnings) && output.warnings.length ? (
              <InfoCard title="Warnings" body={output.warnings.map(String).join("\n")} />
            ) : null}
            {Array.isArray(output.errors) && output.errors.length ? <InfoCard title="Errors" body={output.errors.map(String).join("\n")} /> : null}
            {state.showDebugDetails ? (
              <details className="rounded-[22px] border border-warm-border bg-white/74 p-4">
                <summary className="flex cursor-pointer items-center gap-2 font-semibold text-warm-text">
                  <Code2 size={17} aria-hidden="true" />
                  Raw JSON
                </summary>
                <pre className="mt-4 max-h-[520px] overflow-auto rounded-2xl bg-[#2f2f2f] p-4 text-xs leading-6 text-cream-50 soft-scrollbar">
                  {JSON.stringify(output, null, 2)}
                </pre>
              </details>
            ) : (
              <div className="rounded-[22px] border border-warm-border bg-white/74 p-4 text-sm text-warm-muted">
                Raw JSON is hidden. Enable debug details in Advanced settings to view it.
              </div>
            )}
          </div>
        ) : null}
      </div>
    </section>
  );
}

function AnswerBlock({ title, body, highlight = false }: { title: string; body: string; highlight?: boolean }) {
  return (
    <article className={`rounded-[24px] border p-5 ${highlight ? "border-sage-200 bg-white" : "border-warm-border bg-white/70"}`}>
      <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-warm-muted">{title}</h3>
      <p className="mt-3 whitespace-pre-wrap text-base leading-7 text-warm-text">{body}</p>
    </article>
  );
}

function InfoCard({ title, body }: { title: string; body: string }) {
  return (
    <article className="rounded-[22px] border border-warm-border bg-white/72 p-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-warm-text">
        <Info size={16} className="text-sage-700" aria-hidden="true" />
        {title}
      </div>
      <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-warm-muted">{body}</p>
    </article>
  );
}

import { motion } from "framer-motion";
import { AlertTriangle, ShieldCheck } from "lucide-react";
import { getSummary } from "@/lib/api";
import type { TemporalGuardOutput } from "@/types/temporalguard";
import { StatusBadge } from "@/components/StatusBadge";

export function ResultCard({ output }: { output: TemporalGuardOutput }) {
  const summary = getSummary(output);
  const trustPercent = Math.round(summary.trustScore * 100);

  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="rounded-[28px] border border-sage-200 bg-white/82 p-5 shadow-soft md:p-7"
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <StatusBadge label={summary.badge} />
          <h2 className="mt-4 text-2xl font-semibold tracking-[-0.02em] text-warm-text">Final answer</h2>
        </div>
        <div className="rounded-3xl border border-warm-border bg-cream-50 px-5 py-4 text-right">
          <div className="text-sm font-medium text-warm-muted">Trust score</div>
          <div className="text-3xl font-semibold text-warm-text">{trustPercent}%</div>
          <div className="mt-1 text-xs uppercase tracking-[0.14em] text-sage-700">{summary.riskLabel.replaceAll("_", " ")}</div>
        </div>
      </div>

      <p className="mt-6 whitespace-pre-wrap rounded-[22px] border border-warm-border bg-cream-50 p-5 text-lg leading-8 text-warm-text">
        {summary.finalAnswer || "Run TemporalGuard to see a verified final answer."}
      </p>

      {summary.warning ? (
        <div className="mt-4 flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-800">
          <AlertTriangle className="mt-1 shrink-0" size={17} aria-hidden="true" />
          <span>{summary.warning}</span>
        </div>
      ) : null}

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {["Extracted factual claims", "Compared with evidence", "Generated risk label"].map((item) => (
          <div key={item} className="flex items-center gap-2 rounded-2xl bg-sage-100 px-4 py-3 text-sm font-medium text-sage-700">
            <ShieldCheck size={16} aria-hidden="true" />
            {item}
          </div>
        ))}
      </div>
    </motion.section>
  );
}

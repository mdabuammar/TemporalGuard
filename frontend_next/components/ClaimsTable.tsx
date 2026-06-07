import type { ClaimItem } from "@/types/temporalguard";
import { StatusBadge } from "@/components/StatusBadge";

export function ClaimsTable({ items }: { items: ClaimItem[] }) {
  if (!items.length) {
    return <div className="rounded-[22px] border border-warm-border bg-white/70 p-5 text-sm text-warm-muted">No extracted claims were returned.</div>;
  }

  return (
    <div className="grid gap-4">
      {items.map((item, index) => {
        const claim = item.claim || item.claim_text || "Claim";
        const status = item.verification_status || item.risk_label || item.risk_level || "unknown";
        return (
          <article key={`${claim}-${index}`} className="rounded-[22px] border border-warm-border bg-white/74 p-4 shadow-card">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <p className="text-base font-semibold leading-7 text-warm-text">{claim}</p>
              <StatusBadge label={status} />
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <Value label="Claim value" value={item.claim_value} />
              <Value label="Evidence value" value={item.evidence_value} />
            </div>
          </article>
        );
      })}
    </div>
  );
}

function Value({ label, value }: { label: string; value?: string }) {
  return (
    <div className="rounded-2xl bg-cream-50 px-4 py-3">
      <div className="text-xs font-semibold uppercase tracking-[0.12em] text-warm-muted">{label}</div>
      <div className="mt-1 text-sm text-warm-text">{value || "Not available"}</div>
    </div>
  );
}

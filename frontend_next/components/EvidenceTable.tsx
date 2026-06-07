import { ExternalLink } from "lucide-react";
import type { EvidenceItem } from "@/types/temporalguard";

export function EvidenceTable({ items }: { items: EvidenceItem[] }) {
  if (!items.length) {
    return <Empty message="No evidence sources were returned for this run." />;
  }

  return (
    <div className="grid gap-4">
      {items.map((item, index) => (
        <article key={`${item.title}-${index}`} className="rounded-[22px] border border-warm-border bg-white/74 p-4 shadow-card">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <h3 className="text-base font-semibold text-warm-text">{item.title || item.source || "Evidence source"}</h3>
              <p className="mt-1 text-sm text-warm-muted">{item.publisher || "Unknown publisher"}</p>
            </div>
            <span className="w-fit rounded-full bg-sage-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-sage-700">
              {item.freshness_label || item.published_date || item.updated_date || "Evidence"}
            </span>
          </div>
          {item.snippet ? <p className="mt-3 text-sm leading-6 text-warm-muted">{item.snippet}</p> : null}
          <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
            {item.score !== undefined ? <span className="text-warm-muted">Score: {String(item.score)}</span> : null}
            {item.url ? (
              <a className="inline-flex items-center gap-1 font-semibold text-sage-700 hover:text-sage-700/80" href={item.url} target="_blank" rel="noreferrer">
                Open source
                <ExternalLink size={14} aria-hidden="true" />
              </a>
            ) : null}
          </div>
        </article>
      ))}
    </div>
  );
}

function Empty({ message }: { message: string }) {
  return <div className="rounded-[22px] border border-warm-border bg-white/70 p-5 text-sm text-warm-muted">{message}</div>;
}

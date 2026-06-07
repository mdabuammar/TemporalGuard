import type { AnalyzeRequest, TemporalGuardOutput } from "@/types/temporalguard";

export function getDefaultApiUrl() {
  return process.env.NEXT_PUBLIC_TEMPORALGUARD_API_URL || "http://127.0.0.1:8000";
}

export async function analyzeTemporalGuard(apiUrl: string, payload: AnalyzeRequest): Promise<TemporalGuardOutput> {
  const base = apiUrl.replace(/\/$/, "");
  let response: Response;
  try {
    response = await fetch(`${base}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  } catch {
    throw new Error("TemporalGuard backend is unavailable. Start FastAPI and try again.");
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data?.detail;
    const message =
      detail?.message ||
      detail?.error_message ||
      data?.message ||
      "TemporalGuard could not complete the analysis.";
    throw new Error(message);
  }
  return data as TemporalGuardOutput;
}

export function getFinalAnswer(output: TemporalGuardOutput | null) {
  if (!output) return "";
  return (
    output.correction?.corrected_answer ||
    output.report?.final_answer ||
    output.final_answer ||
    output.original_answer ||
    ""
  );
}

export function getOriginalAnswer(output: TemporalGuardOutput | null) {
  if (!output) return "";
  return String(output.original_answer || "");
}

export function getSummary(output: TemporalGuardOutput | null) {
  const dashboard = output?.report?.dashboard_summary || {};
  const risk = output?.risk_label || {};
  const badge = String(risk.dashboard_badge || dashboard.badge || "Ready");
  const riskLabel = String(risk.final_risk_label || dashboard.risk_label || "unknown_risk");
  const trustScore = Number(risk.trust_score ?? dashboard.trust_score ?? 0);
  return {
    badge,
    riskLabel,
    trustScore: Number.isFinite(trustScore) ? trustScore : 0,
    warning: String(risk.user_warning || dashboard.user_warning || output?.correction?.safety_note || ""),
    finalAnswer: getFinalAnswer(output),
    originalAnswer: getOriginalAnswer(output),
    status: String(risk.temporal_safety_status || dashboard.temporal_safety_status || "needs_review")
  };
}

export function getEvidence(output: TemporalGuardOutput | null) {
  const reportItems = output?.report?.evidence_report;
  if (Array.isArray(reportItems) && reportItems.length > 0) return reportItems;
  const evidence = output?.evidence;
  if (Array.isArray(evidence?.evidence_items)) return evidence.evidence_items;
  if (Array.isArray(evidence?.sources)) return evidence.sources;
  return [];
}

export function getClaims(output: TemporalGuardOutput | null) {
  const reportItems = output?.report?.claim_report;
  if (Array.isArray(reportItems) && reportItems.length > 0) return reportItems;
  const verification = output?.verification?.verification_results;
  if (Array.isArray(verification) && verification.length > 0) return verification;
  const claims = output?.claims?.claims;
  if (Array.isArray(claims)) return claims;
  return [];
}

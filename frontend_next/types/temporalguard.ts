export type RunMode = "Demo Mode" | "Local Pipeline" | "Backend + Model API";
export type LlmProvider = "mock" | "openrouter" | "openai" | "gemini" | "anthropic";
export type SearchProvider = "none" | "mock" | "tavily" | "brave";
export type ReportType = "dashboard" | "technical" | "debug";

export interface AnalyzeRequest {
  question: string;
  base_answer: string | null;
  llm_provider: LlmProvider;
  model_name: string | null;
  search_provider: SearchProvider;
  report_type: ReportType;
}

export interface DashboardState {
  mode: RunMode;
  llmProvider: LlmProvider;
  searchProvider: SearchProvider;
  modelName: string;
  useOwnAnswer: boolean;
  apiUrl: string;
  reportType: ReportType;
  maxSources: number;
  showRawJson: boolean;
  showDebugDetails: boolean;
}

export interface EvidenceItem {
  title?: string;
  publisher?: string;
  source?: string;
  url?: string;
  freshness_label?: string;
  published_date?: string;
  updated_date?: string;
  score?: number | string;
  snippet?: string;
}

export interface ClaimItem {
  claim?: string;
  claim_text?: string;
  verification_status?: string;
  risk_level?: string;
  risk_label?: string;
  claim_value?: string;
  evidence_value?: string;
}

export interface TemporalGuardOutput {
  question?: string;
  original_answer?: string;
  final_answer?: string;
  correction?: {
    corrected_answer?: string;
    correction_status?: string;
    safety_note?: string;
  };
  report?: {
    final_answer?: string;
    dashboard_summary?: Record<string, unknown>;
    evidence_report?: EvidenceItem[];
    claim_report?: ClaimItem[];
    pipeline_summary?: Record<string, unknown>;
  };
  risk_label?: {
    dashboard_badge?: string;
    final_risk_label?: string;
    trust_score?: number;
    user_warning?: string;
    temporal_safety_status?: string;
    uncertainty_label?: string;
  };
  claims?: {
    claims?: ClaimItem[];
    total_claims?: number;
  };
  evidence?: {
    evidence_items?: EvidenceItem[];
    sources?: EvidenceItem[];
  };
  verification?: {
    verification_results?: ClaimItem[];
    overall_verification_status?: string;
  };
  outdatedness?: {
    outdatedness_status?: string;
  };
  temporal_detection?: {
    temporal_category?: string;
    needs_fresh_evidence?: boolean;
  };
  warnings?: unknown[];
  errors?: unknown[];
  [key: string]: unknown;
}

export interface NormalizedSummary {
  badge: string;
  riskLabel: string;
  trustScore: number;
  warning?: string;
  finalAnswer: string;
  originalAnswer: string;
  status: string;
}

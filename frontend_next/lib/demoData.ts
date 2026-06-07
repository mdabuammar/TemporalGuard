import type { TemporalGuardOutput } from "@/types/temporalguard";

export const demoQuestions = [
  "What is the latest Python version?",
  "What is binary search?",
  "Is this visa rule still active?"
];

export function createDemoOutput(question: string, ownAnswer?: string): TemporalGuardOutput {
  const normalized = question.toLowerCase();
  if (normalized.includes("binary search")) {
    return {
      question,
      original_answer: ownAnswer || "Binary search is an algorithm for finding a target in a sorted list.",
      correction: {
        corrected_answer: ownAnswer || "Binary search finds a target value in a sorted collection by repeatedly halving the search interval.",
        correction_status: "not_needed"
      },
      risk_label: {
        dashboard_badge: "SAFE",
        final_risk_label: "low_risk",
        trust_score: 0.94,
        temporal_safety_status: "supported"
      },
      report: {
        dashboard_summary: { badge: "SAFE", trust_score: 0.94, risk_label: "low_risk" },
        evidence_report: [
          {
            title: "Stable computer science definition",
            publisher: "TemporalGuard demo",
            freshness_label: "Static knowledge",
            score: 0.92,
            snippet: "The answer is a stable educational definition and does not require fresh evidence."
          }
        ],
        claim_report: [
          {
            claim: "Binary search works on sorted collections by halving the search interval.",
            verification_status: "SUPPORTED",
            risk_level: "LOW",
            claim_value: "halving sorted search interval",
            evidence_value: "halving sorted search interval"
          }
        ]
      }
    };
  }

  if (normalized.includes("visa")) {
    return {
      question,
      original_answer: ownAnswer || "The visa rule is active and applicants can follow the old process.",
      correction: {
        corrected_answer: "Visa and immigration rules can change quickly. Check the official government source before acting on this rule.",
        correction_status: "needs_evidence"
      },
      risk_label: {
        dashboard_badge: "UNVERIFIED",
        final_risk_label: "high_risk",
        trust_score: 0.42,
        user_warning: "This is a high-impact policy question and needs official fresh evidence.",
        temporal_safety_status: "needs_more_evidence"
      },
      report: {
        dashboard_summary: { badge: "UNVERIFIED", trust_score: 0.42, risk_label: "high_risk" },
        evidence_report: [
          {
            title: "Official source needed",
            publisher: "TemporalGuard demo",
            freshness_label: "Fresh evidence required",
            score: 0.38,
            snippet: "No live evidence provider is connected in Demo Mode."
          }
        ],
        claim_report: [
          {
            claim: "The visa rule is still active.",
            verification_status: "INSUFFICIENT_EVIDENCE",
            risk_level: "HIGH",
            claim_value: "active",
            evidence_value: "missing"
          }
        ]
      }
    };
  }

  return {
    question,
    original_answer: ownAnswer || "Python 3.11 is the latest version of Python.",
    correction: {
      corrected_answer: "Python version information changes over time. Use a live evidence provider to verify the latest release before relying on this answer.",
      correction_status: "corrected"
    },
    risk_label: {
      dashboard_badge: "CORRECTED",
      final_risk_label: "medium_risk",
      trust_score: 0.76,
      user_warning: "The original answer may be outdated.",
      temporal_safety_status: "corrected"
    },
    report: {
      dashboard_summary: { badge: "CORRECTED", trust_score: 0.76, risk_label: "medium_risk" },
      evidence_report: [
        {
          title: "Python release status",
          publisher: "TemporalGuard demo",
          freshness_label: "Current claim",
          score: 0.8,
          snippet: "Latest-version claims require fresh release evidence."
        }
      ],
      claim_report: [
        {
          claim: "Python 3.11 is the latest version of Python.",
          verification_status: "OUTDATED",
          risk_level: "MEDIUM",
          claim_value: "Python 3.11",
          evidence_value: "newer release available"
        }
      ]
    }
  };
}

"""Rule-based temporal question detection for TemporalGuard."""

from __future__ import annotations

import re
from typing import Any


TemporalResult = dict[str, Any]


RECENT_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\blatest\b", "latest"),
    (r"\bcurrent\b", "current"),
    (r"\bcurrently\b", "currently"),
    (r"\bnewest\b", "newest"),
    (r"\btoday(?:'s)?\b", "today"),
    (r"\bnow\b", "now"),
    (r"\brecent\b", "recent"),
    (r"\breal[- ]?time\b", "real-time"),
    (r"\bthis week(?:'s)?\b", "this week"),
    (r"\bthis month(?:'s)?\b", "this month"),
    (r"\bthis year(?:'s)?\b", "this year"),
    (r"\bas of now\b", "as of now"),
)

CHANGE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bupdated\b", "updated"),
    (r"\bstill\b", "still"),
    (r"\bactive\b", "active"),
    (r"\bchanged\b", "changed"),
    (r"\bdeprecated\b", "deprecated"),
    (r"\brecommended\b", "recommended"),
)

SOFTWARE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bopenai api\b", "OpenAI API"),
    (r"\bapi\b", "API"),
    (r"\blangchain\b", "LangChain"),
    (r"\bllamaindex\b", "LlamaIndex"),
    (r"\btensorflow\b", "TensorFlow"),
    (r"\bpytorch\b", "PyTorch"),
    (r"\bpandas\b", "pandas"),
    (r"\bnumpy\b", "NumPy"),
    (r"\bcuda\b", "CUDA"),
    (r"\bpython\b", "Python"),
    (r"\bnode\.?js\b", "Node.js"),
    (r"\breact\b", "React"),
    (r"\bnext\.?js\b", "Next.js"),
    (r"\bstreamlit\b", "Streamlit"),
    (r"\bhugging face\b", "Hugging Face"),
    (r"\bvllm\b", "vLLM"),
    (r"\bdocker\b", "Docker"),
    (r"\bpackage\b", "package"),
    (r"\bdependency\b", "dependency"),
    (r"\binstall(?:ation)?\b", "installation"),
    (r"\bfunction\b", "function"),
)

TIME_SENSITIVE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bceo\b", "CEO"),
    (r"\bpresident\b", "president"),
    (r"\bcompany leadership\b", "company leadership"),
    (r"\bowner|owns|owned by\b", "ownership"),
    (r"\blaw\b", "law"),
    (r"\blegal(?:ly)?\b", "legal"),
    (r"\bvisa\b", "visa"),
    (r"\besta\b", "ESTA"),
    (r"\bschengen\b", "Schengen"),
    (r"\bstudy permit\b", "study permit"),
    (r"\btraveller|traveler\b", "traveller"),
    (r"\bpolicy\b", "policy"),
    (r"\brule\b", "rule"),
    (r"\bregulation\b", "regulation"),
    (r"\btax\b", "tax"),
    (r"\binflation\b", "inflation"),
    (r"\binterest rate\b", "interest rate"),
    (r"\bprice\b", "price"),
    (r"\bmarket\b", "market"),
    (r"\bfinance|financial\b", "finance"),
    (r"\bmedicine|medical|guideline|safe\b", "medical guideline"),
    (r"\buniversity admission\b", "university admission"),
    (r"\bweather\b", "weather"),
    (r"\bmatch\b", "match"),
)

STATIC_START_PATTERNS: tuple[str, ...] = (
    r"^what is ",
    r"^what are ",
    r"^explain ",
    r"^define ",
    r"^tell me what ",
)

AMBIGUOUS_TERMS = {"apple", "java", "mercury"}

HISTORICAL_ANCHOR_RE = re.compile(
    r"\b(?:in|during|before|after|since)\s+((?:19|20)\d{2})\b"
    r"|\b((?:19|20)\d{2})\b"
    r"|\b(yesterday|last week|last month|last year)\b",
    re.IGNORECASE,
)
HISTORICAL_QUESTION_RE = re.compile(
    r"\b("
    r"who\s+won|when\s+did|when\s+was|what\s+year\s+did|"
    r"who\s+was\b.+\bin\s+(?:19|20)\d{2}|"
    r"was\b.+\bin\s+(?:19|20)\d{2}"
    r")\b",
    re.IGNORECASE,
)
VERSION_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9 .+-]*\s+\d+(?:\.\d+){1,3}\b")
KNOWN_VERSION_RE = re.compile(
    r"\b("
    r"OpenAI API|LangChain|LlamaIndex|TensorFlow|PyTorch|pandas|NumPy|CUDA|"
    r"Python|Node\.?js|React|Next\.?js|Streamlit|Hugging Face|vLLM|Docker"
    r")\s+\d+(?:\.\d+){1,3}\b",
    re.IGNORECASE,
)


def detect_temporal_category(question: str) -> TemporalResult:
    """Classify a user question into one temporal category."""
    if not isinstance(question, str) or not question.strip():
        return _result(
            "UNKNOWN",
            True,
            0.40,
            "The question is empty or invalid.",
            [],
            None,
            "ask_clarifying_question",
        )

    text = _normalize(question)
    signals: list[str] = []

    if _is_ambiguous_short_question(text):
        return _result(
            "UNKNOWN",
            True,
            0.45,
            "The question is ambiguous and missing the exact topic.",
            [],
            None,
            "ask_clarifying_question",
        )

    historical_anchor = _extract_historical_anchor(text)
    version_anchor = _extract_version_anchor(question)
    recent_signals = _collect_signals(text, RECENT_PATTERNS)
    change_signals = _collect_signals(text, CHANGE_PATTERNS)
    software_signals = _collect_signals(text, SOFTWARE_PATTERNS)
    risk_signals = _collect_signals(text, TIME_SENSITIVE_PATTERNS)

    if historical_anchor or HISTORICAL_QUESTION_RE.search(text):
        signals = _unique(recent_signals + software_signals + risk_signals + ([historical_anchor] if historical_anchor else []))
        return _result(
            "HISTORICAL",
            True,
            0.96,
            "The question asks about a fact at a specific past time.",
            signals,
            historical_anchor,
            "retrieve_historical_evidence",
        )

    if risk_signals and not recent_signals and _asks_policy_duration_or_rule(text):
        signals = _unique(risk_signals + change_signals)
        return _result(
            "TIME_SENSITIVE",
            True,
            0.92,
            "The question asks about a legal, visa, policy, or rule fact that can change over time.",
            signals,
            "current",
            "retrieve_fresh_evidence",
        )

    if software_signals and change_signals and not recent_signals:
        signals = _unique(software_signals + change_signals)
        return _result(
            "VERSION_DEPENDENT",
            True,
            0.92,
            "The answer depends on a software version or support lifecycle.",
            signals,
            version_anchor,
            "retrieve_fresh_evidence",
        )

    if recent_signals or _asks_if_still_active(text):
        signals = _unique(recent_signals + software_signals + risk_signals)
        anchor = _recent_anchor(recent_signals)
        return _result(
            "RECENT_ONLY",
            True,
            0.98,
            "The question explicitly asks for fresh or current information.",
            signals,
            anchor,
            "retrieve_fresh_evidence",
        )

    if software_signals:
        signals = _unique(software_signals + change_signals)
        anchor = version_anchor
        return _result(
            "VERSION_DEPENDENT",
            True,
            0.90,
            "The answer may depend on software, API, library, or documentation versions.",
            signals,
            anchor,
            "retrieve_fresh_evidence",
        )

    if risk_signals or change_signals:
        signals = _unique(risk_signals + change_signals)
        anchor = "current" if risk_signals or change_signals else None
        return _result(
            "TIME_SENSITIVE",
            True,
            0.92,
            "The topic can change over time and should be verified with fresh evidence.",
            signals,
            anchor,
            "retrieve_fresh_evidence",
        )

    if _looks_static_educational(text):
        return _result(
            "STATIC",
            False,
            0.95,
            "This is a stable educational concept.",
            [],
            None,
            "answer_directly",
        )

    return _result(
        "UNKNOWN",
        True,
        0.55,
        "The temporal status cannot be confidently determined from the question.",
        [],
        None,
        "ask_clarifying_question",
    )


def detect_temporal_question(question: str) -> str:
    """Backward-compatible wrapper that returns only the category."""
    return str(detect_temporal_category(question)["temporal_category"])


def _normalize(question: str) -> str:
    return " ".join(question.strip().lower().split())


def _result(
    category: str,
    needs_fresh_evidence: bool,
    confidence: float,
    reason: str,
    temporal_signals: list[str],
    temporal_anchor: str | None,
    recommended_next_action: str,
) -> TemporalResult:
    return {
        "temporal_category": category,
        "needs_fresh_evidence": needs_fresh_evidence,
        "confidence": confidence,
        "reason": reason,
        "temporal_signals": temporal_signals,
        "temporal_anchor": temporal_anchor,
        "recommended_next_action": recommended_next_action,
    }


def _collect_signals(text: str, patterns: tuple[tuple[str, str], ...]) -> list[str]:
    return _unique([signal for pattern, signal in patterns if re.search(pattern, text)])


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            unique_items.append(item)
    return unique_items


def _extract_historical_anchor(text: str) -> str | None:
    match = HISTORICAL_ANCHOR_RE.search(text)
    if not match:
        return None
    return next(group for group in match.groups() if group)


def _extract_version_anchor(question: str) -> str | None:
    match = KNOWN_VERSION_RE.search(question) or VERSION_RE.search(question)
    return match.group(0).strip(" .?,") if match else None


def _recent_anchor(recent_signals: list[str]) -> str:
    if not recent_signals:
        return "current"
    for signal in recent_signals:
        if signal in {"today", "this week", "this month", "this year", "as of now"}:
            return signal
    if any(signal in {"current", "currently", "now"} for signal in recent_signals):
        return "current"
    return recent_signals[0]


def _is_ambiguous_short_question(text: str) -> bool:
    words = re.findall(r"[a-z]+", text)
    if len(words) <= 2 and any(term in words for term in AMBIGUOUS_TERMS):
        return True
    return (
        len(words) <= 5
        and any(term in words for term in AMBIGUOUS_TERMS)
        and re.search(r"^(tell me about|explain|what about|can i use)", text) is not None
    )


def _looks_static_educational(text: str) -> bool:
    if any(re.search(pattern, text) for pattern in STATIC_START_PATTERNS):
        return True
    if re.search(r"^is\s+[a-z0-9 .+-]+\s+(?:an?\s+)?(?:volatile memory|memory|algorithm|data structure|concept|technique)\??$", text):
        return True
    return text.startswith("how does ") and not re.search(r"\buse|install|update|configure\b", text)


def _asks_if_still_active(text: str) -> bool:
    return re.search(r"\bstill\b.*\bactive\b|\bactive\b.*\bstill\b", text) is not None


def _asks_policy_duration_or_rule(text: str) -> bool:
    return re.search(r"\bhow long\b|\bwithin a rolling period\b|\bvalid\b|\bstay\b|\bauthorization\b", text) is not None

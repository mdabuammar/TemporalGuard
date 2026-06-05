"""Deterministic source freshness and reliability scoring for TemporalGuard."""

from __future__ import annotations

from datetime import UTC, datetime
import re
from typing import Any


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3, "unknown": 4}
SOURCE_AUTHORITY = {
    "official": 1.00,
    "government": 1.00,
    "standards": 0.95,
    "documentation": 0.95,
    "academic": 0.90,
    "database": 0.90,
    "company": 0.85,
    "reputable_news": 0.80,
    "other": 0.50,
    "unknown": 0.30,
}
LIVE_CURRENT_SOURCE_TYPES = {"official", "government", "documentation", "database", "standards"}
STRICT_TEMPORAL_CATEGORIES = {"RECENT_ONLY", "TIME_SENSITIVE", "VERSION_DEPENDENT"}
HIGH_RISK_PATTERN = re.compile(
    r"\b("
    r"medical|medicine|clinical guideline|drug safety|law|legal|visa|immigration|tax|"
    r"finance|price|interest rate|stock|crypto|policy|regulation|university admission|"
    r"amazon policy|safety|security advisory|software vulnerability"
    r")\b",
    re.IGNORECASE,
)


def score_source_freshness(
    evidence_payload: dict[str, Any],
    temporal_category: str | None = None,
    scoring_datetime: str | None = None,
) -> dict[str, Any]:
    """
    Score freshness and reliability of retrieved evidence.

    This function does not retrieve evidence, browse URLs, verify truth, or correct claims.
    """
    scoring_dt, warnings = _parse_scoring_datetime(scoring_datetime)
    evidence_results = _extract_evidence_results(evidence_payload)
    freshness_results = [
        _score_claim_evidence(claim_result, temporal_category, scoring_dt, warnings)
        for claim_result in evidence_results
    ]

    if not freshness_results:
        return {
            "freshness_results": [],
            "overall_freshness_score": 0.0,
            "overall_temporal_risk": "unknown",
            "scoring_warnings": warnings or ["No evidence results supplied for scoring."],
        }

    overall_score = _round_score(
        sum(float(result["claim_reliability_score"]) for result in freshness_results) / len(freshness_results)
    )
    overall_risk = _worst_risk(str(result["claim_temporal_risk"]) for result in freshness_results)

    return {
        "freshness_results": freshness_results,
        "overall_freshness_score": overall_score,
        "overall_temporal_risk": overall_risk,
        "scoring_warnings": warnings,
    }


def _parse_scoring_datetime(value: str | None) -> tuple[datetime, list[str]]:
    warnings: list[str] = []
    if value:
        parsed, warning = _parse_date(value)
        if parsed:
            return parsed, warnings
        warnings.append(warning or "Malformed scoring_datetime; current UTC time used.")
    return datetime.now(UTC), warnings


def _extract_evidence_results(evidence_payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(evidence_payload, dict):
        return []
    results = evidence_payload.get("evidence_results")
    if not isinstance(results, list):
        return []
    return [result for result in results if isinstance(result, dict)]


def _score_claim_evidence(
    claim_result: dict[str, Any],
    temporal_category: str | None,
    scoring_dt: datetime,
    warnings: list[str],
) -> dict[str, Any]:
    claim_id = str(claim_result.get("claim_id") or "")
    claim_text = str(claim_result.get("claim_text") or "")
    evidence_items = claim_result.get("evidence_items")
    high_risk = _detect_high_risk_domain(claim_text)

    if not isinstance(evidence_items, list) or not evidence_items:
        risk = _risk_for_no_evidence(claim_text, temporal_category, high_risk)
        return {
            "claim_id": claim_id,
            "claim_text": claim_text,
            "claim_freshness_score": 0.0,
            "claim_reliability_score": 0.0,
            "claim_temporal_risk": risk,
            "best_evidence_id": None,
            "evidence_scores": [],
            "notes": "No evidence available for freshness scoring.",
        }

    scores = [
        _score_evidence_item(item, claim_result, temporal_category, scoring_dt, warnings)
        for item in evidence_items
        if isinstance(item, dict)
    ]
    if not scores:
        risk = _risk_for_no_evidence(claim_text, temporal_category, high_risk)
        return {
            "claim_id": claim_id,
            "claim_text": claim_text,
            "claim_freshness_score": 0.0,
            "claim_reliability_score": 0.0,
            "claim_temporal_risk": risk,
            "best_evidence_id": None,
            "evidence_scores": [],
            "notes": "No valid evidence items available for freshness scoring.",
        }

    best = max(scores, key=lambda score: float(score["combined_score"]))
    risk = _risk_from_scores(
        float(best["combined_score"]),
        float(best["freshness_score"]),
        list(best["risk_flags"]),
        high_risk,
        True,
    )
    return {
        "claim_id": claim_id,
        "claim_text": claim_text,
        "claim_freshness_score": best["freshness_score"],
        "claim_reliability_score": best["combined_score"],
        "claim_temporal_risk": risk,
        "best_evidence_id": best["evidence_id"],
        "evidence_scores": scores,
        "notes": _claim_notes(risk, best),
    }


def _score_evidence_item(
    item: dict[str, Any],
    claim_result: dict[str, Any],
    temporal_category: str | None,
    scoring_dt: datetime,
    warnings: list[str],
) -> dict[str, Any]:
    claim_text = str(claim_result.get("claim_text") or "")
    source_type = _normalize_source_type(str(item.get("source_type") or "unknown"))
    date_used, date_basis, parsed_date, date_flags = _select_date(item, source_type)
    age_days = _calculate_age_days(parsed_date, scoring_dt)
    evidence_need = str(claim_result.get("evidence_need") or item.get("evidence_need") or "")
    if not evidence_need:
        evidence_need = _infer_evidence_need(claim_text, temporal_category)

    freshness_score, freshness_label, risk_flags = _score_freshness(
        age_days,
        evidence_need,
        temporal_category,
        source_type,
        date_basis,
        claim_text,
    )
    risk_flags.extend(date_flags)
    if _detect_high_risk_domain(claim_text):
        risk_flags.append("high_risk_domain")

    authority = _authority_score(source_type)
    if authority <= 0.50:
        risk_flags.append("low_authority_source")

    relevance = _relevance_score(item, claim_text)
    if relevance < 0.50:
        risk_flags.append("low_relevance_source")

    combined = _combined_score(freshness_score, authority, relevance, _detect_high_risk_domain(claim_text))
    notes = _evidence_notes(freshness_label, source_type, risk_flags)

    for flag in date_flags:
        if flag == "malformed_date":
            warnings.append(f"Malformed date found for evidence {item.get('evidence_id') or 'unknown'}.")

    return {
        "evidence_id": str(item.get("evidence_id") or ""),
        "url": str(item.get("url") or ""),
        "source_type": source_type,
        "publisher": str(item.get("publisher") or "unknown"),
        "date_used": date_used,
        "date_basis": date_basis,
        "source_age_days": age_days,
        "freshness_score": _round_score(freshness_score),
        "authority_score": _round_score(authority),
        "relevance_score": _round_score(relevance),
        "combined_score": combined,
        "freshness_label": freshness_label,
        "risk_flags": _unique(risk_flags),
        "notes": notes,
    }


def _parse_date(value: str | None) -> tuple[datetime | None, str | None]:
    if not value:
        return None, None
    text = str(value).strip()
    try:
        if re.fullmatch(r"\d{4}", text):
            return datetime(int(text), 1, 1, tzinfo=UTC), "year_only_date"
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=UTC), None
        iso_text = text.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(iso_text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC), None
    except ValueError:
        return None, "malformed_date"


def _select_date(item: dict[str, Any], source_type: str) -> tuple[str | None, str, datetime | None, list[str]]:
    flags: list[str] = []
    for field, basis in (("updated_date", "updated_date"), ("published_date", "published_date")):
        raw_value = item.get(field)
        parsed, flag = _parse_date(raw_value)
        if parsed:
            if flag:
                flags.append(flag)
            return _format_date_used(raw_value), basis, parsed, flags
        if flag:
            flags.append(flag)

    retrieved_at = item.get("retrieved_at")
    if source_type in LIVE_CURRENT_SOURCE_TYPES and retrieved_at:
        parsed, flag = _parse_date(retrieved_at)
        if parsed:
            flags.append("official_live_page_no_update_date")
            return _format_date_used(retrieved_at), "retrieved_at", parsed, flags
        if flag:
            flags.append(flag)

    if not item.get("updated_date") and not item.get("published_date"):
        flags.append("no_date_available")
    return None, "unavailable", None, flags


def _calculate_age_days(date_value: datetime | None, scoring_dt: datetime) -> int | None:
    if date_value is None:
        return None
    return max(0, (scoring_dt.date() - date_value.date()).days)


def _authority_score(source_type: str) -> float:
    return SOURCE_AUTHORITY.get(_normalize_source_type(source_type), 0.30)


def _detect_high_risk_domain(claim_text: str) -> bool:
    return HIGH_RISK_PATTERN.search(claim_text) is not None


def _score_freshness(
    age_days: int | None,
    evidence_need: str | None,
    temporal_category: str | None,
    source_type: str,
    date_basis: str,
    claim_text: str,
) -> tuple[float, str, list[str]]:
    flags: list[str] = []
    need = str(evidence_need or "").lower()
    is_strict = temporal_category in STRICT_TEMPORAL_CATEGORIES or need == "fresh"

    if need == "historical" or temporal_category == "HISTORICAL":
        flags.extend(_historical_flags(claim_text))
        if source_type in {"official", "government", "academic"}:
            return 0.92, "very_fresh", flags
        if source_type in {"database", "standards", "documentation", "reputable_news"}:
            return 0.78, "fresh", flags
        return 0.55, "stale", flags + ["low_authority_source"]

    if need == "version_specific" or temporal_category == "VERSION_DEPENDENT":
        flags.append("version_specific_claim")
        if source_type in {"official", "documentation", "standards"}:
            return (0.85 if date_basis == "unavailable" else 0.95), "fresh", flags
        if source_type in {"academic", "database", "company"}:
            return 0.75, "fresh", flags
        if age_days is None:
            return 0.35, "unknown", flags + ["no_date_available"]
        return _fresh_score_from_age(age_days, strict=True, flags=flags)

    if age_days is None:
        if date_basis == "unavailable":
            flags.append("no_date_available")
        if is_strict:
            return 0.35, "unknown", flags
        return 0.60, "acceptable", flags

    if is_strict:
        return _fresh_score_from_age(age_days, strict=True, flags=flags)

    if need == "optional" or temporal_category == "STATIC":
        if age_days <= 3650:
            return 0.75, "fresh", flags
        return 0.65, "acceptable", flags

    return _fresh_score_from_age(age_days, strict=False, flags=flags)


def _fresh_score_from_age(age_days: int, strict: bool, flags: list[str]) -> tuple[float, str, list[str]]:
    if strict:
        if age_days <= 30:
            return 0.98, "very_fresh", flags
        if age_days <= 90:
            return 0.85, "fresh", flags
        if age_days <= 180:
            return 0.68, "acceptable", flags
        if age_days <= 365:
            flags.append("source_too_old_for_recent_claim")
            return 0.50, "stale", flags
        flags.append("source_too_old_for_recent_claim")
        return 0.25, "outdated", flags

    if age_days <= 365:
        return 0.85, "fresh", flags
    if age_days <= 1095:
        return 0.70, "acceptable", flags
    return 0.50, "stale", flags


def _combined_score(
    freshness_score: float,
    authority_score: float,
    relevance_score: float,
    high_risk: bool,
) -> float:
    if high_risk:
        score = (0.50 * freshness_score) + (0.35 * authority_score) + (0.15 * relevance_score)
    else:
        score = (0.45 * freshness_score) + (0.35 * authority_score) + (0.20 * relevance_score)
    return _round_score(score)


def _risk_from_scores(
    combined_score: float,
    freshness_score: float,
    risk_flags: list[str],
    high_risk: bool,
    has_evidence: bool,
) -> str:
    if not has_evidence:
        return "critical" if high_risk else "high"
    flags = set(risk_flags)
    if high_risk and ("no_date_available" in flags or "source_too_old_for_recent_claim" in flags):
        return "critical"
    if combined_score >= 0.85 and freshness_score >= 0.75 and not {"low_authority_source", "low_relevance_source"} & flags:
        return "low"
    if combined_score >= 0.70 and freshness_score >= 0.60:
        return "medium"
    if combined_score >= 0.45:
        return "high"
    return "critical" if high_risk else "high"


def _risk_for_no_evidence(claim_text: str, temporal_category: str | None, high_risk: bool) -> str:
    if high_risk:
        return "critical"
    if temporal_category in STRICT_TEMPORAL_CATEGORIES or _is_current_claim(claim_text):
        return "high"
    if temporal_category == "STATIC":
        return "low"
    return "medium"


def _relevance_score(item: dict[str, Any], claim_text: str) -> float:
    raw = item.get("relevance_score")
    if isinstance(raw, int | float):
        return _clamp(float(raw))
    text = f"{item.get('title') or ''} {item.get('evidence_summary') or ''} {item.get('url') or ''}".lower()
    terms = [term.lower() for term in re.findall(r"[A-Za-z0-9]+", claim_text) if len(term) > 3]
    if not terms:
        return 0.50
    matches = sum(1 for term in terms[:8] if term in text)
    ratio = matches / min(len(terms), 8)
    if ratio >= 0.50:
        return 0.85
    if ratio >= 0.25:
        return 0.65
    return 0.40


def _infer_evidence_need(claim_text: str, temporal_category: str | None) -> str:
    if temporal_category == "HISTORICAL" or re.search(r"\b(?:19|20)\d{2}\b", claim_text):
        return "historical"
    if temporal_category in {"RECENT_ONLY", "TIME_SENSITIVE"} or _is_current_claim(claim_text):
        return "fresh"
    if temporal_category == "VERSION_DEPENDENT" or re.search(r"\b(api|sdk|version|documentation|deprecated)\b", claim_text, re.I):
        return "version_specific"
    return "optional"


def _historical_flags(claim_text: str) -> list[str]:
    return [] if re.search(r"\b(?:19|20)\d{2}\b", claim_text) else ["historical_claim_date_match_needed"]


def _is_current_claim(claim_text: str) -> bool:
    return re.search(r"\b(latest|current|currently|still|active|today|no longer)\b", claim_text, re.I) is not None


def _format_date_used(value: Any) -> str:
    text = str(value)
    if re.fullmatch(r"\d{4}", text):
        return text
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text
    return text.replace("+00:00", "Z")


def _freshness_label(score: float) -> str:
    if score >= 0.90:
        return "very_fresh"
    if score >= 0.75:
        return "fresh"
    if score >= 0.60:
        return "acceptable"
    if score >= 0.40:
        return "stale"
    return "outdated"


def _normalize_source_type(source_type: str) -> str:
    normalized = str(source_type or "unknown").lower().strip()
    return normalized if normalized in SOURCE_AUTHORITY else "unknown"


def _claim_notes(risk: str, best: dict[str, Any]) -> str:
    return f"Best evidence is {best['freshness_label']} with {risk} temporal risk."


def _evidence_notes(freshness_label: str, source_type: str, risk_flags: list[str]) -> str:
    if risk_flags:
        return f"{source_type} source scored as {freshness_label} with risk flags."
    return f"{source_type} source scored as {freshness_label}."


def _worst_risk(risks: Any) -> str:
    risk_list = list(risks)
    if not risk_list:
        return "unknown"
    return max(risk_list, key=lambda risk: RISK_ORDER.get(risk, 4))


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items


def _round_score(value: float) -> float:
    return round(_clamp(value), 3)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))

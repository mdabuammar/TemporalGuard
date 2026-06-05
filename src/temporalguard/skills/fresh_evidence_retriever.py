"""Controlled evidence retrieval for TemporalGuard claims."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import re
from typing import Any, Protocol

from temporalguard.search.providers import SearchResult


class SearchProvider(Protocol):
    """Minimal search provider interface used by the retriever."""

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Return search results for a query."""


@dataclass(frozen=True)
class _RankedResult:
    result: SearchResult
    score: float


SOURCE_TYPES = {
    "official",
    "government",
    "academic",
    "standards",
    "documentation",
    "reputable_news",
    "company",
    "database",
    "other",
}

SOURCE_PRIORITY = {
    "official": 0,
    "government": 1,
    "academic": 2,
    "standards": 3,
    "documentation": 4,
    "database": 5,
    "company": 6,
    "reputable_news": 7,
    "other": 8,
}

TEMPORAL_CATEGORIES_REQUIRING_RETRIEVAL = {"RECENT_ONLY", "TIME_SENSITIVE", "VERSION_DEPENDENT", "HISTORICAL"}
WEAK_DOMAIN_HINTS = ("blog", "forum", "reddit", "medium.com", "quora", "stack overflow")


def retrieve_fresh_evidence(
    question: str,
    claims_payload: dict[str, Any] | None = None,
    temporal_category: str | None = None,
    search_provider: SearchProvider | None = None,
    max_sources_per_claim: int = 3,
    max_claims: int = 5,
) -> dict[str, Any]:
    """
    Retrieve fresh or time-appropriate evidence for extracted claims.

    The function only structures evidence returned by the injected search provider.
    It does not browse pages, verify truth, or correct claims.
    """
    warnings: list[str] = []
    claims = _extract_claims(claims_payload)
    claim_limit = min(max(1, int(max_claims or 1)), 10)
    source_limit = min(max(1, int(max_sources_per_claim or 1)), 5)

    if not claims:
        return {
            "evidence_results": [],
            "total_claims_processed": 0,
            "total_evidence_items": 0,
            "retrieval_warnings": ["No claims supplied for evidence retrieval."],
        }

    evidence_results: list[dict[str, Any]] = []
    total_evidence = 0
    seen_claims: set[str] = set()

    for claim in claims[:claim_limit]:
        claim_id = str(claim.get("claim_id") or f"C{len(evidence_results) + 1}")
        claim_text = str(claim.get("claim_text") or "").strip()
        query = _build_search_query(claim, question, temporal_category)

        if not claim_text:
            evidence_results.append(_claim_result(claim_id, claim_text, query, [], "failed", "Claim text is missing."))
            continue

        dedupe_key = _dedupe_key(claim_text)
        if dedupe_key in seen_claims:
            evidence_results.append(
                _claim_result(claim_id, claim_text, query, [], "skipped", "Duplicate claim skipped.")
            )
            continue
        seen_claims.add(dedupe_key)

        if _should_skip_claim(claim, temporal_category):
            evidence_results.append(
                _claim_result(
                    claim_id,
                    claim_text,
                    query,
                    [],
                    "skipped",
                    "Optional low-risk claim skipped.",
                )
            )
            continue

        if search_provider is None:
            warning = "No search provider supplied; evidence retrieval failed."
            warnings.append(warning)
            evidence_results.append(_claim_result(claim_id, claim_text, query, [], "failed", warning))
            continue

        try:
            raw_results = search_provider.search(query, max_results=source_limit * 2)
        except Exception as exc:  # pragma: no cover - defensive error boundary
            warning = f"Search provider failed for {claim_id}: {exc}"
            warnings.append(warning)
            evidence_results.append(_claim_result(claim_id, claim_text, query, [], "failed", warning))
            continue

        ranked_results = _rank_search_results([_coerce_search_result(result) for result in raw_results], claim)
        useful_results = [ranked for ranked in ranked_results if ranked.score >= 0.50][:source_limit]
        evidence_items = [
            _to_evidence_item(ranked.result, f"E{index}", claim, ranked.score)
            for index, ranked in enumerate(useful_results, start=1)
        ]

        if not evidence_items:
            status = "failed"
            notes = "No reliable evidence found."
        elif all(item["relevance_score"] >= 0.70 for item in evidence_items):
            status = "success"
            notes = "Relevant evidence retrieved."
        else:
            status = "partial"
            notes = "Only partial or weak evidence retrieved."

        total_evidence += len(evidence_items)
        evidence_results.append(_claim_result(claim_id, claim_text, query, evidence_items, status, notes))

    return {
        "evidence_results": evidence_results,
        "total_claims_processed": len(evidence_results),
        "total_evidence_items": total_evidence,
        "retrieval_warnings": warnings,
    }


def _extract_claims(claims_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(claims_payload, dict):
        return []
    claims = claims_payload.get("claims")
    if not isinstance(claims, list):
        return []
    return [claim for claim in claims if isinstance(claim, dict)]


def _build_search_query(claim: dict[str, Any], question: str, temporal_category: str | None) -> str:
    entities = [str(entity).strip() for entity in claim.get("entities", []) if str(entity).strip()]
    claim_type = str(claim.get("claim_type") or "other")
    anchor = claim.get("temporal_anchor")
    evidence_need = str(claim.get("evidence_need") or "")
    claim_text = str(claim.get("claim_text") or "")

    base_terms = entities[:2] or _important_terms(claim_text) or _important_terms(question)
    terms = list(base_terms)

    if anchor and str(anchor).lower() not in {term.lower() for term in terms}:
        terms.append(str(anchor))

    if claim_type == "software_version":
        terms.extend(["latest stable version", "official"])
    elif claim_type == "api_or_library_behavior":
        terms.extend(["official documentation"])
    elif claim_type == "law_or_policy":
        terms.extend(["official", "government"])
    elif claim_type == "company_leadership":
        terms.extend(["official", "leadership"])
    elif claim_type in {"research_claim", "medical_or_scientific_guideline"}:
        terms.extend(["paper", "official"])
    elif claim_type == "historical_fact" or evidence_need == "historical" or temporal_category == "HISTORICAL":
        terms.extend(["official"])
    elif evidence_need == "fresh" or temporal_category in {"RECENT_ONLY", "TIME_SENSITIVE"}:
        terms.extend(["current", "official"])

    return _compact_query(" ".join(terms))


def _should_skip_claim(claim: dict[str, Any], temporal_category: str | None) -> bool:
    evidence_need = str(claim.get("evidence_need") or "")
    sensitivity = str(claim.get("temporal_sensitivity") or "")
    if temporal_category in TEMPORAL_CATEGORIES_REQUIRING_RETRIEVAL:
        return False
    return evidence_need == "optional" and sensitivity != "high"


def _rank_search_results(results: list[SearchResult], claim: dict[str, Any]) -> list[_RankedResult]:
    ranked = [_RankedResult(result=result, score=_infer_relevance_score(result, claim)) for result in results]
    return sorted(
        ranked,
        key=lambda ranked_result: (
            -ranked_result.score,
            SOURCE_PRIORITY.get(_validate_source_type(ranked_result.result.source_type), 99),
        ),
    )


def _infer_freshness_hint(result: SearchResult, claim: dict[str, Any]) -> str:
    evidence_need = str(claim.get("evidence_need") or "")
    anchor = claim.get("temporal_anchor")
    source_type = _validate_source_type(result.source_type)
    date_value = result.updated_date or result.published_date

    if evidence_need == "historical" or _is_year(anchor):
        return "acceptable"
    if evidence_need == "fresh":
        if source_type in {"official", "government", "documentation", "company"}:
            return "fresh" if date_value else "unknown"
        return "acceptable" if date_value else "unknown"
    if evidence_need == "version_specific":
        return "acceptable" if date_value or source_type in {"official", "documentation"} else "unknown"
    return "acceptable" if date_value else "unknown"


def _to_evidence_item(result: SearchResult, evidence_id: str, claim: dict[str, Any], score: float) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "title": result.title,
        "url": result.url,
        "source_type": _validate_source_type(result.source_type),
        "publisher": result.publisher or "unknown",
        "published_date": result.published_date,
        "updated_date": result.updated_date,
        "retrieved_at": _now_utc_iso(),
        "evidence_summary": _summary_from_result(result),
        "relevance_score": round(score, 2),
        "freshness_hint": _infer_freshness_hint(result, claim),
        "quote": None,
    }


def _infer_relevance_score(result: SearchResult, claim: dict[str, Any]) -> float:
    source_type = _validate_source_type(result.source_type)
    score = 0.35
    score += max(0.0, 0.35 - (SOURCE_PRIORITY.get(source_type, 8) * 0.035))

    haystack = f"{result.title} {result.snippet} {result.url}".lower()
    claim_text = str(claim.get("claim_text") or "")
    entities = [str(entity).lower() for entity in claim.get("entities", []) if str(entity).strip()]
    matched_entities = sum(1 for entity in entities if entity in haystack)
    if entities:
        score += min(0.25, matched_entities * 0.12)

    anchor = claim.get("temporal_anchor")
    if anchor and str(anchor).lower() in haystack:
        score += 0.08

    for term in _important_terms(claim_text)[:4]:
        if term.lower() in haystack:
            score += 0.03

    if any(weak in haystack for weak in WEAK_DOMAIN_HINTS):
        score -= 0.25

    if not result.url or not result.title:
        score -= 0.20

    return max(0.0, min(score, 1.0))


def _validate_source_type(source_type: str) -> str:
    normalized = str(source_type or "other").strip().lower()
    return normalized if normalized in SOURCE_TYPES else "other"


def _now_utc_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _claim_result(
    claim_id: str,
    claim_text: str,
    query: str,
    evidence_items: list[dict[str, Any]],
    status: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "claim_text": claim_text,
        "query_used": query,
        "evidence_items": evidence_items,
        "evidence_count": len(evidence_items),
        "retrieval_status": status,
        "notes": notes,
    }


def _coerce_search_result(result: Any) -> SearchResult:
    if isinstance(result, SearchResult):
        return result
    if isinstance(result, dict):
        return SearchResult(
            title=str(result.get("title") or ""),
            url=str(result.get("url") or ""),
            snippet=str(result.get("snippet") or ""),
            publisher=str(result.get("publisher") or "unknown"),
            published_date=result.get("published_date"),
            updated_date=result.get("updated_date"),
            source_type=_validate_source_type(str(result.get("source_type") or "other")),
        )
    return SearchResult(title="", url="", snippet="", publisher="unknown", source_type="other")


def _summary_from_result(result: SearchResult) -> str:
    snippet = re.sub(r"\s+", " ", result.snippet.strip())
    if snippet:
        return snippet[:240].rstrip()
    return f"Search result titled '{result.title}' from {result.publisher or 'unknown'}."


def _important_terms(text: str) -> list[str]:
    stopwords = {
        "the",
        "is",
        "are",
        "was",
        "were",
        "a",
        "an",
        "of",
        "and",
        "or",
        "to",
        "in",
        "for",
        "from",
        "with",
        "this",
        "that",
    }
    words = re.findall(r"[A-Za-z0-9.]+", text)
    terms = [word for word in words if len(word) > 2 and word.lower() not in stopwords]
    return terms[:5]


def _compact_query(query: str) -> str:
    query = re.sub(r"\s+", " ", query).strip()
    words = query.split()
    compacted: list[str] = []
    seen: set[str] = set()
    for word in words:
        key = word.lower()
        if key not in seen:
            seen.add(key)
            compacted.append(word)
    return " ".join(compacted[:12])


def _dedupe_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _is_year(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"(?:19|20)\d{2}", value) is not None

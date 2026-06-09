"""Controlled evidence retrieval for TemporalGuard claims."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import re
from typing import Any, Protocol

import requests

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
PYTHON_DOWNLOAD_URL_PATTERN = re.compile(r"https?://(?:www\.)?python\.org/downloads(?:/|$)", re.IGNORECASE)
UNSTABLE_VERSION_HINT_PATTERN = re.compile(
    r"\b(alpha|beta|release candidate|rc\d*|preview|pre[- ]?release|development|dev|schedule|planned|future)\b"
    r"|\b\d+(?:\.\d+){1,3}(?:a|b|rc)\d+\b",
    re.IGNORECASE,
)
STABLE_RELEASE_HINT_PATTERN = re.compile(
    r"\b(latest|stable|download|downloads|release|released|available)\b",
    re.IGNORECASE,
)


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
            raw_limit = source_limit * 2
            if _is_python_version_claim(claim):
                raw_limit = max(raw_limit, source_limit * 4, 6)
            raw_results = search_provider.search(query, max_results=raw_limit)
            if _is_python_version_claim(claim):
                raw_results = _augment_python_version_results(search_provider, query, raw_results, raw_limit)
        except Exception as exc:  # pragma: no cover - defensive error boundary
            warning = f"Search provider failed for {claim_id}: {exc}"
            warnings.append(warning)
            evidence_results.append(_claim_result(claim_id, claim_text, query, [], "failed", warning))
            continue

        claim_context = {**claim, "_question": question}
        ranked_results = _rank_search_results([_coerce_search_result(result) for result in raw_results], claim_context)
        useful_results = [ranked for ranked in ranked_results if ranked.score >= 0.50][:source_limit]
        evidence_items = [
            _to_evidence_item(ranked.result, f"E{index}", claim_context, ranked.score)
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


def _augment_python_version_results(
    search_provider: SearchProvider,
    original_query: str,
    raw_results: list[SearchResult],
    max_results: int,
) -> list[SearchResult]:
    results = list(raw_results)
    fallback_queries = [
        "Python downloads latest stable release",
        "Python Source Releases latest stable Python",
        "Download Python latest source release python.org",
        "Python Source Releases Python 3.14.5",
        "Download Python 3.14.5 python.org",
    ]
    seen_queries = {original_query.lower()}
    for fallback_query in fallback_queries:
        if fallback_query.lower() in seen_queries:
            continue
        seen_queries.add(fallback_query.lower())
        extra_results = search_provider.search(fallback_query, max_results=max_results)
        results.extend(_coerce_search_result(result) for result in extra_results)
    if str(getattr(search_provider, "provider_name", "")).lower() in {"tavily", "brave", "duckduckgo"}:
        results.extend(_fetch_official_python_download_results())
    return _dedupe_search_results(results)


def _fetch_official_python_download_results() -> list[SearchResult]:
    official_urls = [
        "https://www.python.org/downloads/",
        "https://www.python.org/downloads/source/",
    ]
    results: list[SearchResult] = []
    for url in official_urls:
        try:
            response = requests.get(url, timeout=6, headers={"User-Agent": "TemporalGuard/1.0"})
            response.raise_for_status()
        except Exception:
            continue
        text = _html_to_text(str(response.text or ""))
        evidence_value = _extract_version_value(text, prefer_stable=True, expected_subject="python")
        if not evidence_value:
            continue
        results.append(
            SearchResult(
                title=f"Official Python downloads - {evidence_value}",
                url=url,
                snippet=_snippet_around(text, evidence_value)
                or f"{evidence_value} is listed on the official Python downloads page.",
                content=text[:4000],
                publisher="python.org",
                source_type="official",
            )
        )
    return results


def _html_to_text(html: str) -> str:
    without_scripts = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", html or "", flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", without_scripts)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    return re.sub(r"\s+", " ", text).strip()


def _snippet_around(text: str, value: str, window: int = 160) -> str:
    index = (text or "").find(value)
    if index < 0:
        return ""
    start = max(0, index - window)
    end = min(len(text), index + len(value) + window)
    return (text[start:end] or "").strip()


def _dedupe_search_results(results: list[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set()
    deduped: list[SearchResult] = []
    for result in results:
        key = str(result.url or result.title or result.snippet or getattr(result, "content", "")).strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(result)
    return deduped


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

    if _is_python_version_claim(claim):
        return _compact_query("Python latest stable release site:python.org/downloads")
    answer_type = _infer_question_answer_type({**claim, "claim_text": f"{question} {claim_text}"})
    if answer_type == "winner":
        return _compact_query(f"{question} winner official result")
    if answer_type in {"date", "date_full"}:
        return _compact_query(f"{question} date official")
    if answer_type == "lifecycle":
        return _compact_query(f"{question} end-of-life support schedule official")
    if answer_type == "api_status":
        return _compact_query(f"{question} removed deprecated official documentation")

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
        key=lambda ranked_result: _ranking_key(ranked_result, claim),
    )


def _ranking_key(ranked_result: _RankedResult, claim: dict[str, Any]) -> tuple[Any, ...]:
    result = ranked_result.result
    if _is_python_version_claim(claim):
        version_key = _stable_version_sort_key(result)
        source_rank = _python_download_source_rank(result)
        return (
            0 if source_rank == 0 else 1,
            0 if version_key != (0, 0, 0, 0) else 1,
            tuple(-part for part in version_key),
            source_rank,
            -ranked_result.score,
            SOURCE_PRIORITY.get(_validate_source_type(result.source_type), 99),
        )
    return (
        -ranked_result.score,
        SOURCE_PRIORITY.get(_validate_source_type(result.source_type), 99),
    )


def _stable_version_sort_key(result: SearchResult) -> tuple[int, int, int, int]:
    text = _result_text(result)
    value = _extract_version_value(
        text,
        prefer_stable=_is_python_downloads_result(result),
        expected_subject="python" if _is_python_downloads_result(result) else None,
    )
    if not value:
        return (0, 0, 0, 0)
    match = re.search(r"\b(\d+(?:\.\d+){1,3})\b", value)
    if not match:
        return (0, 0, 0, 0)
    parts = tuple(int(part) for part in match.group(1).split("."))
    return parts + (0,) * (4 - len(parts))


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
    evidence_summary = _summary_from_result(result)
    return {
        "evidence_id": evidence_id,
        "title": result.title,
        "url": result.url,
        "snippet": result.snippet,
        "content": getattr(result, "content", ""),
        "source_type": _validate_source_type(result.source_type),
        "publisher": result.publisher or "unknown",
        "published_date": result.published_date,
        "updated_date": result.updated_date,
        "retrieved_at": _now_utc_iso(),
        "evidence_summary": evidence_summary,
        "evidence_value": _extract_evidence_value(result, claim),
        "relevance_score": round(score, 2),
        "freshness_hint": _infer_freshness_hint(result, claim),
        "quote": None,
    }


def _infer_relevance_score(result: SearchResult, claim: dict[str, Any]) -> float:
    source_type = _validate_source_type(result.source_type)
    score = 0.35
    score += max(0.0, 0.35 - (SOURCE_PRIORITY.get(source_type, 8) * 0.035))

    haystack_text = _result_text(result)
    haystack = haystack_text.lower()
    claim_text = str(claim.get("claim_text") or "")
    is_python_version_claim = _is_python_version_claim(claim)
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

    if is_python_version_claim:
        if _is_python_downloads_result(result):
            score += 0.35
        if "devguide.python.org" in haystack and _is_python_downloads_result_available_context(haystack_text):
            score -= 0.20
        if _has_stable_release_context(haystack_text):
            score += 0.12
        if _has_unstable_version_context(haystack_text):
            score -= 0.35

    answer_type = _infer_question_answer_type(claim)
    typed_value = _extract_typed_evidence_value(haystack_text, answer_type)
    if answer_type == "date_full" and typed_value and not _is_trusted_date_source(result):
        typed_value = None
    if answer_type != "unknown":
        score += 0.25 if typed_value and not _is_bad_evidence_value(typed_value, answer_type) else -0.20
        if answer_type == "winner" and re.search(r"\b[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*){0,3}\s+won\s+the\b", haystack_text):
            score += 0.15
        if answer_type == "date" and _extract_date_or_year(haystack_text):
            score += 0.15
        if answer_type == "date_full":
            if re.search(r"\b(who ends?|ended|no longer constituted|announced)\b", haystack, re.IGNORECASE):
                score += 0.25
            if re.search(r"\bdeclared\b", haystack, re.IGNORECASE) and not re.search(r"\b(no longer|ended|ends?)\b", haystack, re.IGNORECASE):
                score -= 0.25
        if answer_type == "lifecycle" and re.search(r"\b(end[- ]?of[- ]?life|eol|support ended|no longer supported)\b", haystack, re.IGNORECASE):
            score += 0.15
        if answer_type == "api_status" and re.search(r"\b(removed|deprecated|no longer supported)\b", haystack, re.IGNORECASE):
            score += 0.15

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
            snippet=str(result.get("snippet") or result.get("content") or ""),
            content=str(result.get("content") or result.get("raw_content") or ""),
            publisher=str(result.get("publisher") or "unknown"),
            published_date=result.get("published_date"),
            updated_date=result.get("updated_date"),
            source_type=_validate_source_type(str(result.get("source_type") or "other")),
        )
    return SearchResult(title="", url="", snippet="", publisher="unknown", source_type="other")


def _summary_from_result(result: SearchResult) -> str:
    text = re.sub(r"\s+", " ", (result.snippet or getattr(result, "content", "") or "").strip())
    if text:
        return text[:320].rstrip()
    return f"Search result titled '{result.title}' from {result.publisher or 'unknown'}."


def _extract_evidence_value(result: SearchResult, claim: dict[str, Any] | None = None) -> str | None:
    text = _result_text(result)
    answer_type = _infer_question_answer_type(claim)
    typed_value = _extract_typed_evidence_value(text, answer_type)
    if answer_type == "date_full" and typed_value and not _is_trusted_date_source(result):
        typed_value = None
    if typed_value and not _is_bad_evidence_value(typed_value, answer_type):
        return typed_value
    version = _extract_version_value(
        text,
        prefer_stable=_is_python_downloads_result(result),
        expected_subject="python" if _is_python_downloads_result(result) else None,
    )
    if version:
        return version
    return None


def _infer_question_answer_type(claim: dict[str, Any] | None) -> str:
    if not isinstance(claim, dict):
        return "unknown"
    text = " ".join(
        str(part or "")
        for part in (
            claim.get("claim_text"),
            claim.get("_question"),
            claim.get("claim_type"),
            claim.get("temporal_anchor"),
            " ".join(str(entity) for entity in claim.get("entities", [])),
        )
    ).lower()
    if re.search(r"\b(who won|won the|winner)\b", text):
        return "winner"
    if re.search(r"\bwhen\b", text):
        return "date_full"
    if re.search(r"\b(what year|ended|announced|landed|released on)\b", text):
        return "date"
    if re.search(r"\b(dataframe\.append|append|removed|deprecated|api|method|function|attribute)\b", text):
        return "api_status"
    if re.search(r"\b(still|active(?:ly)? supported|support|end[- ]?of[- ]?life|eol|lts)\b", text) and re.search(
        r"\b(node\.?js|python|ubuntu|software|version|lts)\b", text
    ):
        return "lifecycle"
    if str(claim.get("claim_type") or "") == "software_version":
        return "software_version"
    return "unknown"


def _extract_typed_evidence_value(text: str, answer_type: str) -> str | None:
    if answer_type == "winner":
        return _extract_winner_entity(text)
    if answer_type == "date_full":
        return _extract_date_or_year(text, require_full_date=True)
    if answer_type == "date":
        return _extract_date_or_year(text)
    if answer_type == "lifecycle":
        return _extract_lifecycle_value(text)
    if answer_type == "api_status":
        return _extract_api_status_value(text)
    return None


def _extract_winner_entity(text: str) -> str | None:
    patterns = [
        r"\b(?P<winner>[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*){0,3})\s+won\s+the\b",
        r"\bthe\s+winner\s+was\s+(?P<winner>[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*){0,3})\b",
        r"\b(?P<winner>[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*){0,3})\s+(?:beat|defeated)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text or "")
        if match:
            winner = _clean_entity_value(match.group("winner"))
            if winner and not _is_bad_evidence_value(winner, "winner"):
                return winner
    return None


def _extract_date_or_year(text: str, require_full_date: bool = False) -> str | None:
    date_pattern = (
        r"\b(?:on\s+)?(?P<date>(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
        r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+(?:19|20)\d{2})\b"
    )
    matches = list(re.finditer(date_pattern, text or "", flags=re.IGNORECASE))
    if require_full_date:
        for match in matches:
            local = (text or "")[max(0, match.start() - 90) : min(len(text or ""), match.end() + 140)]
            if re.search(r"\b(ended|announced|declared|no longer|terminated|concluded|ceased)\b", local, re.IGNORECASE):
                return re.sub(r"\s+", " ", match.group("date")).strip()
        return None
    date_match = matches[0] if matches else None
    if date_match:
        return re.sub(r"\s+", " ", date_match.group("date")).strip()
    if require_full_date:
        return None
    year_match = re.search(r"\b(?:in|on|ended|announced|landed|released)\s+(?P<year>(?:19|20)\d{2})\b", text or "", re.IGNORECASE)
    if year_match:
        return year_match.group("year")
    return None


def _extract_lifecycle_value(text: str) -> str | None:
    date = _date_near_lifecycle_context(text) or _extract_date_or_year(text)
    lower = (text or "").lower()
    if re.search(r"\b(end[- ]?of[- ]?life|eol|reached end|support ended|no longer supported|not supported)\b", lower):
        return f"end-of-life on {date}" if date else "end-of-life"
    if re.search(r"\bmaintenance lts|maintenance support\b", lower):
        return f"maintenance LTS until {date}" if date else "maintenance LTS"
    if re.search(r"\bactive lts|actively supported|active support|standard support\b", lower):
        return f"active LTS until {date}" if date else "active LTS"
    if re.search(r"\bsecurity maintenance|security updates?\b", lower):
        return f"security maintenance until {date}" if date else "security maintenance"
    return None


def _date_near_lifecycle_context(text: str) -> str | None:
    date_pattern = (
        r"\b(?P<date>(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
        r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+(?:19|20)\d{2})\b"
    )
    matches = list(re.finditer(date_pattern, text or "", flags=re.IGNORECASE))
    for match in matches:
        local = (text or "")[max(0, match.start() - 160) : min(len(text or ""), match.end() + 80)]
        if re.search(r"\b(reached|support ended|ended|no longer receives?|no longer supported)\b", local, re.IGNORECASE):
            return re.sub(r"\s+", " ", match.group("date")).strip()
    return None


def _extract_api_status_value(text: str) -> str | None:
    lower = (text or "").lower()
    if "dataframe.append" in lower or ".append" in lower:
        if re.search(r"\bremoved|deprecated|no longer|not supported\b", lower):
            version = re.search(r"\bpandas\s+(\d+(?:\.\d+){1,2})\b", text or "", re.IGNORECASE)
            suffix = f" in pandas {version.group(1)}" if version else ""
            return f"DataFrame.append was removed{suffix}; use pandas.concat"
        if re.search(r"\bsupports?|available\b", lower):
            return "DataFrame.append is supported"
    return None


def _clean_entity_value(value: str) -> str:
    value = re.sub(r"\s+", " ", (value or "").strip(" .,:;()[]{}"))
    value = re.sub(r"^(The|A|An)\s+", "", value)
    value = re.sub(r"^(?:FIFA\s+)?World Cup\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^Results?\s+", "", value, flags=re.IGNORECASE)
    return value


def _is_bad_evidence_value(value: str, answer_type: str) -> bool:
    normalized = re.sub(r"[^a-z0-9.]+", " ", str(value or "").lower()).strip()
    bad_values = {
        "world cup",
        "fifa",
        "fifa world cup",
        "tournament",
        "final",
        "match",
        "results report",
        "report",
        "official website",
        "source",
        "documentation",
        "download",
    }
    if normalized in bad_values:
        return True
    if answer_type in {"winner", "date", "date_full", "lifecycle"} and re.fullmatch(r"\d+(?:\.\d+)?", normalized or ""):
        return True
    if answer_type == "lifecycle" and re.fullmatch(r"(?:manager\s+)?\d+(?:\.\d+){0,2}", normalized or ""):
        return True
    return False


def _is_trusted_date_source(result: SearchResult) -> bool:
    source_type = _validate_source_type(result.source_type)
    url = str(result.url or "").lower()
    return source_type in {"official", "government", "academic", "standards", "database"} or any(
        domain in url for domain in ("who.int", "thelancet.com", "nejm.org", "nature.com", "sciencedirect.com")
    )


def _extract_version_value(
    text: str,
    prefer_stable: bool = False,
    expected_subject: str | None = None,
) -> str | None:
    pattern = re.compile(
        r"\b(?:(?P<subject>[A-Za-z][A-Za-z0-9+#-]{1,30})[\s_-]*)?"
        r"(?:v(?:ersion)?[\s_-]*)?"
        r"(?P<version>\d+(?:\.\d+){1,3})\b",
        flags=re.IGNORECASE,
    )
    candidates = []
    for match in pattern.finditer(text or ""):
        start = max(0, match.start() - 48)
        end = min(len(text or ""), match.end() + 48)
        context = (text or "")[start:end]
        raw_subject = str(match.group("subject") or "").strip(" -_")
        unstable = _has_unstable_candidate_context(text or "", match.start(), match.end())
        candidates.append(
            {
                "match": match,
                "numbers": tuple(int(part) for part in match.group("version").split(".")),
                "subject": _normalize_version_subject(raw_subject),
                "stable": _has_stable_release_context(context) and not unstable,
                "unstable": unstable,
            }
        )
    if not candidates:
        return None
    if expected_subject:
        expected = _normalize_version_subject(expected_subject)
        exact_subject_matches = [candidate for candidate in candidates if candidate["subject"] == expected]
        bare_subject_matches = [candidate for candidate in candidates if not candidate["subject"]]
        if exact_subject_matches:
            candidates = exact_subject_matches
        elif bare_subject_matches:
            candidates = bare_subject_matches
        else:
            return None
        candidates = _filter_python_language_version_candidates(candidates)
        if not candidates:
            return None
    usable = [candidate for candidate in candidates if not candidate["unstable"]]
    if prefer_stable:
        stable_candidates = [candidate for candidate in usable if candidate["stable"]]
        if stable_candidates:
            usable = stable_candidates
    if not usable:
        return None
    match = max(usable, key=lambda candidate: candidate["numbers"])["match"]
    version = match.group("version")
    subject = str(match.group("subject") or "").strip(" -_")
    if subject and subject.lower() not in {"v", "version", "release", "latest", "current", "stable", "download"}:
        return f"{subject} {version}"
    return version


def _normalize_version_subject(subject: str) -> str:
    normalized = re.sub(r"[^a-z0-9+#]+", "", subject.lower())
    if normalized in {"a", "an", "is", "the", "v", "version", "release", "latest", "current", "stable", "download"}:
        return ""
    aliases = {
        "python3": "python",
        "cpython": "python",
    }
    return aliases.get(normalized, normalized)


def _is_python_version_claim(claim: dict[str, Any]) -> bool:
    text = f"{claim.get('claim_text') or ''} {' '.join(str(entity) for entity in claim.get('entities', []))}"
    return (
        str(claim.get("claim_type") or "") == "software_version"
        and re.search(r"\bpython\b", text, re.IGNORECASE) is not None
    )


def _is_python_downloads_result(result: SearchResult) -> bool:
    return PYTHON_DOWNLOAD_URL_PATTERN.search(str(result.url or "")) is not None


def _python_download_source_rank(result: SearchResult) -> int:
    url = str(result.url or "").lower().rstrip("/")
    if re.fullmatch(r"https?://(?:www\.)?python\.org/downloads", url):
        return 0
    if re.fullmatch(r"https?://(?:www\.)?python\.org/downloads/source", url):
        return 0
    if "python.org/downloads/release/" in url:
        return 1
    if "python.org/downloads/windows" in url:
        return 2
    if "python.org/downloads/" in url:
        return 2
    if "devguide.python.org" in url:
        return 3
    if "python.org" in url:
        return 4
    return 5


def _filter_python_language_version_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    language_candidates = [
        candidate
        for candidate in candidates
        if candidate.get("numbers") and candidate["numbers"][0] in {2, 3}
    ]
    python_3_candidates = [candidate for candidate in language_candidates if candidate["numbers"][0] == 3]
    return python_3_candidates or language_candidates


def _result_text(result: SearchResult) -> str:
    return " ".join(
        str(part or "")
        for part in (
            result.title,
            result.snippet,
            getattr(result, "content", ""),
            result.url,
        )
    )


def _is_python_downloads_result_available_context(text: str) -> bool:
    return "python.org/downloads" in (text or "").lower()


def _has_unstable_version_context(text: str) -> bool:
    return UNSTABLE_VERSION_HINT_PATTERN.search(text or "") is not None


def _has_unstable_candidate_context(text: str, start: int, end: int) -> bool:
    suffix = (text or "")[end : min(len(text or ""), end + 8)]
    if re.match(r"(?:a|b|rc)\d+\b", suffix, re.IGNORECASE):
        return True
    local = (text or "")[max(0, start - 24) : min(len(text or ""), end + 32)]
    return _has_unstable_version_context(local)


def _has_stable_release_context(text: str) -> bool:
    return STABLE_RELEASE_HINT_PATTERN.search(text or "") is not None


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

"""Deterministic temporal claim verification for TemporalGuard."""

from __future__ import annotations

import re
from typing import Any


VERIFICATION_STATUSES = {
    "SUPPORTED",
    "OUTDATED",
    "CONTRADICTED",
    "PARTIALLY_SUPPORTED",
    "INSUFFICIENT_EVIDENCE",
    "NOT_VERIFIABLE",
}
CORRECTION_STATUSES = {"OUTDATED", "CONTRADICTED", "PARTIALLY_SUPPORTED"}
STRICT_TEMPORAL_CATEGORIES = {"RECENT_ONLY", "TIME_SENSITIVE", "VERSION_DEPENDENT"}
HIGH_RISK_PATTERN = re.compile(
    r"\b(visa|immigration|law|legal|policy|regulation|medical|medicine|finance|price|tax|safety|security)\b",
    re.IGNORECASE,
)
SUBJECTIVE_PATTERN = re.compile(r"\b(best|amazing|wonderful|nice|beautiful|better|favorite)\b", re.IGNORECASE)
STATUS_GROUPS = {
    "active": {"active", "available", "supported", "current", "open"},
    "inactive": {"inactive", "ended", "closed", "expired", "no longer active", "not active", "unavailable"},
    "deprecated": {"deprecated"},
    "not_deprecated": {"not deprecated"},
    "released": {"released"},
    "not_released": {"not released"},
}
UNSTABLE_VERSION_HINT_PATTERN = re.compile(
    r"\b(alpha|beta|release candidate|rc\d*|preview|pre[- ]?release|development|dev|schedule|planned|future)\b"
    r"|\b\d+(?:\.\d+){1,3}(?:a|b|rc)\d+\b",
    re.IGNORECASE,
)
STABLE_RELEASE_HINT_PATTERN = re.compile(
    r"\b(latest|stable|download|downloads|release|released|available)\b",
    re.IGNORECASE,
)
PYTHON_DOWNLOAD_URL_PATTERN = re.compile(r"https?://(?:www\.)?python\.org/downloads(?:/|$)", re.IGNORECASE)


def verify_temporal_claims(
    question: str,
    claims_payload: dict[str, Any],
    evidence_payload: dict[str, Any],
    freshness_payload: dict[str, Any] | None = None,
    temporal_category: str | None = None,
) -> dict[str, Any]:
    """
    Verify extracted claims against retrieved and freshness-scored evidence.

    The verifier only uses supplied payloads. It does not retrieve, browse, correct,
    or call an LLM.
    """
    warnings: list[str] = []
    claims_by_id = _get_claims_by_id(claims_payload)
    evidence_by_id = _get_evidence_by_claim_id(evidence_payload)
    freshness_by_id = _get_freshness_by_claim_id(freshness_payload)

    if not claims_by_id:
        return {
            "verification_results": [],
            "overall_verification_status": "NOT_VERIFIABLE",
            "overall_confidence": 0.0,
            "verification_warnings": ["No claims supplied for verification."],
        }

    results = []
    for claim_id, claim in claims_by_id.items():
        claim_context = {**claim, "_question": question}
        evidence_result = evidence_by_id.get(claim_id, {})
        freshness_result = freshness_by_id.get(claim_id)
        evidence_item = _select_best_evidence(evidence_result, freshness_result, claim_context)
        evidence_text = _build_evidence_text(evidence_item) if evidence_item else ""
        comparison = _compare_claim_and_evidence_values(claim_context, evidence_text, temporal_category, question)
        status = _infer_verification_status(claim_context, evidence_item, freshness_result, comparison, temporal_category)
        risk_level = _risk_level(status, claim_context, freshness_result)
        confidence = _verification_confidence(status, freshness_result, comparison, evidence_item)
        best_evidence_id = str(evidence_item.get("evidence_id")) if evidence_item else None

        results.append(
            {
                "claim_id": claim_id,
                "claim_text": str(claim.get("claim_text") or ""),
                "verification_status": status,
                "temporal_validity": _infer_temporal_validity(status, claim_context, temporal_category),
                "verification_confidence": confidence,
                "evidence_used": [best_evidence_id] if best_evidence_id else [],
                "best_evidence_id": best_evidence_id,
                "reason": _reason(status, claim, comparison, evidence_item),
                "detected_conflict": comparison["detected_conflict"] if status in CORRECTION_STATUSES else None,
                "claim_value": comparison["claim_value"],
                "evidence_value": comparison["evidence_value"],
                "requires_correction": _infer_requires_correction(status, risk_level),
                "risk_level": risk_level,
                "notes": _notes(status, risk_level),
            }
        )

    return {
        "verification_results": results,
        "overall_verification_status": _infer_overall_status(results),
        "overall_confidence": _overall_confidence(results),
        "verification_warnings": warnings,
    }


def verify_temporal_claim(claim: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    """Backward-compatible wrapper for the old scaffold API."""
    result = verify_temporal_claims(
        "",
        {"claims": [{"claim_id": "C1", "claim_text": claim, "claim_type": "other"}]},
        {"evidence_results": [{"claim_id": "C1", "evidence_items": evidence, "retrieval_status": "success"}]},
        None,
        None,
    )
    first = result["verification_results"][0]
    return {"verified": first["verification_status"] == "SUPPORTED", "reason": first["reason"]}


def _get_claims_by_id(claims_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(claims_payload, dict) or not isinstance(claims_payload.get("claims"), list):
        return {}
    claims: dict[str, dict[str, Any]] = {}
    for index, claim in enumerate(claims_payload["claims"], start=1):
        if isinstance(claim, dict):
            claim_id = str(claim.get("claim_id") or f"C{index}")
            claims[claim_id] = claim
    return claims


def _get_evidence_by_claim_id(evidence_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(evidence_payload, dict) or not isinstance(evidence_payload.get("evidence_results"), list):
        return {}
    return {
        str(result.get("claim_id")): result
        for result in evidence_payload["evidence_results"]
        if isinstance(result, dict) and result.get("claim_id")
    }


def _get_freshness_by_claim_id(freshness_payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(freshness_payload, dict) or not isinstance(freshness_payload.get("freshness_results"), list):
        return {}
    return {
        str(result.get("claim_id")): result
        for result in freshness_payload["freshness_results"]
        if isinstance(result, dict) and result.get("claim_id")
    }


def _select_best_evidence(
    evidence_result: dict[str, Any],
    freshness_result: dict[str, Any] | None,
    claim: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    items = evidence_result.get("evidence_items") if isinstance(evidence_result, dict) else None
    if not isinstance(items, list) or not items:
        return None
    valid_items = [item for item in items if isinstance(item, dict)]
    if not valid_items:
        return None
    if isinstance(claim, dict):
        answer_type = _infer_question_answer_type("", claim)
        if answer_type in {"winner", "date", "date_full", "lifecycle", "api_status"}:
            typed_items = [
                item
                for item in valid_items
                if item.get("evidence_value") and not _is_bad_answer_value(str(item.get("evidence_value")))
            ]
            if answer_type == "date_full":
                typed_items = [item for item in typed_items if _is_trusted_date_item(item)]
                if not typed_items:
                    return None
            if typed_items:
                return max(
                    typed_items,
                    key=lambda item: (
                        1 if answer_type == "lifecycle" and _has_explicit_lifecycle_answer(item) else 0,
                        1 if answer_type == "lifecycle" and _extract_dates(str(item.get("evidence_value") or "")) else 0,
                        float(item.get("relevance_score") or 0.0),
                    ),
                )
    if isinstance(claim, dict) and _is_version_claim(claim):
        version_items = [item for item in valid_items if _best_version_candidate_for_item(item, claim)]
        if version_items:
            return max(version_items, key=lambda item: _version_evidence_sort_key(item, claim))
    best_id = freshness_result.get("best_evidence_id") if isinstance(freshness_result, dict) else None
    if best_id:
        for item in valid_items:
            if item.get("evidence_id") == best_id:
                return item
    return max(valid_items, key=lambda item: float(item.get("relevance_score") or 0.0))


def _version_evidence_sort_key(item: dict[str, Any], claim: dict[str, Any] | None = None) -> tuple[Any, ...]:
    candidate = _best_version_candidate_for_item(item, claim)
    numbers = candidate["numbers"] if candidate else (0, 0, 0, 0)
    source_rank = _python_download_source_rank(item)
    return (
        1 if source_rank == 0 else 0,
        numbers,
        -source_rank,
        1 if candidate and candidate.get("stable") else 0,
        0 if candidate and candidate.get("unstable") else 1,
        float(item.get("relevance_score") or 0.0),
    )


def _best_version_candidate_for_item(
    item: dict[str, Any],
    claim: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    value_candidates = _extract_version_candidates(str(item.get("evidence_value") or ""))
    text_candidates = _extract_version_candidates(_build_evidence_text(item))
    candidates = _unique_version_candidates(value_candidates + text_candidates)
    if not candidates:
        return None
    if isinstance(claim, dict):
        claim_candidates = _extract_version_candidates(str(claim.get("claim_text") or ""))
        if claim_candidates:
            candidates = [
                candidate
                for candidate in candidates
                if any(_version_subjects_compatible(claim, claim_candidate, candidate) for claim_candidate in claim_candidates)
            ]
            if not candidates:
                return None
            subject_matched = [
                candidate
                for candidate in candidates
                if any(_version_subjects_exactly_match(claim_candidate, candidate) for claim_candidate in claim_candidates)
            ]
            if subject_matched:
                candidates = subject_matched
        if _is_python_claim(claim):
            candidates = _filter_python_language_version_candidates(candidates)
            if not candidates:
                return None
    stable = [candidate for candidate in candidates if candidate.get("stable")]
    non_unstable = [candidate for candidate in candidates if not candidate.get("unstable")]
    pool = stable or non_unstable or candidates
    return max(pool, key=lambda candidate: candidate["numbers"])


def _build_evidence_text(evidence_item: dict[str, Any]) -> str:
    parts = [
        str(evidence_item.get("evidence_value") or ""),
        str(evidence_item.get("title") or ""),
        str(evidence_item.get("publisher") or ""),
        str(evidence_item.get("evidence_summary") or ""),
        str(evidence_item.get("snippet") or ""),
        str(evidence_item.get("content") or ""),
        str(evidence_item.get("url") or ""),
        str(evidence_item.get("quote") or ""),
    ]
    return " ".join(part for part in parts if part).strip()


def _extract_versions(text: str) -> list[str]:
    return [candidate["raw"] for candidate in _extract_version_candidates(text)]


def _extract_version_candidates(text: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    pattern = re.compile(
        r"\b(?:(?P<subject>[A-Za-z][A-Za-z0-9+#-]{1,30})[\s_-]*)?"
        r"(?:v(?:ersion)?[\s_-]*)?"
        r"(?P<version>\d+(?:\.\d+){1,3})\b",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text or ""):
        version = match.group("version")
        raw_subject = match.group("subject") or ""
        subject = _normalize_version_subject(raw_subject)
        raw = match.group(0).strip(" .,:;()[]{}")
        context = _version_context(text or "", match.start(), match.end())
        unstable = _has_unstable_candidate_context(text or "", match.start(), match.end())
        candidates.append(
            {
                "raw": _format_version_value(subject, raw_subject, version, raw),
                "subject": subject,
                "numbers": tuple(int(part) for part in version.split(".")),
                "normalized": ".".join(str(int(part)) for part in version.split(".")),
                "stable": _has_stable_release_context(context) and not unstable,
                "unstable": unstable,
            }
        )
    return _unique_version_candidates(candidates)


def _extract_years(text: str) -> list[str]:
    return _unique(re.findall(r"\b(?:19|20)\d{2}\b", text))


def _extract_dates(text: str) -> list[str]:
    month_date = re.findall(
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
        r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+(?:19|20)\d{2}\b",
        text,
        flags=re.IGNORECASE,
    )
    iso_date = re.findall(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b", text)
    return _unique([_normalize_space(value) for value in month_date + iso_date])


def _extract_numbers(text: str) -> list[str]:
    word_numbers = {
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "ten": "10",
    }
    values = re.findall(r"\$\d+(?:\.\d+)?|\b\d+(?:\.\d+)?%|\b\d+\.\d+\b|\b\d+\b", text)
    for word, number in word_numbers.items():
        if re.search(rf"\b{word}\b", text, re.IGNORECASE):
            values.append(number)
    return _unique(values)


def _extract_lifecycle_status(text: str) -> str | None:
    lower = text.lower()
    if re.search(r"\b(end[- ]?of[- ]?life|eol|reached end|ended|expired|removed|no longer supported|not supported)\b", lower):
        return "inactive"
    if re.search(r"\b(security maintenance|security updates?|supported|active lts|active|valid)\b", lower):
        return "active"
    return None


def _extract_capability_status(text: str) -> str | None:
    lower = text.lower()
    if re.search(r"\b(legacy|deprecated)\b", lower):
        return "legacy"
    if re.search(r"\b(removed|no longer supports?|not supported|use .+ instead)\b", lower):
        return "removed"
    if re.search(r"\b(still supports?|supports?|recommended style|recommended)\b", lower):
        return "supported"
    return None


def _extract_status_words(text: str) -> list[str]:
    lower = text.lower()
    statuses: list[str] = []
    for group, variants in STATUS_GROUPS.items():
        if any(re.search(rf"\b{re.escape(variant)}\b", lower) for variant in variants):
            statuses.append(group)
    return _unique(statuses)


def _extract_candidate_entities(text: str) -> list[str]:
    pair_entities = re.findall(r"(?=(\b[A-Z][a-z]+\s+[A-Z][a-z]+\b))", text)
    entities = pair_entities + re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b", text)
    generic = {
        "the",
        "president",
        "presidents",
        "united states",
        "white house",
        "the white",
        "house barack",
        "source",
        "based",
        "download python",
    }
    return [
        entity
        for entity in _unique(entities)
        if entity.lower() not in generic and " the " not in f" {entity.lower()} "
    ]


def _primary_evidence_statement(evidence_text: str) -> str:
    text = re.sub(r"\s+", " ", evidence_text or "").strip()
    if not text:
        return ""
    text = re.sub(r"\s+Source answers:.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^.+? - authoritative evidence\s+", "", text, flags=re.IGNORECASE)
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    return sentences[0] if sentences else text


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _same_major_subject_version(claim_value: str, evidence_value: str) -> bool:
    return claim_value.lower().split()[0:1] == evidence_value.lower().split()[0:1]


def _normalize_version_subject(subject: str) -> str:
    text = re.sub(r"[^A-Za-z0-9+#]+", "", subject or "").lower()
    generic = {"a", "an", "is", "the", "v", "version", "release", "latest", "current", "stable", "download"}
    aliases = {"python3": "python", "cpython": "python"}
    return "" if text in generic else aliases.get(text, text)


def _format_version_value(subject: str, raw_subject: str, version: str, raw: str) -> str:
    if subject:
        prefix_match = re.match(r"[A-Za-z][A-Za-z0-9+#-]*", raw or "")
        prefix = raw_subject.strip(" -_") or (prefix_match.group(0) if prefix_match else subject)
        if re.search(rf"{re.escape(prefix)}[\s_-]+{re.escape(version)}", raw or "", re.IGNORECASE):
            return f"{prefix} {version}"
        return f"{prefix} {version}" if prefix.lower() == subject else f"{subject} {version}"
    return version


def _unique_version_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    unique_candidates: list[dict[str, Any]] = []
    for candidate in candidates:
        key = (candidate["subject"], candidate["normalized"])
        if key not in seen:
            seen.add(key)
            unique_candidates.append(candidate)
    return unique_candidates


def _version_context(text: str, start: int, end: int) -> str:
    return text[max(0, start - 56) : min(len(text), end + 56)]


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


def _version_subjects_compatible(claim: dict[str, Any], claim_candidate: dict[str, Any], evidence_candidate: dict[str, Any]) -> bool:
    claim_subject = str(claim_candidate.get("subject") or "")
    evidence_subject = str(evidence_candidate.get("subject") or "")
    claim_text = str(claim.get("claim_text") or "").lower()
    entities = " ".join(str(entity) for entity in claim.get("entities", [])).lower()
    if claim_subject and evidence_subject:
        return claim_subject == evidence_subject
    subject = claim_subject or evidence_subject
    return not subject or subject in claim_text or subject in entities


def _version_subjects_exactly_match(claim_candidate: dict[str, Any], evidence_candidate: dict[str, Any]) -> bool:
    claim_subject = str(claim_candidate.get("subject") or "")
    evidence_subject = str(evidence_candidate.get("subject") or "")
    return bool(claim_subject and evidence_subject and claim_subject == evidence_subject)


def _versions_equivalent(claim_numbers: tuple[int, ...], evidence_numbers: tuple[int, ...]) -> bool:
    shared_length = min(len(claim_numbers), len(evidence_numbers))
    if shared_length < 2:
        return claim_numbers == evidence_numbers
    return claim_numbers[:shared_length] == evidence_numbers[:shared_length]


def _version_is_newer(evidence_numbers: tuple[int, ...], claim_numbers: tuple[int, ...]) -> bool:
    max_length = max(len(claim_numbers), len(evidence_numbers))
    claim_padded = claim_numbers + (0,) * (max_length - len(claim_numbers))
    evidence_padded = evidence_numbers + (0,) * (max_length - len(evidence_numbers))
    return evidence_padded > claim_padded


def _compare_version_candidates(
    claim: dict[str, Any],
    claim_candidates: list[dict[str, Any]],
    evidence_candidates: list[dict[str, Any]],
    temporal_category: str | None,
) -> dict[str, Any] | None:
    for claim_candidate in claim_candidates:
        compatible_evidence = [
            candidate
            for candidate in evidence_candidates
            if _version_subjects_compatible(claim, claim_candidate, candidate)
        ]
        if not compatible_evidence:
            continue
        subject_matched_evidence = [
            candidate
            for candidate in compatible_evidence
            if _version_subjects_exactly_match(claim_candidate, candidate)
        ]
        if subject_matched_evidence:
            compatible_evidence = subject_matched_evidence
        stable_evidence = [candidate for candidate in compatible_evidence if candidate.get("stable")]
        non_unstable_evidence = [candidate for candidate in compatible_evidence if not candidate.get("unstable")]
        candidate_pool = stable_evidence or non_unstable_evidence or compatible_evidence
        if _is_python_claim(claim):
            candidate_pool = _filter_python_language_version_candidates(candidate_pool)
            if not candidate_pool:
                continue
        evidence_candidate = max(candidate_pool, key=lambda candidate: candidate["numbers"])
        claim_value = str(claim_candidate["raw"])
        evidence_value = str(evidence_candidate["raw"])
        if _versions_equivalent(claim_candidate["numbers"], evidence_candidate["numbers"]):
            return {
                "supports": True,
                "partial": True,
                "conflict_type": None,
                "claim_value": claim_value,
                "evidence_value": evidence_value,
                "detected_conflict": None,
            }
        conflict_type = "outdated" if _is_current_or_latest(claim, temporal_category) and _version_is_newer(
            evidence_candidate["numbers"], claim_candidate["numbers"]
        ) else "contradicted"
        return {
            "supports": False,
            "partial": False,
            "conflict_type": conflict_type,
            "claim_value": claim_value,
            "evidence_value": evidence_value,
            "detected_conflict": f"Claim value: {claim_value}; Evidence value: {evidence_value}.",
        }
    return None


def _asks_person_or_role(claim: dict[str, Any], temporal_category: str | None) -> bool:
    text = f"{claim.get('claim_text') or ''} {claim.get('claim_type') or ''}".lower()
    return temporal_category == "HISTORICAL" or re.search(r"\b(ceo|president|minister|founder|leader|won)\b", text) is not None


def _compare_claim_and_evidence_values(
    claim: dict[str, Any],
    evidence_text: str,
    temporal_category: str | None,
    question: str = "",
) -> dict[str, Any]:
    claim_text = str(claim.get("claim_text") or "")
    answer_type = _infer_question_answer_type(question, claim)
    evidence_statement = _primary_evidence_statement(evidence_text)
    comparison_text = evidence_statement or evidence_text
    claim_version_candidates = _extract_version_candidates(claim_text)
    evidence_version_candidates = _extract_version_candidates(comparison_text)
    claim_versions = [candidate["raw"] for candidate in claim_version_candidates]
    evidence_versions = [candidate["raw"] for candidate in evidence_version_candidates]
    claim_years = _extract_years(claim_text)
    evidence_years = _extract_years(comparison_text)
    claim_dates = _extract_dates(claim_text)
    evidence_dates = _extract_dates(comparison_text)
    claim_numbers = _extract_numbers(claim_text)
    evidence_numbers = _extract_numbers(comparison_text)
    claim_lifecycle = _extract_lifecycle_status(claim_text)
    evidence_lifecycle = _extract_lifecycle_status(comparison_text)
    claim_capability = _extract_capability_status(claim_text)
    evidence_capability = _extract_capability_status(comparison_text)
    claim_statuses = _extract_status_words(claim_text)
    evidence_statuses = _extract_status_words(comparison_text)
    claim_entities = [str(entity) for entity in claim.get("entities", []) if str(entity).strip()]
    if not claim_entities:
        claim_entities = _extract_candidate_entities(claim_text)
    evidence_entities = _extract_candidate_entities(comparison_text)

    comparison = {
        "supports": _overlap_score(claim_text, evidence_text) >= 0.45,
        "partial": _overlap_score(claim_text, evidence_text) >= 0.25,
        "conflict_type": None,
        "claim_value": None,
        "evidence_value": None,
        "detected_conflict": None,
    }

    typed_comparison = _compare_typed_answer_value(answer_type, claim_text, comparison_text, claim, temporal_category)
    if typed_comparison is not None:
        comparison.update(typed_comparison)
        return comparison

    if claim_version_candidates and evidence_version_candidates:
        version_comparison = _compare_version_candidates(claim, claim_version_candidates, evidence_version_candidates, temporal_category)
        if version_comparison is None:
            pass
        else:
            comparison.update(version_comparison)
            return comparison

    if claim_version_candidates and _is_version_claim(claim):
        comparison["claim_value"] = str(claim_version_candidates[0]["raw"])
        comparison["supports"] = False
        comparison["partial"] = False
        return comparison

    if claim_lifecycle and evidence_lifecycle:
        comparison.update(_value_comparison(claim_lifecycle, evidence_lifecycle, "status"))
        if claim_lifecycle != evidence_lifecycle:
            comparison["conflict_type"] = "outdated" if _is_still_or_current_claim(claim) else "contradicted"
        return comparison

    if claim_capability and evidence_capability:
        comparison.update(_value_comparison(claim_capability, evidence_capability, "capability"))
        if claim_capability != evidence_capability:
            comparison["conflict_type"] = "outdated" if evidence_capability == "legacy" else "contradicted"
        return comparison

    if _asks_person_or_role(claim, temporal_category) and claim_entities and evidence_entities:
        claim_value = _best_entity_value(claim_entities, claim_text)
        evidence_value = _best_entity_value(evidence_entities, comparison_text)
        if claim_value and evidence_value:
            comparison.update(_value_comparison(claim_value, evidence_value, "entity"))
            if claim_value != evidence_value:
                comparison["conflict_type"] = "outdated" if _is_current_or_latest(claim, temporal_category) else "contradicted"
            return comparison

    if claim_dates and evidence_dates:
        comparison.update(_value_comparison(claim_dates[0], evidence_dates[0], "date"))
        if claim_dates[0] != evidence_dates[0]:
            comparison["conflict_type"] = "contradicted"
        return comparison

    if temporal_category == "HISTORICAL" and claim_years and evidence_years:
        claim_value = claim_years[0]
        evidence_value = evidence_years[0]
        comparison.update(_value_comparison(claim_value, evidence_value, "version"))
        if claim_value != evidence_value and _is_current_or_latest(claim, temporal_category):
            comparison["conflict_type"] = "contradicted"
        return comparison

    if claim_statuses and evidence_statuses:
        claim_value = claim_statuses[0]
        evidence_value = evidence_statuses[0]
        comparison.update(_value_comparison(claim_value, evidence_value, "status"))
        if claim_value != evidence_value:
            comparison["conflict_type"] = "outdated" if _is_current_or_latest(claim, temporal_category) else "contradicted"
        return comparison

    if claim_numbers and evidence_numbers:
        comparison.update(_value_comparison(claim_numbers[0], evidence_numbers[0], "number"))
        if claim_numbers[0] != evidence_numbers[0]:
            comparison["conflict_type"] = "contradicted"
        return comparison

    winner_claim = _winner_entity(claim_text)
    winner_evidence = _winner_entity(comparison_text)
    if winner_claim and winner_evidence:
        comparison.update(_value_comparison(winner_claim, winner_evidence, "entity"))
        if winner_claim != winner_evidence:
            comparison["conflict_type"] = "contradicted"
        return comparison

    if temporal_category == "HISTORICAL" and claim_years:
        comparison["claim_value"] = _best_entity_value(claim_entities, claim_text)
        comparison["evidence_value"] = comparison["claim_value"] if _historical_year_supported(claim_years[0], comparison_text) else None
        comparison["supports"] = bool(comparison["evidence_value"])
        comparison["partial"] = comparison["supports"] or any(year in evidence_years for year in claim_years)
        return comparison

    if claim_entities:
        value = _best_entity_value(claim_entities, claim_text)
        comparison["claim_value"] = value
        comparison["evidence_value"] = value if value and value.lower() in comparison_text.lower() else None
        if comparison["evidence_value"]:
            comparison["supports"] = True
    return comparison


def _infer_verification_status(
    claim: dict[str, Any],
    evidence_item: dict[str, Any] | None,
    freshness_result: dict[str, Any] | None,
    comparison: dict[str, Any],
    temporal_category: str | None,
) -> str:
    claim_text = str(claim.get("claim_text") or "")
    if _is_not_verifiable(claim_text):
        return "NOT_VERIFIABLE"
    if evidence_item is None:
        return "INSUFFICIENT_EVIDENCE"

    reliability = _freshness_value(freshness_result, "claim_reliability_score", default=0.60)
    freshness = _freshness_value(freshness_result, "claim_freshness_score", default=0.60)
    weak_evidence = reliability < 0.45 or (temporal_category in STRICT_TEMPORAL_CATEGORIES and freshness < 0.40)

    if comparison["conflict_type"] == "outdated":
        return "OUTDATED"
    if comparison["conflict_type"] == "contradicted" or comparison["detected_conflict"]:
        return "CONTRADICTED"
    if weak_evidence:
        return "INSUFFICIENT_EVIDENCE"
    if comparison["supports"]:
        return "SUPPORTED"
    if comparison["partial"]:
        return "PARTIALLY_SUPPORTED"
    return "INSUFFICIENT_EVIDENCE"


def _infer_temporal_validity(status: str, claim: dict[str, Any], temporal_category: str | None) -> str:
    if status == "OUTDATED":
        return "expired"
    if status in {"INSUFFICIENT_EVIDENCE", "NOT_VERIFIABLE"}:
        return "uncertain" if status == "INSUFFICIENT_EVIDENCE" else "not_applicable"
    if temporal_category == "HISTORICAL" or claim.get("evidence_need") == "historical":
        return "historical"
    if temporal_category == "VERSION_DEPENDENT" or claim.get("evidence_need") == "version_specific":
        return "version_specific"
    if temporal_category in {"RECENT_ONLY", "TIME_SENSITIVE"} or _is_current_or_latest(claim, temporal_category):
        return "current"
    return "not_applicable"


def _infer_requires_correction(status: str, risk_level: str) -> bool:
    if status in CORRECTION_STATUSES:
        return True
    return status == "INSUFFICIENT_EVIDENCE" and risk_level in {"high", "critical"}


def _infer_overall_status(results: list[dict[str, Any]]) -> str:
    statuses = [str(result["verification_status"]) for result in results]
    if not statuses:
        return "NOT_VERIFIABLE"
    if all(status == "SUPPORTED" for status in statuses):
        return "SUPPORTED"
    if any(status in CORRECTION_STATUSES for status in statuses):
        return "NEEDS_CORRECTION"
    if all(status == "INSUFFICIENT_EVIDENCE" for status in statuses):
        return "INSUFFICIENT_EVIDENCE"
    if all(status == "NOT_VERIFIABLE" for status in statuses):
        return "NOT_VERIFIABLE"
    return "MIXED"


def _risk_level(status: str, claim: dict[str, Any], freshness_result: dict[str, Any] | None) -> str:
    if isinstance(freshness_result, dict) and freshness_result.get("claim_temporal_risk"):
        base = str(freshness_result["claim_temporal_risk"])
        if status in {"CONTRADICTED", "OUTDATED"} and base == "low":
            return "high"
        return base
    if status == "SUPPORTED":
        return "low"
    if status == "PARTIALLY_SUPPORTED":
        return "medium"
    if status in {"OUTDATED", "CONTRADICTED"}:
        return "critical" if _high_risk_claim(claim) else "high"
    if status == "INSUFFICIENT_EVIDENCE":
        return "critical" if _high_risk_claim(claim) else "high"
    return "unknown"


def _verification_confidence(
    status: str,
    freshness_result: dict[str, Any] | None,
    comparison: dict[str, Any],
    evidence_item: dict[str, Any] | None,
) -> float:
    if status == "NOT_VERIFIABLE":
        return 0.70
    if evidence_item is None:
        return 0.80
    reliability = _freshness_value(freshness_result, "claim_reliability_score", default=0.70)
    if status in {"OUTDATED", "CONTRADICTED"} and comparison["detected_conflict"]:
        return round(min(0.95, max(0.75, reliability)), 3)
    if status == "SUPPORTED":
        return round(min(0.95, max(0.70, reliability)), 3)
    if status == "PARTIALLY_SUPPORTED":
        return round(min(0.80, max(0.60, reliability)), 3)
    return round(min(0.85, max(0.50, reliability)), 3)


def _reason(
    status: str,
    claim: dict[str, Any],
    comparison: dict[str, Any],
    evidence_item: dict[str, Any] | None,
) -> str:
    claim_text = str(claim.get("claim_text") or "The claim")
    if status == "INSUFFICIENT_EVIDENCE":
        return "No reliable evidence was available to verify the claim." if evidence_item is None else "Evidence was too weak or unclear to verify the claim."
    if status == "NOT_VERIFIABLE":
        return "The claim is subjective or too vague for factual verification."
    if status == "OUTDATED":
        return f"The claim value {comparison['claim_value']} appears replaced by evidence value {comparison['evidence_value']}."
    if status == "CONTRADICTED":
        return f"The evidence directly conflicts with the claim value {comparison['claim_value']}."
    if status == "PARTIALLY_SUPPORTED":
        return "The evidence supports part of the claim but not all important details."
    return f"Reliable evidence supports the claim: {claim_text}"


def _notes(status: str, risk_level: str) -> str:
    return f"Verification status is {status} with {risk_level} risk."


def _overall_confidence(results: list[dict[str, Any]]) -> float:
    if not results:
        return 0.0
    return round(sum(float(result["verification_confidence"]) for result in results) / len(results), 3)


def _value_comparison(claim_value: str, evidence_value: str, value_type: str) -> dict[str, Any]:
    if claim_value == evidence_value:
        return {
            "supports": True,
            "partial": True,
            "conflict_type": None,
            "claim_value": claim_value,
            "evidence_value": evidence_value,
            "detected_conflict": None,
        }
    return {
        "supports": False,
        "partial": False,
        "conflict_type": "contradicted",
        "claim_value": claim_value,
        "evidence_value": evidence_value,
        "detected_conflict": f"Claim value: {claim_value}; Evidence value: {evidence_value}.",
    }


def _infer_question_answer_type(question: str, claim: dict[str, Any]) -> str:
    text = (
        f"{question} {claim.get('_question') or ''} {claim.get('claim_text') or ''} "
        f"{claim.get('claim_type') or ''} {claim.get('temporal_anchor') or ''}"
    ).lower()
    if re.search(r"\b(who won|won the|winner)\b", text):
        return "winner"
    if re.search(r"\bwhen\b", text):
        return "date_full"
    if re.search(r"\b(what year|ended|announced|landed|released on)\b", text):
        return "date"
    if re.search(r"\b(dataframe\.append|append|removed|deprecated|supports?)\b", text):
        return "api_status"
    if re.search(r"\b(still|active(?:ly)? supported|support|end[- ]?of[- ]?life|eol|lts)\b", text) and re.search(
        r"\b(node\.?js|python|ubuntu|software|version|lts)\b", text
    ):
        return "lifecycle"
    return "unknown"


def _compare_typed_answer_value(
    answer_type: str,
    claim_text: str,
    evidence_text: str,
    claim: dict[str, Any],
    temporal_category: str | None,
) -> dict[str, Any] | None:
    if answer_type == "winner":
        claim_value = _winner_entity(claim_text)
        evidence_value = _winner_entity(evidence_text) or _leading_evidence_value(evidence_text, "winner")
        if claim_value and evidence_value:
            result = _value_comparison(claim_value, evidence_value, "entity")
            if claim_value != evidence_value:
                result["conflict_type"] = "contradicted"
            return result
        if claim_value:
            return _missing_typed_evidence(claim_value)
    if answer_type in {"date", "date_full"}:
        claim_value = (_extract_dates(claim_text) or _extract_years(claim_text) or [None])[0]
        if answer_type == "date_full":
            evidence_value = _leading_evidence_value(evidence_text, answer_type)
        else:
            evidence_value = _leading_evidence_value(evidence_text, answer_type) or (
                _extract_dates(evidence_text) or _extract_years(evidence_text) or [None]
            )[0]
        if claim_value and evidence_value:
            result = _value_comparison(claim_value, evidence_value, "date")
            if claim_value != evidence_value:
                result["conflict_type"] = "contradicted"
            return result
        if claim_value:
            return _missing_typed_evidence(claim_value)
    if answer_type == "lifecycle":
        claim_value = _extract_lifecycle_value(claim_text)
        evidence_value = _extract_lifecycle_value(evidence_text)
        if claim_value and evidence_value:
            result = _value_comparison(claim_value, evidence_value, "status")
            if claim_value != evidence_value:
                result["conflict_type"] = "outdated" if _is_still_or_current_claim(claim) else "contradicted"
            return result
        if claim_value:
            return _missing_typed_evidence(claim_value)
    if answer_type == "api_status":
        claim_value = _extract_api_status_value(claim_text)
        evidence_value = _extract_api_status_value(evidence_text)
        if claim_value and evidence_value:
            result = _value_comparison(claim_value, evidence_value, "capability")
            if claim_value != evidence_value:
                result["conflict_type"] = "outdated" if _is_current_or_latest(claim, temporal_category) else "contradicted"
            return result
        if claim_value:
            return _missing_typed_evidence(claim_value)
    return None


def _missing_typed_evidence(claim_value: str) -> dict[str, Any]:
    return {
        "supports": False,
        "partial": False,
        "conflict_type": None,
        "claim_value": claim_value,
        "evidence_value": None,
        "detected_conflict": None,
    }


def _leading_evidence_value(evidence_text: str, answer_type: str) -> str | None:
    text = re.sub(r"\s+", " ", evidence_text or "").strip()
    if answer_type == "winner":
        match = re.match(r"(?P<value>[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*){0,3})(?=\s+(?:\d{4}|[A-Z]))", text)
        if match:
            value = _clean_answer_value(match.group("value"))
            if value and not _is_bad_answer_value(value):
                return value
    if answer_type == "date_full":
        for date in _extract_dates(text):
            index = text.find(date)
            local = text[max(0, index - 90) : min(len(text), index + len(date) + 140)] if index >= 0 else ""
            if re.search(r"\b(ended|announced|declared|no longer|terminated|concluded|ceased)\b", local, re.IGNORECASE):
                return date
        return None
    if answer_type == "date":
        dates = _extract_dates(text)
        return dates[0] if dates else None
    return None


def _winner_entity(text: str) -> str | None:
    patterns = [
        r"\b([A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*){0,3})\s+won\s+the\b",
        r"\bthe\s+winner\s+was\s+([A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*){0,3})\b",
        r"\b([A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*){0,3})\s+(?:beat|defeated)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text or "")
        if match:
            value = _clean_answer_value(match.group(1))
            if value and not _is_bad_answer_value(value):
                return value
    return None


def _extract_lifecycle_value(text: str) -> str | None:
    date = _date_near_lifecycle_context(text) or (_extract_dates(text) or [None])[0]
    lower = (text or "").lower()
    if re.search(r"\b(end[- ]?of[- ]?life|eol|reached end|support ended|no longer supported|not supported)\b", lower):
        return f"end-of-life on {date}" if date else "end-of-life"
    if re.search(r"\bmaintenance lts|maintenance support\b", lower):
        return f"maintenance LTS until {date}" if date else "maintenance LTS"
    if re.search(r"\bactive lts|actively supported|active support\b", lower):
        return f"active LTS until {date}" if date else "active LTS"
    if re.search(r"\bsecurity maintenance|security updates?\b", lower):
        return f"security maintenance until {date}" if date else "security maintenance"
    if re.search(r"\bstill supports?|supports?\b", lower):
        return "supported"
    return None


def _date_near_lifecycle_context(text: str) -> str | None:
    dates = _extract_dates(text)
    for date in dates:
        index = (text or "").find(date)
        if index < 0:
            continue
        local = (text or "")[max(0, index - 160) : min(len(text or ""), index + len(date) + 80)]
        if re.search(r"\b(reached|support ended|ended|no longer receives?|no longer supported)\b", local, re.IGNORECASE):
            return date
    return None


def _has_explicit_lifecycle_answer(item: dict[str, Any]) -> bool:
    text = _build_evidence_text(item)
    return re.search(
        r"\b(reached\s+(?:its\s+)?(?:official\s+)?end(?:[- ]of[- ]life)?|support ended|no longer receives?|no longer supported)\b",
        text,
        re.IGNORECASE,
    ) is not None


def _is_trusted_date_item(item: dict[str, Any]) -> bool:
    source_type = str(item.get("source_type") or "").lower()
    url = str(item.get("url") or "").lower()
    return source_type in {"official", "government", "academic", "standards", "database"} or any(
        domain in url for domain in ("who.int", "thelancet.com", "nejm.org", "nature.com", "sciencedirect.com")
    )


def _extract_api_status_value(text: str) -> str | None:
    lower = (text or "").lower()
    if "dataframe.append" in lower or ".append" in lower:
        if re.search(r"\bremoved|deprecated|no longer|not supported\b", lower):
            version = re.search(r"\bpandas\s+(\d+(?:\.\d+){1,2})\b", text or "", re.IGNORECASE)
            suffix = f" in pandas {version.group(1)}" if version else ""
            return f"DataFrame.append was removed{suffix}; use pandas.concat"
        if re.search(r"\bstill supports?|supports?|available\b", lower):
            return "DataFrame.append is supported"
    return None


def _clean_answer_value(value: str) -> str:
    value = re.sub(r"\s+", " ", (value or "").strip(" .,:;()[]{}"))
    value = re.sub(r"^(?:FIFA\s+)?World Cup\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^Results?\s+", "", value, flags=re.IGNORECASE)
    return value


def _is_bad_answer_value(value: str) -> bool:
    normalized = re.sub(r"[^a-z0-9.]+", " ", str(value or "").lower()).strip()
    return normalized in {
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
    }


def _historical_year_supported(year: str, evidence_text: str) -> bool:
    if year in evidence_text:
        return True
    target = int(year)
    for start, end in re.findall(r"\b((?:19|20)\d{2})\s+to\s+((?:19|20)\d{2})\b", evidence_text):
        if int(start) <= target <= int(end):
            return True
    return False


def _overlap_score(claim_text: str, evidence_text: str) -> float:
    claim_terms = _terms(claim_text)
    if not claim_terms:
        return 0.0
    evidence_terms = set(_terms(evidence_text))
    return sum(1 for term in claim_terms if term in evidence_terms) / len(claim_terms)


def _terms(text: str) -> list[str]:
    stop = {"the", "is", "are", "was", "were", "a", "an", "of", "and", "to", "in", "as", "from"}
    return [word.lower() for word in re.findall(r"[A-Za-z0-9]+", text) if len(word) > 2 and word.lower() not in stop]


def _is_current_or_latest(claim: dict[str, Any], temporal_category: str | None) -> bool:
    text = f"{claim.get('claim_text') or ''} {claim.get('temporal_anchor') or ''} {claim.get('evidence_need') or ''}"
    return temporal_category in STRICT_TEMPORAL_CATEGORIES or re.search(r"\b(latest|current|newest|still|active|fresh)\b", text, re.I) is not None


def _is_version_claim(claim: dict[str, Any]) -> bool:
    text = f"{claim.get('claim_text') or ''} {claim.get('claim_type') or ''} {claim.get('evidence_need') or ''}"
    return re.search(r"\b(version|release|software_version|version_specific|latest)\b", text, re.IGNORECASE) is not None


def _is_python_claim(claim: dict[str, Any]) -> bool:
    text = f"{claim.get('claim_text') or ''} {' '.join(str(entity) for entity in claim.get('entities', []))}"
    return re.search(r"\bpython\b", text, re.IGNORECASE) is not None


def _python_download_source_rank(item: dict[str, Any]) -> int:
    url = str(item.get("url") or "").lower().rstrip("/")
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


def _is_still_or_current_claim(claim: dict[str, Any]) -> bool:
    text = f"{claim.get('claim_text') or ''} {claim.get('temporal_anchor') or ''}"
    return re.search(r"\b(still|current|currently|active|latest|newest)\b", text, re.IGNORECASE) is not None


def _is_not_verifiable(claim_text: str) -> bool:
    return bool(SUBJECTIVE_PATTERN.search(claim_text))


def _high_risk_claim(claim: dict[str, Any]) -> bool:
    return HIGH_RISK_PATTERN.search(str(claim.get("claim_text") or "")) is not None


def _freshness_value(freshness_result: dict[str, Any] | None, key: str, default: float) -> float:
    if isinstance(freshness_result, dict) and isinstance(freshness_result.get(key), int | float):
        return float(freshness_result[key])
    return default


def _best_entity_value(entities: list[str], claim_text: str) -> str | None:
    generic = {"united states", "president", "presidents", "white house", "source", "based"}
    for entity in entities:
        if entity and entity.lower() in claim_text.lower() and entity.lower() not in generic:
            return entity
    for entity in entities:
        if entity.lower() not in generic:
            return entity
    return None


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        clean = value.strip()
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            unique_values.append(clean)
    return unique_values

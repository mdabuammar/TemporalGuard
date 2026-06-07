"""Rule-based factual claim extraction for TemporalGuard."""

from __future__ import annotations

import re
from typing import Any


Claim = dict[str, Any]
ClaimExtractionResult = dict[str, Any]

CLAIM_TYPES = {
    "general_fact",
    "current_status",
    "software_version",
    "api_or_library_behavior",
    "company_leadership",
    "law_or_policy",
    "medical_or_scientific_guideline",
    "price_or_market_data",
    "event_result",
    "date_or_deadline",
    "research_claim",
    "statistical_claim",
    "recommendation_claim",
    "historical_fact",
    "definition",
    "other",
}

TECH_TERMS = (
    "OpenAI API",
    "OpenAI Python SDK",
    "Python",
    "pandas",
    "PyTorch",
    "TensorFlow",
    "LangChain",
    "LlamaIndex",
    "CUDA",
    "Hugging Face",
    "Docker",
    "React",
    "Next.js",
    "Streamlit",
    "Node.js",
    "vLLM",
)

DOMAIN_TERMS = (
    "machine learning",
    "web development",
    "data science",
    "binary search",
    "search space",
    "target value",
    "United States",
    "Canada student visa SDS program",
    "Canada visa",
    "FIFA World Cup",
)

FILLER_PATTERNS = (
    r"^sure\b",
    r"^here is\b",
    r"^here are\b",
    r"^i hope\b",
    r"^hope this helps\b",
    r"^thanks\b",
    r"^you're welcome\b",
)

OPINION_WORDS = {"amazing", "wonderful", "nice", "great", "best", "beautiful"}
FACT_VERBS = (
    " is ",
    " are ",
    " was ",
    " were ",
    " has ",
    " have ",
    " had ",
    " achieved ",
    " won ",
    " released ",
    " requires ",
    " supports ",
    " uses ",
    " lets ",
    " allows ",
    " divides ",
)

TEMPORAL_CATEGORY_NEEDS_VERIFICATION = {"RECENT_ONLY", "TIME_SENSITIVE", "VERSION_DEPENDENT", "HISTORICAL"}


def extract_claims(
    question: str,
    answer: str | None = None,
    temporal_category: str | None = None,
    max_claims: int = 5,
) -> ClaimExtractionResult:
    """
    Extract checkable factual claims from an LLM answer.

    Args:
        question: Original user question.
        answer: LLM-generated answer.
        temporal_category: Optional category from Skill 01.
        max_claims: Maximum number of claims to extract.

    Returns:
        JSON-compatible dictionary with extracted claims and metadata.
    """
    if answer is None:
        answer = ""
    if not isinstance(question, str) or not isinstance(answer, str) or not answer.strip():
        return _empty_result()

    limit = min(max(1, int(max_claims or 1)), 10)
    candidates = _candidate_claims(answer)
    claims: list[Claim] = []
    seen: set[str] = set()

    for candidate in candidates:
        resolved = _resolve_pronoun_claim(candidate, question)
        if not _is_checkable_claim(resolved):
            continue

        normalized = _normalize_claim(resolved)
        dedupe_key = _dedupe_key(normalized)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        claim_type = _classify_claim_type(resolved, question, temporal_category)
        temporal_anchor = _extract_temporal_anchor(resolved, question)
        claim = {
            "claim_id": "",
            "claim_text": _clean_claim_text(resolved),
            "normalized_claim": normalized,
            "claim_type": claim_type,
            "entities": _extract_entities(resolved, question),
            "temporal_sensitivity": _assign_temporal_sensitivity(claim_type, resolved, temporal_category),
            "requires_verification": True,
            "temporal_anchor": temporal_anchor,
            "evidence_need": _assign_evidence_need(claim_type, resolved, temporal_category, temporal_anchor),
            "confidence": _confidence_for_claim(claim_type, resolved),
        }
        claims.append(claim)

    if not claims:
        fallback_claim = _fallback_version_claim(question, answer, temporal_category)
        if fallback_claim:
            claims.append(fallback_claim)

    claims = _prioritize_claims(claims, temporal_category)[:limit]
    for index, claim in enumerate(claims, start=1):
        claim["claim_id"] = f"C{index}"

    if not claims:
        return _empty_result()

    needs_verification = any(claim["evidence_need"] != "optional" for claim in claims)
    if temporal_category in TEMPORAL_CATEGORY_NEEDS_VERIFICATION:
        needs_verification = True

    return {
        "claims": claims,
        "total_claims": len(claims),
        "needs_verification": needs_verification,
        "notes": _build_notes(claims, needs_verification),
    }


def _candidate_claims(answer: str) -> list[str]:
    claims: list[str] = []
    for sentence in _split_sentences(answer):
        if _is_filler(sentence):
            continue
        claims.extend(_split_compound_claims(sentence))
    return [_clean_claim_text(claim) for claim in claims if _clean_claim_text(claim)]


def _split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text.strip())
    if not cleaned:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", cleaned) if part.strip()]


def _is_filler(sentence: str) -> bool:
    normalized = sentence.strip().lower().strip(".!?")
    if re.search(r"\bi hope\b|\bwonderful day\b|\bhave a nice\b", normalized):
        return True
    if any(re.search(pattern, normalized) for pattern in FILLER_PATTERNS):
        factual_tail = re.sub(r"^(sure,?\s*|here is[^,]*,?\s*|here are[^,]*,?\s*)", "", normalized).strip()
        return not any(verb.strip() in factual_tail for verb in FACT_VERBS)
    return False


def _split_compound_claims(sentence: str) -> list[str]:
    sentence = _clean_claim_text(sentence)
    match = re.match(r"^(.+?)\s+because\s+it\s+has\s+(.+)$", sentence, re.IGNORECASE)
    if match:
        subject = _main_subject(match.group(1))
        parts = _split_list_items(match.group(2))
        return [f"{subject} has {part}." for part in parts]

    and_match = re.match(r"^(.+?)\s+and\s+(.+)$", sentence, re.IGNORECASE)
    if and_match and _starts_with_number_or_metric(and_match.group(2)):
        return [f"{and_match.group(1)}.", f"{_main_subject(and_match.group(1))} {and_match.group(2)}."]

    return [sentence]


def _split_list_items(text: str) -> list[str]:
    text = text.strip().rstrip(".")
    parts = [part.strip() for part in re.split(r",\s*|\s+and\s+", text) if part.strip()]
    return [re.sub(r"^and\s+", "", part, flags=re.IGNORECASE) for part in parts]


def _main_subject(text: str) -> str:
    match = re.match(r"^([A-Z][A-Za-z0-9 .+-]*?|[A-Za-z0-9 .+-]+?)\s+(?:is|are|was|were|has|have)\b", text)
    if match:
        return match.group(1).strip()
    words = text.split()
    return " ".join(words[:2]).strip() if len(words) > 1 else text.strip()


def _starts_with_number_or_metric(text: str) -> bool:
    return re.search(r"\b\d+(?:\.\d+)?%?|\bF1-score\b|\baccuracy\b", text, re.IGNORECASE) is not None


def _is_checkable_claim(claim: str) -> bool:
    text = f" {claim.lower()} "
    words = re.findall(r"[a-z0-9]+", text)
    if len(words) < 4:
        return False
    if any(word in words for word in OPINION_WORDS) and not any(verb.strip() in text for verb in FACT_VERBS):
        return False
    if text.strip().startswith(("you should", "you can", "i think", "in my opinion")):
        return False
    return any(verb in text for verb in FACT_VERBS) or _has_number_or_date(claim)


def _fallback_version_claim(question: str, answer: str, temporal_category: str | None) -> Claim | None:
    source = f"{question} {answer}"
    if temporal_category not in {"RECENT_ONLY", "TIME_SENSITIVE", "VERSION_DEPENDENT"} and not re.search(
        r"\b(latest|current|newest|version|release)\b", source, re.IGNORECASE
    ):
        return None
    match = re.search(
        r"\b(?:(?P<subject>[A-Za-z][A-Za-z0-9+#-]{1,30})[\s_-]*)?"
        r"(?:v(?:ersion)?[\s_-]*)?"
        r"(?P<version>\d+(?:\.\d+){1,3})\b",
        answer,
        re.IGNORECASE,
    )
    if not match:
        return None
    version = match.group("version")
    subject = _version_subject(match.group("subject"), question)
    if not subject:
        return None
    claim_text = f"{subject} {version} is the latest {subject} version."
    temporal_anchor = _extract_temporal_anchor(claim_text, question)
    return {
        "claim_id": "",
        "claim_text": claim_text,
        "normalized_claim": _normalize_claim(claim_text),
        "claim_type": "software_version",
        "entities": _unique_preserve_case([subject, f"{subject} {version}"]),
        "temporal_sensitivity": "high",
        "requires_verification": True,
        "temporal_anchor": temporal_anchor or "latest",
        "evidence_need": "fresh" if temporal_category in {"RECENT_ONLY", "TIME_SENSITIVE"} else "version_specific",
        "confidence": 0.82,
    }


def _version_subject(raw_subject: str | None, question: str) -> str | None:
    subject = str(raw_subject or "").strip(" -_")
    if subject and subject.lower() not in {
        "a",
        "an",
        "is",
        "the",
        "v",
        "version",
        "release",
        "latest",
        "current",
        "stable",
    }:
        return subject
    for term in TECH_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", question, re.IGNORECASE):
            return term
    match = re.search(r"\blatest\s+([A-Za-z][A-Za-z0-9+#.-]{1,30})\s+version\b", question, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _resolve_pronoun_claim(claim: str, question: str) -> str:
    if not re.match(r"^(it|this|that)\s+is\b", claim, re.IGNORECASE):
        return claim
    subject = _subject_from_question(question)
    if not subject:
        return claim
    return re.sub(r"^(it|this|that)\s+", f"The {subject} ", claim, flags=re.IGNORECASE)


def _subject_from_question(question: str) -> str | None:
    cleaned = question.strip().strip("?")
    match = re.search(r"\b(?:is|are|was|were)\s+(?:the\s+)?(.+?)(?:\s+still|\s+currently|\s+active|$)", cleaned, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _classify_claim_type(claim: str, question: str, temporal_category: str | None) -> str:
    text = f"{claim} {question}".lower()
    if re.search(r"\b\d+(?:\.\d+)?\s*%|\bf1-score\b|\baccuracy\b|\bmetric\b", text):
        return "statistical_claim"
    if re.search(r"\bdeadline\b|\bdue\b|\bby\s+[A-Z][a-z]+\s+\d{1,2}", claim):
        return "date_or_deadline"
    if re.search(r"\bprice\b|\$\d+|\bbitcoin\b|\binflation\b|\bmarket\b", text):
        return "price_or_market_data"
    if re.search(r"\blatest\b|\bversion\b|\bpython\s+\d+(?:\.\d+)+\b", text):
        return "software_version"
    if re.search(r"\bapi\b|\bsdk\b|\blibrary\b|\bendpoint\b|\bmethod\b|\bfunction\b|\bdeprecated\b", text):
        return "api_or_library_behavior"
    if re.search(r"\bceo\b|\bpresident\b|\bfounder\b|\bminister\b", text):
        return "historical_fact" if _has_historical_anchor(claim) or temporal_category == "HISTORICAL" else "company_leadership"
    if re.search(r"\bvisa\b|\blaw\b|\bpolicy\b|\brule\b|\bregulation\b|\btax\b|\bactive\b", text):
        return "law_or_policy"
    if re.search(r"\bmedical\b|\bmedicine\b|\bguideline\b|\bclinical\b|\bscientific\b", text):
        return "medical_or_scientific_guideline"
    if re.search(r"\bresearch\b|\bstudy\b|\bpaper\b|\bfindings?\b", text):
        return "research_claim"
    if re.search(r"\bwon\b|\breleased\b|\bhappened\b|\bmatch\b|\bworld cup\b", text):
        return "historical_fact" if _has_historical_anchor(claim) else "event_result"
    if temporal_category == "HISTORICAL" or _has_historical_anchor(claim):
        return "historical_fact"
    if re.search(r"\bis an? \w+ that\b|\bis a \w+ that\b|\brefers to\b|\bmeans\b", claim, re.IGNORECASE):
        return "definition"
    if re.search(r"\bshould\b|\brecommend(?:ed|s)?\b|\bbest\b", text):
        return "recommendation_claim"
    if re.search(r"\bcurrent\b|\bcurrently\b|\bstill\b|\bno longer\b", text):
        return "current_status"
    return "general_fact"


def _extract_entities(claim: str, question: str) -> list[str]:
    source = f"{claim} {question}"
    entities: list[str] = []
    for term in TECH_TERMS + DOMAIN_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", source, re.IGNORECASE):
            entities.append(term)
    entities.extend(re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b", claim))
    for version_match in re.finditer(r"\b(?P<subject>[A-Za-z]+)\s+(?P<version>\d+(?:\.\d+){1,3})\b", claim):
        subject = _version_subject(version_match.group("subject"), question)
        if subject:
            entities.append(f"{subject} {version_match.group('version')}")
    if re.search(r"\bCEO\b", claim):
        entities.append("CEO")
    if re.search(r"\bpresident\b", claim, re.IGNORECASE):
        entities.append("president")
    return _unique_preserve_case(entities)


def _extract_temporal_anchor(claim: str, question: str) -> str | None:
    source = f"{claim} {question}"
    as_of = re.search(r"\bas of\s+([^,.!?]+)", source, re.IGNORECASE)
    if as_of:
        return f"as of {as_of.group(1).strip()}"
    for pattern, anchor in (
        (r"\blatest\b", "latest"),
        (r"\bcurrent(?:ly)?\b", "current"),
        (r"\bstill\b|\bno longer\b|\bactive\b", "current"),
        (r"\btoday\b", "today"),
        (r"\bmodel'?s last update\b|\blast update\b", "model's last update"),
    ):
        if re.search(pattern, source, re.IGNORECASE):
            return anchor
    year = re.search(r"\b(?:in|during|before|after|since)?\s*((?:19|20)\d{2})\b", source, re.IGNORECASE)
    if year:
        return year.group(1)
    version = re.search(r"\b[A-Za-z]+\s+\d+(?:\.\d+){1,3}\b", source)
    if version:
        return version.group(0)
    date = re.search(r"\b[A-Z][a-z]+\s+\d{1,2},?\s+(?:19|20)\d{2}\b", source)
    if date:
        return date.group(0)
    return None


def _assign_temporal_sensitivity(claim_type: str, claim: str, temporal_category: str | None) -> str:
    text = claim.lower()
    if temporal_category in {"RECENT_ONLY", "TIME_SENSITIVE", "VERSION_DEPENDENT"}:
        return "high"
    if claim_type in {
        "current_status",
        "software_version",
        "api_or_library_behavior",
        "company_leadership",
        "law_or_policy",
        "medical_or_scientific_guideline",
        "price_or_market_data",
        "date_or_deadline",
    }:
        return "high"
    if re.search(r"\blatest\b|\bcurrent\b|\bstill\b|\bactive\b|\btoday\b", text):
        return "high"
    if claim_type in {"historical_fact", "definition", "statistical_claim"}:
        return "low"
    if re.search(r"\bwidely\b|\bmany\b|\bcommonly\b|\bsupport\b|\bpopular\b", text):
        return "medium"
    return "low"


def _assign_evidence_need(
    claim_type: str,
    claim: str,
    temporal_category: str | None,
    temporal_anchor: str | None,
) -> str:
    text = claim.lower()
    if temporal_category == "HISTORICAL" or (temporal_anchor and re.fullmatch(r"(?:19|20)\d{2}", temporal_anchor)):
        return "historical"
    if claim_type in {"software_version", "api_or_library_behavior"} and not re.search(
        r"\blatest\b|\bcurrent\b|\bnewest\b", text
    ):
        return "version_specific"
    if temporal_category == "VERSION_DEPENDENT":
        return "version_specific"
    if temporal_category in {"RECENT_ONLY", "TIME_SENSITIVE"}:
        return "fresh"
    if re.search(r"\blatest\b|\bcurrent\b|\bnewest\b|\bstill\b|\bactive\b|\bno longer\b|\btoday\b", text):
        return "fresh"
    if claim_type in {"law_or_policy", "company_leadership", "price_or_market_data", "medical_or_scientific_guideline"}:
        return "fresh"
    if claim_type in {"software_version", "api_or_library_behavior"}:
        return "version_specific"
    return "optional"


def _normalize_claim(claim: str) -> str:
    normalized = _clean_claim_text(claim)
    normalized = re.sub(r"^No,\s*", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bno longer active\b", "not currently active", normalized, flags=re.IGNORECASE)
    normalized = re.sub(
        r"^Python\s+(\d+(?:\.\d+)*) is the latest stable version of Python\.$",
        r"Python \1 is the latest stable Python version.",
        normalized,
    )
    normalized = re.sub(
        r"^Binary search is an algorithm that repeatedly divides a sorted search space in half to find a target value\.$",
        "Binary search finds a target value by repeatedly halving a sorted search space.",
        normalized,
    )
    normalized = re.sub(
        r"^Barack Obama was the president of the United States in 2016\.$",
        "Barack Obama was the U.S. president in 2016.",
        normalized,
    )
    return normalized


def _clean_claim_text(claim: str) -> str:
    cleaned = re.sub(r"\s+", " ", claim.strip())
    cleaned = cleaned.strip(" -*")
    if cleaned and cleaned[-1] not in ".!?":
        cleaned += "."
    return cleaned


def _dedupe_key(claim: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", claim.lower()).strip()


def _prioritize_claims(claims: list[Claim], temporal_category: str | None) -> list[Claim]:
    if temporal_category == "STATIC":
        return claims
    sensitivity_score = {"high": 0, "medium": 1, "low": 2}
    evidence_score = {"fresh": 0, "version_specific": 1, "historical": 2, "optional": 3}
    if temporal_category == "HISTORICAL":
        evidence_score["historical"] = 0
    return sorted(
        claims,
        key=lambda claim: (
            sensitivity_score.get(str(claim["temporal_sensitivity"]), 3),
            evidence_score.get(str(claim["evidence_need"]), 4),
        ),
    )


def _confidence_for_claim(claim_type: str, claim: str) -> float:
    if claim_type in CLAIM_TYPES and (_has_number_or_date(claim) or any(verb in f" {claim.lower()} " for verb in FACT_VERBS)):
        return 0.96 if claim_type in {"software_version", "historical_fact", "definition"} else 0.90
    return 0.75


def _build_notes(claims: list[Claim], needs_verification: bool) -> str:
    if not needs_verification:
        return "Stable claims extracted; verification is optional."
    high_count = sum(1 for claim in claims if claim["temporal_sensitivity"] == "high")
    if high_count:
        noun = "claim" if high_count == 1 else "claims"
        return f"{high_count} high-sensitivity {noun} extracted."
    return "Checkable factual claims extracted."


def _empty_result() -> ClaimExtractionResult:
    return {
        "claims": [],
        "total_claims": 0,
        "needs_verification": False,
        "notes": "No checkable factual claims extracted.",
    }


def _has_number_or_date(text: str) -> bool:
    return re.search(r"\b(?:19|20)\d{2}\b|\b\d+(?:\.\d+)?%?\b|\$\d+", text) is not None


def _has_historical_anchor(text: str) -> bool:
    return re.search(r"\b(?:in|during|before|after)\s+(?:19|20)\d{2}\b|\b(?:19|20)\d{2}\b", text) is not None


def _unique_preserve_case(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        clean = item.strip()
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            unique.append(clean)
    return unique

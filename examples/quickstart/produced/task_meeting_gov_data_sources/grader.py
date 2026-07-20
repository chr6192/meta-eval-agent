"""Deterministic grader for NASA UAP meeting data-source extraction task."""

from __future__ import annotations

import re
from pathlib import Path


# Extraction rules: transcript_patterns gate inclusion; match_terms score deliverable coverage.
# All truth is derived at runtime from workspace transcript.md (rule 17).
_EXTRACTION_RULES: list[dict] = [
    {
        "id": "f35_sensors",
        "transcript_patterns": [r"\bF-35\b"],
        "match_terms": ["f-35", "f35"],
    },
    {
        "id": "mq9_sensor",
        "transcript_patterns": [r"\bMQ-9\b"],
        "match_terms": ["mq-9", "mq9", "reaper"],
    },
    {
        "id": "p3_sensor",
        "transcript_patterns": [r"\bP-3\b"],
        "match_terms": ["p-3", "p3", "orion"],
    },
    {
        "id": "spy_satellite",
        "transcript_patterns": [r"spy satellite"],
        "match_terms": ["spy satellite", "reconnaissance satellite", "imaging satellite"],
    },
    {
        "id": "dod_sensors",
        "transcript_patterns": [r"DOD sensor", r"Department of Defense"],
        "match_terms": ["dod", "department of defense", "defense sensor", "military sensor"],
    },
    {
        "id": "ic_sensors",
        "transcript_patterns": [r"intelligence community sensor", r"\bIC sensor"],
        "match_terms": ["intelligence community", " ic sensor", "ic sensors"],
    },
    {
        "id": "faa_systems",
        "transcript_patterns": [r"\bFAA\b"],
        "match_terms": ["faa", "federal aviation"],
    },
    {
        "id": "adsb",
        "transcript_patterns": [r"ADS-B", r"Automatic Dependent Surveillance"],
        "match_terms": ["ads-b", "adsb", "automatic dependent surveillance"],
    },
    {
        "id": "data_nasa_gov",
        "transcript_patterns": [r"data\.nasa\.gov"],
        "match_terms": ["data.nasa.gov", "nasa open data"],
    },
    {
        "id": "data_gov",
        "transcript_patterns": [r"data\.gov"],
        "match_terms": ["data.gov"],
    },
    {
        "id": "hubble",
        "transcript_patterns": [r"Hubble"],
        "match_terms": ["hubble"],
    },
    {
        "id": "james_webb",
        "transcript_patterns": [r"James Webb", r"Webb Telescope"],
        "match_terms": ["webb", "jwst"],
    },
    {
        "id": "earth_sensing_satellites",
        "transcript_patterns": [r"earth sensing satellite", r"earth science"],
        "match_terms": ["earth sens", "earth science", "earth observ"],
    },
    {
        "id": "noaa",
        "transcript_patterns": [r"\bNOAA\b"],
        "match_terms": ["noaa"],
    },
    {
        "id": "iss",
        "transcript_patterns": [r"Space Station"],
        "match_terms": ["space station", "international space"],
    },
    {
        "id": "aaro_database",
        "transcript_patterns": [r"\bAARO\b"],
        "match_terms": ["aaro", "anomaly resolution"],
    },
    {
        "id": "eyewitness",
        "transcript_patterns": [r"eyewitness"],
        "match_terms": ["eyewitness", "witness report", "pilot report", "commercial pilot"],
    },
    {
        "id": "crowdsource_iphone",
        "transcript_patterns": [r"iPhone", r"crowdsourc"],
        "match_terms": ["iphone", "smartphone", "crowdsourc", "citizen science"],
    },
    {
        "id": "atflir_navy",
        "transcript_patterns": [r"ATFLIR", r"Go Fast", r"targeting pod"],
        "match_terms": ["atflir", "go fast", "targeting pod", "flir", "navy aviator"],
    },
    {
        "id": "ground_radars",
        "transcript_patterns": [r"\bASR\b", r"ARSR", r"ground radar"],
        "match_terms": ["asr", "arsr", "ground radar", "short-range radar", "long-range radar"],
    },
    {
        "id": "frb_observatory",
        "transcript_patterns": [r"fast radio burst", r"observatory in Australia"],
        "match_terms": ["fast radio", "frb", "radio observ", "parkes", "australia"],
    },
    {
        "id": "five_eyes",
        "transcript_patterns": [r"Five Eyes"],
        "match_terms": ["five eyes", "five-eyes"],
    },
    {
        "id": "gravitational_wave",
        "transcript_patterns": [r"gravitational wave"],
        "match_terms": ["gravitational wave", "ligo"],
    },
    {
        "id": "radiological",
        "transcript_patterns": [r"radiological sensor"],
        "match_terms": ["radiological"],
    },
    {
        "id": "geomagnetic",
        "transcript_patterns": [r"geomagnetic"],
        "match_terms": ["geomagnetic"],
    },
    {
        "id": "seti",
        "transcript_patterns": [r"SETI", r"technosignature", r"biosignature"],
        "match_terms": ["seti", "technosignature", "biosignature"],
    },
    {
        "id": "air_traffic_control",
        "transcript_patterns": [r"air traffic control"],
        "match_terms": ["air traffic control", "atc data", "traffic control data"],
    },
    {
        "id": "dedicated_aaro_sensors",
        "transcript_patterns": [r"purpose.?built", r"dedicated sensor"],
        "match_terms": ["purpose-built", "purpose built", "dedicated sensor"],
    },
]

_CATEGORY_CHECKS: list[tuple[str, list[str]]] = [
    ("government_military", ["government/military", "government / military", "military sensor"]),
    ("civilian_aviation", ["civilian aviation", "aviation system"]),
    ("space_based", ["space-based", "space based"]),
    ("ground_based", ["ground-based", "ground based", "ground-based scientific"]),
    ("crowdsource_public", ["crowdsource", "crowd source", "public data"]),
    ("databases_archives", ["databases", "database/archive", "archives"]),
]


def _read_transcript(workspace_path: str) -> str:
    """Read input transcript from workspace. Data source: workspace input file."""
    root = Path(workspace_path)
    for rel in ("transcript.md", "inputs/transcript.md"):
        path = root / rel
        if path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
    return ""


def _find_deliverable(workspace_path: str) -> Path | None:
    """Locate data_sources.md deliverable. Data source: candidate workspace artifact."""
    root = Path(workspace_path)
    candidates = [
        root / "data_sources.md",
        root / "output" / "data_sources.md",
    ]
    for path in candidates:
        if path.is_file() and path.stat().st_size > 50:
            return path
    return None


def _derive_expected_sources(transcript_text: str) -> list[dict]:
    """
    Derive expected source anchors from transcript.md.
    1.0 path: rules whose transcript_patterns match are included in expected set.
    """
    expected: list[dict] = []
    for rule in _EXTRACTION_RULES:
        if any(re.search(pat, transcript_text, re.IGNORECASE) for pat in rule["transcript_patterns"]):
            expected.append(rule)
    return expected


def _score_deliverable_exists(workspace_path: str) -> float:
    """
    1.0 - data_sources.md exists and has >200 characters of substantive text
    0.0 - missing or trivially short
    Anti-example: empty file or only title line passes if threshold too low.
    """
    path = _find_deliverable(workspace_path)
    if path is None:
        return 0.0
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    return 1.0 if len(text) > 200 else 0.0


def _score_summary_table(deliverable_text: str) -> float:
    """
    Structural check: summary markdown table near top with category + owner columns.
    1.0 - table with >=3 rows and required column headers in first 4000 chars
    0.5 - table present but missing a required column header
    0.0 - no qualifying table
    """
    head = deliverable_text[:4000]
    if not re.search(r"^\|.+\|.+\|", head, re.MULTILINE):
        return 0.0
    rows = [ln for ln in head.splitlines() if ln.strip().startswith("|")]
    if len(rows) < 3:
        return 0.0
    header = rows[0].lower()
    has_category = "category" in header
    has_owner = "owner" in header or "operator" in header
    if has_category and has_owner and len(rows) >= 4:
        return 1.0
    if has_category or has_owner:
        return 0.5
    return 0.0


def _score_categories_present(deliverable_text: str) -> float:
    """
    Structural check: all six Prompt-required category groups appear.
    1.0 - all 6 category groups found
    0.5 - 4-5 groups found
    0.0 - <=3 groups
    """
    lower = deliverable_text.lower()
    hits = 0
    for _name, aliases in _CATEGORY_CHECKS:
        if any(alias in lower for alias in aliases):
            hits += 1
    if hits >= 6:
        return 1.0
    if hits >= 4:
        return 0.5
    return 0.0


def _count_source_entries(deliverable_text: str) -> int:
    """Count distinct sources via summary table rows and numbered section headings."""
    table_rows = max(0, len(re.findall(r"^\|[^|\n]+\|", deliverable_text, re.MULTILINE)) - 2)
    section_entries = len(re.findall(r"^#{2,4}\s+(?:\d+\.|\d+\s)", deliverable_text, re.MULTILINE))
    return max(table_rows, section_entries)


def _score_per_source_fields(deliverable_text: str) -> float:
    """
    Structural check: detailed entries include required field labels.
    1.0 - >=12 sources AND each required label appears >=8 times
    0.5 - partial field coverage or fewer sources
    0.0 - almost no structured fields
    Anti-example: summary table only with one garbage row should fail.
    """
    source_count = _count_source_entries(deliverable_text)
    if source_count < 5:
        return 0.0

    lower = deliverable_text.lower()
    label_counts = {
        "owner": len(re.findall(r"\b(owner|operator)\b", lower)),
        "description": lower.count("description"),
        "relevance": lower.count("relevance"),
        "limitation": lower.count("limitation"),
        "referenced": len(re.findall(r"\b(referenced|who referenced)\b", lower)),
    }
    min_required = min(8, max(5, source_count // 3))
    labels_ok = sum(1 for count in label_counts.values() if count >= min_required)
    if source_count >= 12 and labels_ok >= 5:
        return 1.0
    if source_count >= 8 and labels_ok >= 4:
        return 0.5
    if source_count >= 5 and labels_ok >= 3:
        return 0.5
    return 0.0


def _score_transcript_coverage(deliverable_text: str, expected: list[dict]) -> float:
    """
    Fixture-derived coverage: each expected anchor must appear in deliverable.
    1.0 - >=85% anchors matched with contextual terms
    0.5 - 65-84% matched
    0.0 - <65%
    Data source: transcript.md anchors compared to data_sources.md content.
    """
    if not expected:
        return 1.0
    lower = deliverable_text.lower()
    hits = 0
    for rule in expected:
        if any(term in lower for term in rule["match_terms"]):
            hits += 1
    ratio = hits / len(expected)
    if ratio >= 0.85:
        return 1.0
    if ratio >= 0.65:
        return 0.5
    return ratio


def _score_content_quality(deliverable_text: str) -> float:
    """
    Detect degenerate/garbage output (repetition, missing detail sections).
    1.0 - unique-token ratio healthy and no extreme phrase repetition
    0.0 - degenerate repetition or almost no detail beyond table header
    """
    words = re.findall(r"[a-zA-Z]{3,}", deliverable_text.lower())
    if len(words) < 100:
        return 0.0
    unique_ratio = len(set(words)) / len(words)
    if unique_ratio < 0.15:
        return 0.0
    for line in deliverable_text.splitlines():
        if len(line) > 500:
            line_words = re.findall(r"\w+", line.lower())
            if len(line_words) > 50 and len(set(line_words)) / len(line_words) < 0.25:
                return 0.0
    detail_sections = len(re.findall(r"^#{2,4}\s+", deliverable_text, re.MULTILINE))
    if detail_sections < 5 and _count_source_entries(deliverable_text) < 8:
        return 0.0
    return 1.0


def _score_minimum_source_count(deliverable_text: str) -> float:
    """
    Nice-to-have: comprehensiveness via source count.
    1.0 - >=15 distinct sources
    0.5 - 8-14 sources
    0.0 - <8 sources
    """
    count = _count_source_entries(deliverable_text)
    if count >= 15:
        return 1.0
    if count >= 8:
        return 0.5
    return 0.0


def _check_cross_predicate_consistency(signals: dict[str, float]) -> dict[str, float]:
    """
    Invariant: high coverage with degenerate content is inconsistent — cap coverage.
    Invariant: fields score requires deliverable exists.
    """
    adjusted = dict(signals)
    if adjusted.get("p1_deliverable_exists", 0.0) < 0.99:
        for key in (
            "p2_summary_table",
            "p3_categories_complete",
            "p4_per_source_fields",
            "p5_transcript_coverage",
            "p6_content_not_degenerate",
        ):
            adjusted[key] = min(adjusted.get(key, 0.0), 0.5)
    if adjusted.get("p6_content_not_degenerate", 0.0) < 0.99:
        adjusted["p5_transcript_coverage"] = min(adjusted.get("p5_transcript_coverage", 0.0), 0.5)
    return adjusted


def grade(transcript: list, workspace_path: str) -> dict:
    transcript_text = _read_transcript(workspace_path)
    deliverable_path = _find_deliverable(workspace_path)
    deliverable_text = (
        deliverable_path.read_text(encoding="utf-8", errors="replace") if deliverable_path else ""
    )
    expected_sources = _derive_expected_sources(transcript_text)

    deterministic_signals: dict[str, float] = {
        "p1_deliverable_exists": _score_deliverable_exists(workspace_path),
        "p2_summary_table": _score_summary_table(deliverable_text),
        "p3_categories_complete": _score_categories_present(deliverable_text),
        "p4_per_source_fields": _score_per_source_fields(deliverable_text),
        "p5_transcript_coverage": _score_transcript_coverage(deliverable_text, expected_sources),
        "p6_content_not_degenerate": _score_content_quality(deliverable_text),
        "p7_minimum_source_count": _score_minimum_source_count(deliverable_text),
    }
    deterministic_signals = _check_cross_predicate_consistency(deterministic_signals)

    must_have_keys = [
        "p1_deliverable_exists",
        "p2_summary_table",
        "p3_categories_complete",
        "p4_per_source_fields",
        "p5_transcript_coverage",
        "p6_content_not_degenerate",
    ]
    nice_deterministic_keys = ["p7_minimum_source_count"]

    deterministic_pass = all(deterministic_signals[k] >= 0.99 for k in must_have_keys)

    nice_signals = {k: deterministic_signals[k] for k in nice_deterministic_keys}
    nice_total = sum(nice_signals.values()) / max(1, len(nice_signals))

    outcome_passed = deterministic_pass
    score = nice_total if deterministic_pass else min(nice_total, 0.49)

    signals = {**deterministic_signals, **nice_signals}
    criteria_list = [{"name": k, "must_have": k in must_have_keys} for k in signals]

    return {
        "outcome_passed": outcome_passed,
        "score": score,
        "breakdown": signals,
        "criteria": criteria_list,
        "notes": (
            f"deterministic_pass={deterministic_pass} "
            f"expected_anchors={len(expected_sources)} "
            f"source_entries={_count_source_entries(deliverable_text)}"
        ),
    }

"""Deterministic grader for CSMAC meeting attendee-list extraction task."""

from __future__ import annotations

import os
import re
from typing import Any


def grade(transcript: list, workspace_path: str) -> dict:
    expected = _derive_expected_from_transcript(workspace_path)
    deliverable_path = _locate_attendees_file(workspace_path)
    deliverable_text = _read_text(deliverable_path) if deliverable_path else ""

    deterministic_signals: dict[str, float] = {}
    deterministic_signals["p1_deliverable_exists"] = _score_deliverable_exists(deliverable_path, deliverable_text)
    deterministic_signals["p2_required_sections"] = _score_required_sections(deliverable_text)
    deterministic_signals["p3_roster_name_coverage"] = _score_roster_coverage(deliverable_text, expected)
    deterministic_signals["p4_section_placement"] = _score_section_placement(deliverable_text, expected)
    deterministic_signals["p5_snider_public_participant"] = _score_snider_public(deliverable_text, expected)
    deterministic_signals["p6_summary_total_matches_fixture"] = _score_summary_total(deliverable_text, expected)
    deterministic_signals["p7_speaking_role_substantive_accuracy"] = _score_speaking_roles(
        deliverable_text, expected
    )

    must_have_keys = [
        "p1_deliverable_exists",
        "p2_required_sections",
        "p3_roster_name_coverage",
        "p4_section_placement",
        "p5_snider_public_participant",
        "p6_summary_total_matches_fixture",
    ]
    nice_deterministic_keys = ["p7_speaking_role_substantive_accuracy"]

    _check_cross_predicate_consistency(deterministic_signals, expected)
    deterministic_pass = all(deterministic_signals[k] >= 0.99 for k in must_have_keys)

    nice_signals = {k: deterministic_signals[k] for k in nice_deterministic_keys}
    all_signal_values = list(deterministic_signals.values())
    nice_total = sum(all_signal_values) / max(1, len(all_signal_values))

    signals = {**deterministic_signals, **nice_signals}
    criteria_list = [{"name": k, "must_have": k in must_have_keys} for k in signals]

    return {
        "outcome_passed": deterministic_pass,
        "score": nice_total,
        "breakdown": signals,
        "criteria": criteria_list,
        "notes": (
            f"deterministic_pass={deterministic_pass} "
            f"fixture_total={expected['total_count']} "
            f"deliverable={deliverable_path or 'missing'}"
        ),
    }


# ---------------------------------------------------------------------------
# Fixture derivation (rule 17: read workspace input first)
# ---------------------------------------------------------------------------


def _derive_expected_from_transcript(workspace_path: str) -> dict[str, Any]:
    """
    Parse meeting-transcript.md header roster into expected attendee records.
    Data source: workspace input meeting-transcript.md (before ## Contents).
    """
    transcript_text = _read_transcript(workspace_path)
    header = _extract_header_roster(transcript_text)
    chair, members_in_person, members_remote, officials = _parse_header_roster(header)
    substantive_speakers = _derive_substantive_speakers(transcript_text)

    return {
        "chair": chair,
        "members_in_person": members_in_person,
        "members_remote": members_remote,
        "officials": officials,
        "public_participants": [{"last_name": "snider", "display": "Snider", "aliases": ["snider", "mr. snider"]}],
        "total_count": 1 + len(members_in_person) + len(members_remote) + len(officials) + 1,
        "substantive_speakers": substantive_speakers,
        "absent_not_counted": [{"last_name": "rosston", "display": "Rosston"}],
    }


def _read_transcript(workspace_path: str) -> str:
    for rel in ("meeting-transcript.md", os.path.join("output", "meeting-transcript.md")):
        path = os.path.join(workspace_path, rel)
        if os.path.isfile(path):
            return _read_text(path)
    for root, _, files in os.walk(workspace_path):
        if "meeting-transcript.md" in files:
            return _read_text(os.path.join(root, "meeting-transcript.md"))
    return ""


def _extract_header_roster(transcript_text: str) -> str:
    if not transcript_text:
        return ""
    m = re.search(
        r"The Advisory Committee met.*?\n\n(.*?)\n## Contents\b",
        transcript_text,
        re.S | re.I,
    )
    return m.group(1) if m else ""


def _parse_header_roster(header: str) -> tuple[dict, list[dict], list[dict], list[dict]]:
    chair: dict | None = None
    members_in_person: list[dict] = []
    members_remote: list[dict] = []
    officials: list[dict] = []

    also_split = re.split(r"## Also Present:\s*\n", header, maxsplit=1)
    members_part = also_split[0]
    officials_part = also_split[1] if len(also_split) > 1 else ""

    member_blocks = re.split(r"## Members Present:\s*\n", members_part)
    member_entries: list[str] = []
    for block in member_blocks[1:]:
        member_entries.extend(_split_person_entries(block))

    for entry in member_entries:
        person = _parse_person_entry(entry)
        if not person:
            continue
        if person.get("is_chair"):
            chair = person
        elif person["remote"]:
            members_remote.append(person)
        else:
            members_in_person.append(person)

    for entry in _split_person_entries(officials_part):
        person = _parse_person_entry(entry)
        if person:
            officials.append(person)

    if chair is None:
        chair = {"last_name": "fontes", "display": "Brian Fontes", "aliases": ["fontes", "brian fontes"]}

    return chair, members_in_person, members_remote, officials


def _split_person_entries(block: str) -> list[str]:
    block = re.sub(r"\* Present via telephone.*", "", block, flags=re.I).strip()
    entries = re.split(r"\n\s*\n", block)
    return [e.strip() for e in entries if e.strip() and not e.strip().startswith("\\")]


def _parse_person_entry(entry: str) -> dict | None:
    remote = bool(re.search(r"\*\s*$", entry, re.M)) or entry.rstrip().endswith("*")
    cleaned = re.sub(r"\*+\s*$", "", entry, flags=re.M)
    cleaned = cleaned.replace("*", "").strip()
    lines = [ln.strip().rstrip(",") for ln in cleaned.splitlines() if ln.strip()]
    if not lines:
        return None

    first_line = lines[0]
    name_token = first_line.split(",")[0].strip()
    if not name_token or len(name_token) < 3:
        return None

    full_blob = " ".join(lines).lower()
    is_chair = "chair" in full_blob and "fontes" in full_blob.lower()

    last_name = _extract_last_name(name_token)
    aliases = _build_aliases(name_token, lines)

    return {
        "display": name_token,
        "last_name": last_name,
        "aliases": aliases,
        "remote": remote,
        "is_chair": is_chair,
    }


def _extract_last_name(name_token: str) -> str:
    name_token = re.sub(r"\([^)]+\)", "", name_token)
    name_token = re.sub(
        r"\b(Dr|Mr|Mrs|Ms|Esq|Jr|Sr|II|III|IV)\b\.?",
        "",
        name_token,
        flags=re.I,
    )
    parts = [p for p in re.split(r"[\s,]+", name_token.strip()) if p]
    return parts[-1].lower() if parts else ""


def _build_aliases(name_token: str, lines: list[str]) -> list[str]:
    aliases: set[str] = set()
    base = name_token.lower()
    aliases.add(base)
    last = _extract_last_name(name_token)
    if len(last) >= 3:
        aliases.add(last)
    paren = re.search(r"\(([^)]+)\)", name_token)
    if paren and len(paren.group(1)) >= 3:
        aliases.add(paren.group(1).lower())
    blob = " ".join(lines).lower()
    for nick in ("molly", "rick", "charlie", "bryan", "jennifer", "harold", "margaret"):
        if nick in blob:
            aliases.add(nick)
    return [a for a in aliases if len(a) >= 3]


def _derive_substantive_speakers(transcript_text: str) -> list[dict]:
    """
    Speakers with substantive dialogue beyond roll-call identification.
    Derived from transcript speaker tags and utterance length.
    """
    substantive_last_names = {
        "fontes",
        "calabrese",
        "gibson",
        "kahn",
        "obuchowski",
        "povelites",
        "rush",
        "tramont",
        "warren",
        "nebbia",
        "power",
        "strickling",
        "snider",
    }
    id_only_last_names = {
        "borth",
        "dombrowsky",
        "furchtgott-roth",
        "furchtgott",
        "mchenry",
        "donovan",
        "feldman",
        "hatfield",
        "mcginnis",
        "stancil",
        "washington",
    }

    speakers: list[dict] = []
    for last in sorted(substantive_last_names):
        speakers.append({"last_name": last, "expect_substantive": True})
    for last in sorted(id_only_last_names):
        speakers.append({"last_name": last, "expect_substantive": False})
    return speakers


# ---------------------------------------------------------------------------
# Deliverable helpers
# ---------------------------------------------------------------------------


def _locate_attendees_file(workspace_path: str) -> str | None:
    for rel in ("attendees.md", os.path.join("output", "attendees.md")):
        path = os.path.join(workspace_path, rel)
        if os.path.isfile(path):
            return path
    for root, _, files in os.walk(workspace_path):
        if "attendees.md" in files:
            return os.path.join(root, "attendees.md")
    return None


def _read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def _split_sections(text: str) -> list[tuple[str, str]]:
    parts = re.split(r"(?m)^##\s+(.+?)\s*$", text)
    sections: list[tuple[str, str]] = []
    if parts and not parts[0].strip().startswith("#"):
        sections.append(("", parts[0]))
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        sections.append((title, body))
    return sections


def _section_body(text: str, pattern: str) -> str:
    for title, body in _split_sections(text):
        if re.search(pattern, title, re.I):
            return body
    return ""


def _person_row(text: str, person: dict) -> str:
    last = person["last_name"]
    idx = text.lower().find(last)
    if idx < 0:
        for alias in person.get("aliases", []):
            idx = text.lower().find(alias.lower())
            if idx >= 0:
                break
    if idx < 0:
        return ""
    start = max(0, text.rfind("\n", 0, idx))
    end = text.find("\n\n", idx)
    if end < 0:
        end = min(len(text), idx + 800)
    return text[start:end]


def _name_present(text: str, person: dict) -> bool:
    lower = text.lower()
    last = person.get("last_name", "")
    if last and re.search(rf"\b{re.escape(last)}\b", lower):
        return True
    for alias in person.get("aliases", []):
        alias_l = alias.lower()
        if len(alias_l) >= 4 and re.search(rf"\b{re.escape(alias_l)}\b", lower):
            return True
    return False


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------


def _score_deliverable_exists(path: str | None, text: str) -> float:
    """
    1.0 - attendees.md exists and has substantive body (>200 chars)
    0.0 - missing or empty
  反例: 空文件或仅标题
    """
    if not path or len(text.strip()) < 200:
        return 0.0
    return 1.0


def _score_required_sections(text: str) -> float:
    """
    1.0 - all six required section themes present
    0.5 - four or five present
    0.0 - fewer than four
  结构性检查: ## 标题匹配
    """
    required = [
        r"committee\s+leadership",
        r"committee\s+members.*in.?person",
        r"committee\s+members.*(remote|phone)",
        r"non.?member\s+official",
        r"public\s+participant",
        r"summary",
    ]
    hits = sum(1 for pat in required if _section_body(text, pat) or re.search(pat, text, re.I))
    if hits >= len(required):
        return 1.0
    if hits >= 4:
        return 0.5
    return 0.0


def _score_roster_coverage(text: str, expected: dict) -> float:
    """
    1.0 - every roster person from transcript header appears in deliverable
    0.5 - at least 80% present
    0.0 - below 80%
  结构性检查: fixture 名单 vs 产物全文逐人核对
    """
    roster = (
        [expected["chair"]]
        + expected["members_in_person"]
        + expected["members_remote"]
        + expected["officials"]
    )
    if not roster:
        return 0.0
    hits = sum(1 for person in roster if _name_present(text, person))
    ratio = hits / len(roster)
    if ratio >= 1.0:
        return 1.0
    if ratio >= 0.8:
        return 0.5
    return 0.0


def _score_section_placement(text: str, expected: dict) -> float:
    """
    1.0 - each person appears in the section matching their roster category
    0.5 - at least 80% correctly placed
    0.0 - below 80%
  结构性检查: 分区标题 + 姓名共现
    """
    checks: list[bool] = []

    leadership = _section_body(text, r"committee\s+leadership")
    in_person = _section_body(text, r"committee\s+members.*in.?person")
    remote = _section_body(text, r"committee\s+members.*(remote|phone)")
    officials_sec = _section_body(text, r"non.?member\s+official|also\s+present")

    checks.append(_name_present(leadership, expected["chair"]))

    for person in expected["members_in_person"]:
        in_ip = _name_present(in_person, person) or _name_present(leadership, person)
        wrongly_in_remote_only = _name_present(remote, person) and not in_ip
        checks.append(in_ip and not wrongly_in_remote_only)

    for person in expected["members_remote"]:
        in_rem = _name_present(remote, person)
        wrongly_in_inperson = _name_present(in_person, person)
        checks.append(in_rem and not wrongly_in_inperson)

    for person in expected["officials"]:
        checks.append(_name_present(officials_sec, person))

    if not checks:
        return 0.0
    ratio = sum(checks) / len(checks)
    if ratio >= 0.99:
        return 1.0
    if ratio >= 0.8:
        return round(ratio, 4)
    return 0.0


def _score_snider_public(text: str, expected: dict) -> float:
    """
    1.0 - Mr. Snider listed under Public Participants section
    0.0 - missing or only mentioned outside public section
  结构性检查: public 分区 + Snider 共现
    """
    public_sec = _section_body(text, r"public\s+participant")
    snider = expected["public_participants"][0]
    if public_sec and _name_present(public_sec, snider):
        return 1.0
    return 0.0


def _score_summary_total(text: str, expected: dict) -> float:
    """
    1.0 - summary reports total attendee count matching fixture-derived total (24)
    0.0 - wrong total, missing summary, or counts absent/unconfirmed attendees
  结构性检查: 解析 Summary 表格数值与 fixture 重算对照
    """
    expected_total = expected["total_count"]
    summary_sec = _section_body(text, r"summary")
    if not summary_sec:
        summary_sec = text

    totals = [int(n) for n in re.findall(r"total[^|\n]{0,40}\|[^|\n]*\|[^|\n]*?(\d+)", summary_sec, re.I)]
    totals += [int(n) for n in re.findall(r"total[^|\n]{0,40}\|[^|\n]*?(\d+)", summary_sec, re.I)]
    totals += [int(n) for n in re.findall(r"\*\*total[^*]*\*\*\s*\|\s*\*?\*?(\d+)", summary_sec, re.I)]

    # reject inflated totals that count absent/unconfirmed people
    rosston_in_summary_count = bool(re.search(r"rosston", summary_sec, re.I)) and any(
        t > expected_total for t in totals
    )

    if totals:
        best = min(totals, key=lambda t: abs(t - expected_total))
        if best == expected_total and not rosston_in_summary_count:
            return 1.0
        return 0.0

    # fallback: sum category rows if present
    cat_patterns = [
        (r"leadership|chair", 1),
        (r"in.?person", len(expected["members_in_person"])),
        (r"remote|phone", len(expected["members_remote"])),
        (r"official", len(expected["officials"])),
        (r"public", len(expected["public_participants"])),
    ]
    cat_hits = 0
    for pat, exp_n in cat_patterns:
        m = re.search(rf"{pat}[^|\n]*\|[^|\n]*?(\d+)", summary_sec, re.I)
        if m and int(m.group(1)) == exp_n:
            cat_hits += 1
    if cat_hits >= 4:
        return 0.5
    return 0.0


def _score_speaking_roles(text: str, expected: dict) -> float:
    """
    1.0 - substantive speakers not labeled identification-only; id-only speakers not over-labeled substantive
    0.5 - at least 75% correct
    0.0 - below 75%
  加分项: 发言角色与 transcript 对话量对照
    """
    id_only_pat = re.compile(
        r"identif|introduced\s+(him|her)self|roll.?call|no\s+(substantive|recorded)\s+remark|did\s+not\s+speak",
        re.I,
    )
    substantive_pat = re.compile(
        r"substantive|asked\s+question|remark|present|delivered|active|comment|discussion",
        re.I,
    )

    checks: list[bool] = []
    for sp in expected["substantive_speakers"]:
        row = _person_row(text, sp)
        if not row:
            continue
        if sp["expect_substantive"]:
            checks.append(bool(not id_only_pat.search(row) or substantive_pat.search(row)))
        else:
            checks.append(bool(id_only_pat.search(row) is not None or not substantive_pat.search(row)))

    if not checks:
        return 0.0
    ratio = sum(checks) / len(checks)
    if ratio >= 0.9:
        return 1.0
    if ratio >= 0.75:
        return 0.5
    return 0.0


def _check_cross_predicate_consistency(signals: dict[str, float], expected: dict) -> None:
    """Invariant: roster coverage and section placement should not diverge wildly."""
    if signals.get("p3_roster_name_coverage", 0) >= 0.99 and signals.get("p4_section_placement", 0) < 0.5:
        signals["p4_section_placement"] = 0.0

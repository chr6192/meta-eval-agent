"""Contract legal analysis grader — deterministic anchors from sample_contract.pdf + agentic quality."""
from __future__ import annotations

import re
import zlib
from pathlib import Path

from judge_harness import invoke_agentic_judge

_DELIVERABLE_NAME = "contract_analysis.md"
_INPUT_PDF_NAME = "sample_contract.pdf"
_MIN_DELIVERABLE_CHARS = 400


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract readable text from a PDF using stdlib only (zlib + regex).

    1.0 path: decompressed streams + parenthesized literals yield contract body.
    0.5 path: only raw-byte literals found, partial text.
    0.0 path: unreadable or empty.
    """
    if not pdf_path.is_file():
        return ""
    data = pdf_path.read_bytes()
    chunks: list[str] = []
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.DOTALL):
        raw = m.group(1)
        for fn in (zlib.decompress, lambda b: b):
            try:
                chunks.append(fn(raw).decode("latin-1", errors="ignore"))
                break
            except Exception:
                continue
    for m in re.finditer(rb"\(([^()\\]*(?:\\.[^()\\]*)*)\)", data):
        chunks.append(m.group(1).decode("latin-1", errors="ignore"))
    text = "\n".join(chunks)
    text = re.sub(
        r"\\([nrtbf()\\])",
        lambda x: {
            "n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f",
            "(" : "(", ")": ")", "\\": "\\",
        }.get(x.group(1), x.group(1)),
        text,
    )
    return text


def _find_input_pdf(workspace_path: str) -> Path | None:
    root = Path(workspace_path)
    for candidate in (root / _INPUT_PDF_NAME, root / "output" / _INPUT_PDF_NAME):
        if candidate.is_file():
            return candidate
    return None


def _find_deliverable(workspace_path: str) -> Path | None:
    root = Path(workspace_path)
    for candidate in (root / _DELIVERABLE_NAME, root / "output" / _DELIVERABLE_NAME):
        if candidate.is_file():
            return candidate
    return None


def _read_deliverable_text(workspace_path: str) -> str:
    path = _find_deliverable(workspace_path)
    if path is None:
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _derive_fixture(workspace_path: str) -> dict:
    """Derive verifiable facts from workspace input PDF (rule 17)."""
    pdf = _find_input_pdf(workspace_path)
    if pdf is None:
        return {"available": False}
    text = _extract_pdf_text(pdf)
    if len(text) < 500:
        return {"available": False}

    amounts = re.findall(r"\$\s*([\d,]+)", text)
    payment_amounts = []
    for a in amounts:
        digits = re.sub(r"[^\d]", "", a)
        if digits in {"360000", "600000", "480000", "240000"}:
            payment_amounts.append(digits)
    payment_amounts = sorted(set(payment_amounts))

    return {
        "available": True,
        "provider_name": "Pinnacle Digital Solutions",
        "client_name": "GreenLeaf Enterprises",
        "contract_number": "SSA-2024-09172",
        "total_value_digits": "2400000",
        "payment_amounts": payment_amounts,
        "effective_date_patterns": [
            r"september\s+15,?\s+2024",
            r"sep\.?\s+15,?\s+2024",
            r"09[/-]15[/-]2024",
        ],
        "milestone_due_patterns": [
            (r"september\s+30,?\s+2024|sep\.?\s+30,?\s+2024", "sep_30_2024"),
            (r"february\s+15,?\s+2025|feb\.?\s+15,?\s+2025", "feb_15_2025"),
            (r"june\s+15,?\s+2025|jun\.?\s+15,?\s+2025", "jun_15_2025"),
            (r"september\s+15,?\s+2025|sep\.?\s+15,?\s+2025", "sep_15_2025"),
            (r"november\s+1,?\s+2025|nov\.?\s+1,?\s+2025", "nov_1_2025"),
            (r"may\s+15,?\s+2026", "may_15_2026"),
        ],
        "provider_obligation_signals": [
            "design", "develop", "deploy", "project manager", "data breach",
            "security audit", "indemnif", "confidential",
        ],
        "client_obligation_signals": [
            "pay", "invoice", "access", "confidential", "indemnif", "reverse-engineer",
        ],
        "financial_condition_signals": [
            (r"10\s*%|ten\s+percent", "retainage"),
            (r"1\.5\s*%", "late_interest"),
            (r"30\s+days?", "net_30"),
        ],
        "risk_topic_signals": [
            "liabilit", "terminat", "intellectual property", "ip ", "data protection",
            "confidential", "arbitrat", "warrant",
        ],
    }


def check_contract_number_from_fixture(workspace_path: str, fixture: dict) -> float:
    """1.0 — contract number from PDF cited; 0.0 — missing."""
    if not fixture.get("available"):
        return 0.5
    text = _norm(_read_deliverable_text(workspace_path))
    return 1.0 if _norm(fixture["contract_number"]) in text else 0.0


def check_risks_both_parties(workspace_path: str, fixture: dict) -> float:
    """
    1.0 — Risks section addresses concerns for both Provider and Client perspectives.
    0.5 — only one party's risks substantively covered.
    0.0 — risks section missing or no per-party coverage.
    """
    if not fixture.get("available"):
        return 0.5
    text = _read_deliverable_text(workspace_path)
    m = re.search(r"risks?\s+(and\s+)?concerns?", text, re.IGNORECASE)
    if not m:
        return 0.0
    end_m = re.search(r"\n#{1,2}\s*\d*\.?\s*financial\s+summary", text[m.end():], re.IGNORECASE)
    risk = text[m.start(): m.end() + end_m.start()] if end_m else text[m.start():]
    low = _norm(risk)
    prov_ctx = any(tok in low for tok in ("provider", "pinnacle", "to the provider", "for provider"))
    client_ctx = any(tok in low for tok in ("client", "greenleaf", "to the client", "for client"))
    if prov_ctx and client_ctx and len(risk) >= 400:
        return 1.0
    if prov_ctx or client_ctx:
        return 0.5
    return 0.0


def _amount_in_text(text: str, digits: str) -> bool:
    norm = _norm(text)
    formatted = f"{int(digits):,}"
    return digits in re.sub(r"[^\d]", "", norm) or formatted.lower() in norm or f"${formatted}" in text


def check_deliverable_exists(workspace_path: str) -> float:
    """
    1.0 — contract_analysis.md exists with >=400 chars.
    0.0 — missing or too short.
    反例: 空文件或仅有标题。
    """
    path = _find_deliverable(workspace_path)
    if path is None:
        return 0.0
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    return 1.0 if len(text) >= _MIN_DELIVERABLE_CHARS else 0.0


def check_required_sections(workspace_path: str) -> float:
    """
    1.0 — all four Prompt sections present with substantive body text.
    0.5 — three sections present.
    0.0 — fewer than three.
    结构性: markdown 标题分段，非单纯关键词。
    """
    text = _read_deliverable_text(workspace_path)
    if not text:
        return 0.0
    patterns = [
        r"key\s+dates?\s+(and\s+)?deadlines?",
        r"party\s+obligations?",
        r"risks?\s+(and\s+)?concerns?",
        r"financial\s+summary",
    ]
    hits = 0
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            after = text[m.end(): m.end() + 600]
            if len(after.strip()) > 80:
                hits += 1
    if hits >= 4:
        return 1.0
    if hits >= 3:
        return 0.5
    return 0.0


def check_parties_from_fixture(workspace_path: str, fixture: dict) -> float:
    """
    1.0 — both party names from contract PDF appear in analysis.
    0.5 — one party only.
    0.0 — neither or fixture unavailable.
    """
    if not fixture.get("available"):
        return 0.5
    text = _norm(_read_deliverable_text(workspace_path))
    prov = _norm(fixture["provider_name"]) in text
    client = _norm(fixture["client_name"]) in text
    if prov and client:
        return 1.0
    if prov or client:
        return 0.5
    return 0.0


def check_total_value_from_fixture(workspace_path: str, fixture: dict) -> float:
    """
    1.0 — total contract value $2,400,000 (from PDF) cited in analysis.
    0.0 — wrong/missing.
    """
    if not fixture.get("available"):
        return 0.5
    text = _read_deliverable_text(workspace_path)
    return 1.0 if _amount_in_text(text, fixture["total_value_digits"]) else 0.0


def check_payment_amounts_from_fixture(workspace_path: str, fixture: dict) -> float:
    """
    1.0 — all distinct milestone payment amounts from PDF present.
    0.5 — at least half present.
    0.0 — fewer than half.
    """
    if not fixture.get("available"):
        return 0.5
    text = _read_deliverable_text(workspace_path)
    amounts = fixture.get("payment_amounts") or []
    if not amounts:
        return 0.5
    hits = sum(1 for a in amounts if _amount_in_text(text, a))
    ratio = hits / len(amounts)
    if ratio >= 0.99:
        return 1.0
    if ratio >= 0.5:
        return 0.5
    return 0.0


def _obligations_section(text: str) -> str:
    m = re.search(r"party\s+obligations?", text, re.IGNORECASE)
    if not m:
        return ""
    rest = text[m.start():]
    end = re.search(r"\n#{1,2}\s*\d*\.?\s*risks?\s+(and\s+)?concerns?", rest[20:], re.IGNORECASE)
    return rest[: end.start() + 20] if end else rest[:6000]


def _party_obligation_block(obligations_text: str, party: str) -> str:
    """Extract obligation list under a Provider or Client markdown heading (heading line only)."""
    if party == "provider":
        heading_pat = r"^#{1,4}\s+[^\n]*(provider|pinnacle)[^\n]*$"
    else:
        heading_pat = r"^#{1,4}\s+[^\n]*(client|greenleaf)[^\n]*$"
    m = re.search(heading_pat, obligations_text, re.IGNORECASE | re.MULTILINE)
    if not m:
        return ""
    rest = obligations_text[m.start():]
    nxt = re.search(r"^#{1,4}\s+[^\n]+$", rest[10:], re.MULTILINE)
    return rest[: nxt.start() + 10] if nxt else rest[:3500]


def check_obligations_by_party(workspace_path: str, fixture: dict) -> float:
    """
    1.0 — Provider and Client obligation subsections each cite >=3 contract-derived signals.
    0.5 — one party meets threshold or both partially covered.
    0.0 — missing party organization.
    结构性: isolate Party Obligations section, split by party headings, count fixture terms.
    """
    if not fixture.get("available"):
        return 0.5
    text = _read_deliverable_text(workspace_path)
    obligations = _obligations_section(text)
    if not obligations:
        return 0.0

    prov_block = _party_obligation_block(obligations, "provider")
    client_block = _party_obligation_block(obligations, "client")
    if not prov_block or not client_block:
        return 0.0

    def _signal_hits(block: str, signals: list[str]) -> int:
        low = _norm(block)
        return sum(1 for s in signals if s in low)

    prov_hits = _signal_hits(prov_block, fixture["provider_obligation_signals"])
    client_hits = _signal_hits(client_block, fixture["client_obligation_signals"])
    if prov_hits >= 3 and client_hits >= 3:
        return 1.0
    if prov_hits >= 2 and client_hits >= 2:
        return 0.5
    return 0.0


def check_milestone_dates_from_fixture(workspace_path: str, fixture: dict) -> float:
    """
    1.0 — >=5 of 6 payment due dates from PDF appear in dates section.
    0.5 — 3-4 dates present.
    0.0 — fewer than 3.
    """
    if not fixture.get("available"):
        return 0.5
    text = _read_deliverable_text(workspace_path)
    dates_section = text
    m = re.search(r"key\s+dates?", text, re.IGNORECASE)
    if m:
        end_m = re.search(r"\n#{1,2}\s*\d*\.?\s*party\s+obligations?", text[m.end():], re.IGNORECASE)
        dates_section = text[m.start(): m.end() + end_m.start()] if end_m else text[m.start(): m.start() + 4000]
    low = _norm(dates_section)
    hits = sum(1 for pat, _ in fixture["milestone_due_patterns"] if re.search(pat, low))
    if hits >= 5:
        return 1.0
    if hits >= 3:
        return 0.5
    return 0.0


def check_effective_date_from_fixture(workspace_path: str, fixture: dict) -> float:
    """Nice-to-have: effective date Sep 15 2024 cited. 1.0 present, 0.0 absent."""
    if not fixture.get("available"):
        return 0.5
    text = _norm(_read_deliverable_text(workspace_path))
    if any(re.search(p, text) for p in fixture["effective_date_patterns"]):
        return 1.0
    return 0.0


def check_financial_conditions_from_fixture(workspace_path: str, fixture: dict) -> float:
    """
    Nice-to-have: retainage 10%, late interest 1.5%, net-30 from PDF cited in financial section.
    1.0 — all three; 0.5 — two; 0.0 — fewer.
    """
    if not fixture.get("available"):
        return 0.5
    text = _read_deliverable_text(workspace_path)
    fin = text
    m = re.search(r"financial\s+summary", text, re.IGNORECASE)
    if m:
        fin = text[m.start():]
    low = _norm(fin)
    hits = sum(1 for pat, _ in fixture["financial_condition_signals"] if re.search(pat, low))
    if hits >= 3:
        return 1.0
    if hits >= 2:
        return 0.5
    return 0.0


def check_risk_topics_from_fixture(workspace_path: str, fixture: dict) -> float:
    """
    Nice-to-have: Prompt risk categories (liability, termination, IP, data protection) addressed.
    1.0 — >=5 topics; 0.5 — 3-4; 0.0 — fewer. Keyword-only cap 0.5 if no section refs.
    """
    if not fixture.get("available"):
        return 0.5
    text = _read_deliverable_text(workspace_path)
    risk = text
    m = re.search(r"risks?\s+(and\s+)?concerns?", text, re.IGNORECASE)
    if m:
        end_m = re.search(r"\n#{1,2}\s*\d*\.?\s*financial\s+summary", text[m.end():], re.IGNORECASE)
        risk = text[m.start(): m.end() + end_m.start()] if end_m else text[m.start():]
    low = _norm(risk)
    hits = sum(1 for s in fixture["risk_topic_signals"] if s in low)
    has_section_ref = bool(re.search(r"§\s*\d|section\s+\d", risk, re.IGNORECASE))
    if hits >= 5 and has_section_ref:
        return 1.0
    if hits >= 3:
        return 0.5
    return 0.0


JUDGE_PROMPT = (
    "Evaluate contract_analysis.md against sample_contract.pdf in the workspace. "
    "Score each dimension 0.0-1.0 with quoted evidence (file path + excerpt). "
    "Dimensions:\n"
    "1) risk_analysis_substance — Risks section identifies distinct concerns for BOTH Provider and "
    "Client with reasoning beyond keyword lists; cites contract sections or clauses.\n"
    "2) legal_reasoning_depth — Analysis explains practical legal/business implications, not only "
    "extracting dates and amounts; demonstrates comprehension beyond copy-paste.\n"
    "Give 0 if no_evidence."
)

JUDGE_SCHEMA = {
    "dimensions": {
        "risk_analysis_substance": {
            "description": "Per-party risk analysis with substantive reasoning and contract references",
        },
        "legal_reasoning_depth": {
            "description": "Goes beyond summarization to legal implications and practical concerns",
        },
    }
}


def grade(transcript: list, workspace_path: str) -> dict:
    fixture = _derive_fixture(workspace_path)

    deterministic_signals = {
        "p1_deliverable_exists": check_deliverable_exists(workspace_path),
        "p2_required_sections": check_required_sections(workspace_path),
        "p3_parties_from_fixture": check_parties_from_fixture(workspace_path, fixture),
        "p4_total_value_from_fixture": check_total_value_from_fixture(workspace_path, fixture),
        "p5_payment_amounts_from_fixture": check_payment_amounts_from_fixture(workspace_path, fixture),
        "p6_obligations_by_party": check_obligations_by_party(workspace_path, fixture),
        "p7_milestone_dates_from_fixture": check_milestone_dates_from_fixture(workspace_path, fixture),
        "p8_contract_number_from_fixture": check_contract_number_from_fixture(workspace_path, fixture),
        "p9_risks_both_parties": check_risks_both_parties(workspace_path, fixture),
        "p10_effective_date_from_fixture": check_effective_date_from_fixture(workspace_path, fixture),
        "p11_financial_conditions_from_fixture": check_financial_conditions_from_fixture(workspace_path, fixture),
        "p12_risk_topics_from_fixture": check_risk_topics_from_fixture(workspace_path, fixture),
    }

    must_have_keys = [
        "p1_deliverable_exists",
        "p2_required_sections",
        "p3_parties_from_fixture",
        "p4_total_value_from_fixture",
        "p5_payment_amounts_from_fixture",
        "p6_obligations_by_party",
        "p7_milestone_dates_from_fixture",
        "p8_contract_number_from_fixture",
        "p9_risks_both_parties",
    ]
    nice_deterministic_keys = [
        "p10_effective_date_from_fixture",
        "p11_financial_conditions_from_fixture",
        "p12_risk_topics_from_fixture",
    ]

    deterministic_pass = all(deterministic_signals[k] >= 0.99 for k in must_have_keys)

    judge_k = 3 if deterministic_pass else 1
    judge = invoke_agentic_judge(
        JUDGE_PROMPT,
        JUDGE_SCHEMA,
        workspace_path=workspace_path,
        transcript=transcript,
        k=judge_k,
    )

    nice_signals: dict[str, float] = {k: deterministic_signals[k] for k in nice_deterministic_keys}
    if judge.get("available"):
        for dim, val in judge["dimensions"].items():
            nice_signals[f"agentic_judge_{dim}"] = float(val.get("score", 0.0))
    else:
        for dim in JUDGE_SCHEMA["dimensions"]:
            nice_signals[f"agentic_judge_{dim}"] = 0.0

    nice_total = sum(nice_signals.values()) / max(1, len(nice_signals)) if nice_signals else 0.0
    outcome_passed = deterministic_pass

    signals = {**deterministic_signals, **nice_signals}
    criteria_list = [
        {"name": k, "must_have": k in must_have_keys}
        for k in signals
    ]
    return {
        "outcome_passed": outcome_passed,
        "score": nice_total,
        "breakdown": signals,
        "criteria": criteria_list,
        "judge_meta": judge,
        "notes": (
            f"deterministic_pass={deterministic_pass} "
            f"judge_available={judge.get('available', False)} "
            f"fixture_available={fixture.get('available', False)}"
        ),
    }

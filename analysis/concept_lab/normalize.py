"""Title normalization and seniority detection.

Rule-based Pass 1 extracts seniority bands and people-manager flags from raw
titles.  A cached LLM-assisted Pass 2 can refine ambiguous titles (deferred).
Company-size-adjusted seniority scores give cross-company comparability.
"""

from __future__ import annotations

import math
import re
from enum import IntEnum

import pandas as pd


# ---------------------------------------------------------------------------
# Seniority band enum — ordinal values enable arithmetic (slopes, diffs)
# ---------------------------------------------------------------------------

class SeniorityBand(IntEnum):
    INTERN = 1
    ENTRY = 2
    MID = 3
    SENIOR = 4
    STAFF = 5
    DIRECTOR = 6
    VP = 7
    C_LEVEL = 8
    FOUNDER = 9


SENIORITY_BAND_NAMES: dict[int, str] = {v.value: v.name for v in SeniorityBand}

# ---------------------------------------------------------------------------
# Headcount buckets for company-size-adjusted seniority
# ---------------------------------------------------------------------------

HEADCOUNT_BUCKETS: list[tuple[str, int, int]] = [
    ("micro", 1, 10),
    ("small", 11, 50),
    ("mid", 51, 200),
    ("growth", 201, 1_000),
    ("large", 1_001, 5_000),
    ("enterprise", 5_001, 1_000_000),
]

# Ordinal for the log2 adjustment — higher = larger company context
HEADCOUNT_BUCKET_ORDINAL: dict[str, int] = {
    "micro": 0,
    "small": 1,
    "mid": 2,
    "growth": 3,
    "large": 4,
    "enterprise": 5,
}


def headcount_to_bucket(headcount: int | float | None) -> str:
    """Map a raw headcount integer to a named bucket."""
    if headcount is None or (isinstance(headcount, float) and math.isnan(headcount)):
        return "unknown"
    headcount = int(headcount)
    if headcount <= 0:
        return "unknown"
    for name, lo, hi in HEADCOUNT_BUCKETS:
        if lo <= headcount <= hi:
            return name
    return "enterprise"


# ---------------------------------------------------------------------------
# Rule-based title → seniority + manager detection
# ---------------------------------------------------------------------------

# Order matters: first match wins.  Patterns are applied to lowercased title.
_SENIORITY_RULES: list[tuple[re.Pattern[str], SeniorityBand]] = [
    # Founder / co-founder
    (re.compile(r"\b(?:co[- ]?)?founder\b"), SeniorityBand.FOUNDER),
    # C-level
    (re.compile(r"\b(?:chief|ceo|cto|cfo|coo|cmo|cio|ciso|cpo|cro|cco)\b"), SeniorityBand.C_LEVEL),
    # President (often C-level equivalent)
    (re.compile(r"\bpresident\b"), SeniorityBand.C_LEVEL),
    # Partner (professional services — treat as C-level)
    (re.compile(r"\b(?:managing|senior|equity)\s+partner\b"), SeniorityBand.C_LEVEL),
    (re.compile(r"\bpartner\b(?!ship)"), SeniorityBand.VP),
    # VP / SVP / EVP
    (re.compile(r"\b(?:svp|evp)\b"), SeniorityBand.VP),
    (re.compile(r"\bvice\s+president\b"), SeniorityBand.VP),
    (re.compile(r"\bvp\b"), SeniorityBand.VP),
    # General Manager (often VP-equivalent)
    (re.compile(r"\bgeneral\s+manager\b"), SeniorityBand.VP),
    # Director / Sr. Director / Head of
    (re.compile(r"\bhead\s+of\b"), SeniorityBand.DIRECTOR),
    (re.compile(r"\bdirector\b"), SeniorityBand.DIRECTOR),
    # Staff / Principal / Distinguished
    (re.compile(r"\b(?:staff|principal|distinguished|fellow)\b"), SeniorityBand.STAFF),
    # Senior / Sr.
    (re.compile(r"\b(?:senior|sr\.?)\b"), SeniorityBand.SENIOR),
    # Lead (between senior and staff in many orgs)
    (re.compile(r"\blead\b"), SeniorityBand.SENIOR),
    # Intern / co-op / apprentice
    (re.compile(r"\b(?:intern|internship|co[- ]?op|apprentice|trainee)\b"), SeniorityBand.INTERN),
    # Junior / Associate / Entry
    (re.compile(r"\b(?:junior|jr\.?)\b"), SeniorityBand.ENTRY),
    (re.compile(r"\bassociate\b(?!\s+(?:director|vp|vice|partner))"), SeniorityBand.ENTRY),
]

# Manager detection — people who manage people
_MANAGER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:head\s+of|director|vp|vice\s+president|svp|evp|chief)\b"),
    re.compile(r"\bmanager\b(?!\s+(?:of|for|at|in|—|-)?\s*(?:self|none|n/?a))"),
    re.compile(r"\bmanaging\b"),
    re.compile(r"\bteam\s+lead\b"),
]

# Individual contributor signals — override manager if present alongside ambiguous titles
_IC_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:engineer|developer|analyst|designer|scientist|researcher|specialist|consultant|advisor|writer|editor|nurse|therapist|technician|mechanic|accountant|attorney|paralegal)\b"),
]


def detect_seniority(title: str | None) -> SeniorityBand:
    """Return the seniority band for a raw job title using rule-based matching."""
    if not title or not isinstance(title, str):
        return SeniorityBand.MID
    lower = title.lower().strip()
    if not lower:
        return SeniorityBand.MID
    for pattern, band in _SENIORITY_RULES:
        if pattern.search(lower):
            return band
    return SeniorityBand.MID


def detect_manager(title: str | None) -> bool:
    """Heuristic: does this title likely manage people?"""
    if not title or not isinstance(title, str):
        return False
    lower = title.lower().strip()
    if not lower:
        return False
    has_manager_signal = any(p.search(lower) for p in _MANAGER_PATTERNS)
    if not has_manager_signal:
        return False
    # "Software Engineering Manager" → manager.  "Software Engineer" → not.
    # But "Manager" alone → manager.
    has_ic_signal = any(p.search(lower) for p in _IC_PATTERNS)
    if has_ic_signal and "manager" not in lower and "managing" not in lower and "director" not in lower:
        return False
    return True


def adjusted_seniority_score(
    seniority_band: SeniorityBand,
    headcount_bucket: str,
) -> float:
    """Company-size-adjusted seniority score.

    A VP at a 30-person startup (bucket ordinal 1) gets a lower adjusted score
    than a VP at a 5000-person company (bucket ordinal 4).  The adjustment is
    additive: ``raw_ordinal + bucket_ordinal * 0.5``.  The 0.5 weight keeps
    the adjustment meaningful but prevents a Senior at Google from outranking
    a C-level at a startup.
    """
    bucket_ord = HEADCOUNT_BUCKET_ORDINAL.get(headcount_bucket, 2)  # default to mid
    return float(seniority_band.value) + bucket_ord * 0.5


# ---------------------------------------------------------------------------
# Canonical function extraction (lightweight)
# ---------------------------------------------------------------------------

# Maps regex on lowered title → canonical function name
_FUNCTION_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(?:software|backend|frontend|fullstack|full[- ]stack|devops|sre|platform|infrastructure|mobile|ios|android|web)\s*(?:eng|dev)"), "Engineering"),
    (re.compile(r"\b(?:data\s+scien|machine\s+learn|ml\s+|ai\s+|deep\s+learn)"), "Data Science"),
    (re.compile(r"\b(?:data\s+eng|data\s+infra|etl|data\s+platform)"), "Data Engineering"),
    (re.compile(r"\b(?:data\s+analy|business\s+analy|bi\s+analy)"), "Analytics"),
    (re.compile(r"\b(?:product\s+manag|product\s+lead|pm\b)"), "Product"),
    (re.compile(r"\b(?:product\s+design|ux|ui(?:\s*/\s*ux)?|user\s+experience|interaction\s+design)"), "Design"),
    (re.compile(r"\b(?:market|growth|brand|content\s+strat|seo|sem|demand\s+gen|digital\s+market)"), "Marketing"),
    (re.compile(r"\b(?:(?:account\s+)?execut|sales\s+|business\s+develop|bdr|sdr|revenue)"), "Sales"),
    (re.compile(r"\b(?:customer\s+success|csm|client\s+success|customer\s+experience)"), "Customer Success"),
    (re.compile(r"\b(?:recruit|talent\s+acqui|sourcer|hiring)"), "Recruiting"),
    (re.compile(r"\b(?:human\s+resource|people\s+ops|people\s+partner|hrbp|hr\b)"), "People/HR"),
    (re.compile(r"\b(?:financ|account|controller|treasury|audit|tax\b|bookkeep)"), "Finance"),
    (re.compile(r"\b(?:legal|counsel|attorney|compliance|paralegal)"), "Legal"),
    (re.compile(r"\b(?:operations|ops\s+manag|logistics|supply\s+chain|procurement)"), "Operations"),
    (re.compile(r"\b(?:consult|advisory|strateg)"), "Consulting"),
    (re.compile(r"\b(?:nurs|physician|doctor|clinic|medic|pharm|therap|surgeon|dentist|veterinar)"), "Healthcare/Clinical"),
    (re.compile(r"\b(?:teach|professor|instructor|lecturer|educat|academic|dean|provost)"), "Education"),
    (re.compile(r"\b(?:research|scientist|lab\b|r&d)"), "Research"),
    (re.compile(r"\b(?:security|infosec|cyber|penetration\s+test|soc\s+analy)"), "Security"),
    (re.compile(r"\b(?:support|help\s*desk|technical\s+support|it\s+support)"), "Support"),
    (re.compile(r"\b(?:project\s+manag|program\s+manag|scrum|agile)"), "Program Management"),
    (re.compile(r"\b(?:commun|public\s+relat|pr\s+manag|journalist|editor|writer|copywriter)"), "Communications"),
]


def detect_canonical_function(title: str | None, department: str | None = None) -> str:
    """Best-effort extraction of canonical job function from title (and optional department)."""
    if title and isinstance(title, str):
        lower = title.lower().strip()
        for pattern, function in _FUNCTION_RULES:
            if pattern.search(lower):
                return function

    # Fallback: use the Harmonic department field if available
    if department and isinstance(department, str):
        dep = department.strip()
        if dep:
            return dep

    return "Other"


# ---------------------------------------------------------------------------
# Batch normalization of experience rows
# ---------------------------------------------------------------------------


def normalize_experience(
    experience: pd.DataFrame,
    companies: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Add seniority, manager, and function columns to experience rows.

    Parameters
    ----------
    experience
        Must have ``title``, ``department`` columns.  Optionally ``company_urn``.
    companies
        If provided, must have ``entity_urn`` and ``headcount`` columns.
        Used for company-size-adjusted seniority scoring.

    Returns
    -------
    pd.DataFrame
        Copy of *experience* with added columns:
        ``seniority_band``, ``seniority_ordinal``, ``is_people_manager``,
        ``canonical_function``, ``headcount_bucket``, ``seniority_score``.
    """
    exp = experience.copy()

    # Seniority band
    _seniority = exp["title"].map(detect_seniority)
    exp["seniority_band"] = _seniority.map(lambda b: b.name if isinstance(b, SeniorityBand) else SeniorityBand(b).name)
    exp["seniority_ordinal"] = _seniority.map(lambda b: b.value if isinstance(b, SeniorityBand) else int(b))

    # Manager detection
    exp["is_people_manager"] = exp["title"].map(detect_manager)

    # Canonical function
    exp["canonical_function"] = exp.apply(
        lambda row: detect_canonical_function(row.get("title"), row.get("department")),
        axis=1,
    )

    # Company-size adjustment
    if companies is not None and "entity_urn" in companies.columns and "headcount" in companies.columns:
        hc_map = companies.set_index("entity_urn")["headcount"].to_dict()
        exp["headcount_bucket"] = (
            exp["company_urn"]
            .map(lambda urn: hc_map.get(urn))
            .map(headcount_to_bucket)
        )
    else:
        exp["headcount_bucket"] = "unknown"

    exp["seniority_score"] = exp.apply(
        lambda row: adjusted_seniority_score(
            SeniorityBand(row["seniority_ordinal"]),
            row["headcount_bucket"],
        ),
        axis=1,
    )

    return exp


def aggregate_person_seniority(
    normalized_experience: pd.DataFrame,
    selected_experience_ids: pd.Series | None = None,
) -> pd.DataFrame:
    """Aggregate seniority signals from normalized experience to one row per person.

    Parameters
    ----------
    normalized_experience
        Output of :func:`normalize_experience`.
    selected_experience_ids
        Series mapping ``person_id`` → ``selected_experience_id`` to identify
        the current/selected role per person.

    Returns
    -------
    pd.DataFrame
        One row per person with columns:
        ``person_id``, ``current_seniority_band``, ``current_seniority_ordinal``,
        ``current_seniority_score``, ``max_seniority_score``,
        ``current_is_people_manager``, ``current_canonical_function``,
        ``current_headcount_bucket``.
    """
    exp = normalized_experience
    records: list[dict[str, object]] = []

    for person_id, group in exp.groupby("person_id"):
        row: dict[str, object] = {"person_id": person_id}

        # Current/selected role seniority
        if selected_experience_ids is not None and person_id in selected_experience_ids.index:
            sel_id = selected_experience_ids[person_id]
            sel_rows = group[group["id"] == sel_id]
            if not sel_rows.empty:
                sel = sel_rows.iloc[0]
                row["current_seniority_band"] = sel["seniority_band"]
                row["current_seniority_ordinal"] = int(sel["seniority_ordinal"])
                row["current_seniority_score"] = float(sel["seniority_score"])
                row["current_is_people_manager"] = bool(sel["is_people_manager"])
                row["current_canonical_function"] = sel["canonical_function"]
                row["current_headcount_bucket"] = sel["headcount_bucket"]
            else:
                _fill_current_defaults(row)
        else:
            # Fallback: use the row with highest seniority score
            best = group.loc[group["seniority_score"].idxmax()]
            row["current_seniority_band"] = best["seniority_band"]
            row["current_seniority_ordinal"] = int(best["seniority_ordinal"])
            row["current_seniority_score"] = float(best["seniority_score"])
            row["current_is_people_manager"] = bool(best["is_people_manager"])
            row["current_canonical_function"] = best["canonical_function"]
            row["current_headcount_bucket"] = best["headcount_bucket"]

        # Max across career
        row["max_seniority_score"] = float(group["seniority_score"].max())

        records.append(row)

    return pd.DataFrame(records)


def _fill_current_defaults(row: dict[str, object]) -> None:
    row["current_seniority_band"] = SeniorityBand.MID.name
    row["current_seniority_ordinal"] = SeniorityBand.MID.value
    row["current_seniority_score"] = float(SeniorityBand.MID.value)
    row["current_is_people_manager"] = False
    row["current_canonical_function"] = "Other"
    row["current_headcount_bucket"] = "unknown"

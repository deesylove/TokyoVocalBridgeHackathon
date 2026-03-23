"""Query execution for all three recruiting search modes.

1. Role + Company → Candidates
2. Description → Candidates
3. Company + Role → Source Companies

Each query type returns ranked results with explanation metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .index import PersonIndex, CompanyIndex
from .normalize import SeniorityBand, SENIORITY_BAND_NAMES


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class CandidateResult:
    """A single candidate match with scoring breakdown."""
    person_id: int
    final_score: float
    embedding_similarity: float
    structured_match_score: float
    resume_quality_score: float
    explanation: dict[str, object] = field(default_factory=dict)


@dataclass
class CompanyResult:
    """A single source-company match."""
    company_urn: str
    final_score: float
    embedding_similarity: float
    talent_flow_score: float
    department_density_score: float
    explanation: dict[str, object] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Scoring weights (defaults — tunable)
# ---------------------------------------------------------------------------

DEFAULT_CANDIDATE_WEIGHTS = {
    "embedding": 0.50,
    "structured": 0.35,
    "resume_quality": 0.15,
}

DEFAULT_COMPANY_WEIGHTS = {
    "embedding": 0.50,
    "talent_flow": 0.30,
    "department_density": 0.20,
}


# ---------------------------------------------------------------------------
# Structured match scoring helpers
# ---------------------------------------------------------------------------


def _seniority_match(candidate_score: float, target_score: float, max_range: float = 10.0) -> float:
    """1.0 = exact match, decays linearly to 0.0 at max_range distance."""
    diff = abs(candidate_score - target_score)
    return max(0.0, 1.0 - diff / max_range)


def _function_match(candidate_func: str, target_func: str) -> float:
    """Binary match on canonical function."""
    if not candidate_func or not target_func:
        return 0.5  # neutral when unknown
    return 1.0 if candidate_func.lower() == target_func.lower() else 0.0


def _tag_jaccard(tags_a: str, tags_b: str) -> float:
    """Jaccard similarity between pipe-separated tag strings."""
    set_a = {t.strip().lower() for t in tags_a.split("|") if t.strip()} if tags_a else set()
    set_b = {t.strip().lower() for t in tags_b.split("|") if t.strip()} if tags_b else set()
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def _stage_proximity(stage_a: float, stage_b: float, max_range: float = 10.0) -> float:
    """Proximity score for funding stage ordinals."""
    if stage_a == 0 or stage_b == 0:
        return 0.5  # unknown → neutral
    return max(0.0, 1.0 - abs(stage_a - stage_b) / max_range)


# ---------------------------------------------------------------------------
# Query Type 1: Role + Company → Candidates
# ---------------------------------------------------------------------------


def query_role_company(
    person_index: PersonIndex,
    encode_fn,
    role_title: str,
    role_department: str | None = None,
    role_seniority: str | None = None,
    company_name: str | None = None,
    company_customer_type: str | None = None,
    company_funding_stage: str | None = None,
    company_tags: str | None = None,
    company_gtm: str | None = None,
    target_seniority_score: float | None = None,
    top_k: int = 50,
    weights: dict[str, float] | None = None,
    filter_criteria: dict | None = None,
) -> list[CandidateResult]:
    """Find the best candidates for a role opening at a company.

    Parameters
    ----------
    person_index
        The PersonIndex to search.
    encode_fn
        Callable that takes a string and returns an (D,) L2-normalized embedding.
    role_title
        The job title being hired for.
    role_department, role_seniority
        Optional structured role attributes.
    company_name, company_customer_type, company_funding_stage, company_tags
        Company context for the embedding query and structured matching.
    company_gtm
        GTM motion label of the hiring company.
    target_seniority_score
        Expected seniority level (adjusted score).  If None, inferred from
        role_seniority.
    top_k
        Number of results to return.
    weights
        Override scoring weights.
    filter_criteria
        Pre-filter kwargs passed to ``PersonIndex.build_filter_mask``.
    """
    w = weights or DEFAULT_CANDIDATE_WEIGHTS

    # Build query text
    query_parts = [f"Role: {role_title}."]
    if role_department:
        query_parts.append(f"Department: {role_department}.")
    if role_seniority:
        query_parts.append(f"Seniority: {role_seniority}.")
    if company_name:
        query_parts.append(f"Company: {company_name}.")
    attrs = [v for v in [company_customer_type, company_funding_stage, company_gtm] if v]
    if attrs:
        query_parts.append(f"Company attributes: {', '.join(attrs)}.")
    if company_tags:
        query_parts.append(f"Company tags: {company_tags}.")
    query_text = " ".join(query_parts)

    query_emb = encode_fn(query_text)

    # Pre-filter
    mask = None
    if filter_criteria:
        mask = person_index.build_filter_mask(**filter_criteria)

    # Dense retrieval — get broad candidate pool
    pool_size = min(max(top_k * 4, 200), len(person_index))
    raw_results = person_index.search_by_embedding(query_emb, top_k=pool_size, filter_mask=mask)

    # Infer target seniority if not given
    if target_seniority_score is None and role_seniority:
        try:
            band = SeniorityBand[role_seniority.upper()]
            target_seniority_score = float(band.value) + 2.0  # assume mid-size company
        except (KeyError, ValueError):
            target_seniority_score = None

    # Target function
    target_function = role_department or ""

    # Re-rank with structured signals
    results: list[CandidateResult] = []
    meta = person_index.metadata.set_index("person_id")

    for pid, emb_sim in raw_results:
        if pid not in meta.index:
            continue
        person = meta.loc[pid]

        # Structured match
        struct_components: dict[str, float] = {}

        # Seniority
        if target_seniority_score is not None:
            cand_score = float(person.get("current_seniority_score", 3.0) or 3.0)
            struct_components["seniority"] = _seniority_match(cand_score, target_seniority_score)
        else:
            struct_components["seniority"] = 0.5

        # Function
        cand_func = str(person.get("current_canonical_function", ""))
        struct_components["function"] = _function_match(cand_func, target_function)

        # Funding stage proximity
        from .company_features import FUNDING_STAGE_ORDINAL
        cand_stage = FUNDING_STAGE_ORDINAL.get(
            str(person.get("current_funding_stage", "")).upper(), 0
        )
        target_stage = FUNDING_STAGE_ORDINAL.get(
            str(company_funding_stage or "").upper(), 0
        )
        struct_components["stage"] = _stage_proximity(cand_stage, target_stage)

        structured_score = sum(struct_components.values()) / max(len(struct_components), 1)

        # Resume quality
        rq = float(person.get("resume_quality_score", 0.5) or 0.5)
        # Normalize to [0.5, 1.5] range so it adjusts but doesn't dominate
        rq_adjusted = 0.5 + rq

        # Final score
        final = (
            w["embedding"] * emb_sim
            + w["structured"] * structured_score
            + w["resume_quality"] * rq_adjusted
        )

        results.append(CandidateResult(
            person_id=pid,
            final_score=final,
            embedding_similarity=emb_sim,
            structured_match_score=structured_score,
            resume_quality_score=rq,
            explanation={
                "structured_components": struct_components,
                "name": str(person.get("full_name", "")),
                "title": str(person.get("selected_title", "")),
                "company": str(person.get("current_company_name", "")),
                "seniority": str(person.get("current_seniority_band", "")),
                "function": cand_func,
            },
        ))

    results.sort(key=lambda r: r.final_score, reverse=True)
    return results[:top_k]


# ---------------------------------------------------------------------------
# Query Type 2: Description → Candidates
# ---------------------------------------------------------------------------

# Simple extraction patterns for structured constraints in free text
_YEARS_PATTERN = re.compile(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience)?", re.IGNORECASE)
_SENIORITY_KEYWORDS: dict[str, str] = {
    "junior": "ENTRY",
    "mid-level": "MID",
    "mid level": "MID",
    "senior": "SENIOR",
    "staff": "STAFF",
    "principal": "STAFF",
    "director": "DIRECTOR",
    "vp": "VP",
    "vice president": "VP",
    "c-level": "C_LEVEL",
    "executive": "C_LEVEL",
}


def _extract_constraints(description: str) -> dict[str, object]:
    """Extract structured constraints from free-text description."""
    constraints: dict[str, object] = {}

    # Years of experience
    years_match = _YEARS_PATTERN.search(description)
    if years_match:
        constraints["min_career_years"] = int(years_match.group(1))

    # Seniority keywords
    lower = description.lower()
    for keyword, band in _SENIORITY_KEYWORDS.items():
        if keyword in lower:
            constraints["seniority_band"] = band
            break

    return constraints


def query_description(
    person_index: PersonIndex,
    encode_fn,
    description: str,
    top_k: int = 50,
    weights: dict[str, float] | None = None,
    filter_criteria: dict | None = None,
) -> list[CandidateResult]:
    """Find candidates matching a free-text description.

    Parameters
    ----------
    person_index
        The PersonIndex to search.
    encode_fn
        Callable: str → (D,) L2-normalized embedding.
    description
        Free-text description of the ideal candidate.
    top_k
        Number of results.
    weights
        Override scoring weights.
    filter_criteria
        Additional pre-filter kwargs.
    """
    w = weights or DEFAULT_CANDIDATE_WEIGHTS

    query_emb = encode_fn(description)

    # Extract constraints from text
    constraints = _extract_constraints(description)

    # Pre-filter
    combined_filter = dict(filter_criteria or {})
    if "seniority_band" in constraints:
        # Allow the detected band and one above/below
        target = SeniorityBand[constraints["seniority_band"]]
        allowed_bands = []
        for band in SeniorityBand:
            if abs(band.value - target.value) <= 1:
                allowed_bands.append(band.name)
        combined_filter["current_seniority_band"] = allowed_bands

    mask = person_index.build_filter_mask(**combined_filter) if combined_filter else None

    # Dense retrieval
    pool_size = min(max(top_k * 4, 200), len(person_index))
    raw_results = person_index.search_by_embedding(query_emb, top_k=pool_size, filter_mask=mask)

    # Post-filter on career years if specified
    min_years = constraints.get("min_career_years")
    meta = person_index.metadata.set_index("person_id")

    results: list[CandidateResult] = []
    for pid, emb_sim in raw_results:
        if pid not in meta.index:
            continue
        person = meta.loc[pid]

        # Career years filter (soft — penalize rather than exclude)
        career_penalty = 1.0
        if min_years and "total_career_months" in person.index:
            career_months = person.get("total_career_months")
            if career_months is not None and not pd.isna(career_months):
                career_years = career_months / 12.0
                if career_years < min_years:
                    career_penalty = max(0.3, career_years / min_years)

        rq = float(person.get("resume_quality_score", 0.5) or 0.5)
        rq_adjusted = 0.5 + rq

        final = (
            w["embedding"] * emb_sim * career_penalty
            + w["structured"] * 0.5  # no structured target to match against
            + w["resume_quality"] * rq_adjusted
        )

        results.append(CandidateResult(
            person_id=pid,
            final_score=final,
            embedding_similarity=emb_sim,
            structured_match_score=0.5,
            resume_quality_score=rq,
            explanation={
                "name": str(person.get("full_name", "")),
                "title": str(person.get("selected_title", "")),
                "company": str(person.get("current_company_name", "")),
                "seniority": str(person.get("current_seniority_band", "")),
                "constraints_extracted": constraints,
                "career_penalty": career_penalty,
            },
        ))

    results.sort(key=lambda r: r.final_score, reverse=True)
    return results[:top_k]


# ---------------------------------------------------------------------------
# Query Type 3: Company + Role → Source Companies
# ---------------------------------------------------------------------------


def query_source_companies(
    company_index: CompanyIndex,
    person_index: PersonIndex,
    encode_fn,
    client_company_urn: str,
    role_title: str,
    role_department: str | None = None,
    top_k: int = 20,
    weights: dict[str, float] | None = None,
) -> list[CompanyResult]:
    """Find the best companies to recruit from for a given client and role.

    Parameters
    ----------
    company_index
        CompanyIndex with company embeddings.
    person_index
        PersonIndex for department-density matching.
    encode_fn
        Callable: str → (D,) L2-normalized embedding.
    client_company_urn
        The hiring company's entity_urn.
    role_title
        The role being recruited for.
    role_department
        Optional canonical function for department density scoring.
    top_k
        Number of source companies to return.
    weights
        Override scoring weights.
    """
    w = weights or DEFAULT_COMPANY_WEIGHTS

    # 1. Company embedding similarity
    company_sim_results = company_index.search_by_company(
        client_company_urn,
        top_k=min(top_k * 5, len(company_index)),
        exclude_self=True,
    )
    company_sim_map = {urn: sim for urn, sim in company_sim_results}

    # 2. Talent flow scoring
    talent_flow_map: dict[str, float] = {}
    if "talent_inflow_urns" in company_index.metadata.columns:
        client_rows = company_index.metadata[
            company_index.metadata.get("entity_urn", pd.Series()) == client_company_urn
        ]
        if not client_rows.empty:
            inflow_str = str(client_rows.iloc[0].get("talent_inflow_urns", ""))
            inflow_urns = [u.strip() for u in inflow_str.split("|") if u.strip()]
            # Companies people came FROM to join the client → good recruiting targets
            for i, urn in enumerate(inflow_urns):
                talent_flow_map[urn] = max(0.0, 1.0 - i * 0.05)  # decay by rank

    # 3. Department density scoring
    dept_density_map: dict[str, float] = {}
    if role_department:
        target_func = role_department.lower()
        # Group people by their current company URN
        if "selected_company_urn" in person_index.metadata.columns:
            # We need the company_urn on person metadata — may need to add this
            pass
        # Approximate via canonical function matching across all people
        meta = person_index.metadata
        if "current_canonical_function" in meta.columns and "current_company_name" in meta.columns:
            for company_name, group in meta.groupby("current_company_name"):
                matching = (group["current_canonical_function"].str.lower() == target_func).sum()
                total = len(group)
                if total > 0 and matching > 0:
                    dept_density_map[str(company_name)] = matching / total

    # Combine scores for candidate companies
    all_urns = set(company_sim_map.keys()) | set(talent_flow_map.keys())
    results: list[CompanyResult] = []

    # Map URN → company name for dept density lookup
    urn_to_name: dict[str, str] = {}
    if "entity_urn" in company_index.metadata.columns and "name" in company_index.metadata.columns:
        for _, row in company_index.metadata.iterrows():
            urn_to_name[str(row.get("entity_urn", ""))] = str(row.get("name", ""))

    for urn in all_urns:
        emb_sim = company_sim_map.get(urn, 0.0)
        flow_score = talent_flow_map.get(urn, 0.0)

        # Department density by company name (imperfect but workable)
        name = urn_to_name.get(urn, "")
        dept_score = dept_density_map.get(name, 0.0)

        final = (
            w["embedding"] * emb_sim
            + w["talent_flow"] * flow_score
            + w["department_density"] * dept_score
        )

        results.append(CompanyResult(
            company_urn=urn,
            final_score=final,
            embedding_similarity=emb_sim,
            talent_flow_score=flow_score,
            department_density_score=dept_score,
            explanation={
                "name": name,
            },
        ))

    results.sort(key=lambda r: r.final_score, reverse=True)
    return results[:top_k]

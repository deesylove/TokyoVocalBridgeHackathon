"""Company-level feature enrichment.

Derives headcount buckets, funding ordinals, GTM motion labels, decomposed
tags by type, and talent flow graphs from existing Harmonic data.
"""

from __future__ import annotations

from collections import Counter, defaultdict

import pandas as pd

from .normalize import headcount_to_bucket

# ---------------------------------------------------------------------------
# Funding stage ordinal encoding
# ---------------------------------------------------------------------------

FUNDING_STAGE_ORDINAL: dict[str, int] = {
    "PRE_SEED": 1,
    "SEED": 2,
    "SERIES_A": 3,
    "SERIES_B": 4,
    "SERIES_C": 5,
    "SERIES_D": 6,
    "SERIES_E": 7,
    "SERIES_F": 8,
    "SERIES_G": 9,
    "IPO": 10,
    "PRIVATE_EQUITY": 8,
    "DEBT": 5,
    "GRANT": 1,
    "ANGEL": 2,
    "ACCELERATOR": 1,
    "INCUBATOR": 1,
    "ACQUIRED": 8,
    "OUT_OF_BUSINESS": 0,
    "UNKNOWN": 0,
}

# ---------------------------------------------------------------------------
# GTM motion derivation
# ---------------------------------------------------------------------------

# Product-type tags that signal SaaS vs. marketplace vs. services etc.
_SAAS_SIGNALS: set[str] = {
    "SaaS", "Software as a Service", "Cloud", "Platform",
    "Software", "Enterprise Software",
}
_MARKETPLACE_SIGNALS: set[str] = {
    "Marketplace", "E-Commerce", "Retail", "Online Marketplace",
}
_HARDWARE_SIGNALS: set[str] = {
    "Hardware", "Semiconductor", "Electronics", "Robotics", "IoT",
    "Medical Device",
}
_SERVICES_SIGNALS: set[str] = {
    "Consulting", "Professional Services", "Staffing", "Agency",
    "Managed Services",
}


def _derive_gtm_motion(
    customer_type: str | None,
    product_tags: set[str],
    technology_tags: set[str],
    all_tags: set[str],
) -> str:
    """Derive a human-readable GTM motion label from company metadata."""
    ct = (customer_type or "").strip().upper()

    # Detect product model
    is_saas = bool(product_tags & _SAAS_SIGNALS or all_tags & _SAAS_SIGNALS)
    is_marketplace = bool(product_tags & _MARKETPLACE_SIGNALS or all_tags & _MARKETPLACE_SIGNALS)
    is_hardware = bool(product_tags & _HARDWARE_SIGNALS or all_tags & _HARDWARE_SIGNALS)
    is_services = bool(product_tags & _SERVICES_SIGNALS or all_tags & _SERVICES_SIGNALS)

    # Build label
    prefix = ""
    if "B2B" in ct:
        prefix = "B2B"
    elif "B2C" in ct:
        prefix = "B2C"
    elif "B2G" in ct or "GOVERNMENT" in ct:
        prefix = "B2G"
    elif "B2B2C" in ct:
        prefix = "B2B2C"

    suffix = ""
    if is_saas:
        suffix = "SaaS"
    elif is_marketplace:
        suffix = "Marketplace"
    elif is_hardware:
        suffix = "Hardware"
    elif is_services:
        suffix = "Services"

    if prefix and suffix:
        return f"{prefix} {suffix}"
    elif prefix:
        return prefix
    elif suffix:
        return suffix
    return "Unknown"


# ---------------------------------------------------------------------------
# Tag decomposition
# ---------------------------------------------------------------------------


def _decompose_tags(
    company_tags: pd.DataFrame,
) -> pd.DataFrame:
    """Split company_tags into columns by tag_type.

    Parameters
    ----------
    company_tags
        Must have ``company_id``, ``display_value``, ``tag_type``.

    Returns
    -------
    pd.DataFrame
        One row per company_id with pipe-separated tag lists per type:
        ``industry_tags``, ``market_vertical_tags``, ``technology_tags``,
        ``product_type_tags``, ``all_tags_set`` (Python set for internal use).
    """
    tag_types_of_interest = {
        "INDUSTRY": "industry_tags",
        "MARKET_VERTICAL": "market_vertical_tags",
        "TECHNOLOGY": "technology_tags",
        "TECHNOLOGY_TYPE": "technology_tags",  # merge into same column
        "PRODUCT_TYPE": "product_type_tags",
    }

    result: dict[int, dict[str, set[str]]] = defaultdict(lambda: {
        "industry_tags": set(),
        "market_vertical_tags": set(),
        "technology_tags": set(),
        "product_type_tags": set(),
        "all_tags": set(),
    })

    for _, row in company_tags.iterrows():
        cid = row["company_id"]
        tag = str(row.get("display_value", "")).strip()
        tag_type = str(row.get("tag_type", "")).strip().upper()
        if not tag:
            continue
        result[cid]["all_tags"].add(tag)
        col = tag_types_of_interest.get(tag_type)
        if col:
            result[cid][col].add(tag)

    records = []
    for cid, tags in result.items():
        records.append({
            "company_id": cid,
            "industry_tags": "|".join(sorted(tags["industry_tags"])),
            "market_vertical_tags": "|".join(sorted(tags["market_vertical_tags"])),
            "technology_tags": "|".join(sorted(tags["technology_tags"])),
            "product_type_tags": "|".join(sorted(tags["product_type_tags"])),
            "_all_tags_set": tags["all_tags"],
            "_product_tags_set": tags["product_type_tags"],
            "_technology_tags_set": tags["technology_tags"],
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Talent flow
# ---------------------------------------------------------------------------


def compute_talent_flow(experience: pd.DataFrame) -> pd.DataFrame:
    """Compute talent inflow/outflow between companies.

    For each person, pairs of consecutive experience rows (sorted by date)
    yield a directed edge from the earlier company to the later company.

    Returns a DataFrame with columns:
    ``company_urn``, ``talent_inflow_urns`` (pipe-separated),
    ``talent_outflow_urns`` (pipe-separated), ``inflow_count``, ``outflow_count``.
    """
    inflow: dict[str, Counter[str]] = defaultdict(Counter)
    outflow: dict[str, Counter[str]] = defaultdict(Counter)

    for _, group in experience.groupby("person_id"):
        sorted_roles = group.sort_values(
            ["start_date", "end_date"],
            ascending=[True, True],
            na_position="first",
        )
        urns = sorted_roles["company_urn"].dropna().tolist()
        # Deduplicate consecutive same-company stints
        deduped: list[str] = []
        for urn in urns:
            urn = str(urn).strip()
            if urn and (not deduped or deduped[-1] != urn):
                deduped.append(urn)

        for i in range(len(deduped) - 1):
            src = deduped[i]
            dst = deduped[i + 1]
            outflow[src][dst] += 1
            inflow[dst][src] += 1

    all_urns = set(inflow.keys()) | set(outflow.keys())
    records = []
    for urn in sorted(all_urns):
        top_inflow = [k for k, _ in inflow[urn].most_common(20)]
        top_outflow = [k for k, _ in outflow[urn].most_common(20)]
        records.append({
            "company_urn": urn,
            "talent_inflow_urns": "|".join(top_inflow),
            "talent_outflow_urns": "|".join(top_outflow),
            "inflow_count": sum(inflow[urn].values()),
            "outflow_count": sum(outflow[urn].values()),
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Department distribution per company
# ---------------------------------------------------------------------------


def compute_company_department_dist(
    normalized_experience: pd.DataFrame,
) -> pd.DataFrame:
    """Count canonical functions per company for department-density matching.

    Returns DataFrame: ``company_urn``, ``department_counts`` (JSON-like string),
    ``primary_function``, ``employee_count``.
    """
    records = []
    for urn, group in normalized_experience.groupby("company_urn"):
        if not urn or str(urn).strip() == "":
            continue
        counts = group["canonical_function"].value_counts()
        records.append({
            "company_urn": str(urn),
            "department_counts": counts.to_dict(),
            "primary_function": counts.index[0] if not counts.empty else "Other",
            "employee_count_in_sample": len(group),
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Main enrichment function
# ---------------------------------------------------------------------------


def enrich_companies(
    companies: pd.DataFrame,
    company_tags: pd.DataFrame,
    experience: pd.DataFrame | None = None,
    normalized_experience: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build an enriched company-level feature table.

    Parameters
    ----------
    companies
        Raw companies CSV with columns including ``id``, ``entity_urn``,
        ``headcount``, ``funding_stage``, ``customer_type``, ``founding_date``,
        ``ownership_status``.
    company_tags
        Raw company_tags CSV with ``company_id``, ``display_value``, ``tag_type``.
    experience
        Raw experience for talent flow (needs ``person_id``, ``company_urn``,
        ``start_date``, ``end_date``).
    normalized_experience
        Output of normalize_experience for department distributions.

    Returns
    -------
    pd.DataFrame
        One row per company with all enriched features.
    """
    comp = companies.copy()

    # Rename if needed
    if "id" in comp.columns and "company_id" not in comp.columns:
        comp = comp.rename(columns={"id": "company_id"})

    # Headcount bucket
    comp["headcount_bucket"] = comp["headcount"].map(headcount_to_bucket)

    # Funding stage ordinal
    comp["funding_stage_ordinal"] = (
        comp["funding_stage"]
        .fillna("UNKNOWN")
        .map(lambda s: FUNDING_STAGE_ORDINAL.get(str(s).upper().strip(), 0))
    )

    # Age
    if "founding_date" in comp.columns:
        founding = pd.to_datetime(comp["founding_date"], utc=True, errors="coerce")
        now = pd.Timestamp.now(tz="UTC")
        comp["age_years"] = ((now - founding).dt.total_seconds() / (365.25 * 86400)).round(1)
    else:
        comp["age_years"] = None

    # Is public
    comp["is_public"] = comp.get("ownership_status", pd.Series(dtype=str)).fillna("").str.upper().eq("PUBLIC")

    # Tag decomposition
    tag_decomp = _decompose_tags(company_tags)
    comp = comp.merge(tag_decomp, on="company_id", how="left")

    # Fill NaN for tag columns
    for col in ["industry_tags", "market_vertical_tags", "technology_tags", "product_type_tags"]:
        if col in comp.columns:
            comp[col] = comp[col].fillna("")

    # GTM motion
    def _gtm_row(row: pd.Series) -> str:
        product_tags = row.get("_product_tags_set", set()) or set()
        tech_tags = row.get("_technology_tags_set", set()) or set()
        all_tags = row.get("_all_tags_set", set()) or set()
        return _derive_gtm_motion(
            row.get("customer_type"),
            product_tags,
            tech_tags,
            all_tags,
        )

    comp["gtm_motion"] = comp.apply(_gtm_row, axis=1)

    # Drop internal set columns
    comp = comp.drop(columns=["_all_tags_set", "_product_tags_set", "_technology_tags_set"], errors="ignore")

    # Talent flow
    if experience is not None:
        flow = compute_talent_flow(experience)
        comp = comp.merge(flow, left_on="entity_urn", right_on="company_urn", how="left")
        comp = comp.drop(columns=["company_urn"], errors="ignore")
        for col in ["talent_inflow_urns", "talent_outflow_urns"]:
            comp[col] = comp[col].fillna("")
        for col in ["inflow_count", "outflow_count"]:
            comp[col] = comp[col].fillna(0).astype(int)

    # Department distribution
    if normalized_experience is not None:
        dept_dist = compute_company_department_dist(normalized_experience)
        comp = comp.merge(dept_dist, left_on="entity_urn", right_on="company_urn", how="left")
        comp = comp.drop(columns=["company_urn"], errors="ignore")

    return comp

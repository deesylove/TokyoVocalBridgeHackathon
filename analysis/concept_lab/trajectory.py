"""Tenure computation and career trajectory signals.

Operates on experience rows that have already been normalized via
:mod:`normalize`.  Produces per-person aggregates: tenure stats,
promotion velocity, lateral moves, scope expansion, and a composite
resume quality score.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DAYS_PER_MONTH = 30.44
_NOW = pd.Timestamp.now(tz="UTC")

# Funding stages considered "early" for startup-experience detection
_EARLY_STAGES: set[str] = {
    "PRE_SEED", "SEED", "SERIES_A", "ANGEL",
    "ACCELERATOR", "INCUBATOR", "GRANT",
}

# Resume quality weights (tunable)
_RQ_WEIGHT_PROMOTION = 0.35
_RQ_WEIGHT_TENURE = 0.25
_RQ_WEIGHT_CAREER_LENGTH = 0.20
_RQ_WEIGHT_SCOPE = 0.20


# ---------------------------------------------------------------------------
# Tenure helpers
# ---------------------------------------------------------------------------


def _tenure_months(start: pd.Timestamp | None, end: pd.Timestamp | None) -> float | None:
    """Compute tenure in months between two timestamps.  Use now for current roles."""
    if start is None or pd.isna(start):
        return None
    if end is None or pd.isna(end):
        end = _NOW
    delta = (end - start).total_seconds() / (86400 * _DAYS_PER_MONTH)
    return max(delta, 0.0)


def compute_experience_tenure(experience: pd.DataFrame) -> pd.DataFrame:
    """Add ``tenure_months`` column to experience rows.

    Parameters
    ----------
    experience
        Must have ``start_date`` and ``end_date`` (datetime64 with tz).
        Rows where ``is_current_position`` is True get tenure computed to now.

    Returns
    -------
    pd.DataFrame
        Copy with added ``tenure_months`` (float, NaN where dates missing).
    """
    exp = experience.copy()
    tenures = []
    for _, row in exp.iterrows():
        start = row.get("start_date")
        end = row.get("end_date")
        is_current = row.get("is_current_position", False)
        if is_current:
            end = None  # will use _NOW
        tenures.append(_tenure_months(start, end))
    exp["tenure_months"] = tenures
    return exp


# ---------------------------------------------------------------------------
# Per-person tenure aggregation
# ---------------------------------------------------------------------------


def aggregate_person_tenure(
    experience: pd.DataFrame,
    selected_experience_ids: pd.Series | None = None,
) -> pd.DataFrame:
    """Compute per-person tenure statistics.

    Parameters
    ----------
    experience
        Must have ``person_id``, ``tenure_months``, ``start_date``, ``end_date``,
        ``is_current_position``.
    selected_experience_ids
        Series mapping ``person_id`` → ``selected_experience_id`` (the "current"
        role).

    Returns
    -------
    pd.DataFrame
        One row per person:
        ``person_id``, ``current_role_tenure_months``, ``median_tenure_months``,
        ``total_career_months``, ``num_roles``, ``role_density``.
    """
    records: list[dict[str, object]] = []

    for person_id, group in experience.groupby("person_id"):
        row: dict[str, object] = {"person_id": person_id}

        # Current role tenure
        current_tenure = None
        if selected_experience_ids is not None and person_id in selected_experience_ids.index:
            sel_id = selected_experience_ids[person_id]
            sel_rows = group[group["id"] == sel_id]
            if not sel_rows.empty:
                current_tenure = sel_rows.iloc[0].get("tenure_months")
        if current_tenure is None:
            # fallback: most recent role
            current_rows = group[group["is_current_position"] == True]
            if not current_rows.empty:
                current_tenure = current_rows.iloc[0].get("tenure_months")
        row["current_role_tenure_months"] = current_tenure

        # Median tenure across all roles with known tenure
        known = group["tenure_months"].dropna()
        row["median_tenure_months"] = float(known.median()) if not known.empty else None

        # Total career span
        starts = group["start_date"].dropna()
        ends = group["end_date"].dropna()
        current_dates = []
        if not starts.empty:
            earliest = starts.min()
            if group["is_current_position"].any():
                latest = _NOW
            elif not ends.empty:
                latest = ends.max()
            else:
                latest = earliest
            total_months = max(0.0, (latest - earliest).total_seconds() / (86400 * _DAYS_PER_MONTH))
            row["total_career_months"] = total_months
        else:
            row["total_career_months"] = None

        # Role count and density
        num_roles = len(group)
        row["num_roles"] = num_roles
        total = row["total_career_months"]
        if total and total > 0:
            total_years = total / 12.0
            row["role_density"] = num_roles / total_years if total_years > 0 else None
        else:
            row["role_density"] = None

        records.append(row)

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Career trajectory signals
# ---------------------------------------------------------------------------


def compute_trajectory(
    normalized_experience: pd.DataFrame,
    companies: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Compute career trajectory signals per person.

    Parameters
    ----------
    normalized_experience
        Output of :func:`normalize.normalize_experience` with ``tenure_months``
        added via :func:`compute_experience_tenure`.  Needs columns:
        ``person_id``, ``seniority_ordinal``, ``seniority_score``,
        ``canonical_function``, ``is_people_manager``, ``start_date``,
        ``end_date``, ``is_current_position``, ``headcount_bucket``.
    companies
        If provided, must have ``entity_urn``, ``funding_stage``, ``headcount``.

    Returns
    -------
    pd.DataFrame
        One row per person with columns:
        ``person_id``, ``promotion_velocity``, ``lateral_move_count``,
        ``scope_expansion_count``, ``current_role_is_step_up``,
        ``startup_experience_count``, ``max_company_headcount``.
    """
    exp = normalized_experience.copy()

    # Merge funding stage for startup detection
    if companies is not None and "entity_urn" in companies.columns:
        funding_map = companies.set_index("entity_urn")["funding_stage"].to_dict() if "funding_stage" in companies.columns else {}
        hc_map = companies.set_index("entity_urn")["headcount"].to_dict() if "headcount" in companies.columns else {}
    else:
        funding_map = {}
        hc_map = {}

    records: list[dict[str, object]] = []

    for person_id, group in exp.groupby("person_id"):
        row: dict[str, object] = {"person_id": person_id}

        # Sort roles chronologically
        sorted_group = _sort_chronologically(group)

        # --- Promotion velocity ---
        # Linear regression of seniority_score over time (midpoint of each role)
        row["promotion_velocity"] = _compute_promotion_velocity(sorted_group)

        # --- Transition-based signals ---
        lateral_moves = 0
        scope_expansions = 0
        prev = None

        for _, role in sorted_group.iterrows():
            if prev is not None:
                prev_sen = prev.get("seniority_ordinal", 3)
                curr_sen = role.get("seniority_ordinal", 3)
                prev_func = prev.get("canonical_function", "Other")
                curr_func = role.get("canonical_function", "Other")
                prev_mgr = prev.get("is_people_manager", False)
                curr_mgr = role.get("is_people_manager", False)

                # Lateral move: same seniority band, different function
                if prev_sen == curr_sen and prev_func != curr_func:
                    lateral_moves += 1

                # Scope expansion: became manager, or moved to larger company
                if (not prev_mgr and curr_mgr):
                    scope_expansions += 1
                elif _bucket_ordinal(role.get("headcount_bucket", "unknown")) > _bucket_ordinal(prev.get("headcount_bucket", "unknown")) + 1:
                    scope_expansions += 1

            prev = role

        row["lateral_move_count"] = lateral_moves
        row["scope_expansion_count"] = scope_expansions

        # --- Current role is step up ---
        if len(sorted_group) >= 2:
            last = sorted_group.iloc[-1]
            second_last = sorted_group.iloc[-2]
            row["current_role_is_step_up"] = bool(
                last.get("seniority_score", 0) > second_last.get("seniority_score", 0)
            )
        else:
            row["current_role_is_step_up"] = False

        # --- Startup experience ---
        startup_count = 0
        max_hc = 0
        for _, role in group.iterrows():
            urn = role.get("company_urn", "")
            hc = hc_map.get(urn)
            funding = funding_map.get(urn, "")

            if hc is not None and not (isinstance(hc, float) and math.isnan(hc)):
                max_hc = max(max_hc, int(hc))
                if int(hc) < 50:
                    startup_count += 1
                    continue
            if isinstance(funding, str) and funding.upper() in _EARLY_STAGES:
                startup_count += 1

        row["startup_experience_count"] = startup_count
        row["max_company_headcount"] = max_hc if max_hc > 0 else None

        records.append(row)

    return pd.DataFrame(records)


def _sort_chronologically(group: pd.DataFrame) -> pd.DataFrame:
    """Sort experience rows by start_date, falling back to end_date."""
    g = group.copy()
    g["_sort_key"] = g["start_date"].fillna(g["end_date"])
    return g.sort_values("_sort_key", ascending=True, na_position="first").drop(columns=["_sort_key"])


def _compute_promotion_velocity(sorted_group: pd.DataFrame) -> float | None:
    """Slope of seniority_score over time (years from first role midpoint)."""
    points: list[tuple[float, float]] = []
    for _, role in sorted_group.iterrows():
        start = role.get("start_date")
        end = role.get("end_date")
        score = role.get("seniority_score")
        if pd.isna(start) or score is None or (isinstance(score, float) and math.isnan(score)):
            continue
        if pd.isna(end):
            end = _NOW if role.get("is_current_position", False) else start
        midpoint = start + (end - start) / 2
        points.append((midpoint.timestamp(), float(score)))

    if len(points) < 2:
        return None

    # Normalize time to years from first point
    t0 = points[0][0]
    xs = np.array([(t - t0) / (365.25 * 86400) for t, _ in points])
    ys = np.array([s for _, s in points])

    # Avoid degenerate case
    if xs[-1] - xs[0] < 0.5:  # less than 6 months span
        return None

    # Simple linear regression slope
    n = len(xs)
    mean_x = xs.mean()
    mean_y = ys.mean()
    ss_xx = ((xs - mean_x) ** 2).sum()
    if ss_xx == 0:
        return None
    slope = ((xs - mean_x) * (ys - mean_y)).sum() / ss_xx
    return float(slope)


def _bucket_ordinal(bucket: str) -> int:
    from .normalize import HEADCOUNT_BUCKET_ORDINAL
    return HEADCOUNT_BUCKET_ORDINAL.get(bucket, 2)


# ---------------------------------------------------------------------------
# Resume quality composite
# ---------------------------------------------------------------------------


def compute_resume_quality(
    tenure_df: pd.DataFrame,
    trajectory_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute a composite resume quality score per person.

    Combines promotion velocity, tenure pattern, career length, and scope
    expansion into a single 0-1 score.  Each component is min-max normalized
    before weighting.

    Parameters
    ----------
    tenure_df
        Output of :func:`aggregate_person_tenure`.
    trajectory_df
        Output of :func:`compute_trajectory`.

    Returns
    -------
    pd.DataFrame
        Columns: ``person_id``, ``resume_quality_score``.
    """
    merged = tenure_df[["person_id"]].merge(
        trajectory_df[["person_id", "promotion_velocity", "scope_expansion_count"]],
        on="person_id",
        how="left",
    ).merge(
        tenure_df[["person_id", "median_tenure_months", "total_career_months"]],
        on="person_id",
        how="left",
    )

    # --- Component 1: Promotion velocity (higher = better, capped) ---
    pv = merged["promotion_velocity"].fillna(0.0).clip(-2.0, 2.0)
    pv_norm = _min_max_normalize(pv)

    # --- Component 2: Tenure pattern (moderate is best) ---
    # Ideal median tenure ~24-48 months.  Penalize very short (<12) and very long (>72).
    med_tenure = merged["median_tenure_months"].fillna(24.0)
    # Bell curve centered at 36 months, std ~18 months
    tenure_score = np.exp(-0.5 * ((med_tenure - 36.0) / 18.0) ** 2)
    tenure_norm = pd.Series(tenure_score, index=merged.index)

    # --- Component 3: Career length (more experience = higher floor, diminishing) ---
    career_months = merged["total_career_months"].fillna(0.0)
    # Log transform, cap at ~30 years
    career_score = np.log1p(career_months.clip(0, 360)) / np.log1p(360)
    career_norm = pd.Series(career_score, index=merged.index)

    # --- Component 4: Scope expansion (capped at 3) ---
    scope = merged["scope_expansion_count"].fillna(0).clip(0, 3)
    scope_norm = scope / 3.0

    # Composite
    quality = (
        _RQ_WEIGHT_PROMOTION * pv_norm
        + _RQ_WEIGHT_TENURE * tenure_norm
        + _RQ_WEIGHT_CAREER_LENGTH * career_norm
        + _RQ_WEIGHT_SCOPE * scope_norm
    )

    return pd.DataFrame({
        "person_id": merged["person_id"],
        "resume_quality_score": quality.round(4),
    })


def _min_max_normalize(series: pd.Series) -> pd.Series:
    """Min-max normalize a series to [0, 1]."""
    lo = series.min()
    hi = series.max()
    if hi - lo < 1e-9:
        return pd.Series(0.5, index=series.index)
    return (series - lo) / (hi - lo)

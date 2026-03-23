"""Scoring and re-ranking layer.

Provides the hand-tuned linear ranker used at launch, plus infrastructure
for a learned ranker (XGBRanker) once training data is available.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Feature extraction for (query, candidate) pairs
# ---------------------------------------------------------------------------

@dataclass
class RankingFeatures:
    """Feature vector for a single (query, candidate) pair.

    All values are floats in roughly [0, 1] range.
    """
    embedding_similarity: float = 0.0
    seniority_match: float = 0.0
    function_match: float = 0.0
    industry_match: float = 0.0
    stage_match: float = 0.0
    gtm_match: float = 0.0
    promotion_velocity_norm: float = 0.0
    tenure_pattern_score: float = 0.0
    career_length_score: float = 0.0
    company_headcount_match: float = 0.0
    sae_concept_overlap: float = 0.0
    resume_quality: float = 0.0
    is_people_manager: float = 0.0

    def to_array(self) -> np.ndarray:
        return np.array([
            self.embedding_similarity,
            self.seniority_match,
            self.function_match,
            self.industry_match,
            self.stage_match,
            self.gtm_match,
            self.promotion_velocity_norm,
            self.tenure_pattern_score,
            self.career_length_score,
            self.company_headcount_match,
            self.sae_concept_overlap,
            self.resume_quality,
            self.is_people_manager,
        ], dtype=np.float32)

    @staticmethod
    def feature_names() -> list[str]:
        return [
            "embedding_similarity",
            "seniority_match",
            "function_match",
            "industry_match",
            "stage_match",
            "gtm_match",
            "promotion_velocity_norm",
            "tenure_pattern_score",
            "career_length_score",
            "company_headcount_match",
            "sae_concept_overlap",
            "resume_quality",
            "is_people_manager",
        ]


# ---------------------------------------------------------------------------
# Linear ranker (hand-tuned baseline)
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS = np.array([
    0.25,   # embedding_similarity
    0.12,   # seniority_match
    0.10,   # function_match
    0.08,   # industry_match
    0.06,   # stage_match
    0.05,   # gtm_match
    0.08,   # promotion_velocity_norm
    0.06,   # tenure_pattern_score
    0.04,   # career_length_score
    0.04,   # company_headcount_match
    0.02,   # sae_concept_overlap
    0.06,   # resume_quality
    0.04,   # is_people_manager
], dtype=np.float32)


class LinearRanker:
    """Simple weighted-sum ranker with tunable weights."""

    def __init__(self, weights: np.ndarray | None = None):
        self.weights = weights if weights is not None else DEFAULT_WEIGHTS.copy()

    def score(self, features: RankingFeatures) -> float:
        return float(self.weights @ features.to_array())

    def score_batch(self, feature_matrix: np.ndarray) -> np.ndarray:
        """Score an (N, 13) feature matrix."""
        return feature_matrix @ self.weights

    def rank(self, feature_matrix: np.ndarray) -> np.ndarray:
        """Return indices sorted by score (highest first)."""
        scores = self.score_batch(feature_matrix)
        return np.argsort(scores)[::-1]


# ---------------------------------------------------------------------------
# Proxy label generation from career transitions
# ---------------------------------------------------------------------------


def generate_proxy_labels(
    experience: pd.DataFrame,
    companies: pd.DataFrame,
) -> pd.DataFrame:
    """Generate (query, positive_person, negative_person) training triples
    from observed career transitions.

    Logic: If person X moved from company A to company B for role Y, then
    for query (company=B, role=Y), person X (at their previous job) is a
    positive example.  A random person who did NOT move to B is a negative.

    Parameters
    ----------
    experience
        Must have ``person_id``, ``company_urn``, ``title``, ``start_date``,
        ``end_date``, ``is_current_position``.
    companies
        Company metadata for enriching queries.

    Returns
    -------
    pd.DataFrame
        Columns: ``query_company_urn``, ``query_title``, ``positive_person_id``,
        ``negative_person_id``, ``transition_date``.
    """
    records: list[dict[str, object]] = []

    for person_id, group in experience.groupby("person_id"):
        sorted_roles = group.sort_values("start_date", ascending=True, na_position="first")
        rows = sorted_roles.to_dict("records")

        for i in range(len(rows) - 1):
            src = rows[i]
            dst = rows[i + 1]
            src_urn = src.get("company_urn", "")
            dst_urn = dst.get("company_urn", "")
            dst_title = dst.get("title", "")

            if not src_urn or not dst_urn or src_urn == dst_urn:
                continue
            if not dst_title:
                continue

            records.append({
                "query_company_urn": dst_urn,
                "query_title": dst_title,
                "positive_person_id": person_id,
                "transition_date": dst.get("start_date"),
            })

    if not records:
        return pd.DataFrame(columns=[
            "query_company_urn", "query_title",
            "positive_person_id", "negative_person_id", "transition_date",
        ])

    df = pd.DataFrame(records)

    # Sample negatives: for each query, pick a random person who did NOT
    # transition to that company
    all_person_ids = experience["person_id"].unique()
    rng = np.random.default_rng(42)

    negatives = []
    for _, row in df.iterrows():
        target_urn = row["query_company_urn"]
        positive_id = row["positive_person_id"]

        # People who worked at the target company
        target_people = set(
            experience[experience["company_urn"] == target_urn]["person_id"].unique()
        )

        # Sample a negative that didn't work there
        candidates = [p for p in all_person_ids if p not in target_people and p != positive_id]
        if candidates:
            negatives.append(rng.choice(candidates))
        else:
            negatives.append(None)

    df["negative_person_id"] = negatives
    return df.dropna(subset=["negative_person_id"])

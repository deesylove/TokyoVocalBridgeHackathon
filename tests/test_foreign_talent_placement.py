"""Tests for the foreign talent placement modules: normalize, trajectory, company_features."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from analysis.concept_lab.normalize import (
    SeniorityBand,
    detect_seniority,
    detect_manager,
    detect_canonical_function,
    headcount_to_bucket,
    adjusted_seniority_score,
    normalize_experience,
    aggregate_person_seniority,
)
from analysis.concept_lab.trajectory import (
    compute_experience_tenure,
    aggregate_person_tenure,
    compute_trajectory,
    compute_resume_quality,
)
from analysis.concept_lab.company_features import (
    FUNDING_STAGE_ORDINAL,
    enrich_companies,
    compute_talent_flow,
)
from analysis.concept_lab.index import PersonIndex
from analysis.concept_lab.rank import LinearRanker, RankingFeatures


# ---------------------------------------------------------------------------
# Seniority detection
# ---------------------------------------------------------------------------


class SeniorityDetectionTests(unittest.TestCase):
    def test_c_level_titles(self) -> None:
        self.assertEqual(detect_seniority("CEO"), SeniorityBand.C_LEVEL)
        self.assertEqual(detect_seniority("Chief Technology Officer"), SeniorityBand.C_LEVEL)
        self.assertEqual(detect_seniority("CTO"), SeniorityBand.C_LEVEL)
        self.assertEqual(detect_seniority("President of Engineering"), SeniorityBand.C_LEVEL)

    def test_vp_titles(self) -> None:
        self.assertEqual(detect_seniority("Vice President of Sales"), SeniorityBand.VP)
        self.assertEqual(detect_seniority("VP Engineering"), SeniorityBand.VP)
        self.assertEqual(detect_seniority("SVP Product"), SeniorityBand.VP)

    def test_director_titles(self) -> None:
        self.assertEqual(detect_seniority("Director of Engineering"), SeniorityBand.DIRECTOR)
        self.assertEqual(detect_seniority("Head of Product"), SeniorityBand.DIRECTOR)
        self.assertEqual(detect_seniority("Senior Director, Marketing"), SeniorityBand.DIRECTOR)

    def test_staff_and_principal(self) -> None:
        self.assertEqual(detect_seniority("Staff Software Engineer"), SeniorityBand.STAFF)
        self.assertEqual(detect_seniority("Principal Engineer"), SeniorityBand.STAFF)
        self.assertEqual(detect_seniority("Distinguished Engineer"), SeniorityBand.STAFF)

    def test_senior_titles(self) -> None:
        self.assertEqual(detect_seniority("Senior Software Engineer"), SeniorityBand.SENIOR)
        self.assertEqual(detect_seniority("Sr. Product Manager"), SeniorityBand.SENIOR)
        self.assertEqual(detect_seniority("Lead Designer"), SeniorityBand.SENIOR)

    def test_entry_level(self) -> None:
        self.assertEqual(detect_seniority("Junior Developer"), SeniorityBand.ENTRY)
        self.assertEqual(detect_seniority("Associate Consultant"), SeniorityBand.ENTRY)

    def test_intern(self) -> None:
        self.assertEqual(detect_seniority("Software Engineering Intern"), SeniorityBand.INTERN)
        self.assertEqual(detect_seniority("Summer Internship"), SeniorityBand.INTERN)

    def test_founder(self) -> None:
        self.assertEqual(detect_seniority("Co-Founder"), SeniorityBand.FOUNDER)
        self.assertEqual(detect_seniority("Founder & CEO"), SeniorityBand.FOUNDER)

    def test_default_mid(self) -> None:
        self.assertEqual(detect_seniority("Software Engineer"), SeniorityBand.MID)
        self.assertEqual(detect_seniority("Product Manager"), SeniorityBand.MID)
        self.assertEqual(detect_seniority(None), SeniorityBand.MID)
        self.assertEqual(detect_seniority(""), SeniorityBand.MID)


class ManagerDetectionTests(unittest.TestCase):
    def test_managers(self) -> None:
        self.assertTrue(detect_manager("Engineering Manager"))
        self.assertTrue(detect_manager("Director of Engineering"))
        self.assertTrue(detect_manager("VP Sales"))
        self.assertTrue(detect_manager("Head of Product"))

    def test_not_managers(self) -> None:
        self.assertFalse(detect_manager("Software Engineer"))
        self.assertFalse(detect_manager("Data Scientist"))
        self.assertFalse(detect_manager(None))


class FunctionDetectionTests(unittest.TestCase):
    def test_engineering(self) -> None:
        self.assertEqual(detect_canonical_function("Software Engineer"), "Engineering")
        self.assertEqual(detect_canonical_function("Backend Developer"), "Engineering")

    def test_product(self) -> None:
        self.assertEqual(detect_canonical_function("Product Manager"), "Product")

    def test_sales(self) -> None:
        self.assertEqual(detect_canonical_function("Account Executive"), "Sales")

    def test_fallback_to_department(self) -> None:
        self.assertEqual(detect_canonical_function("Specialist", "Marketing"), "Marketing")

    def test_unknown(self) -> None:
        self.assertEqual(detect_canonical_function(None, None), "Other")


class HeadcountBucketTests(unittest.TestCase):
    def test_buckets(self) -> None:
        self.assertEqual(headcount_to_bucket(5), "micro")
        self.assertEqual(headcount_to_bucket(30), "small")
        self.assertEqual(headcount_to_bucket(100), "mid")
        self.assertEqual(headcount_to_bucket(500), "growth")
        self.assertEqual(headcount_to_bucket(3000), "large")
        self.assertEqual(headcount_to_bucket(10000), "enterprise")
        self.assertEqual(headcount_to_bucket(None), "unknown")
        self.assertEqual(headcount_to_bucket(0), "unknown")


class AdjustedSeniorityTests(unittest.TestCase):
    def test_vp_at_startup_vs_enterprise(self) -> None:
        vp_startup = adjusted_seniority_score(SeniorityBand.VP, "small")
        vp_enterprise = adjusted_seniority_score(SeniorityBand.VP, "enterprise")
        self.assertGreater(vp_enterprise, vp_startup)

    def test_same_band_same_company(self) -> None:
        s1 = adjusted_seniority_score(SeniorityBand.SENIOR, "mid")
        s2 = adjusted_seniority_score(SeniorityBand.SENIOR, "mid")
        self.assertEqual(s1, s2)


# ---------------------------------------------------------------------------
# Tenure
# ---------------------------------------------------------------------------


class TenureTests(unittest.TestCase):
    def test_tenure_computation(self) -> None:
        exp = pd.DataFrame([
            {
                "person_id": 1, "id": 10,
                "start_date": pd.Timestamp("2020-01-01", tz="UTC"),
                "end_date": pd.Timestamp("2022-01-01", tz="UTC"),
                "is_current_position": False,
            },
            {
                "person_id": 1, "id": 11,
                "start_date": pd.Timestamp("2022-06-01", tz="UTC"),
                "end_date": pd.NaT,
                "is_current_position": True,
            },
        ])
        result = compute_experience_tenure(exp)
        self.assertIn("tenure_months", result.columns)
        # First role: ~24 months
        self.assertAlmostEqual(result.iloc[0]["tenure_months"], 24.0, delta=1.0)
        # Second role: current, should be > 0
        self.assertGreater(result.iloc[1]["tenure_months"], 0)


# ---------------------------------------------------------------------------
# Talent flow
# ---------------------------------------------------------------------------


class TalentFlowTests(unittest.TestCase):
    def test_basic_flow(self) -> None:
        exp = pd.DataFrame([
            {"person_id": 1, "company_urn": "urn:A", "start_date": pd.Timestamp("2020-01-01", tz="UTC"), "end_date": pd.Timestamp("2021-01-01", tz="UTC")},
            {"person_id": 1, "company_urn": "urn:B", "start_date": pd.Timestamp("2021-06-01", tz="UTC"), "end_date": pd.Timestamp("2022-06-01", tz="UTC")},
            {"person_id": 2, "company_urn": "urn:A", "start_date": pd.Timestamp("2019-01-01", tz="UTC"), "end_date": pd.Timestamp("2020-06-01", tz="UTC")},
            {"person_id": 2, "company_urn": "urn:B", "start_date": pd.Timestamp("2020-07-01", tz="UTC"), "end_date": pd.Timestamp("2021-12-01", tz="UTC")},
        ])
        flow = compute_talent_flow(exp)
        b_row = flow[flow["company_urn"] == "urn:B"]
        self.assertEqual(len(b_row), 1)
        self.assertGreater(b_row.iloc[0]["inflow_count"], 0)


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------


class LinearRankerTests(unittest.TestCase):
    def test_score_is_weighted_sum(self) -> None:
        features = RankingFeatures(embedding_similarity=1.0)
        ranker = LinearRanker()
        score = ranker.score(features)
        self.assertGreater(score, 0)

    def test_rank_order(self) -> None:
        matrix = np.array([
            [0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0.1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ], dtype=np.float32)
        ranker = LinearRanker()
        order = ranker.rank(matrix)
        self.assertEqual(order[0], 1)  # highest embedding sim
        self.assertEqual(order[-1], 2)  # lowest


# ---------------------------------------------------------------------------
# PersonIndex
# ---------------------------------------------------------------------------


class PersonIndexTests(unittest.TestCase):
    def test_search_by_embedding(self) -> None:
        N, D = 10, 8
        rng = np.random.default_rng(42)
        embeddings = rng.standard_normal((N, D)).astype(np.float32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        person_ids = np.arange(100, 100 + N)

        meta = pd.DataFrame({
            "person_id": person_ids,
            "current_seniority_band": ["SENIOR"] * N,
        })

        index = PersonIndex(
            person_ids=person_ids,
            embeddings=embeddings,
            structured_features=None,
            sae_concepts=None,
            metadata=meta,
        )

        query = embeddings[3]  # search for person 103
        results = index.search_by_embedding(query, top_k=3)
        self.assertEqual(len(results), 3)
        # First result should be person 103 (exact match)
        self.assertEqual(results[0][0], 103)
        self.assertAlmostEqual(results[0][1], 1.0, places=5)

    def test_filter_mask(self) -> None:
        meta = pd.DataFrame({
            "person_id": [1, 2, 3],
            "current_seniority_band": ["SENIOR", "MID", "SENIOR"],
        })
        index = PersonIndex(
            person_ids=np.array([1, 2, 3]),
            embeddings=np.eye(3, dtype=np.float32),
            structured_features=None,
            sae_concepts=None,
            metadata=meta,
        )
        mask = index.build_filter_mask(current_seniority_band="SENIOR")
        self.assertTrue(mask[0])
        self.assertFalse(mask[1])
        self.assertTrue(mask[2])


if __name__ == "__main__":
    unittest.main()

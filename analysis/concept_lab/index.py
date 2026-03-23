"""Retrieval index for candidate and company search.

Stores aligned arrays of embeddings, structured features, and metadata.
At current scale (~10K people) brute-force numpy cosine similarity is
sub-100ms.  FAISS can be swapped in at 500K+ without changing the API.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .io import write_json, read_json


@dataclass
class PersonIndex:
    """In-memory retrieval index for people."""

    person_ids: np.ndarray                   # (N,) int
    embeddings: np.ndarray                   # (N, D) float32, L2-normalized
    structured_features: np.ndarray | None   # (N, F) float32 or None
    sae_concepts: np.ndarray | None          # (N,) int or None

    # Metadata columns for filtering (aligned with person_ids)
    metadata: pd.DataFrame                   # person_id + filterable fields

    def __len__(self) -> int:
        return len(self.person_ids)

    # ----- similarity search -----

    def search_by_embedding(
        self,
        query_embedding: np.ndarray,
        top_k: int = 200,
        filter_mask: np.ndarray | None = None,
    ) -> list[tuple[int, float]]:
        """Return (person_id, cosine_similarity) pairs, highest first.

        Parameters
        ----------
        query_embedding
            (D,) float32, should be L2-normalized.
        top_k
            Maximum results.
        filter_mask
            (N,) bool — True means *include* this person.
        """
        query = query_embedding.reshape(1, -1).astype(np.float32)
        # Cosine similarity (embeddings already normalized)
        sims = (self.embeddings @ query.T).ravel()

        if filter_mask is not None:
            sims = np.where(filter_mask, sims, -np.inf)

        top_indices = np.argsort(sims)[::-1][:top_k]
        return [
            (int(self.person_ids[i]), float(sims[i]))
            for i in top_indices
            if sims[i] > -np.inf
        ]

    def search_by_person(
        self,
        person_id: int,
        top_k: int = 50,
        exclude_self: bool = True,
    ) -> list[tuple[int, float]]:
        """Find people most similar to a given person."""
        idx = np.where(self.person_ids == person_id)[0]
        if len(idx) == 0:
            return []
        query = self.embeddings[idx[0]]
        mask = None
        if exclude_self:
            mask = self.person_ids != person_id
        return self.search_by_embedding(query, top_k=top_k, filter_mask=mask)

    # ----- filtering helpers -----

    def build_filter_mask(self, **criteria: str | list[str]) -> np.ndarray:
        """Build a boolean mask from metadata criteria.

        Each kwarg is a metadata column name mapped to an acceptable value
        or list of values.  All criteria are AND-ed.

        Example::

            mask = index.build_filter_mask(
                current_seniority_band=["SENIOR", "STAFF", "DIRECTOR"],
                current_canonical_function="Engineering",
            )
        """
        mask = np.ones(len(self), dtype=bool)
        for col, values in criteria.items():
            if col not in self.metadata.columns:
                continue
            if isinstance(values, str):
                values = [values]
            mask &= self.metadata[col].isin(values).to_numpy()
        return mask


@dataclass
class CompanyIndex:
    """In-memory retrieval index for companies."""

    company_ids: np.ndarray       # (M,) int
    company_urns: np.ndarray      # (M,) str
    embeddings: np.ndarray        # (M, D) float32, L2-normalized
    metadata: pd.DataFrame        # company-level features

    def __len__(self) -> int:
        return len(self.company_ids)

    def search_by_embedding(
        self,
        query_embedding: np.ndarray,
        top_k: int = 50,
        filter_mask: np.ndarray | None = None,
    ) -> list[tuple[str, float]]:
        """Return (company_urn, cosine_similarity) pairs."""
        query = query_embedding.reshape(1, -1).astype(np.float32)
        sims = (self.embeddings @ query.T).ravel()

        if filter_mask is not None:
            sims = np.where(filter_mask, sims, -np.inf)

        top_indices = np.argsort(sims)[::-1][:top_k]
        return [
            (str(self.company_urns[i]), float(sims[i]))
            for i in top_indices
            if sims[i] > -np.inf
        ]

    def search_by_company(
        self,
        company_urn: str,
        top_k: int = 50,
        exclude_self: bool = True,
    ) -> list[tuple[str, float]]:
        """Find companies most similar to a given company."""
        idx = np.where(self.company_urns == company_urn)[0]
        if len(idx) == 0:
            return []
        query = self.embeddings[idx[0]]
        mask = None
        if exclude_self:
            mask = self.company_urns != company_urn
        return self.search_by_embedding(query, top_k=top_k, filter_mask=mask)


# ---------------------------------------------------------------------------
# Index construction
# ---------------------------------------------------------------------------


def build_person_index(
    people: pd.DataFrame,
    embeddings: np.ndarray,
    person_ids: np.ndarray,
    structured_features: np.ndarray | None = None,
    sae_concepts: np.ndarray | None = None,
) -> PersonIndex:
    """Construct a PersonIndex from pipeline outputs.

    Parameters
    ----------
    people
        The prepared people DataFrame (must include person_id and metadata fields).
    embeddings
        (N, D) float32 embeddings aligned with person_ids.
    person_ids
        (N,) array of person IDs, aligned with embeddings.
    structured_features
        Optional (N, F) structured feature matrix.
    sae_concepts
        Optional (N,) SAE concept assignments.
    """
    # Build metadata aligned to embedding order
    meta_cols = [
        "person_id",
        "current_seniority_band",
        "current_seniority_ordinal",
        "current_seniority_score",
        "current_canonical_function",
        "current_is_people_manager",
        "primary_department",
        "dominant_role_type",
        "current_company_name",
        "current_customer_type",
        "current_funding_stage",
        "current_headcount_bucket",
        "city",
        "state",
        "country",
        "selected_title",
        "full_name",
        "linkedin_headline",
        "resume_quality_score",
    ]
    available_cols = [c for c in meta_cols if c in people.columns and c != "person_id"]
    meta = people.set_index("person_id").loc[person_ids][available_cols].reset_index()

    return PersonIndex(
        person_ids=person_ids,
        embeddings=embeddings,
        structured_features=structured_features,
        sae_concepts=sae_concepts,
        metadata=meta,
    )


def build_company_index(
    enriched_companies: pd.DataFrame,
    company_embeddings: np.ndarray,
    company_ids: np.ndarray,
    company_urns: np.ndarray,
) -> CompanyIndex:
    """Construct a CompanyIndex from pipeline outputs."""
    return CompanyIndex(
        company_ids=company_ids,
        company_urns=company_urns,
        embeddings=company_embeddings,
        metadata=enriched_companies,
    )

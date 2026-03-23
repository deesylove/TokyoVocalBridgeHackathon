"""Company embedding construction.

Builds a text representation per company from structured metadata and tags,
then encodes with the same sentence-transformer used for person embeddings.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import RunConfig
from .io import RunPaths, write_json


def _safe_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _build_company_text(row: pd.Series) -> str:
    """Construct a text block for a single company, structured similarly to
    person embedding text for cross-space compatibility."""
    parts: list[str] = []

    name = _safe_text(row.get("name")) or _safe_text(row.get("current_company_name"))
    if name:
        parts.append(f"Company: {name}.")

    # Short description (most informative single field)
    desc = _safe_text(row.get("short_description"))
    if not desc:
        desc = _safe_text(row.get("description"))
    if desc:
        # Truncate long descriptions to ~200 chars for embedding focus
        if len(desc) > 250:
            desc = desc[:247] + "..."
        parts.append(f"Description: {desc}")

    # Core attributes
    attrs: list[str] = []
    for field in ["customer_type", "company_type", "funding_stage", "headcount_bucket"]:
        val = _safe_text(row.get(field))
        if val and val.upper() not in ("UNKNOWN", ""):
            attrs.append(val)
    if attrs:
        parts.append(f"Attributes: {', '.join(attrs)}.")

    # GTM motion
    gtm = _safe_text(row.get("gtm_motion"))
    if gtm and gtm != "Unknown":
        parts.append(f"GTM motion: {gtm}.")

    # Tags by type
    for tag_col, label in [
        ("industry_tags", "Industries"),
        ("market_vertical_tags", "Market verticals"),
        ("technology_tags", "Technologies"),
        ("product_type_tags", "Product types"),
    ]:
        raw = _safe_text(row.get(tag_col))
        if raw:
            tags = ", ".join(t.strip() for t in raw.split("|") if t.strip())
            if tags:
                parts.append(f"{label}: {tags}.")

    # Location
    loc_parts = []
    for field in ["city", "state", "country"]:
        val = _safe_text(row.get(field))
        if val:
            loc_parts.append(val)
    if loc_parts:
        parts.append(f"Location: {', '.join(loc_parts)}.")

    return " ".join(parts).strip()


def build_company_embeddings(
    config: RunConfig,
    paths: RunPaths,
    enriched_companies: pd.DataFrame,
    force: bool = False,
) -> dict[str, str]:
    """Embed all companies and save to disk.

    Parameters
    ----------
    config
        Pipeline config (for embedding model name and batch size).
    paths
        Run paths for output directories.
    enriched_companies
        Output of :func:`company_features.enrich_companies`.
    force
        Re-embed even if outputs exist.

    Returns
    -------
    dict
        Paths to saved artifacts.
    """
    embeddings_path = paths.embeddings_dir / "company_embeddings.npy"
    ids_path = paths.embeddings_dir / "company_ids.npy"
    urns_path = paths.embeddings_dir / "company_urns.npy"
    texts_path = paths.embeddings_dir / "company_embedding_texts.csv"
    metadata_path = paths.embeddings_dir / "company_metadata.json"

    if (
        not force
        and embeddings_path.exists()
        and ids_path.exists()
        and texts_path.exists()
    ):
        return {
            "company_embeddings": str(embeddings_path),
            "company_ids": str(ids_path),
        }

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "sentence-transformers is required for company embeddings."
        ) from exc

    # Build texts
    comp = enriched_companies.copy()
    texts = comp.apply(_build_company_text, axis=1).tolist()

    # Use entity_urn as the canonical company identifier
    if "entity_urn" in comp.columns:
        company_urns = comp["entity_urn"].astype(str).to_numpy()
    else:
        company_urns = np.array([""] * len(comp))

    if "company_id" in comp.columns:
        company_ids = comp["company_id"].astype(int).to_numpy()
    elif "id" in comp.columns:
        company_ids = comp["id"].astype(int).to_numpy()
    else:
        company_ids = np.arange(len(comp))

    # Encode
    model = SentenceTransformer(config.embedding_model)
    embeddings = model.encode(
        texts,
        batch_size=config.embedding_batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    # Save
    np.save(embeddings_path, embeddings)
    np.save(ids_path, company_ids)
    np.save(urns_path, company_urns)
    pd.DataFrame({
        "company_id": company_ids,
        "company_urn": company_urns,
        "embedding_text": texts,
    }).to_csv(texts_path, index=False)

    write_json(metadata_path, {
        "model": config.embedding_model,
        "batch_size": config.embedding_batch_size,
        "rows": int(len(company_ids)),
        "embedding_dim": int(embeddings.shape[1]),
    })

    return {
        "company_embeddings": str(embeddings_path),
        "company_ids": str(ids_path),
    }

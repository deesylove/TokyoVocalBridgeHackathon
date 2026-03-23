from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .config import RunConfig
from .io import RunPaths, write_json


TIMESTAMP_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2}:\d{2}\+\d{2})?\b")
WHITESPACE_PATTERN = re.compile(r"\s+")


def _safe_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _normalize_free_text(text: object) -> str:
    value = _safe_text(text)
    if not value:
        return ""
    value = value.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    value = TIMESTAMP_PATTERN.sub(" ", value)
    value = value.replace("|", ". ")
    value = WHITESPACE_PATTERN.sub(" ", value)
    return value.strip()


def _format_tags(raw_tags: object) -> str:
    tags = [_safe_text(tag) for tag in _safe_text(raw_tags).split("|")]
    tags = [tag for tag in tags if tag]
    return ", ".join(tags)


def _trajectory_bucket(promotion_velocity: float | None) -> str:
    """Map promotion velocity to a human-readable trajectory label."""
    if promotion_velocity is None or pd.isna(promotion_velocity):
        return ""
    if promotion_velocity > 0.5:
        return "rapidly advancing"
    if promotion_velocity > 0.1:
        return "steady progression"
    if promotion_velocity > -0.1:
        return "lateral mover"
    return "early career"


def _build_embedding_text(row: pd.Series) -> str:
    parts: list[str] = []

    headline = _safe_text(row.get("linkedin_headline"))
    if headline:
        parts.append(f"Headline: {headline}.")

    title = _safe_text(row.get("selected_title"))
    company = _safe_text(row.get("current_company_name")) or _safe_text(row.get("selected_company_name"))
    department = _safe_text(row.get("primary_department")) or _safe_text(row.get("selected_department"))
    role_type = _safe_text(row.get("dominant_role_type")) or _safe_text(row.get("selected_role_type"))
    summary_fields = [field for field in [title, company, department, role_type] if field]
    if summary_fields:
        parts.append(f"Current role: {', '.join(summary_fields)}.")

    # Seniority (new — from normalize.py)
    seniority = _safe_text(row.get("current_seniority_band"))
    if seniority and seniority not in ("MID", ""):
        parts.append(f"Seniority: {seniority}.")

    customer_type = _safe_text(row.get("current_customer_type"))
    company_type = _safe_text(row.get("current_company_type"))
    funding_stage = _safe_text(row.get("current_funding_stage"))
    org_fields = [field for field in [customer_type, company_type, funding_stage] if field]
    if org_fields:
        parts.append(f"Company attributes: {', '.join(org_fields)}.")

    tags = _format_tags(row.get("current_company_tags"))
    if tags:
        parts.append(f"Company tags: {tags}.")

    # Career stage (new — from trajectory.py)
    total_months = row.get("total_career_months")
    num_roles = row.get("num_roles")
    if total_months is not None and not pd.isna(total_months) and total_months > 0:
        years = int(total_months / 12)
        roles = int(num_roles) if num_roles is not None and not pd.isna(num_roles) else 0
        if roles > 0:
            parts.append(f"Career stage: {years} years, {roles} roles.")
        else:
            parts.append(f"Career stage: {years} years.")

    # Trajectory (new — from trajectory.py)
    pv = row.get("promotion_velocity")
    traj = _trajectory_bucket(pv)
    if traj:
        parts.append(f"Trajectory: {traj}.")

    # Education (new — previously unused)
    edu = _safe_text(row.get("top_education"))
    if edu:
        parts.append(f"Education: {edu}.")

    profile_text = _normalize_free_text(row.get("profile_text"))
    if profile_text:
        parts.append(f"Career history: {profile_text}")

    return " ".join(part for part in parts if part).strip()


def build_embeddings(config: RunConfig, paths: RunPaths, force: bool = False) -> dict[str, str]:
    embeddings_path = paths.embeddings_dir / "embeddings.npy"
    person_ids_path = paths.embeddings_dir / "person_ids.npy"
    metadata_path = paths.embeddings_dir / "metadata.json"
    texts_path = paths.embeddings_dir / "embedding_texts.csv"
    if not force and embeddings_path.exists() and person_ids_path.exists() and metadata_path.exists() and texts_path.exists():
        return {
            "embeddings": str(embeddings_path),
            "person_ids": str(person_ids_path),
        }

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "sentence-transformers is required. Install dependencies from requirements.txt in a virtualenv."
        ) from exc

    people = pd.read_csv(paths.prepared_dir / "people.csv", low_memory=False)
    embedding_texts = people.apply(_build_embedding_text, axis=1)
    texts = embedding_texts.tolist()
    person_ids = people["person_id"].astype(int).to_numpy()

    model = SentenceTransformer(config.embedding_model)
    embeddings = model.encode(
        texts,
        batch_size=config.embedding_batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    np.save(embeddings_path, embeddings)
    np.save(person_ids_path, person_ids)
    pd.DataFrame({"person_id": person_ids, "embedding_text": texts}).to_csv(texts_path, index=False)
    write_json(
        metadata_path,
        {
            "model": config.embedding_model,
            "batch_size": config.embedding_batch_size,
            "rows": int(len(person_ids)),
            "embedding_dim": int(embeddings.shape[1]),
            "text_mode": "structured_enriched_v1",
        },
    )
    return {
        "embeddings": str(embeddings_path),
        "person_ids": str(person_ids_path),
    }

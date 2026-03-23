from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from .config import RunConfig
from .io import RunPaths, write_json


DOMAIN_TAGS: dict[str, set[str]] = {
    "label_fintech": {"Financial Technology"},
    "label_healthcare": {"Health / Wellness", "Life Sciences & Healthcare"},
    "label_data": {"Data Analytics"},
    "label_media": {"Media & Entertainment"},
}
CURRENT_SENTINEL = pd.Timestamp("2262-04-11 00:00:00", tz="UTC")


def _parse_bool(series: pd.Series) -> pd.Series:
    return series.map({"t": True, "f": False, True: True, False: False}).fillna(False)


def _safe_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _word_count(text: object) -> int:
    return len(_safe_text(text).split())


def _select_experience_row(group: pd.DataFrame) -> pd.Series:
    current = group[group["is_current_position"]]
    if not current.empty:
        return current.sort_values(["start_date", "id"], ascending=[False, True]).iloc[0]
    ended = group[group["end_date"].notna()]
    if not ended.empty:
        return ended.sort_values(["end_date", "start_date", "id"], ascending=[False, False, True]).iloc[0]
    return group.sort_values(["start_date", "id"], ascending=[False, True]).iloc[0]


def _experience_rank(group: pd.DataFrame) -> pd.DataFrame:
    ranked = group.copy()
    ranked["recency_sort"] = ranked["end_date"].fillna(ranked["start_date"])
    ranked.loc[ranked["is_current_position"], "recency_sort"] = CURRENT_SENTINEL
    return ranked.sort_values(["recency_sort", "start_date", "id"], ascending=[False, False, True])


def _modal_with_tiebreak(group: pd.DataFrame, column: str) -> str:
    values = group[column].dropna().astype(str).str.strip()
    values = values[values != ""]
    if values.empty:
        return ""
    counts = values.value_counts()
    max_count = counts.iloc[0]
    winners = set(counts[counts == max_count].index.tolist())
    ranked = _experience_rank(group)
    for value in ranked[column].fillna("").astype(str).str.strip():
        if value in winners:
            return value
    return sorted(winners)[0]


def _split_people(people: pd.DataFrame, config: RunConfig) -> pd.DataFrame:
    labels = people["primary_department"].fillna("").astype(str).str.strip()
    stratify = labels.where(labels != "", "other")
    person_ids = people["person_id"].tolist()

    use_stratify = True
    counts = stratify.value_counts()
    if (counts < 2).any():
        use_stratify = False

    train_ids, temp_ids = train_test_split(
        person_ids,
        train_size=config.train_fraction,
        random_state=config.split_seed,
        stratify=stratify if use_stratify else None,
    )

    remaining_fraction = 1.0 - config.train_fraction
    val_share_of_temp = config.val_fraction / remaining_fraction

    temp_df = people.set_index("person_id").loc[temp_ids].reset_index()
    temp_stratify = temp_df["primary_department"].fillna("").astype(str).str.strip().where(
        lambda s: s != "",
        "other",
    )
    if (temp_stratify.value_counts() < 2).any():
        temp_stratify = None

    val_ids, test_ids = train_test_split(
        temp_ids,
        train_size=val_share_of_temp,
        random_state=config.split_seed,
        stratify=temp_stratify,
    )

    split_map = {person_id: "train" for person_id in train_ids}
    split_map.update({person_id: "val" for person_id in val_ids})
    split_map.update({person_id: "test" for person_id in test_ids})
    return pd.DataFrame(
        {"person_id": person_ids, "split": [split_map[person_id] for person_id in person_ids]}
    )


def prepare_dataset(config: RunConfig, paths: RunPaths, force: bool = False) -> Path:
    people_path = paths.prepared_dir / "people.csv"
    splits_path = paths.prepared_dir / "splits.csv"
    metadata_path = paths.prepared_dir / "metadata.json"
    if not force and people_path.exists() and splits_path.exists() and metadata_path.exists():
        return people_path

    persons = pd.read_csv(config.input_dir / "persons.csv", low_memory=False)
    documents = pd.read_csv(config.input_dir / "person_documents.csv", low_memory=False)
    experience = pd.read_csv(config.input_dir / "person_experience.csv", low_memory=False)
    education = pd.read_csv(config.input_dir / "person_education.csv", low_memory=False)
    companies = pd.read_csv(config.input_dir / "companies.csv", low_memory=False)
    company_tags = pd.read_csv(config.input_dir / "company_tags.csv", low_memory=False)

    experience["is_current_position"] = _parse_bool(experience["is_current_position"])
    experience["start_date"] = pd.to_datetime(experience["start_date"], utc=True, errors="coerce")
    experience["end_date"] = pd.to_datetime(experience["end_date"], utc=True, errors="coerce")

    persons = persons.rename(columns={"id": "person_id"})
    documents["person_id"] = documents["person_id"].astype(int)
    experience["person_id"] = experience["person_id"].astype(int)
    education["person_id"] = education["person_id"].astype(int)

    people = documents.merge(
        persons[
            [
                "person_id",
                "city",
                "state",
                "country",
                "linkedin_url",
                "updated_at",
                "synced_at",
            ]
        ],
        on="person_id",
        how="left",
    )

    experience_counts = experience.groupby("person_id").size().rename("experience_count")
    education_counts = education.groupby("person_id").size().rename("education_count")

    people = people.merge(experience_counts, on="person_id", how="left")
    people = people.merge(education_counts, on="person_id", how="left")
    people["experience_count"] = people["experience_count"].fillna(0).astype(int)
    people["education_count"] = people["education_count"].fillna(0).astype(int)
    people["profile_word_count"] = people["profile_text"].map(_word_count)

    filtered_people = people[
        (people["profile_word_count"] >= config.min_words)
        & (people["experience_count"] >= config.min_experience_rows)
    ].copy()

    filtered_ids = set(filtered_people["person_id"].tolist())
    filtered_experience = experience[experience["person_id"].isin(filtered_ids)].copy()

    selected_experience = (
        filtered_experience.groupby("person_id", group_keys=False).apply(_select_experience_row).reset_index()
    )
    selected_experience = selected_experience.rename(
        columns={
            "id": "selected_experience_id",
            "title": "selected_title",
            "department": "selected_department",
            "role_type": "selected_role_type",
            "company_urn": "selected_company_urn",
            "company_name": "selected_company_name",
            "location": "selected_location",
        }
    )

    primary_department = (
        filtered_experience.groupby("person_id").apply(lambda g: _modal_with_tiebreak(g, "department")).rename("primary_department")
    )
    dominant_role_type = (
        filtered_experience.groupby("person_id").apply(lambda g: _modal_with_tiebreak(g, "role_type")).rename("dominant_role_type")
    )

    company_tag_map = (
        company_tags.groupby("company_id")["display_value"]
        .apply(
            lambda values: "|".join(
                sorted({_safe_text(value) for value in values.tolist() if _safe_text(value)})
            )
        )
        .rename("current_company_tags")
        .reset_index()
        .rename(columns={"company_id": "current_company_id"})
    )

    current_company = companies.rename(
        columns={
            "id": "current_company_id",
            "entity_urn": "selected_company_urn",
            "name": "current_company_name",
            "customer_type": "current_customer_type",
            "company_type": "current_company_type",
            "funding_stage": "current_funding_stage",
        }
    )[
        [
            "current_company_id",
            "selected_company_urn",
            "current_company_name",
            "current_customer_type",
            "current_company_type",
            "current_funding_stage",
        ]
    ]

    filtered_people = filtered_people.merge(
        selected_experience[
            [
                "person_id",
                "selected_experience_id",
                "selected_title",
                "selected_department",
                "selected_role_type",
                "selected_company_urn",
                "selected_company_name",
                "selected_location",
            ]
        ],
        on="person_id",
        how="left",
    )
    filtered_people = filtered_people.merge(primary_department, on="person_id", how="left")
    filtered_people = filtered_people.merge(dominant_role_type, on="person_id", how="left")
    filtered_people = filtered_people.merge(current_company, on="selected_company_urn", how="left")
    filtered_people = filtered_people.merge(company_tag_map, on="current_company_id", how="left")

    filtered_people["current_company_tags"] = filtered_people["current_company_tags"].fillna("")
    for label, tags in DOMAIN_TAGS.items():
        filtered_people[label] = filtered_people["current_company_tags"].map(
            lambda raw: any(tag in set(raw.split("|")) for tag in tags if raw)
        )

    filtered_people["selected_department"] = filtered_people["selected_department"].fillna("")
    filtered_people["selected_role_type"] = filtered_people["selected_role_type"].fillna("")
    filtered_people["primary_department"] = filtered_people["primary_department"].fillna("")
    filtered_people["dominant_role_type"] = filtered_people["dominant_role_type"].fillna("")

    # ------------------------------------------------------------------
    # Foreign talent placement enrichment (seniority, tenure, trajectory, education)
    # ------------------------------------------------------------------
    if config.enable_foreign_talent_placement:
        from .normalize import normalize_experience, aggregate_person_seniority
        from .trajectory import (
            compute_experience_tenure,
            aggregate_person_tenure,
            compute_trajectory,
            compute_resume_quality,
        )

        # Normalize titles → seniority + function + manager
        norm_exp = normalize_experience(filtered_experience, companies=companies)
        norm_exp = compute_experience_tenure(norm_exp)

        # Per-person selected experience ID map
        sel_map = (
            filtered_people[["person_id", "selected_experience_id"]]
            .dropna(subset=["selected_experience_id"])
            .set_index("person_id")["selected_experience_id"]
        )

        # Aggregate seniority to person level
        seniority_df = aggregate_person_seniority(norm_exp, selected_experience_ids=sel_map)
        filtered_people = filtered_people.merge(seniority_df, on="person_id", how="left")

        # Aggregate tenure to person level
        tenure_df = aggregate_person_tenure(norm_exp, selected_experience_ids=sel_map)
        filtered_people = filtered_people.merge(tenure_df, on="person_id", how="left")

        # Career trajectory signals
        trajectory_df = compute_trajectory(norm_exp, companies=companies)
        filtered_people = filtered_people.merge(trajectory_df, on="person_id", how="left")

        # Resume quality composite
        rq_df = compute_resume_quality(tenure_df, trajectory_df)
        filtered_people = filtered_people.merge(rq_df, on="person_id", how="left")

        # Top education string (for embedding text)
        top_edu = _build_top_education(education, filtered_ids)
        filtered_people = filtered_people.merge(top_edu, on="person_id", how="left")

        # Save normalized experience for downstream use (company features etc.)
        norm_exp_path = paths.prepared_dir / "normalized_experience.csv"
        norm_exp.to_csv(norm_exp_path, index=False)

    # ------------------------------------------------------------------

    filtered_people = filtered_people.sort_values("person_id").reset_index(drop=True)
    splits = _split_people(filtered_people, config).sort_values("person_id").reset_index(drop=True)

    filtered_people.to_csv(people_path, index=False)
    splits.to_csv(splits_path, index=False)

    metadata = {
        "input_rows": {
            "persons": int(len(persons)),
            "documents": int(len(documents)),
            "experience": int(len(experience)),
            "education": int(len(education)),
            "companies": int(len(companies)),
            "company_tags": int(len(company_tags)),
        },
        "filtered_people": int(len(filtered_people)),
        "split_counts": splits["split"].value_counts().sort_index().to_dict(),
        "min_words": config.min_words,
        "min_experience_rows": config.min_experience_rows,
        "foreign_talent_placement_enrichment": config.enable_foreign_talent_placement,
    }
    write_json(metadata_path, metadata)
    return people_path


def _build_top_education(
    education: pd.DataFrame,
    person_ids: set[int],
) -> pd.DataFrame:
    """Build a single education summary string per person.

    Picks the highest-degree education row and formats as
    ``"{degree} in {field} from {school_name}"``.
    """
    DEGREE_RANK = {
        "phd": 6, "doctorate": 6, "doctor": 6,
        "md": 5, "jd": 5, "mba": 5,
        "master": 4, "ms": 4, "ma": 4,
        "bachelor": 3, "bs": 3, "ba": 3, "bsc": 3,
        "associate": 2, "aa": 2,
        "diploma": 1, "certificate": 1,
    }

    def _degree_rank(degree: str | None) -> int:
        if not degree or not isinstance(degree, str):
            return 0
        lower = degree.lower().strip()
        for keyword, rank in DEGREE_RANK.items():
            if keyword in lower:
                return rank
        return 0

    filtered_edu = education[education["person_id"].isin(person_ids)].copy()
    if filtered_edu.empty:
        return pd.DataFrame({"person_id": list(person_ids), "top_education": [""] * len(person_ids)})

    filtered_edu["_rank"] = filtered_edu["degree"].map(_degree_rank)

    records = []
    for person_id, group in filtered_edu.groupby("person_id"):
        best = group.sort_values("_rank", ascending=False).iloc[0]
        parts = []
        degree = _safe_text(best.get("degree"))
        field = _safe_text(best.get("field"))
        school = _safe_text(best.get("school_name"))
        if degree:
            parts.append(degree)
        if field:
            parts.append(f"in {field}")
        if school:
            parts.append(f"from {school}")
        records.append({"person_id": person_id, "top_education": " ".join(parts)})

    result = pd.DataFrame(records)
    # Add empty rows for people without education
    missing = set(person_ids) - set(result["person_id"])
    if missing:
        missing_df = pd.DataFrame({"person_id": list(missing), "top_education": ""})
        result = pd.concat([result, missing_df], ignore_index=True)

    return result

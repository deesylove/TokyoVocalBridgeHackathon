from __future__ import annotations

import argparse
from pathlib import Path

from .config import RunConfig
from .embed import build_embeddings
from .evaluate import evaluate_concepts
from .io import RunPaths, write_json
from .nmf_baseline import train_nmf_baseline
from .prepare import prepare_dataset
from .report import build_report
from .sae import train_sae_models


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Harmonic concept lab pipeline.")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--embedding-batch-size", type=int, default=128)
    parser.add_argument("--min-words", type=int, default=50)
    parser.add_argument("--min-experience-rows", type=int, default=2)
    parser.add_argument("--tfidf-max-features", type=int, default=50_000)
    parser.add_argument("--tfidf-min-df", type=int, default=5)
    parser.add_argument("--nmf-components", type=int, default=128)
    parser.add_argument("--sae-hidden-dim", type=int, default=64)
    parser.add_argument("--sae-top-k", type=int, default=1)
    parser.add_argument("--sae-batch-size", type=int, default=256)
    parser.add_argument("--sae-epochs", type=int, default=100)
    parser.add_argument("--sae-lr", type=float, default=1e-3)
    parser.add_argument("--sae-weight-decay", type=float, default=1e-5)
    parser.add_argument("--sae-patience", type=int, default=10)
    parser.add_argument("--sae-balance-loss-coef", type=float, default=20.0)
    parser.add_argument("--sae-standardize-input", action=argparse.BooleanOptionalAction, default=True)
    # Foreign talent placement pipeline
    parser.add_argument("--enable-foreign-talent-placement", action="store_true",
                        help="Enable foreign talent placement pipeline (seniority, tenure, trajectory, company features, retrieval index)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = RunConfig(
        input_dir=args.input_dir.resolve(),
        run_dir=args.run_dir.resolve(),
        min_words=args.min_words,
        min_experience_rows=args.min_experience_rows,
        embedding_model=args.embedding_model,
        embedding_batch_size=args.embedding_batch_size,
        tfidf_max_features=args.tfidf_max_features,
        tfidf_min_df=args.tfidf_min_df,
        nmf_components=args.nmf_components,
        sae_hidden_dim=args.sae_hidden_dim,
        sae_top_k=args.sae_top_k,
        sae_batch_size=args.sae_batch_size,
        sae_epochs=args.sae_epochs,
        sae_lr=args.sae_lr,
        sae_weight_decay=args.sae_weight_decay,
        sae_patience=args.sae_patience,
        sae_balance_loss_coef=args.sae_balance_loss_coef,
        sae_standardize_input=args.sae_standardize_input,
        enable_foreign_talent_placement=args.enable_foreign_talent_placement,
    )
    paths = RunPaths(config.run_dir)
    paths.ensure()

    write_json(paths.run_dir / "config.json", config.to_json())

    # --- Core concept lab pipeline ---
    prepare_dataset(config, paths, force=args.force)
    build_embeddings(config, paths, force=args.force)
    train_nmf_baseline(config, paths, force=args.force)
    train_sae_models(config, paths, force=args.force)
    evaluate_concepts(config, paths, force=args.force)
    report_path = build_report(config, paths)

    manifest = {
        "report_path": str(report_path),
        "prepared_people": str(paths.prepared_dir / "people.csv"),
        "embeddings": str(paths.embeddings_dir / "embeddings.npy"),
        "nmf_weights": str(paths.nmf_dir / "topic_weights.npy"),
        "sae_summary": str(paths.sae_dir / "summary.json"),
        "evaluation_summary": str(paths.evaluation_dir / "summary.json"),
    }

    # --- Foreign talent placement pipeline ---
    if config.enable_foreign_talent_placement:
        paths.ensure_foreign_talent_placement()
        _run_foreign_talent_placement_pipeline(config, paths, manifest, force=args.force)

    write_json(paths.run_dir / "manifest.json", manifest)

    print(report_path)
    return 0


def _run_foreign_talent_placement_pipeline(
    config: RunConfig,
    paths: RunPaths,
    manifest: dict[str, object],
    force: bool = False,
) -> None:
    """Run the foreign talent placement enrichment stages after the core pipeline."""
    import numpy as np
    import pandas as pd

    from .company_features import enrich_companies
    from .company_embed import build_company_embeddings

    print("=== Foreign Talent Placement Pipeline ===")

    # Load raw data for company enrichment
    companies = pd.read_csv(config.input_dir / "companies.csv", low_memory=False)
    company_tags_df = pd.read_csv(config.input_dir / "company_tags.csv", low_memory=False)
    experience = pd.read_csv(config.input_dir / "person_experience.csv", low_memory=False)
    experience["start_date"] = pd.to_datetime(experience["start_date"], utc=True, errors="coerce")
    experience["end_date"] = pd.to_datetime(experience["end_date"], utc=True, errors="coerce")

    # Load normalized experience if available (from prepare step)
    norm_exp_path = paths.prepared_dir / "normalized_experience.csv"
    norm_exp = None
    if norm_exp_path.exists():
        norm_exp = pd.read_csv(norm_exp_path, low_memory=False)

    # --- Company enrichment ---
    enriched_path = paths.foreign_talent_placement_dir / "companies_enriched.csv"
    if force or not enriched_path.exists():
        print("  Enriching companies...")
        enriched = enrich_companies(
            companies,
            company_tags_df,
            experience=experience,
            normalized_experience=norm_exp,
        )
        enriched.to_csv(enriched_path, index=False)
        print(f"  → {len(enriched)} companies enriched")
    else:
        enriched = pd.read_csv(enriched_path, low_memory=False)

    # --- Company embeddings ---
    print("  Building company embeddings...")
    company_emb_result = build_company_embeddings(
        config, paths, enriched, force=force,
    )
    manifest["company_embeddings"] = company_emb_result.get("company_embeddings", "")

    # --- Summary ---
    print("  Foreign talent placement pipeline complete.")
    manifest["foreign_talent_placement_companies_enriched"] = str(enriched_path)


if __name__ == "__main__":
    raise SystemExit(main())

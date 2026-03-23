from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(slots=True)
class RunConfig:
    input_dir: Path
    run_dir: Path
    min_words: int = 50
    min_experience_rows: int = 2
    split_seed: int = 42
    train_fraction: float = 0.70
    val_fraction: float = 0.15
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_batch_size: int = 128
    tfidf_max_features: int = 50_000
    tfidf_min_df: int = 5
    nmf_components: int = 128
    sae_hidden_dim: int = 64
    sae_top_k: int = 1
    sae_batch_size: int = 256
    sae_epochs: int = 100
    sae_lr: float = 1e-3
    sae_weight_decay: float = 1e-5
    sae_patience: int = 10
    sae_balance_loss_coef: float = 20.0
    sae_standardize_input: bool = True
    seeds: list[int] = field(default_factory=lambda: [0, 1, 2])
    dead_unit_threshold: float = 0.001
    # --- Foreign talent placement pipeline ---
    enable_foreign_talent_placement: bool = False
    # Retrieval scoring weights
    retrieval_weight_embedding: float = 0.50
    retrieval_weight_structured: float = 0.35
    retrieval_weight_resume_quality: float = 0.15
    # Company scoring weights
    company_weight_embedding: float = 0.50
    company_weight_talent_flow: float = 0.30
    company_weight_dept_density: float = 0.20

    def to_json(self) -> dict[str, object]:
        data = asdict(self)
        data["input_dir"] = str(self.input_dir)
        data["run_dir"] = str(self.run_dir)
        return data

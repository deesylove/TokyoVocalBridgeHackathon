from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RunPaths:
    run_dir: Path

    @property
    def prepared_dir(self) -> Path:
        return self.run_dir / "prepared"

    @property
    def embeddings_dir(self) -> Path:
        return self.run_dir / "embeddings"

    @property
    def nmf_dir(self) -> Path:
        return self.run_dir / "nmf"

    @property
    def sae_dir(self) -> Path:
        return self.run_dir / "sae"

    @property
    def evaluation_dir(self) -> Path:
        return self.run_dir / "evaluation"

    @property
    def report_dir(self) -> Path:
        return self.run_dir / "report"

    @property
    def figures_dir(self) -> Path:
        return self.report_dir / "figures"

    @property
    def foreign_talent_placement_dir(self) -> Path:
        return self.run_dir / "foreign_talent_placement"

    def ensure(self) -> None:
        for path in [
            self.run_dir,
            self.prepared_dir,
            self.embeddings_dir,
            self.nmf_dir,
            self.sae_dir,
            self.evaluation_dir,
            self.report_dir,
            self.figures_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def ensure_foreign_talent_placement(self) -> None:
        """Create foreign talent placement directories."""
        self.foreign_talent_placement_dir.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())

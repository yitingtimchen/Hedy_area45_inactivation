from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = ROOT / "results" / "unblinded"
DOCS_ROOT = ROOT / "docs" / "unblinded"


def results_section_dir(cohort_name: str, section: str) -> Path:
    path = RESULTS_ROOT / cohort_name / section
    path.mkdir(parents=True, exist_ok=True)
    return path


def docs_section_dir(cohort_name: str, section: str) -> Path:
    path = DOCS_ROOT / cohort_name / section
    path.mkdir(parents=True, exist_ok=True)
    return path


def results_tables_dir(cohort_name: str, section: str) -> Path:
    path = results_section_dir(cohort_name, section) / "tables"
    path.mkdir(parents=True, exist_ok=True)
    return path


def results_figures_dir(cohort_name: str, section: str) -> Path:
    path = results_section_dir(cohort_name, section) / "figures"
    path.mkdir(parents=True, exist_ok=True)
    return path

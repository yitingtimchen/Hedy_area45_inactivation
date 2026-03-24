from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = ROOT / "results" / "unblinded"
DOCS_ROOT = ROOT / "docs" / "unblinded"

DATA_SELECTIONS = [
    ("full", "Full analyzed session"),
    ("exclude_vet_entry", "Exclude vet-entry session"),
    ("exclude_smoothed_loud_epochs", "Exclude smoothed loud epochs"),
    ("include_smoothed_loud_epochs_only", "Include smoothed loud epochs only"),
]

OUTPUT_SELECTION_DIRS = {
    "full": "full",
    "exclude_vet_entry": "exclude_vet_entry",
    "exclude_smoothed_loud_epochs": "quiet_mask",
    "include_smoothed_loud_epochs_only": "include_smoothed_loud_epochs_only",
}


def ensure_output_dirs(data_selection: str, aggregation_mode: str) -> tuple[Path, Path, Path]:
    selection_dir = OUTPUT_SELECTION_DIRS[data_selection]
    figures_dir = RESULTS_ROOT / selection_dir / aggregation_mode / "figures"
    tables_dir = RESULTS_ROOT / selection_dir / aggregation_mode / "tables"
    docs_dir = DOCS_ROOT / selection_dir / aggregation_mode
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    return figures_dir, tables_dir, docs_dir


def canonical_selection_name(data_selection: str) -> str:
    return OUTPUT_SELECTION_DIRS[data_selection]


def exact_label_permutation_p(values: np.ndarray, labels: np.ndarray) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    labels = np.asarray(labels)
    n = len(values)
    dcz_n = int(np.sum(labels == "DCZ"))
    observed = values[labels == "DCZ"].mean() - values[labels == "vehicle"].mean()
    diffs = []
    for idx in combinations(range(n), dcz_n):
        mask = np.zeros(n, dtype=bool)
        mask[list(idx)] = True
        diffs.append(values[mask].mean() - values[~mask].mean())
    diffs_arr = np.asarray(diffs, dtype=float)
    p = np.mean(np.abs(diffs_arr) >= abs(observed))
    return float(observed), float(p)


def bootstrap_ci_for_mean_diff(dcz: np.ndarray, vehicle: np.ndarray, seed: int = 23, n_boot: int = 20000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    dcz = np.asarray(dcz, dtype=float)
    vehicle = np.asarray(vehicle, dtype=float)
    dcz_draws = rng.choice(dcz, size=(n_boot, len(dcz)), replace=True).mean(axis=1)
    veh_draws = rng.choice(vehicle, size=(n_boot, len(vehicle)), replace=True).mean(axis=1)
    diffs = dcz_draws - veh_draws
    low, high = np.percentile(diffs, [2.5, 97.5])
    return float(low), float(high)


def sample_sd(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    if len(values) < 2:
        return float("nan")
    return float(np.std(values, ddof=1))


def summarize_by_condition(df: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for metric in metrics:
        sub = df[["condition", metric]].copy()
        sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
        sub = sub.dropna(subset=[metric]).reset_index(drop=True)
        if sub.empty:
            continue
        dcz = sub.loc[sub["condition"] == "DCZ", metric].to_numpy(dtype=float)
        vehicle = sub.loc[sub["condition"] == "vehicle", metric].to_numpy(dtype=float)
        if len(dcz) == 0 or len(vehicle) == 0:
            continue
        mean_diff, perm_p = exact_label_permutation_p(sub[metric].to_numpy(dtype=float), sub["condition"].to_numpy())
        ci_low, ci_high = bootstrap_ci_for_mean_diff(dcz, vehicle)
        rows.append(
            {
                "metric": metric,
                "vehicle_mean": float(np.mean(vehicle)),
                "vehicle_sd": sample_sd(vehicle),
                "DCZ_mean": float(np.mean(dcz)),
                "DCZ_sd": sample_sd(dcz),
                "mean_diff_DCZ_minus_vehicle": mean_diff,
                "bootstrap_ci95_low": ci_low,
                "bootstrap_ci95_high": ci_high,
                "exact_permutation_p_two_sided": perm_p,
                "n_vehicle": int(len(vehicle)),
                "n_DCZ": int(len(dcz)),
            }
        )
    return pd.DataFrame(rows)


def format_summary_line(row: pd.Series, label: str) -> str:
    return (
        f"- {label}: vehicle mean `{row['vehicle_mean']:.3f}`, DCZ mean `{row['DCZ_mean']:.3f}`, "
        f"mean difference `{row['mean_diff_DCZ_minus_vehicle']:.3f}`, 95% CI "
        f"`[{row['bootstrap_ci95_low']:.3f}, {row['bootstrap_ci95_high']:.3f}]`, "
        f"exact permutation `p = {row['exact_permutation_p_two_sided']:.4f}`."
    )


def add_data_selection_and_mode_header(lines: list[str], data_selection_label: str, aggregation_mode_label: str) -> None:
    lines.extend(
        [
            f"- Data selection: `{data_selection_label}`",
            f"- Aggregation mode: `{aggregation_mode_label}`",
            "",
        ]
    )

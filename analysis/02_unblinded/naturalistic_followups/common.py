from __future__ import annotations

from itertools import combinations
from pathlib import Path
from zipfile import ZipFile
import re
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

from output_layout import docs_section_dir, results_figures_dir, results_tables_dir


ROOT = Path(__file__).resolve().parents[3]
INTERVALS_DIR = ROOT / "data" / "derived" / "behavior" / "cleaned_intervals"
UNBLINDED_ROOT = ROOT / "results" / "unblinded"
DOCS_ROOT = ROOT / "docs" / "unblinded"
KEY_PATH = ROOT / "data" / "raw" / "session_key" / "Sessions name encoding.xlsx"

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def normalize_text(value: object) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = str(value)
    return text.replace("’", "'").replace("â€™", "'").strip()


def load_xlsx_sheet_rows(path: Path) -> pd.DataFrame:
    with ZipFile(path) as zf:
        shared_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        shared = [
            "".join(t.text or "" for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))
            for si in shared_root.findall("a:si", NS)
        ]
        sheet_root = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))

    rows: list[dict[str, str]] = []
    for row in sheet_root.findall(".//a:sheetData/a:row", NS):
        cells: dict[str, str] = {}
        for cell in row.findall("a:c", NS):
            ref = cell.get("r", "")
            col = re.sub(r"\d+", "", ref)
            cell_type = cell.get("t")
            value_node = cell.find("a:v", NS)
            value = ""
            if value_node is not None:
                value = value_node.text or ""
                if cell_type == "s":
                    value = shared[int(value)]
            cells[col] = value
        if cells.get("A") and cells.get("B") and cells.get("D"):
            rows.append(cells)
    return pd.DataFrame(rows)


def load_unblinding_map() -> pd.DataFrame:
    raw = load_xlsx_sheet_rows(KEY_PATH)
    mapping = raw.assign(
        session_id=raw["D"].str.extract(r"(\d+)_"),
        original_name=raw["A"],
        condition=raw["B"],
        date_str=raw["A"].str.extract(r"^(\d{8})_"),
    )
    mapping["date"] = pd.to_datetime(mapping["date_str"], format="%Y%m%d")
    mapping["condition"] = mapping["condition"].replace({"Saline": "vehicle", "Inactivation": "DCZ"})
    session_map = (
        mapping.groupby("session_id", as_index=False)
        .agg(original_name=("original_name", "first"), condition=("condition", "first"), date=("date", "first"))
        .sort_values("date")
        .reset_index(drop=True)
    )
    session_map["session_index"] = np.arange(1, len(session_map) + 1)
    return session_map


def ensure_full_output_dirs() -> tuple[Path, Path, Path]:
    tables_dir = results_tables_dir("full", "naturalistic_followups")
    figures_dir = results_figures_dir("full", "naturalistic_followups")
    docs_dir = docs_section_dir("full", "naturalistic_followups")
    return tables_dir, figures_dir, docs_dir


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
    p_value = float(np.mean(np.abs(diffs_arr) >= abs(observed)))
    return float(observed), p_value


def bootstrap_ci_for_mean_diff(
    dcz: np.ndarray,
    vehicle: np.ndarray,
    seed: int = 23,
    n_boot: int = 20000,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    dcz = np.asarray(dcz, dtype=float)
    vehicle = np.asarray(vehicle, dtype=float)
    dcz_draws = rng.choice(dcz, size=(n_boot, len(dcz)), replace=True).mean(axis=1)
    vehicle_draws = rng.choice(vehicle, size=(n_boot, len(vehicle)), replace=True).mean(axis=1)
    diffs = dcz_draws - vehicle_draws
    low, high = np.percentile(diffs, [2.5, 97.5])
    return float(low), float(high)


def sample_sd(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    if len(values) < 2:
        return float("nan")
    return float(np.std(values, ddof=1))


def compare_conditions(df: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
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
        effect, p_value = exact_label_permutation_p(sub[metric].to_numpy(dtype=float), sub["condition"].to_numpy())
        ci_low, ci_high = bootstrap_ci_for_mean_diff(dcz, vehicle)
        rows.append(
            {
                "metric": metric,
                "vehicle_mean": float(np.mean(vehicle)),
                "vehicle_sd": sample_sd(vehicle),
                "DCZ_mean": float(np.mean(dcz)),
                "DCZ_sd": sample_sd(dcz),
                "mean_diff_DCZ_minus_vehicle": effect,
                "bootstrap_ci95_low": ci_low,
                "bootstrap_ci95_high": ci_high,
                "exact_permutation_p_two_sided": p_value,
                "n_vehicle": int(len(vehicle)),
                "n_DCZ": int(len(dcz)),
            }
        )
    return pd.DataFrame(rows)


def format_summary_line(row: pd.Series, label: str) -> str:
    return (
        f"- {label}: vehicle mean `{row['vehicle_mean']:.3f}`, DCZ mean `{row['DCZ_mean']:.3f}`, "
        f"mean difference `{row['mean_diff_DCZ_minus_vehicle']:.3f}`, 95% CI "
        f"`[{row['bootstrap_ci95_low']:.3f}, {row['bootstrap_ci95_high']:.3f}]`, exact permutation "
        f"`p = {row['exact_permutation_p_two_sided']:.4f}`."
    )


def load_timeline(session_id: str) -> pd.DataFrame:
    timeline = pd.read_csv(INTERVALS_DIR / f"{session_id}_layered_timeline.csv")
    for col in ["social_state", "activity_state", "attention_state", "atypical_state"]:
        if col in timeline.columns:
            timeline[col] = timeline[col].map(normalize_text)
    return timeline


def load_behavior_intervals(session_id: str) -> pd.DataFrame:
    intervals = pd.read_csv(INTERVALS_DIR / f"{session_id}_behavior_intervals.csv")
    intervals["behavior"] = intervals["behavior"].map(normalize_text)
    return intervals


def overlap_duration(df: pd.DataFrame, start_s: float, end_s: float) -> float:
    if df.empty or end_s <= start_s:
        return 0.0
    starts = df["start_s"].to_numpy(dtype=float)
    ends = df["end_s"].to_numpy(dtype=float)
    return float(np.maximum(0.0, np.minimum(ends, end_s) - np.maximum(starts, start_s)).sum())

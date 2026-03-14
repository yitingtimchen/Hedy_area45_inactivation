from __future__ import annotations

from itertools import combinations
from pathlib import Path
from zipfile import ZipFile
import re
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DECISION_PATH = ROOT / "results" / "blinded" / "tables" / "blinded_decision_table.csv"
EXPLORATORY_PATH = ROOT / "results" / "blinded" / "tables" / "blinded_exploratory_nonsocial_table.csv"
KEY_PATH = ROOT / "data" / "raw" / "session_key" / "Sessions name encoding.xlsx"
UNBLINDED_ROOT = ROOT / "results" / "unblinded"
DOCS_ROOT = ROOT / "docs" / "unblinded"

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
VET_ENTRY_SESSION_ID = "596273"


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
    diffs_arr = np.asarray(diffs)
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


def summarize_by_condition(df: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for metric in metrics:
        sub = df[["condition", metric]].copy()
        sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
        sub = sub.dropna(subset=[metric]).reset_index(drop=True)
        dcz = sub.loc[sub["condition"] == "DCZ", metric].to_numpy(dtype=float)
        vehicle = sub.loc[sub["condition"] == "vehicle", metric].to_numpy(dtype=float)
        if len(dcz) == 0 or len(vehicle) == 0:
            rows.append(
                {
                    "metric": metric,
                    "vehicle_mean": pd.NA,
                    "vehicle_sd": pd.NA,
                    "DCZ_mean": pd.NA,
                    "DCZ_sd": pd.NA,
                    "mean_diff_DCZ_minus_vehicle": pd.NA,
                    "bootstrap_ci95_low": pd.NA,
                    "bootstrap_ci95_high": pd.NA,
                    "exact_permutation_p_two_sided": pd.NA,
                    "n_vehicle": int(len(vehicle)),
                    "n_DCZ": int(len(dcz)),
                }
            )
            continue

        mean_diff, perm_p = exact_label_permutation_p(sub[metric].to_numpy(dtype=float), sub["condition"].to_numpy())
        ci_low, ci_high = bootstrap_ci_for_mean_diff(dcz, vehicle)
        rows.append(
            {
                "metric": metric,
                "vehicle_mean": float(np.mean(vehicle)),
                "vehicle_sd": float(np.std(vehicle, ddof=1)),
                "DCZ_mean": float(np.mean(dcz)),
                "DCZ_sd": float(np.std(dcz, ddof=1)),
                "mean_diff_DCZ_minus_vehicle": mean_diff,
                "bootstrap_ci95_low": ci_low,
                "bootstrap_ci95_high": ci_high,
                "exact_permutation_p_two_sided": perm_p,
                "n_vehicle": int(len(vehicle)),
                "n_DCZ": int(len(dcz)),
            }
        )
    return pd.DataFrame(rows)


def build_markdown_summary(
    primary: pd.DataFrame,
    secondary: pd.DataFrame,
    sensitivity: pd.DataFrame,
    n_vehicle: int,
    n_dcz: int,
    cohort_label: str,
) -> str:
    lines = [
        "# Unblinded Condition Comparison",
        "",
        f"Cohort: {cohort_label}.",
        "Condition labels were merged only after the blinded preprocessing, endpoint locking, and audio sensitivity analysis were finalized.",
        "",
        "## Statistical approach",
        "",
        "- Session-level comparisons use the locked outputs.",
        f"- `DCZ` and `vehicle` groups contain `{n_dcz}` and `{n_vehicle}` sessions, respectively.",
        "- For each metric, the group contrast is `DCZ - vehicle`.",
        "- P values come from an exact two-sided label permutation test over all label assignments consistent with the cohort size.",
        "- Bootstrap 95% confidence intervals are provided for the mean difference as descriptive uncertainty intervals.",
        "",
        "## Primary endpoints",
        "",
    ]
    for row in primary.itertuples(index=False):
        lines.append(
            f"- `{row.metric}`: vehicle mean `{row.vehicle_mean:.3f}`, DCZ mean `{row.DCZ_mean:.3f}`, "
            f"mean difference `{row.mean_diff_DCZ_minus_vehicle:.3f}`, 95% CI "
            f"`[{row.bootstrap_ci95_low:.3f}, {row.bootstrap_ci95_high:.3f}]`, exact permutation "
            f"`p = {row.exact_permutation_p_two_sided:.4f}`."
        )
    lines.extend(["", "## Secondary endpoints", ""])
    for row in secondary.itertuples(index=False):
        lines.append(
            f"- `{row.metric}`: vehicle mean `{row.vehicle_mean:.3f}`, DCZ mean `{row.DCZ_mean:.3f}`, "
            f"mean difference `{row.mean_diff_DCZ_minus_vehicle:.3f}`, 95% CI "
            f"`[{row.bootstrap_ci95_low:.3f}, {row.bootstrap_ci95_high:.3f}]`, exact permutation "
            f"`p = {row.exact_permutation_p_two_sided:.4f}`."
        )
    lines.extend(["", "## Quiet-mask sensitivity for primary endpoints", ""])
    for row in sensitivity.itertuples(index=False):
        lines.append(
            f"- `{row.metric}`: vehicle mean `{row.vehicle_mean:.3f}`, DCZ mean `{row.DCZ_mean:.3f}`, "
            f"mean difference `{row.mean_diff_DCZ_minus_vehicle:.3f}`, 95% CI "
            f"`[{row.bootstrap_ci95_low:.3f}, {row.bootstrap_ci95_high:.3f}]`, exact permutation "
            f"`p = {row.exact_permutation_p_two_sided:.4f}`."
        )
    return "\n".join(lines) + "\n"


def cohort_tables_dir(cohort_name: str) -> Path:
    return UNBLINDED_ROOT / cohort_name / "tables"


def cohort_docs_dir(cohort_name: str) -> Path:
    return DOCS_ROOT / cohort_name


def write_analysis_set(
    decision_df: pd.DataFrame,
    exploratory_df: pd.DataFrame,
    cohort_name: str,
    cohort_label: str,
) -> None:
    primary_metrics = [
        "groom_duration_net_receive_minus_give_pct_session",
        "groom_duration_reciprocity_0to1",
    ]
    secondary_metrics = [
        "groom_total_pct_session",
        "groom_bout_net_receive_minus_give",
        "groom_bout_reciprocity_0to1",
        "social_engaged_pct_session",
    ]
    sensitivity_metrics = [
        "groom_duration_net_receive_minus_give_pct_quiet_masked_p90",
        "groom_duration_reciprocity_0to1_quiet_masked_p90",
    ]
    exploratory_metrics = [
        "travel_resolved_pct_session",
        "rest_stationary_resolved_pct_session",
        "vigilant_scan_resolved_pct_session",
        "attention_to_outside_agents_resolved_pct_session",
        "scratch_resolved_pct_session",
        "self_groom_resolved_pct_session",
        "hiccups_resolved_pct_session",
        "pace_resolved_pct_session",
        "forage_search_resolved_pct_session",
        "object_manipulate_resolved_pct_session",
        "inferred_leave_per_hour",
    ]

    tables_dir = cohort_tables_dir(cohort_name)
    docs_dir = cohort_docs_dir(cohort_name)
    tables_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    decision_df.to_csv(tables_dir / "unblinded_decision_table.csv", index=False)
    exploratory_df.to_csv(tables_dir / "unblinded_exploratory_nonsocial_table.csv", index=False)

    primary_summary = summarize_by_condition(decision_df, primary_metrics)
    secondary_summary = summarize_by_condition(decision_df, secondary_metrics)
    sensitivity_summary = summarize_by_condition(decision_df, sensitivity_metrics)
    exploratory_summary = summarize_by_condition(exploratory_df, exploratory_metrics)

    primary_summary.to_csv(tables_dir / "condition_comparison_primary.csv", index=False)
    secondary_summary.to_csv(tables_dir / "condition_comparison_secondary.csv", index=False)
    sensitivity_summary.to_csv(tables_dir / "condition_comparison_quiet_mask_sensitivity.csv", index=False)
    exploratory_summary.to_csv(tables_dir / "condition_comparison_exploratory.csv", index=False)

    n_vehicle = int((decision_df["condition"] == "vehicle").sum())
    n_dcz = int((decision_df["condition"] == "DCZ").sum())
    summary_md = build_markdown_summary(primary_summary, secondary_summary, sensitivity_summary, n_vehicle, n_dcz, cohort_label)
    (docs_dir / "unblinded_condition_summary.md").write_text(summary_md, encoding="utf-8")


def main() -> None:
    UNBLINDED_ROOT.mkdir(parents=True, exist_ok=True)
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)

    session_map = load_unblinding_map()
    (UNBLINDED_ROOT / "session_unblinding_key.csv").parent.mkdir(parents=True, exist_ok=True)
    session_map.to_csv(UNBLINDED_ROOT / "session_unblinding_key.csv", index=False)

    decision = pd.read_csv(DECISION_PATH, dtype={"session_id": str})
    exploratory = pd.read_csv(EXPLORATORY_PATH, dtype={"session_id": str})

    full_decision = session_map.merge(decision, on="session_id", how="inner").sort_values("date").reset_index(drop=True)
    exploratory = exploratory.merge(decision[["session_id", "inferred_leave_per_hour"]], on="session_id", how="left")
    full_exploratory = session_map.merge(exploratory, on="session_id", how="inner").sort_values("date").reset_index(drop=True)

    write_analysis_set(full_decision, full_exploratory, "full", "full session set")

    filtered_decision = full_decision.loc[full_decision["session_id"] != VET_ENTRY_SESSION_ID].reset_index(drop=True)
    filtered_exploratory = full_exploratory.loc[full_exploratory["session_id"] != VET_ENTRY_SESSION_ID].reset_index(drop=True)
    write_analysis_set(filtered_decision, filtered_exploratory, "exclude_vet_entry", "excluding known vet-entry session 596273")


if __name__ == "__main__":
    main()

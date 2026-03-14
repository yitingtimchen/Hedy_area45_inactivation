from __future__ import annotations

from itertools import combinations
from pathlib import Path
from zipfile import ZipFile
import re
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INTERVALS_DIR = ROOT / "data" / "derived" / "behavior" / "cleaned_intervals"
UNBLINDED_ROOT = ROOT / "results" / "unblinded"
DOCS_ROOT = ROOT / "docs" / "unblinded"
KEY_PATH = ROOT / "data" / "raw" / "session_key" / "Sessions name encoding.xlsx"

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
MACRO_STATES = ["social", "nonsocial_activity", "attention_only", "atypical_only", "unscored"]
UNSCORED_BRIDGE_S = 3.0
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


def assign_macro_state(row: pd.Series) -> str:
    if bool(row["social_engaged"]):
        return "social"
    if pd.notna(row["activity_state"]):
        return "nonsocial_activity"
    if pd.notna(row["attention_state"]):
        return "attention_only"
    if pd.notna(row["atypical_state"]):
        return "atypical_only"
    return "unscored"


def collapse_macro_timeline(timeline: pd.DataFrame) -> pd.DataFrame:
    tl = timeline.copy()
    tl["macro_state"] = tl.apply(assign_macro_state, axis=1)
    rows: list[dict[str, object]] = []
    current = tl.iloc[0].to_dict()
    for row in tl.iloc[1:].to_dict("records"):
        contiguous = abs(float(current["end_s"]) - float(row["start_s"])) < 1e-9
        if contiguous and current["macro_state"] == row["macro_state"]:
            current["end_s"] = row["end_s"]
            current["duration_s"] = float(current["end_s"]) - float(current["start_s"])
        else:
            rows.append(
                {
                    "start_s": current["start_s"],
                    "end_s": current["end_s"],
                    "duration_s": current["duration_s"],
                    "macro_state": current["macro_state"],
                }
            )
            current = row.copy()
    rows.append(
        {
            "start_s": current["start_s"],
            "end_s": current["end_s"],
            "duration_s": current["duration_s"],
            "macro_state": current["macro_state"],
        }
    )
    return pd.DataFrame(rows)


def bridge_unscored_gaps(macro: pd.DataFrame, max_gap_s: float = UNSCORED_BRIDGE_S) -> pd.DataFrame:
    if macro.empty:
        return macro.copy()

    kept = macro[~((macro["macro_state"] == "unscored") & (macro["duration_s"] <= max_gap_s))].copy().reset_index(drop=True)
    if kept.empty:
        return kept

    rows: list[dict[str, object]] = []
    current = kept.iloc[0].to_dict()
    for row in kept.iloc[1:].to_dict("records"):
        gap = float(row["start_s"]) - float(current["end_s"])
        if current["macro_state"] == row["macro_state"] and gap <= max_gap_s:
            current["end_s"] = row["end_s"]
            current["duration_s"] = float(current["end_s"]) - float(current["start_s"])
        else:
            rows.append(current.copy())
            current = row.copy()
    rows.append(current.copy())
    return pd.DataFrame(rows)


def transition_counts(macro: pd.DataFrame) -> dict[tuple[str, str], int]:
    counts = {(src, dst): 0 for src in MACRO_STATES for dst in MACRO_STATES if src != dst}
    rows = macro.to_dict("records")
    for idx in range(len(rows) - 1):
        src = rows[idx]["macro_state"]
        dst = rows[idx + 1]["macro_state"]
        if src == dst:
            continue
        counts[(src, dst)] += 1
    return counts


def safe_prob(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return num / den


def summarize_session(session_id: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    timeline = pd.read_csv(INTERVALS_DIR / f"{session_id}_layered_timeline.csv")
    macro = collapse_macro_timeline(timeline)
    macro = bridge_unscored_gaps(macro)
    counts = transition_counts(macro)

    duration_s = float(timeline["duration_s"].sum())
    total_switches = sum(counts.values())

    row: dict[str, object] = {
        "session_id": session_id,
        "macro_switches_per_hour": total_switches / (duration_s / 3600.0) if duration_s else np.nan,
    }

    source_totals = {src: sum(counts[(src, dst)] for dst in MACRO_STATES if src != dst) for src in MACRO_STATES}
    for src in MACRO_STATES:
        for dst in MACRO_STATES:
            if src == dst:
                continue
            row[f"{src}_to_{dst}_prob"] = safe_prob(counts[(src, dst)], source_totals[src])

    matrix_rows = []
    for (src, dst), count in counts.items():
        matrix_rows.append({"session_id": session_id, "source": src, "target": dst, "count": count})
    return row, matrix_rows


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
    diffs = np.asarray(diffs)
    return float(observed), float(np.mean(np.abs(diffs) >= abs(observed)))


def bootstrap_ci_for_mean_diff(dcz: np.ndarray, vehicle: np.ndarray, seed: int = 41, n_boot: int = 20000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    dcz_draws = rng.choice(dcz, size=(n_boot, len(dcz)), replace=True).mean(axis=1)
    veh_draws = rng.choice(vehicle, size=(n_boot, len(vehicle)), replace=True).mean(axis=1)
    diffs = dcz_draws - veh_draws
    low, high = np.percentile(diffs, [2.5, 97.5])
    return float(low), float(high)


def compare_conditions(df: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for metric in metrics:
        sub = df[["condition", metric]].copy()
        sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
        sub = sub.dropna(subset=[metric]).reset_index(drop=True)
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
                "vehicle_sd": float(np.std(vehicle, ddof=1)),
                "DCZ_mean": float(np.mean(dcz)),
                "DCZ_sd": float(np.std(dcz, ddof=1)),
                "mean_diff_DCZ_minus_vehicle": effect,
                "bootstrap_ci95_low": ci_low,
                "bootstrap_ci95_high": ci_high,
                "exact_permutation_p_two_sided": p_value,
                "n_vehicle": int(len(vehicle)),
                "n_DCZ": int(len(dcz)),
            }
        )
    return pd.DataFrame(rows)


def build_condition_matrices(session_df: pd.DataFrame, matrix_df: pd.DataFrame) -> pd.DataFrame:
    merged = session_df[["session_id", "condition"]].merge(matrix_df, on="session_id", how="left")
    rows: list[dict[str, object]] = []
    for condition, sub in merged.groupby("condition", sort=False):
        grouped = sub.groupby(["source", "target"], as_index=False)["count"].sum()
        source_totals = grouped.groupby("source")["count"].sum().to_dict()
        for row in grouped.itertuples(index=False):
            prob = row.count / source_totals[row.source] if source_totals.get(row.source, 0) else np.nan
            rows.append({"condition": condition, "source": row.source, "target": row.target, "count": int(row.count), "prob": prob})
    return pd.DataFrame(rows)


def build_markdown(summary: pd.DataFrame, cohort_label: str) -> str:
    pretty = {
        "macro_switches_per_hour": "Macro-state switches per hour",
        "social_to_nonsocial_activity_prob": "Social to nonsocial-activity probability",
        "social_to_attention_only_prob": "Social to attention-only probability",
        "nonsocial_activity_to_social_prob": "Nonsocial-activity to social probability",
        "attention_only_to_social_prob": "Attention-only to social probability",
    }
    lines = [
        "# Macro-State Transition Analysis",
        "",
        f"Cohort: {cohort_label}.",
        f"This version removes `unscored` macro-bouts of duration `<= {UNSCORED_BRIDGE_S:.0f} s` from the transition stream before recollapsing adjacent macro-states.",
        "",
        "## Condition comparisons",
        "",
    ]
    for row in summary.itertuples(index=False):
        label = pretty.get(row.metric, row.metric)
        lines.append(
            f"- {label}: vehicle mean `{row.vehicle_mean:.3f}`, DCZ mean `{row.DCZ_mean:.3f}`, "
            f"mean difference `{row.mean_diff_DCZ_minus_vehicle:.3f}`, 95% CI "
            f"`[{row.bootstrap_ci95_low:.3f}, {row.bootstrap_ci95_high:.3f}]`, exact permutation "
            f"`p = {row.exact_permutation_p_two_sided:.4f}`."
        )
    return "\n".join(lines) + "\n"


def write_outputs(session_df: pd.DataFrame, matrix_df: pd.DataFrame, cohort_name: str, cohort_label: str) -> None:
    tables_dir = UNBLINDED_ROOT / cohort_name / "tables"
    docs_dir = DOCS_ROOT / cohort_name
    tables_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    cond_matrix = build_condition_matrices(session_df, matrix_df)
    session_df.to_csv(tables_dir / "macro_transition_metrics_by_session.csv", index=False)
    matrix_df.to_csv(tables_dir / "macro_transition_counts_by_session.csv", index=False)
    cond_matrix.to_csv(tables_dir / "macro_transition_condition_matrices.csv", index=False)

    compare_metrics = [
        "macro_switches_per_hour",
        "social_to_nonsocial_activity_prob",
        "social_to_attention_only_prob",
        "nonsocial_activity_to_social_prob",
        "attention_only_to_social_prob",
    ]
    summary = compare_conditions(session_df, compare_metrics)
    summary.to_csv(tables_dir / "macro_transition_condition_comparison.csv", index=False)
    (docs_dir / "macro_transition_analysis.md").write_text(build_markdown(summary, cohort_label), encoding="utf-8")


def main() -> None:
    UNBLINDED_ROOT.mkdir(parents=True, exist_ok=True)
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)

    session_map = load_unblinding_map()
    session_rows = []
    matrix_rows = []
    for session_id in session_map["session_id"].astype(str):
        summary_row, rows = summarize_session(session_id)
        session_rows.append(summary_row)
        matrix_rows.extend(rows)

    full_session_df = pd.DataFrame(session_rows)
    full_session_df = session_map.merge(full_session_df, on="session_id", how="left").sort_values("date").reset_index(drop=True)
    full_matrix_df = pd.DataFrame(matrix_rows)
    write_outputs(full_session_df, full_matrix_df, "full", "full session set")

    filtered_session_df = full_session_df.loc[full_session_df["session_id"] != VET_ENTRY_SESSION_ID].reset_index(drop=True)
    filtered_matrix_df = full_matrix_df.loc[full_matrix_df["session_id"] != VET_ENTRY_SESSION_ID].reset_index(drop=True)
    write_outputs(filtered_session_df, filtered_matrix_df, "exclude_vet_entry", "excluding known vet-entry session 596273")


if __name__ == "__main__":
    main()

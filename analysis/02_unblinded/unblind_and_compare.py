from __future__ import annotations

from itertools import combinations
from pathlib import Path
from zipfile import ZipFile
import re
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

from output_layout import docs_section_dir, results_tables_dir


ROOT = Path(__file__).resolve().parents[2]
DECISION_PATH = ROOT / "results" / "blinded" / "tables" / "blinded_decision_table.csv"
EXPLORATORY_PATH = ROOT / "results" / "blinded" / "tables" / "blinded_exploratory_nonsocial_table.csv"
KEY_PATH = ROOT / "data" / "raw" / "session_key" / "Sessions name encoding.xlsx"
UNBLINDED_ROOT = ROOT / "results" / "unblinded"
DOCS_ROOT = ROOT / "docs" / "unblinded"

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
VET_ENTRY_SESSION_ID = "596273"

GROOM_COMPONENT_METRICS = [
    "groom_give_pct_session",
    "groom_receive_pct_session",
    "groom_total_pct_session",
    "groom_duration_net_receive_minus_give_pct_session",
    "groom_duration_reciprocity_0to1",
]

GROOM_BOUT_COMPONENT_METRICS = [
    "groom_give_resolved_bouts",
    "groom_receive_resolved_bouts",
    "groom_total_resolved_bouts",
    "groom_bout_net_receive_minus_give",
    "groom_bout_reciprocity_0to1",
]

GROOM_BOUT_DURATION_METRICS = [
    "groom_give_bout_mean_duration_s",
    "groom_receive_bout_mean_duration_s",
    "groom_total_bout_mean_duration_s",
    "groom_give_bout_median_duration_s",
    "groom_receive_bout_median_duration_s",
    "groom_total_bout_median_duration_s",
]

PRIMARY_METRICS = [
    "groom_duration_net_receive_minus_give_pct_session",
    "groom_duration_reciprocity_0to1",
]

SECONDARY_METRICS = [
    "groom_total_pct_session",
    "groom_bout_net_receive_minus_give",
    "groom_bout_reciprocity_0to1",
    "social_engaged_pct_session",
]

SENSITIVITY_METRICS = [
    "groom_duration_net_receive_minus_give_pct_quiet_masked_p90",
    "groom_duration_reciprocity_0to1_quiet_masked_p90",
]

EXPLORATORY_METRICS = [
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

SUMMARY_LABELS = {
    "groom_give_pct_session": "Groom give (% session)",
    "groom_receive_pct_session": "Groom receive (% session)",
    "groom_total_pct_session": "Total grooming (% session)",
    "groom_give_resolved_bouts": "Groom give bouts per session",
    "groom_receive_resolved_bouts": "Groom receive bouts per session",
    "groom_total_resolved_bouts": "Total grooming bouts per session",
    "groom_give_bout_mean_duration_s": "Mean groom-give bout duration (s)",
    "groom_receive_bout_mean_duration_s": "Mean groom-receive bout duration (s)",
    "groom_total_bout_mean_duration_s": "Mean total grooming bout duration (s)",
    "groom_give_bout_median_duration_s": "Median groom-give bout duration (s)",
    "groom_receive_bout_median_duration_s": "Median groom-receive bout duration (s)",
    "groom_total_bout_median_duration_s": "Median total grooming bout duration (s)",
    "groom_duration_net_receive_minus_give_pct_session": "Net grooming (% session; receive - give)",
    "groom_duration_reciprocity_0to1": "Grooming reciprocity (0 to 1)",
    "groom_bout_net_receive_minus_give": "Net grooming bouts (receive - give)",
    "groom_bout_reciprocity_0to1": "Grooming bout reciprocity (0 to 1)",
    "social_engaged_pct_session": "Social engagement (% session)",
    "groom_duration_net_receive_minus_give_pct_quiet_masked_p90": "Quiet-masked net grooming (% session; receive - give)",
    "groom_duration_reciprocity_0to1_quiet_masked_p90": "Quiet-masked grooming reciprocity (0 to 1)",
}


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
        f"`[{row['bootstrap_ci95_low']:.3f}, {row['bootstrap_ci95_high']:.3f}]`, exact permutation "
        f"`p = {row['exact_permutation_p_two_sided']:.4f}`."
    )


def summarize_component_story(component_summary: pd.DataFrame) -> str:
    give = component_summary.loc[component_summary["metric"] == "groom_give_pct_session"].iloc[0]
    receive = component_summary.loc[component_summary["metric"] == "groom_receive_pct_session"].iloc[0]
    give_effect = float(give["mean_diff_DCZ_minus_vehicle"])
    receive_effect = float(receive["mean_diff_DCZ_minus_vehicle"])
    give_mag = abs(give_effect)
    receive_mag = abs(receive_effect)

    if give_effect < 0 and receive_effect > 0:
        if give_mag >= 1.5 * max(receive_mag, 1e-9):
            return "The composite shift appears driven mainly by reduced grooming given under DCZ, with a smaller concurrent increase in grooming received."
        if receive_mag >= 1.5 * max(give_mag, 1e-9):
            return "The composite shift appears driven mainly by increased grooming received under DCZ, with a smaller concurrent decrease in grooming given."
        return "The composite shift appears to reflect both reduced grooming given and increased grooming received under DCZ."
    if give_effect < 0 and receive_effect <= 0:
        return "The composite shift appears driven mainly by reduced grooming given under DCZ rather than a clear rise in grooming received."
    if receive_effect > 0 and give_effect >= 0:
        return "The composite shift appears driven mainly by increased grooming received under DCZ rather than a clear drop in grooming given."
    return "The composite shift does not reduce to a clean one-component story; the raw give and receive metrics should be interpreted alongside the composite endpoints."


def build_markdown_summary(
    components: pd.DataFrame,
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
        "## Raw grooming components",
        "",
        f"- Interpretation summary: {summarize_component_story(components)}",
    ]
    for metric in ["groom_give_pct_session", "groom_receive_pct_session", "groom_total_pct_session"]:
        row = components.loc[components["metric"] == metric].iloc[0]
        lines.append(format_summary_line(row, SUMMARY_LABELS[metric]))

    lines.extend(["", "## Composite grooming metrics", ""])
    for metric in PRIMARY_METRICS:
        row = primary.loc[primary["metric"] == metric].iloc[0]
        lines.append(format_summary_line(row, SUMMARY_LABELS[metric]))

    lines.extend(["", "## Secondary endpoints", ""])
    for metric in ["groom_bout_net_receive_minus_give", "groom_bout_reciprocity_0to1", "social_engaged_pct_session"]:
        row = secondary.loc[secondary["metric"] == metric].iloc[0]
        lines.append(format_summary_line(row, SUMMARY_LABELS[metric]))

    lines.extend(["", "## Quiet-mask sensitivity for primary endpoints", ""])
    for metric in SENSITIVITY_METRICS:
        row = sensitivity.loc[sensitivity["metric"] == metric].iloc[0]
        lines.append(format_summary_line(row, SUMMARY_LABELS[metric]))
    return "\n".join(lines) + "\n"


def build_raw_session_markdown(components: pd.DataFrame, n_vehicle: int, n_dcz: int, cohort_label: str) -> str:
    lines = [
        "# Raw Session Summary",
        "",
        f"Cohort: {cohort_label}.",
        f"`DCZ` and `vehicle` groups contain `{n_dcz}` and `{n_vehicle}` sessions, respectively.",
        "",
        "## Raw grooming components",
        "",
        f"- Interpretation summary: {summarize_component_story(components)}",
    ]
    for metric in ["groom_give_pct_session", "groom_receive_pct_session", "groom_total_pct_session"]:
        row = components.loc[components["metric"] == metric].iloc[0]
        lines.append(format_summary_line(row, SUMMARY_LABELS[metric]))
    lines.append("")
    return "\n".join(lines)


def build_groom_bout_markdown(bout_components: pd.DataFrame, secondary: pd.DataFrame, n_vehicle: int, n_dcz: int, cohort_label: str) -> tuple[str, str]:
    raw_lines = [
        "# Groom Bout Session Summary",
        "",
        f"Cohort: {cohort_label}.",
        f"`DCZ` and `vehicle` groups contain `{n_dcz}` and `{n_vehicle}` sessions, respectively.",
        "",
        "## Raw grooming bout components",
        "",
    ]
    for metric in ["groom_give_resolved_bouts", "groom_receive_resolved_bouts", "groom_total_resolved_bouts"]:
        row = bout_components.loc[bout_components["metric"] == metric].iloc[0]
        raw_lines.append(format_summary_line(row, SUMMARY_LABELS[metric]))
    raw_lines.append("")

    composite_lines = [
        "# Groom Bout Composite Summary",
        "",
        f"Cohort: {cohort_label}.",
        f"`DCZ` and `vehicle` groups contain `{n_dcz}` and `{n_vehicle}` sessions, respectively.",
        "",
        "## Composite grooming bout metrics",
        "",
    ]
    for metric in ["groom_bout_net_receive_minus_give", "groom_bout_reciprocity_0to1"]:
        row = secondary.loc[secondary["metric"] == metric].iloc[0]
        composite_lines.append(format_summary_line(row, SUMMARY_LABELS[metric]))
    composite_lines.append("")
    return "\n".join(raw_lines), "\n".join(composite_lines)


def build_groom_bout_duration_markdown(bout_durations: pd.DataFrame, n_vehicle: int, n_dcz: int, cohort_label: str) -> str:
    lines = [
        "# Groom Bout Duration Summary",
        "",
        f"Cohort: {cohort_label}.",
        f"`DCZ` and `vehicle` groups contain `{n_dcz}` and `{n_vehicle}` sessions, respectively.",
        "",
        "## Mean bout duration",
        "",
    ]
    for metric in [
        "groom_give_bout_mean_duration_s",
        "groom_receive_bout_mean_duration_s",
        "groom_total_bout_mean_duration_s",
    ]:
        row = bout_durations.loc[bout_durations["metric"] == metric].iloc[0]
        lines.append(format_summary_line(row, SUMMARY_LABELS[metric]))

    lines.extend(["", "## Median bout duration", ""])
    for metric in [
        "groom_give_bout_median_duration_s",
        "groom_receive_bout_median_duration_s",
        "groom_total_bout_median_duration_s",
    ]:
        row = bout_durations.loc[bout_durations["metric"] == metric].iloc[0]
        lines.append(format_summary_line(row, SUMMARY_LABELS[metric]))
    lines.append("")
    return "\n".join(lines)


def build_quiet_mask_assumptions_markdown() -> str:
    lines = [
        "# Quiet-Mask Assumptions",
        "",
        "- The quiet-mask branch is built from the same sessions as the full branch, but primary session-level metrics are recomputed after removing smoothed loud epochs.",
        "- Loud epochs are defined from a centered 5 s rolling-average loudness trace within each session.",
        "- Bins above the session-specific smoothed 90th-percentile threshold are marked as loud.",
        "- Quiet gaps `<= 2 s` inside loud stretches are filled, and isolated loud blips `< 3 s` are removed from the mask.",
        "- Metrics are recomputed on the retained 1 s bins after those loud epochs are removed.",
        "- This is a robustness analysis for duration-based session summaries; it should not be interpreted as a perfect reconstruction of the original session timeline.",
        "- Episode-level and macro-transition follow-up outputs in the quiet-mask branch are mirrored for organizational consistency and are not themselves re-derived from a time-preserving masked event stream.",
        "",
    ]
    return "\n".join(lines)


def build_composite_session_markdown(
    primary: pd.DataFrame,
    secondary: pd.DataFrame,
    n_vehicle: int,
    n_dcz: int,
    cohort_label: str,
    sensitivity: pd.DataFrame | None = None,
) -> str:
    lines = [
        "# Composite Session Summary",
        "",
        f"Cohort: {cohort_label}.",
        f"`DCZ` and `vehicle` groups contain `{n_dcz}` and `{n_vehicle}` sessions, respectively.",
        "",
        "## Composite grooming metrics",
        "",
    ]
    for metric in PRIMARY_METRICS:
        row = primary.loc[primary["metric"] == metric].iloc[0]
        lines.append(format_summary_line(row, SUMMARY_LABELS[metric]))
    lines.extend(["", "## Secondary endpoints", ""])
    for metric in ["groom_bout_net_receive_minus_give", "groom_bout_reciprocity_0to1", "social_engaged_pct_session"]:
        row = secondary.loc[secondary["metric"] == metric].iloc[0]
        lines.append(format_summary_line(row, SUMMARY_LABELS[metric]))
    if sensitivity is not None:
        lines.extend(["", "## Quiet-mask sensitivity", ""])
        for metric in SENSITIVITY_METRICS:
            row = sensitivity.loc[sensitivity["metric"] == metric].iloc[0]
            lines.append(format_summary_line(row, SUMMARY_LABELS[metric]))
    lines.append("")
    return "\n".join(lines)


def cohort_tables_dir(cohort_name: str) -> Path:
    return results_tables_dir(cohort_name, "single_value_core")


def cohort_docs_dir(cohort_name: str) -> Path:
    return docs_section_dir(cohort_name, "single_value_core")


def write_analysis_set(
    decision_df: pd.DataFrame,
    exploratory_df: pd.DataFrame,
    cohort_name: str,
    cohort_label: str,
    include_nested_quiet_mask: bool = True,
) -> None:
    tables_dir = cohort_tables_dir(cohort_name)
    docs_dir = cohort_docs_dir(cohort_name)
    tables_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    decision_df.to_csv(tables_dir / "unblinded_decision_table.csv", index=False)
    exploratory_df.to_csv(tables_dir / "unblinded_exploratory_nonsocial_table.csv", index=False)

    component_summary = summarize_by_condition(decision_df, GROOM_COMPONENT_METRICS)
    bout_component_summary = summarize_by_condition(decision_df, GROOM_BOUT_COMPONENT_METRICS)
    bout_duration_summary = summarize_by_condition(decision_df, GROOM_BOUT_DURATION_METRICS)
    primary_summary = summarize_by_condition(decision_df, PRIMARY_METRICS)
    secondary_summary = summarize_by_condition(decision_df, SECONDARY_METRICS)
    exploratory_summary = summarize_by_condition(exploratory_df, EXPLORATORY_METRICS)

    component_summary.to_csv(tables_dir / "condition_comparison_groom_components.csv", index=False)
    bout_component_summary.to_csv(tables_dir / "condition_comparison_groom_bout_components.csv", index=False)
    bout_duration_summary.to_csv(tables_dir / "condition_comparison_groom_bout_durations.csv", index=False)
    primary_summary.to_csv(tables_dir / "condition_comparison_primary.csv", index=False)
    secondary_summary.to_csv(tables_dir / "condition_comparison_secondary.csv", index=False)
    sensitivity_summary = None
    if include_nested_quiet_mask:
        sensitivity_summary = summarize_by_condition(decision_df, SENSITIVITY_METRICS)
        sensitivity_summary.to_csv(tables_dir / "condition_comparison_quiet_mask_sensitivity.csv", index=False)
    exploratory_summary.to_csv(tables_dir / "condition_comparison_exploratory.csv", index=False)

    n_vehicle = int((decision_df["condition"] == "vehicle").sum())
    n_dcz = int((decision_df["condition"] == "DCZ").sum())
    raw_bout_markdown, composite_bout_markdown = build_groom_bout_markdown(
        bout_component_summary,
        secondary_summary,
        n_vehicle,
        n_dcz,
        cohort_label,
    )
    (docs_dir / "groom_duration_session_summary.md").write_text(
        build_raw_session_markdown(component_summary, n_vehicle, n_dcz, cohort_label),
        encoding="utf-8",
    )
    (docs_dir / "groom_composite_session_summary.md").write_text(
        build_composite_session_markdown(primary_summary, secondary_summary, n_vehicle, n_dcz, cohort_label, sensitivity_summary),
        encoding="utf-8",
    )
    (docs_dir / "groom_bout_session_summary.md").write_text(raw_bout_markdown, encoding="utf-8")
    (docs_dir / "groom_bout_composite_session_summary.md").write_text(composite_bout_markdown, encoding="utf-8")
    (docs_dir / "groom_bout_duration_session_summary.md").write_text(
        build_groom_bout_duration_markdown(bout_duration_summary, n_vehicle, n_dcz, cohort_label),
        encoding="utf-8",
    )
    if sensitivity_summary is not None:
        (docs_dir / "quiet_mask_supplementary.md").write_text(
            build_composite_session_markdown(primary_summary, secondary_summary, n_vehicle, n_dcz, cohort_label, sensitivity_summary),
            encoding="utf-8",
        )
    if cohort_name == "quiet_mask":
        (docs_dir / "quiet_mask_assumptions.md").write_text(
            build_quiet_mask_assumptions_markdown(),
            encoding="utf-8",
        )


def build_quiet_mask_decision(full_decision: pd.DataFrame) -> pd.DataFrame:
    quiet = full_decision.copy()
    quiet["session_duration_min"] = quiet["duration_min_quiet_masked_p90"]
    quiet["groom_give_pct_session"] = quiet["groom_give_pct_quiet_masked_p90"]
    quiet["groom_receive_pct_session"] = quiet["groom_receive_pct_quiet_masked_p90"]
    quiet["groom_total_pct_session"] = quiet["groom_total_pct_quiet_masked_p90"]
    quiet["groom_give_resolved_bouts"] = quiet["groom_give_bouts_quiet_masked_p90"]
    quiet["groom_receive_resolved_bouts"] = quiet["groom_receive_bouts_quiet_masked_p90"]
    quiet["groom_total_resolved_bouts"] = quiet["groom_total_bouts_quiet_masked_p90"]
    quiet["groom_give_bout_mean_duration_s"] = quiet["groom_give_bout_mean_duration_s_quiet_masked_p90"]
    quiet["groom_receive_bout_mean_duration_s"] = quiet["groom_receive_bout_mean_duration_s_quiet_masked_p90"]
    quiet["groom_total_bout_mean_duration_s"] = quiet["groom_total_bout_mean_duration_s_quiet_masked_p90"]
    quiet["groom_give_bout_median_duration_s"] = quiet["groom_give_bout_median_duration_s_quiet_masked_p90"]
    quiet["groom_receive_bout_median_duration_s"] = quiet["groom_receive_bout_median_duration_s_quiet_masked_p90"]
    quiet["groom_total_bout_median_duration_s"] = quiet["groom_total_bout_median_duration_s_quiet_masked_p90"]
    quiet["groom_duration_net_receive_minus_give_pct_session"] = quiet["groom_duration_net_receive_minus_give_pct_quiet_masked_p90"]
    quiet["groom_bout_net_receive_minus_give"] = quiet["groom_bout_net_receive_minus_give_quiet_masked_p90"]
    quiet["groom_duration_reciprocity_0to1"] = quiet["groom_duration_reciprocity_0to1_quiet_masked_p90"]
    quiet["groom_bout_reciprocity_0to1"] = quiet["groom_bout_reciprocity_0to1_quiet_masked_p90"]
    quiet["social_engaged_pct_session"] = quiet["social_engaged_pct_quiet_masked_p90"]
    quiet["attention_to_outside_agents_resolved_pct_session"] = quiet["attention_outside_pct_quiet_masked_p90"]
    quiet["hiccups_resolved_pct_session"] = quiet["hiccups_pct_quiet_masked_p90"]
    return quiet


def build_quiet_mask_exploratory(full_exploratory: pd.DataFrame) -> pd.DataFrame:
    quiet = full_exploratory.copy()
    quiet["travel_resolved_pct_session"] = quiet["travel_pct_quiet_masked_p90"]
    quiet["attention_to_outside_agents_resolved_pct_session"] = quiet["attention_outside_pct_quiet_masked_p90"]
    quiet["hiccups_resolved_pct_session"] = quiet["hiccups_pct_quiet_masked_p90"]
    return quiet


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

    write_analysis_set(full_decision, full_exploratory, "full", "full session set", include_nested_quiet_mask=False)
    write_analysis_set(
        build_quiet_mask_decision(full_decision),
        build_quiet_mask_exploratory(full_exploratory),
        "quiet_mask",
        "quiet-mask sensitivity session set",
        include_nested_quiet_mask=False,
    )

    filtered_decision = full_decision.loc[full_decision["session_id"] != VET_ENTRY_SESSION_ID].reset_index(drop=True)
    filtered_exploratory = full_exploratory.loc[full_exploratory["session_id"] != VET_ENTRY_SESSION_ID].reset_index(drop=True)
    write_analysis_set(filtered_decision, filtered_exploratory, "exclude_vet_entry", "excluding known vet-entry session 596273")


if __name__ == "__main__":
    main()

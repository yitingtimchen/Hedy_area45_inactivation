from __future__ import annotations

from itertools import combinations
from pathlib import Path
import sys
from zipfile import ZipFile
import re
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PARENT = Path(__file__).resolve().parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from _plot_helpers import exact_slope_permutation_p, fit_line, p_style, style_axis  # noqa: E402
from output_layout import docs_section_dir, results_figures_dir, results_tables_dir  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
BLINDED_METRICS_PATH = ROOT / "results" / "blinded" / "tables" / "blinded_social_nonprecedence_metrics_by_session.csv"
BLINDED_INTERVALS_PATH = ROOT / "results" / "blinded" / "tables" / "blinded_social_nonprecedence_interval_table.csv"
UNBLINDED_ROOT = ROOT / "results" / "unblinded"
DOCS_ROOT = ROOT / "docs" / "unblinded"
KEY_PATH = ROOT / "data" / "raw" / "session_key" / "Sessions name encoding.xlsx"
VET_ENTRY_SESSION_ID = "596273"

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

SOCIAL_BEHAVIORS = [
    "Approach (non-agonistic)",
    "Proximity (<arm's reach)",
    "Groom solicit",
    "Mount attempt",
    "Mount give",
    "Mount receive",
    "Aggressive vocal",
    "Open-mouth threat",
    "Enlist/Recruit",
    "Cage-shake display",
]

FAMILY_MAP = {
    "affiliative_nongroom": [
        "Approach (non-agonistic)",
        "Proximity (<arm's reach)",
        "Groom solicit",
    ],
    "sexual": [
        "Mount attempt",
        "Mount give",
        "Mount receive",
    ],
    "aggression_display": [
        "Aggressive vocal",
        "Open-mouth threat",
        "Enlist/Recruit",
        "Cage-shake display",
    ],
}

PRETTY = {
    "Approach (non-agonistic)_duration_pct_session": "Approach duration (% session)",
    "Approach (non-agonistic)_bout_count": "Approach bouts per session",
    "Proximity (<arm's reach)_duration_pct_session": "Proximity duration (% session)",
    "Proximity (<arm's reach)_bout_count": "Proximity bouts per session",
    "Groom solicit_duration_pct_session": "Groom-solicit duration (% session)",
    "Groom solicit_bout_count": "Groom-solicit bouts per session",
    "Mount attempt_duration_pct_session": "Mount-attempt duration (% session)",
    "Mount attempt_bout_count": "Mount-attempt bouts per session",
    "Mount give_duration_pct_session": "Mount-give duration (% session)",
    "Mount give_bout_count": "Mount-give bouts per session",
    "Mount receive_duration_pct_session": "Mount-receive duration (% session)",
    "Mount receive_bout_count": "Mount-receive bouts per session",
    "Aggressive vocal_duration_pct_session": "Aggressive-vocal duration (% session)",
    "Aggressive vocal_bout_count": "Aggressive-vocal bouts per session",
    "Open-mouth threat_duration_pct_session": "Open-mouth-threat duration (% session)",
    "Open-mouth threat_bout_count": "Open-mouth-threat bouts per session",
    "Enlist/Recruit_duration_pct_session": "Enlist/recruit duration (% session)",
    "Enlist/Recruit_bout_count": "Enlist/recruit bouts per session",
    "Cage-shake display_duration_pct_session": "Cage-shake-display duration (% session)",
    "Cage-shake display_bout_count": "Cage-shake-display bouts per session",
    "affiliative_nongroom_duration_pct_session": "Affiliative non-groom duration (% session)",
    "affiliative_nongroom_bout_count": "Affiliative non-groom bouts per session",
    "sexual_duration_pct_session": "Sexual behavior duration (% session)",
    "sexual_bout_count": "Sexual behavior bouts per session",
    "aggression_display_duration_pct_session": "Aggression-display duration (% session)",
    "aggression_display_bout_count": "Aggression-display bouts per session",
}

SEXUAL_FAMILY_DURATION_METRICS = [
    "Mount give_duration_pct_session",
    "Mount receive_duration_pct_session",
]

SEXUAL_FAMILY_BOUT_METRICS = [
    "Mount give_bout_count",
    "Mount receive_bout_count",
]

SEXUAL_FAMILY_DURATION_TITLES = {
    "Mount give_duration_pct_session": "Mount-give duration",
    "Mount receive_duration_pct_session": "Mount-receive duration",
}

SEXUAL_FAMILY_BOUT_TITLES = {
    "Mount give_bout_count": "Mount-give bouts",
    "Mount receive_bout_count": "Mount-receive bouts",
}

COHORT_SPECS = [
    ("full", "full session set", False, False),
    ("quiet_mask", "quiet-mask sensitivity session set", True, False),
    ("exclude_vet_entry", "excluding known vet-entry session 596273", False, True),
]

SEXUAL_TEMPORAL_DURATION_METRICS = [
    "Mount give_duration_pct_session",
    "Mount receive_duration_pct_session",
]

SEXUAL_TEMPORAL_BOUT_METRICS = [
    "Mount give_bout_count",
    "Mount receive_bout_count",
]

SEXUAL_VEHICLE_COLOR = "#E7B4C8"
SEXUAL_DCZ_COLOR = "#C2185B"


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
    diffs_arr = np.asarray(diffs, dtype=float)
    p = float(np.mean(np.abs(diffs_arr) >= abs(observed)))
    return float(observed), p


def bootstrap_ci_for_mean_diff(dcz: np.ndarray, vehicle: np.ndarray, seed: int = 31, n_boot: int = 20000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    dcz_draws = rng.choice(dcz, size=(n_boot, len(dcz)), replace=True).mean(axis=1)
    veh_draws = rng.choice(vehicle, size=(n_boot, len(vehicle)), replace=True).mean(axis=1)
    diffs = dcz_draws - veh_draws
    low, high = np.percentile(diffs, [2.5, 97.5])
    return float(low), float(high)


def sample_sd(values: np.ndarray) -> float:
    return float(np.std(values, ddof=1)) if len(values) >= 2 else float("nan")


def compare_conditions(df: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for metric in metrics:
        sub = df[["condition", metric]].copy()
        sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
        sub = sub.dropna(subset=[metric]).reset_index(drop=True)
        dcz = sub.loc[sub["condition"] == "DCZ", metric].to_numpy(dtype=float)
        vehicle = sub.loc[sub["condition"] == "vehicle", metric].to_numpy(dtype=float)
        effect, p_value = exact_label_permutation_p(sub[metric].to_numpy(dtype=float), sub["condition"].to_numpy())
        ci_low, ci_high = bootstrap_ci_for_mean_diff(dcz, vehicle)
        rows.append(
            {
                "metric": metric,
                "pretty_metric": PRETTY.get(metric, metric),
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


def padded_limits(df: pd.DataFrame, metric: str) -> tuple[float, float] | None:
    values = pd.to_numeric(df[metric], errors="coerce").dropna().to_numpy(dtype=float)
    if len(values) == 0:
        return None
    vmin = float(np.min(values))
    vmax = float(np.max(values))
    if vmin == vmax:
        pad = max(0.1, abs(vmax) * 0.2, 1.0 if "bout" in metric else 0.02)
        return (vmin - 0.25 * pad, vmax + pad)
    span = vmax - vmin
    lower_pad = 0.10 * span
    upper_pad = 0.22 * span
    if "bout" in metric and vmin >= 0:
        return (max(0.0, vmin - lower_pad), vmax + upper_pad)
    return (vmin - lower_pad, vmax + upper_pad)


def paired_strip_sexual(
    ax: plt.Axes,
    df: pd.DataFrame,
    metric: str,
    ylabel: str,
    title: str,
    p_value: float | None = None,
    y_limits: tuple[float, float] | None = None,
) -> None:
    sub = df[["condition", metric]].copy()
    sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
    sub = sub.dropna(subset=[metric]).reset_index(drop=True)

    vehicle = sub.loc[sub["condition"] == "vehicle", metric].to_numpy(dtype=float)
    dcz = sub.loc[sub["condition"] == "DCZ", metric].to_numpy(dtype=float)

    rng = np.random.default_rng(4)
    veh_jitter = rng.uniform(-0.06, 0.06, size=len(vehicle))
    dcz_jitter = rng.uniform(-0.06, 0.06, size=len(dcz))

    ax.scatter(np.full(len(vehicle), 0) + veh_jitter, vehicle, color=SEXUAL_VEHICLE_COLOR, s=40, zorder=3)
    ax.scatter(np.full(len(dcz), 1) + dcz_jitter, dcz, color=SEXUAL_DCZ_COLOR, s=40, zorder=3)

    for x, values, color in [(0, vehicle, SEXUAL_VEHICLE_COLOR), (1, dcz, SEXUAL_DCZ_COLOR)]:
        if len(values) == 0:
            continue
        mean_value = float(np.mean(values))
        ax.plot([x - 0.18, x + 0.18], [mean_value, mean_value], color=color, linewidth=3.0, zorder=4)

    ax.set_xticks([0, 1], ["Vehicle", "DCZ"])
    ax.set_ylabel(ylabel, fontsize=10.5)
    ax.set_title(title, fontsize=12, loc="left")
    if p_value is not None:
        label = p_style(p_value)
        ax.text(
            0.02,
            0.97,
            label["text"],
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9.6,
            color=label["color"],
            fontweight=label["fontweight"],
        )
    if y_limits is not None:
        ax.set_ylim(*y_limits)
    style_axis(ax)


def build_quiet_mask_metrics(full_metrics: pd.DataFrame) -> pd.DataFrame:
    quiet = full_metrics.copy()
    quiet_duration_col = "session_duration_quiet_masked_s"
    if quiet_duration_col not in quiet.columns:
        matches = [col for col in quiet.columns if "session_duration_quiet_masked" in col]
        if not matches:
            raise KeyError("No quiet-masked session duration column found in social non-precedence table.")
        quiet_duration_col = matches[0]
    quiet["session_duration_s"] = quiet[quiet_duration_col]
    duration_cols = [col for col in full_metrics.columns if col.endswith("_duration_pct_quiet_masked_p90")]
    for col in duration_cols:
        quiet[col.replace("_duration_pct_quiet_masked_p90", "_duration_pct_session")] = quiet[col]
    return quiet


def plot_sexual_family_panel(
    metrics_df: pd.DataFrame,
    summary: pd.DataFrame,
    figures_dir: Path,
    cohort_label: str,
    include_bouts: bool,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.9))
    axes = np.atleast_1d(axes).ravel()
    for ax, metric in zip(axes, SEXUAL_FAMILY_DURATION_METRICS):
        p_value = float(summary.loc[summary["metric"] == metric, "exact_permutation_p_two_sided"].iloc[0])
        paired_strip_sexual(
            ax,
            metrics_df,
            metric,
            PRETTY[metric],
            SEXUAL_FAMILY_DURATION_TITLES[metric],
            p_value,
            y_limits=padded_limits(metrics_df, metric),
        )
    fig.suptitle(f"Sexual-family duration summaries: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.93), w_pad=0.9)
    fig.savefig(figures_dir / "sexual_family_duration_exploratory.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    if not include_bouts:
        return

    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.9))
    axes = np.atleast_1d(axes).ravel()
    for ax, metric in zip(axes, SEXUAL_FAMILY_BOUT_METRICS):
        p_value = float(summary.loc[summary["metric"] == metric, "exact_permutation_p_two_sided"].iloc[0])
        paired_strip_sexual(
            ax,
            metrics_df,
            metric,
            PRETTY[metric],
            SEXUAL_FAMILY_BOUT_TITLES[metric],
            p_value,
            y_limits=padded_limits(metrics_df, metric),
        )
    fig.suptitle(f"Sexual-family bout summaries: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.93), w_pad=0.9)
    fig.savefig(figures_dir / "sexual_family_bout_exploratory.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_sexual_family_markdown(summary: pd.DataFrame, cohort_label: str, include_bouts: bool) -> str:
    lines = [
        "# Sexual-Family Exploratory Summary",
        "",
        f"Cohort: {cohort_label}.",
        "This exploratory summary was derived from a blinded session-level table of raw BORIS social state events that intentionally ignored precedence, then unblinded only at the session-comparison stage.",
        "",
        "## Scope and assumptions",
        "",
        "- Durations can overlap across behaviors because precedence is intentionally ignored.",
        "- These metrics are raw event-family summaries and are not an additive partition of the session.",
        "- The most interpretable metrics in this exploratory family are `Mount give` and `Mount receive`.",
        "",
        "## Sexual-family metrics",
        "",
    ]
    ranked = summary.loc[summary["metric"].isin(SEXUAL_FAMILY_DURATION_METRICS)].copy()
    ranked = ranked.sort_values("exact_permutation_p_two_sided").reset_index(drop=True)
    for row in ranked.itertuples(index=False):
        lines.append(
            f"- {row.pretty_metric}: vehicle mean `{row.vehicle_mean:.3f}`, DCZ mean `{row.DCZ_mean:.3f}`, "
            f"mean difference `{row.mean_diff_DCZ_minus_vehicle:.3f}`, 95% CI "
            f"`[{row.bootstrap_ci95_low:.3f}, {row.bootstrap_ci95_high:.3f}]`, exact permutation "
            f"`p = {row.exact_permutation_p_two_sided:.4f}`."
        )
    if include_bouts:
        lines.extend(["", "## Sexual-family bout metrics", ""])
        ranked = summary.loc[summary["metric"].isin(SEXUAL_FAMILY_BOUT_METRICS)].copy()
        ranked = ranked.sort_values("exact_permutation_p_two_sided").reset_index(drop=True)
        for row in ranked.itertuples(index=False):
            lines.append(
                f"- {row.pretty_metric}: vehicle mean `{row.vehicle_mean:.3f}`, DCZ mean `{row.DCZ_mean:.3f}`, "
                f"mean difference `{row.mean_diff_DCZ_minus_vehicle:.3f}`, 95% CI "
                f"`[{row.bootstrap_ci95_low:.3f}, {row.bootstrap_ci95_high:.3f}]`, exact permutation "
                f"`p = {row.exact_permutation_p_two_sided:.4f}`."
            )
    lines.append("")
    return "\n".join(lines)


def build_markdown(summary: pd.DataFrame, cohort_label: str) -> str:
    lines = [
        "# Raw Social Non-Precedence Exploration",
        "",
        f"Cohort: {cohort_label}.",
        "This exploratory pass ignores precedence within the social layer and summarizes raw trimmed-window behavior events directly from the BORIS state-event stream.",
        "",
        "## Scope and assumptions",
        "",
        "- Durations can overlap across behaviors because precedence is intentionally ignored.",
        "- These metrics should be read as independent event-family summaries, not as an additive partition of the session.",
        "- This analysis is exploratory and intended to surface potentially interesting non-groom social signals for follow-up.",
        "",
        "## Strongest apparent condition differences",
        "",
    ]
    ranked = summary.sort_values("exact_permutation_p_two_sided").reset_index(drop=True)
    for row in ranked.head(12).itertuples(index=False):
        lines.append(
            f"- {row.pretty_metric}: vehicle mean `{row.vehicle_mean:.3f}`, DCZ mean `{row.DCZ_mean:.3f}`, "
            f"mean difference `{row.mean_diff_DCZ_minus_vehicle:.3f}`, 95% CI "
            f"`[{row.bootstrap_ci95_low:.3f}, {row.bootstrap_ci95_high:.3f}]`, exact permutation "
            f"`p = {row.exact_permutation_p_two_sided:.4f}`."
        )
    lines.append("")
    return "\n".join(lines)


def analyze_temporal_metric(df: pd.DataFrame, metric: str) -> dict[str, object]:
    ordered = df.sort_values("session_index").reset_index(drop=True)
    sub = ordered[["session_index", "condition", metric]].copy()
    sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
    sub = sub.dropna(subset=[metric]).reset_index(drop=True)
    y = sub[metric].to_numpy(dtype=float)
    x = sub["session_index"].to_numpy(dtype=float)
    condition = sub["condition"].to_numpy()
    raw_effect, raw_p = exact_label_permutation_p(y, condition)
    vehicle = sub.loc[sub["condition"] == "vehicle", ["session_index", metric]]
    dcz = sub.loc[sub["condition"] == "DCZ", ["session_index", metric]]
    vehicle_fit = fit_line(vehicle["session_index"].to_numpy(dtype=float), vehicle[metric].to_numpy(dtype=float))
    dcz_fit = fit_line(dcz["session_index"].to_numpy(dtype=float), dcz[metric].to_numpy(dtype=float))
    return {
        "metric": metric,
        "pretty_metric": PRETTY[metric],
        "raw_condition_effect": raw_effect,
        "raw_condition_permutation_p_two_sided": raw_p,
        "vehicle_slope_per_session": vehicle_fit[1],
        "vehicle_slope_permutation_p_two_sided": exact_slope_permutation_p(
            vehicle["session_index"].to_numpy(dtype=float),
            vehicle[metric].to_numpy(dtype=float),
        ),
        "dcz_slope_per_session": dcz_fit[1],
        "dcz_slope_permutation_p_two_sided": exact_slope_permutation_p(
            dcz["session_index"].to_numpy(dtype=float),
            dcz[metric].to_numpy(dtype=float),
        ),
    }


def build_temporal_markdown(summary: pd.DataFrame, cohort_label: str, include_bouts: bool) -> str:
    lines = [
        "# Sexual-Family Temporal Dependence",
        "",
        f"Cohort: {cohort_label}.",
        "This exploratory check asks whether sexual-family metrics show simple within-condition drift over session order that could help explain the session-level condition differences.",
        "",
        "## Methods",
        "",
        "- Raw condition effect is the exact two-sided label permutation result on the session-level metric.",
        "- Vehicle and DCZ slopes are fit separately over session order within condition.",
        "- Slope significance is assessed with the same permutation-on-slope logic used in the grooming temporal check.",
        "",
        "## Results",
        "",
    ]
    metrics = SEXUAL_TEMPORAL_DURATION_METRICS + (SEXUAL_TEMPORAL_BOUT_METRICS if include_bouts else [])
    ranked = summary.loc[summary["metric"].isin(metrics)].copy()
    for row in ranked.itertuples(index=False):
        lines.extend(
            [
                f"### {row.pretty_metric}",
                f"- Raw condition effect: `{row.raw_condition_effect:.3f}`, exact permutation `p = {row.raw_condition_permutation_p_two_sided:.4f}`.",
                f"- Vehicle slope: `{row.vehicle_slope_per_session:.3f}` per session, slope permutation `p = {row.vehicle_slope_permutation_p_two_sided:.4f}`.",
                f"- DCZ slope: `{row.dcz_slope_per_session:.3f}` per session, slope permutation `p = {row.dcz_slope_permutation_p_two_sided:.4f}`.",
                "",
            ]
        )
    return "\n".join(lines)


def plot_temporal_metric(ax: plt.Axes, df: pd.DataFrame, metric: str, summary_row: pd.Series, title: str) -> None:
    ordered = df.sort_values("session_index").reset_index(drop=True)
    for condition, color, slope_col, p_col, xpos in [
        ("vehicle", SEXUAL_VEHICLE_COLOR, "vehicle_slope_per_session", "vehicle_slope_permutation_p_two_sided", 0.03),
        ("DCZ", SEXUAL_DCZ_COLOR, "dcz_slope_per_session", "dcz_slope_permutation_p_two_sided", 0.53),
    ]:
        sub = ordered.loc[ordered["condition"] == condition, ["session_index", metric]].copy()
        sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
        sub = sub.dropna(subset=[metric]).reset_index(drop=True)
        x = sub["session_index"].to_numpy(dtype=float)
        y = sub[metric].to_numpy(dtype=float)
        intercept, slope = fit_line(x, y)
        xgrid = np.linspace(x.min(), x.max(), 200)
        ygrid = intercept + slope * (xgrid - x.mean())
        ax.scatter(x, y, color=color, s=42, zorder=3)
        ax.plot(x, y, color=color, linewidth=1.3, alpha=0.9, zorder=2)
        ax.plot(xgrid, ygrid, color=color, linewidth=1.9, linestyle="--", zorder=4)
        label = p_style(float(summary_row[p_col]))
        ax.text(
            xpos,
            0.97,
            f"{condition.capitalize()} slope = {summary_row[slope_col]:.3f}\n{label['text']}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=8.9,
            color=label["color"],
            fontweight=label["fontweight"],
        )
    ax.set_title(title, fontsize=11, loc="left")
    ax.set_xlabel("Session order", fontsize=10.0)
    ax.set_ylabel(PRETTY[metric], fontsize=9.8)
    style_axis(ax, tick_size=9.0)


def plot_temporal_panel(df: pd.DataFrame, summary: pd.DataFrame, figures_dir: Path, cohort_label: str, include_bouts: bool) -> None:
    duration_metrics = SEXUAL_TEMPORAL_DURATION_METRICS
    bout_metrics = SEXUAL_TEMPORAL_BOUT_METRICS if include_bouts else []
    titles = {**SEXUAL_FAMILY_DURATION_TITLES, **SEXUAL_FAMILY_BOUT_TITLES}
    nrows = 2 if include_bouts else 1
    fig, axes = plt.subplots(nrows, 2, figsize=(8.6, 6.2 if include_bouts else 3.6))
    axes_arr = np.atleast_1d(axes).ravel()
    summary_indexed = summary.set_index("metric")
    ordered_metrics = duration_metrics + bout_metrics
    for ax, metric in zip(axes_arr, ordered_metrics):
        plot_temporal_metric(ax, df, metric, summary_indexed.loc[metric], titles[metric])
    for ax in axes_arr[len(ordered_metrics):]:
        ax.axis("off")
    fig.suptitle(f"Sexual-family temporal dependence: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.93), w_pad=0.9, h_pad=0.9)
    fig.savefig(figures_dir / "sexual_family_temporal_dependence.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def write_cohort_outputs(
    metrics_df: pd.DataFrame,
    interval_df: pd.DataFrame,
    cohort_name: str,
    cohort_label: str,
    include_bouts: bool = True,
) -> None:
    tables_dir = results_tables_dir(cohort_name, "social_nonprecedence")
    docs_dir = docs_section_dir(cohort_name, "social_nonprecedence")
    figures_dir = results_figures_dir(cohort_name, "social_nonprecedence")

    metrics = [col for col in metrics_df.columns if col.endswith("_duration_pct_session")]
    if include_bouts:
        metrics.extend(col for col in metrics_df.columns if col.endswith("_bout_count"))
    summary = compare_conditions(metrics_df, metrics)
    metrics_df.to_csv(tables_dir / "social_nonprecedence_metrics_by_session.csv", index=False)
    if not interval_df.empty:
        interval_df.to_csv(tables_dir / "social_nonprecedence_interval_table.csv", index=False)
    summary.to_csv(tables_dir / "social_nonprecedence_condition_comparison.csv", index=False)
    (docs_dir / "social_nonprecedence_analysis.md").write_text(
        build_markdown(summary, cohort_label),
        encoding="utf-8",
    )
    plot_sexual_family_panel(metrics_df, summary, figures_dir, cohort_label, include_bouts)
    (docs_dir / "sexual_family_exploratory.md").write_text(
        build_sexual_family_markdown(summary, cohort_label, include_bouts),
        encoding="utf-8",
    )
    temporal_metrics = SEXUAL_TEMPORAL_DURATION_METRICS + (SEXUAL_TEMPORAL_BOUT_METRICS if include_bouts else [])
    temporal_summary = pd.DataFrame([analyze_temporal_metric(metrics_df, metric) for metric in temporal_metrics])
    temporal_summary.to_csv(tables_dir / "sexual_family_temporal_dependence_summary.csv", index=False)
    plot_temporal_panel(metrics_df, temporal_summary, figures_dir, cohort_label, include_bouts)
    (docs_dir / "sexual_family_temporal_dependence.md").write_text(
        build_temporal_markdown(temporal_summary, cohort_label, include_bouts),
        encoding="utf-8",
    )


def main() -> None:
    session_map = load_unblinding_map()
    blinded_metrics = pd.read_csv(BLINDED_METRICS_PATH, dtype={"session_id": str})
    full_metrics = session_map.merge(blinded_metrics, on="session_id", how="left").sort_values("date").reset_index(drop=True)
    quiet_metrics = build_quiet_mask_metrics(full_metrics).sort_values("date").reset_index(drop=True)

    interval_df = pd.DataFrame()
    if BLINDED_INTERVALS_PATH.exists():
        blinded_intervals = pd.read_csv(BLINDED_INTERVALS_PATH, dtype={"session_id": str})
        interval_df = session_map.merge(blinded_intervals, on="session_id", how="left").sort_values(["date", "start_s"]).reset_index(drop=True)

    for cohort_name, cohort_label, use_quiet_mask, exclude_vet in COHORT_SPECS:
        metrics_df = quiet_metrics.copy() if use_quiet_mask else full_metrics.copy()
        cohort_intervals = interval_df.copy()
        if exclude_vet:
            metrics_df = metrics_df.loc[metrics_df["session_id"] != VET_ENTRY_SESSION_ID].reset_index(drop=True)
            if not cohort_intervals.empty:
                cohort_intervals = cohort_intervals.loc[cohort_intervals["session_id"] != VET_ENTRY_SESSION_ID].reset_index(drop=True)
        write_cohort_outputs(metrics_df, cohort_intervals, cohort_name, cohort_label, include_bouts=not use_quiet_mask)


if __name__ == "__main__":
    main()

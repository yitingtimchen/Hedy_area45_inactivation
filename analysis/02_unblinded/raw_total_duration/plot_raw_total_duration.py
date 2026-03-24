from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PARENT = Path(__file__).resolve().parents[1]
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from _plot_helpers import paired_strip  # noqa: E402
from data_selection import load_all_branch_tables  # noqa: E402
from reorg_common import DATA_SELECTIONS, add_data_selection_and_mode_header, canonical_selection_name, ensure_output_dirs, format_summary_line, summarize_by_condition  # noqa: E402


AGGREGATION_MODE = "raw_total_duration"
AGGREGATION_LABEL = "raw_total_duration"

METRIC_LABELS = {
    "selected_duration_min": "Included session duration (min)",
    "groom_give_duration_s_selected": "Groom give duration (s)",
    "groom_receive_duration_s_selected": "Groom receive duration (s)",
    "groom_total_duration_s_selected": "Total grooming duration (s)",
    "groom_net_duration_s_selected": "Net grooming duration (s; receive - give)",
    "mount_give_duration_s_selected": "Mount give duration (s)",
    "mount_receive_duration_s_selected": "Mount receive duration (s)",
    "groom_solicit_duration_s_selected": "Groom-solicit duration (s)",
    "forage_search_duration_s_selected": "Foraging duration (s)",
    "loud_stress_composite_duration_s_selected": "Loud/stress composite duration (s)",
    "groom_bout_mean_duration_selected_s": "Mean grooming bout duration (s)",
    "groom_bout_median_duration_selected_s": "Median grooming bout duration (s)",
}


def plot_duration_context(df: pd.DataFrame, figures_dir: Path, data_selection: str, selection_label: str) -> pd.DataFrame:
    summary = summarize_by_condition(df, ["selected_duration_min"])
    fig, ax = plt.subplots(1, 1, figsize=(4.6, 3.8))
    p_value = float(summary.loc[summary["metric"] == "selected_duration_min", "exact_permutation_p_two_sided"].iloc[0])
    paired_strip(
        ax,
        df,
        "selected_duration_min",
        "Minutes",
        "Included session duration",
        p_value,
    )
    fig.suptitle(f"Session duration: {selection_label}", fontsize=13, x=0.08, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(figures_dir / f"session_duration__{AGGREGATION_MODE}__{data_selection}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    return summary


def plot_grooming(df: pd.DataFrame, figures_dir: Path, data_selection: str, selection_label: str) -> pd.DataFrame:
    metrics = [
        "groom_give_duration_s_selected",
        "groom_receive_duration_s_selected",
        "groom_total_duration_s_selected",
        "groom_net_duration_s_selected",
        "groom_bout_mean_duration_selected_s",
        "groom_bout_median_duration_selected_s",
    ]
    metrics = [metric for metric in metrics if df[metric].notna().any()]
    summary = summarize_by_condition(df, metrics)
    fig, axes = plt.subplots(2, 3, figsize=(9.6, 6.2))
    specs = [
        ("groom_give_duration_s_selected", "Seconds", "Groom give duration"),
        ("groom_receive_duration_s_selected", "Seconds", "Groom receive duration"),
        ("groom_total_duration_s_selected", "Seconds", "Total grooming duration"),
        ("groom_net_duration_s_selected", "Seconds", "Net grooming duration"),
        ("groom_bout_mean_duration_selected_s", "Seconds", "Mean grooming bout duration"),
        ("groom_bout_median_duration_selected_s", "Seconds", "Median grooming bout duration"),
    ]
    for ax, (metric, ylabel, title) in zip(axes.ravel(), specs):
        if metric not in summary["metric"].tolist():
            ax.set_visible(False)
            continue
        p_value = float(summary.loc[summary["metric"] == metric, "exact_permutation_p_two_sided"].iloc[0])
        paired_strip(ax, df, metric, ylabel, title, p_value)
        if metric == "groom_net_duration_s_selected":
            ax.axhline(0, color="#7F7F7F", linewidth=1.0, linestyle="--")
    fig.suptitle(f"Grooming raw duration summaries: {selection_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94), w_pad=0.9, h_pad=1.0)
    fig.savefig(figures_dir / f"grooming__{AGGREGATION_MODE}__{data_selection}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    return summary


def plot_supporting(df: pd.DataFrame, figures_dir: Path, data_selection: str, selection_label: str) -> pd.DataFrame:
    metrics = [
        "mount_give_duration_s_selected",
        "mount_receive_duration_s_selected",
        "groom_solicit_duration_s_selected",
        "forage_search_duration_s_selected",
        "loud_stress_composite_duration_s_selected",
    ]
    summary = summarize_by_condition(df, metrics)
    fig, axes = plt.subplots(1, 5, figsize=(14.0, 3.8))
    specs = [
        ("mount_give_duration_s_selected", "Seconds", "Mount give duration"),
        ("mount_receive_duration_s_selected", "Seconds", "Mount receive duration"),
        ("groom_solicit_duration_s_selected", "Seconds", "Groom-solicit duration"),
        ("forage_search_duration_s_selected", "Seconds", "Foraging duration"),
        ("loud_stress_composite_duration_s_selected", "Seconds", "Loud/stress composite duration"),
    ]
    for ax, (metric, ylabel, title) in zip(axes, specs):
        p_value = float(summary.loc[summary["metric"] == metric, "exact_permutation_p_two_sided"].iloc[0])
        paired_strip(ax, df, metric, ylabel, title, p_value)
    fig.suptitle(f"Supporting raw duration summaries: {selection_label}", fontsize=13, x=0.05, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92), w_pad=0.8)
    fig.savefig(figures_dir / f"supporting_behavior__{AGGREGATION_MODE}__{data_selection}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    return summary


def write_markdown(
    data_selection: str,
    selection_label: str,
    docs_dir: Path,
    duration_summary: pd.DataFrame,
    grooming_summary: pd.DataFrame,
    supporting_summary: pd.DataFrame,
) -> None:
    lines = [
        "# Raw Total Duration Summary",
        "",
    ]
    add_data_selection_and_mode_header(lines, selection_label, AGGREGATION_LABEL)
    lines.extend(["## Included session duration", ""])
    lines.append(format_summary_line(duration_summary.iloc[0], METRIC_LABELS["selected_duration_min"]))
    lines.extend(["", "## Grooming", ""])
    for metric in grooming_summary["metric"]:
        row = grooming_summary.loc[grooming_summary["metric"] == metric].iloc[0]
        lines.append(format_summary_line(row, METRIC_LABELS[metric]))
    lines.extend(["", "## Supporting behaviors", ""])
    for metric in supporting_summary["metric"]:
        row = supporting_summary.loc[supporting_summary["metric"] == metric].iloc[0]
        lines.append(format_summary_line(row, METRIC_LABELS[metric]))
    (docs_dir / f"session_behavior__{AGGREGATION_MODE}__{data_selection}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    branch_tables = load_all_branch_tables()
    for data_selection, selection_label in DATA_SELECTIONS:
        if data_selection == "include_smoothed_loud_epochs_only":
            continue
        output_name = canonical_selection_name(data_selection)
        df = branch_tables[data_selection].copy()
        figures_dir, tables_dir, docs_dir = ensure_output_dirs(data_selection, AGGREGATION_MODE)
        df.to_csv(tables_dir / f"session_metrics__{AGGREGATION_MODE}__{output_name}.csv", index=False)
        duration_summary = plot_duration_context(df, figures_dir, output_name, selection_label)
        grooming_summary = plot_grooming(df, figures_dir, output_name, selection_label)
        supporting_summary = plot_supporting(df, figures_dir, output_name, selection_label)
        duration_summary.to_csv(tables_dir / f"session_duration_stats__{AGGREGATION_MODE}__{output_name}.csv", index=False)
        grooming_summary.to_csv(tables_dir / f"grooming_stats__{AGGREGATION_MODE}__{output_name}.csv", index=False)
        supporting_summary.to_csv(tables_dir / f"supporting_behavior_stats__{AGGREGATION_MODE}__{output_name}.csv", index=False)
        write_markdown(output_name, selection_label, docs_dir, duration_summary, grooming_summary, supporting_summary)


if __name__ == "__main__":
    main()

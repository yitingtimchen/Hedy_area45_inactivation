from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PARENT = Path(__file__).resolve().parents[1]
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from _plot_helpers import paired_strip  # noqa: E402
from data_selection import load_all_branch_tables  # noqa: E402
from reorg_common import DATA_SELECTIONS, add_data_selection_and_mode_header, canonical_selection_name, ensure_output_dirs, format_summary_line, summarize_by_condition  # noqa: E402


AGGREGATION_MODE = "normalized_total_duration"
AGGREGATION_LABEL = "normalized_total_duration"

METRIC_LABELS = {
    "groom_give_pct_selected": "Groom give (% selected time)",
    "groom_receive_pct_selected": "Groom receive (% selected time)",
    "groom_total_pct_selected": "Total grooming (% selected time)",
    "groom_net_pct_selected": "Net grooming (% selected time; receive - give)",
    "groom_reciprocity_selected": "Grooming reciprocity (0 to 1)",
    "mount_give_pct_selected": "Mount give (% selected time)",
    "mount_receive_pct_selected": "Mount receive (% selected time)",
    "groom_solicit_pct_selected": "Groom-solicit (% selected time)",
    "forage_search_pct_selected": "Foraging (% selected time)",
    "loud_stress_composite_pct_selected": "Loud/stress composite (% selected time)",
}


def plot_grooming(df: pd.DataFrame, figures_dir: Path, data_selection: str, selection_label: str) -> pd.DataFrame:
    metrics = [
        "groom_give_pct_selected",
        "groom_receive_pct_selected",
        "groom_total_pct_selected",
        "groom_net_pct_selected",
        "groom_reciprocity_selected",
    ]
    summary = summarize_by_condition(df, metrics)
    fig, axes = plt.subplots(1, 5, figsize=(14.0, 3.8))
    specs = [
        ("groom_give_pct_selected", "% selected time", "Groom give duration"),
        ("groom_receive_pct_selected", "% selected time", "Groom receive duration"),
        ("groom_total_pct_selected", "% selected time", "Total grooming duration"),
        ("groom_net_pct_selected", "% selected time", "Net grooming duration"),
        ("groom_reciprocity_selected", "0 to 1", "Grooming reciprocity"),
    ]
    for ax, (metric, ylabel, title) in zip(axes, specs):
        p_value = float(summary.loc[summary["metric"] == metric, "exact_permutation_p_two_sided"].iloc[0])
        y_limits = (0.0, 1.05) if metric == "groom_reciprocity_selected" else None
        paired_strip(ax, df, metric, ylabel, title, p_value, y_limits=y_limits)
        if metric == "groom_net_pct_selected":
            ax.axhline(0, color="#7F7F7F", linewidth=1.0, linestyle="--")
    fig.suptitle(f"Grooming normalized duration summaries: {selection_label}", fontsize=13, x=0.05, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92), w_pad=0.8)
    fig.savefig(figures_dir / f"grooming__{AGGREGATION_MODE}__{data_selection}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    return summary


def plot_supporting(df: pd.DataFrame, figures_dir: Path, data_selection: str, selection_label: str) -> pd.DataFrame:
    metrics = [
        "mount_give_pct_selected",
        "mount_receive_pct_selected",
        "groom_solicit_pct_selected",
        "forage_search_pct_selected",
        "loud_stress_composite_pct_selected",
    ]
    summary = summarize_by_condition(df, metrics)
    fig, axes = plt.subplots(1, 5, figsize=(14.0, 3.8))
    specs = [
        ("mount_give_pct_selected", "% selected time", "Mount give duration"),
        ("mount_receive_pct_selected", "% selected time", "Mount receive duration"),
        ("groom_solicit_pct_selected", "% selected time", "Groom-solicit duration"),
        ("forage_search_pct_selected", "% selected time", "Foraging duration"),
        ("loud_stress_composite_pct_selected", "% selected time", "Loud/stress composite"),
    ]
    for ax, (metric, ylabel, title) in zip(axes, specs):
        p_value = float(summary.loc[summary["metric"] == metric, "exact_permutation_p_two_sided"].iloc[0])
        paired_strip(ax, df, metric, ylabel, title, p_value)
    fig.suptitle(f"Supporting normalized duration summaries: {selection_label}", fontsize=13, x=0.05, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92), w_pad=0.8)
    fig.savefig(figures_dir / f"supporting_behavior__{AGGREGATION_MODE}__{data_selection}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    return summary


def write_markdown(data_selection: str, selection_label: str, docs_dir: Path, grooming_summary: pd.DataFrame, supporting_summary: pd.DataFrame) -> None:
    lines = [
        "# Normalized Total Duration Summary",
        "",
    ]
    add_data_selection_and_mode_header(lines, selection_label, AGGREGATION_LABEL)
    lines.extend(["## Grooming", ""])
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
        output_name = canonical_selection_name(data_selection)
        df = branch_tables[data_selection].copy()
        figures_dir, tables_dir, docs_dir = ensure_output_dirs(data_selection, AGGREGATION_MODE)
        df.to_csv(tables_dir / f"session_metrics__{AGGREGATION_MODE}__{output_name}.csv", index=False)
        grooming_summary = plot_grooming(df, figures_dir, output_name, selection_label)
        supporting_summary = plot_supporting(df, figures_dir, output_name, selection_label)
        grooming_summary.to_csv(tables_dir / f"grooming_stats__{AGGREGATION_MODE}__{output_name}.csv", index=False)
        supporting_summary.to_csv(tables_dir / f"supporting_behavior_stats__{AGGREGATION_MODE}__{output_name}.csv", index=False)
        write_markdown(output_name, selection_label, docs_dir, grooming_summary, supporting_summary)


if __name__ == "__main__":
    main()

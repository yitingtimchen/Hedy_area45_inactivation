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

CONTROL_SPECS = [
    ("forage_search_pct_selected", "% selected time", "Forage/Search"),
    ("travel_pct_selected", "% selected time", "Travel"),
    ("rest_stationary_pct_selected", "% selected time", "Rest/Stationary"),
    ("vigilant_scan_pct_selected", "% selected time", "Vigilant/Scan"),
    ("attention_outside_pct_selected", "% selected time", "Attention outside"),
    ("scratch_pct_selected", "% selected time", "Scratch"),
]

METRIC_LABELS = {
    "forage_search_pct_selected": "Forage/Search (% selected time)",
    "travel_pct_selected": "Travel (% selected time)",
    "rest_stationary_pct_selected": "Rest/Stationary (% selected time)",
    "vigilant_scan_pct_selected": "Vigilant/Scan (% selected time)",
    "attention_outside_pct_selected": "Attention to outside agents (% selected time)",
    "scratch_pct_selected": "Scratch (% selected time)",
}


def interpretation_lines(summary: pd.DataFrame) -> list[str]:
    negative_hits = summary.loc[
        (summary["mean_diff_DCZ_minus_vehicle"] < 0.0)
        & (summary["exact_permutation_p_two_sided"] < 0.05),
        "metric",
    ].tolist()
    if not negative_hits:
        return [
            "- None of these nonsocial control metrics shows a clear DCZ-linked suppression across the analyzed sessions.",
            "- The pattern is mixed rather than uniformly downward, which argues against a simple global hypo-arousal account for the social exchange effect.",
        ]

    labels = ", ".join(METRIC_LABELS[metric] for metric in negative_hits)
    return [
        f"- Clear DCZ-linked decreases were detected for: {labels}.",
        "- Any arousal-control interpretation should therefore be framed cautiously rather than ruled out.",
    ]


def plot_panel(df: pd.DataFrame, summary: pd.DataFrame, output_path: Path, selection_label: str) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(10.0, 6.1))
    p_map = {str(row.metric): float(row.exact_permutation_p_two_sided) for row in summary.itertuples(index=False)}
    for ax, (metric, ylabel, title) in zip(axes.ravel(), CONTROL_SPECS):
        paired_strip(ax, df, metric, ylabel, title, p_map.get(metric))
    fig.suptitle(f"Nonsocial arousal-control panel: {selection_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94), w_pad=0.9, h_pad=1.0)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def write_markdown(data_selection: str, selection_label: str, docs_dir: Path, summary: pd.DataFrame) -> None:
    lines = [
        "# Nonsocial Arousal-Control Panel",
        "",
        "This compact control analysis asks whether DCZ shows a coherent downward shift across straightforward nonsocial activity and vigilance-related labels.",
        "",
    ]
    add_data_selection_and_mode_header(lines, selection_label, AGGREGATION_LABEL)
    lines.extend(
        [
            "## Definitions",
            "",
            "- The panel uses simple nonsocial labels rather than composite exchange metrics.",
            "- Values are expressed as percent of selected time so the same panel can be reused for the full session, quiet-mask branch, and loud-only branch.",
            "- A broad arousal-suppression explanation would predict a fairly consistent downward shift across these control measures.",
            "",
            "## Condition comparisons",
            "",
        ]
    )
    for metric in summary["metric"]:
        row = summary.loc[summary["metric"] == metric].iloc[0]
        lines.append(format_summary_line(row, METRIC_LABELS[metric]))
    lines.extend(["", "## Interpretation", ""])
    lines.extend(interpretation_lines(summary))
    lines.append("")
    (docs_dir / f"arousal_controls__{AGGREGATION_MODE}__{data_selection}.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    branch_tables = load_all_branch_tables()
    metrics = [metric for metric, _, _ in CONTROL_SPECS]
    for data_selection, selection_label in DATA_SELECTIONS:
        output_name = canonical_selection_name(data_selection)
        df = branch_tables[data_selection].copy()
        figures_dir, tables_dir, docs_dir = ensure_output_dirs(data_selection, AGGREGATION_MODE)
        session_cols = ["session_id", "original_name", "condition", "date", "session_index", *metrics]
        session_df = df[session_cols].copy()
        session_df.to_csv(tables_dir / f"arousal_control_metrics__{AGGREGATION_MODE}__{output_name}.csv", index=False)
        summary = summarize_by_condition(df, metrics)
        summary.to_csv(tables_dir / f"arousal_control_stats__{AGGREGATION_MODE}__{output_name}.csv", index=False)
        plot_panel(
            df,
            summary,
            figures_dir / f"arousal_controls__{AGGREGATION_MODE}__{output_name}.png",
            selection_label,
        )
        write_markdown(output_name, selection_label, docs_dir, summary)


if __name__ == "__main__":
    main()

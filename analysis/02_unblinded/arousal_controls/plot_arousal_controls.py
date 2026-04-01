from __future__ import annotations

import math
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

FAMILY_SPECS = [
    ("feeding_pct_selected", "Percent of selected time", "Feeding family"),
    ("locomotion_pct_selected", "Percent of selected time", "Locomotion family"),
    ("attention_pct_selected", "Percent of selected time", "Attention family"),
    ("maintenance_pct_selected", "Percent of selected time", "Maintenance family"),
]

COMPONENT_SPECS = [
    ("drink_pct_selected", "Percent of selected time", "Drink"),
    ("eat_pct_selected", "Percent of selected time", "Eat"),
    ("forage_search_pct_selected", "Percent of selected time", "Forage/Search"),
    ("travel_pct_selected", "Percent of selected time", "Travel"),
    ("attention_to_outside_agents_pct_selected", "Percent of selected time", "Attention to outside agents"),
    ("vigilant_scan_pct_selected", "Percent of selected time", "Vigilant/Scan"),
    ("rest_stationary_pct_selected", "Percent of selected time", "Rest/Stationary"),
    ("scratch_pct_selected", "Percent of selected time", "Scratch"),
    ("self_groom_pct_selected", "Percent of selected time", "Self-groom"),
    ("stretch_pct_selected", "Percent of selected time", "Stretch"),
    ("urinate_pct_selected", "Percent of selected time", "Urinate"),
]

METRIC_LABELS = {
    "feeding_pct_selected": "Feeding family (% selected time)",
    "locomotion_pct_selected": "Locomotion family (% selected time)",
    "attention_pct_selected": "Attention family (% selected time)",
    "maintenance_pct_selected": "Maintenance family (% selected time)",
    "drink_pct_selected": "Drink (% selected time)",
    "eat_pct_selected": "Eat (% selected time)",
    "forage_search_pct_selected": "Forage/Search (% selected time)",
    "travel_pct_selected": "Travel (% selected time)",
    "attention_to_outside_agents_pct_selected": "Attention to outside agents (% selected time)",
    "vigilant_scan_pct_selected": "Vigilant/Scan (% selected time)",
    "rest_stationary_pct_selected": "Rest/Stationary (% selected time)",
    "scratch_pct_selected": "Scratch (% selected time)",
    "self_groom_pct_selected": "Self-groom (% selected time)",
    "stretch_pct_selected": "Stretch (% selected time)",
    "urinate_pct_selected": "Urinate (% selected time)",
}


def interpretation_lines(family_summary: pd.DataFrame) -> list[str]:
    negative_hits = family_summary.loc[
        (family_summary["mean_diff_DCZ_minus_vehicle"] < 0.0)
        & (family_summary["exact_permutation_p_two_sided"] < 0.05),
        "metric",
    ].tolist()
    if not negative_hits:
        return [
            "- None of the requested nonsocial families shows a clean across-the-board DCZ-linked drop.",
            "- That keeps the broader control panel supportive rather than an alternative primary account of the grooming result.",
        ]

    labels = ", ".join(METRIC_LABELS[metric] for metric in negative_hits)
    return [
        f"- Clear DCZ-linked decreases were detected for: {labels}.",
        "- Those families should be framed as supportive caveats rather than ignored, while grooming remains the main result story.",
    ]


def plot_panel(df: pd.DataFrame, summary: pd.DataFrame, specs: list[tuple[str, str, str]], output_path: Path, selection_label: str, title: str) -> None:
    n_panels = len(specs)
    n_cols = min(4, n_panels)
    n_rows = int(math.ceil(n_panels / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(4.2 * n_cols, 3.0 * n_rows))
    axes_flat = axes.ravel() if hasattr(axes, "ravel") else [axes]
    p_map = {str(row.metric): float(row.exact_permutation_p_two_sided) for row in summary.itertuples(index=False)}
    for ax, (metric, ylabel, panel_title) in zip(axes_flat, specs):
        paired_strip(ax, df, metric, ylabel, panel_title, p_map.get(metric))
    for ax in axes_flat[len(specs):]:
        ax.axis("off")
    fig.suptitle(f"{title}: {selection_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95), w_pad=1.0, h_pad=1.0)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def write_markdown(data_selection: str, selection_label: str, docs_dir: Path, family_summary: pd.DataFrame, component_summary: pd.DataFrame) -> None:
    lines = [
        "# Nonsocial Arousal-Control Panel",
        "",
        "This supportive control analysis asks whether broader nonsocial behavior families shift with DCZ strongly enough to rival a grooming-specific interpretation.",
        "",
    ]
    add_data_selection_and_mode_header(lines, selection_label, AGGREGATION_LABEL)
    lines.extend(
        [
            "## Definitions",
            "",
            "- The family panel summarizes feeding, locomotion, attention, and maintenance as percent of selected time.",
            "- Component summaries unpack those families into resolved behavior labels where that helps interpretation.",
            "- Grooming remains the primary result; this section is a broader supportive control panel rather than a competing endpoint.",
            "",
            "## Family-level condition comparisons",
            "",
        ]
    )
    for metric in family_summary["metric"]:
        row = family_summary.loc[family_summary["metric"] == metric].iloc[0]
        lines.append(format_summary_line(row, METRIC_LABELS[metric]))
    lines.extend(["", "## Component-level condition comparisons", ""])
    for metric in component_summary["metric"]:
        row = component_summary.loc[component_summary["metric"] == metric].iloc[0]
        lines.append(format_summary_line(row, METRIC_LABELS[metric]))
    lines.extend(["", "## Interpretation", ""])
    lines.extend(interpretation_lines(family_summary))
    lines.append("")
    (docs_dir / f"arousal_controls__{AGGREGATION_MODE}__{data_selection}.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    branch_tables = load_all_branch_tables()
    family_metrics = [metric for metric, _, _ in FAMILY_SPECS]
    component_metrics = [metric for metric, _, _ in COMPONENT_SPECS]
    for data_selection, selection_label in DATA_SELECTIONS:
        output_name = canonical_selection_name(data_selection)
        df = branch_tables[data_selection].copy()
        figures_dir, tables_dir, docs_dir = ensure_output_dirs(data_selection, AGGREGATION_MODE)

        session_cols = [
            "session_id",
            "original_name",
            "condition",
            "date",
            "session_index",
            *family_metrics,
            *component_metrics,
        ]
        session_df = df[session_cols].copy()
        session_df.to_csv(tables_dir / f"arousal_control_metrics__{AGGREGATION_MODE}__{output_name}.csv", index=False)

        family_summary = summarize_by_condition(df, family_metrics)
        component_summary = summarize_by_condition(df, component_metrics)
        family_summary.to_csv(tables_dir / f"arousal_control_family_stats__{AGGREGATION_MODE}__{output_name}.csv", index=False)
        family_summary.to_csv(tables_dir / f"arousal_control_stats__{AGGREGATION_MODE}__{output_name}.csv", index=False)
        component_summary.to_csv(tables_dir / f"arousal_control_component_stats__{AGGREGATION_MODE}__{output_name}.csv", index=False)

        plot_panel(
            df,
            family_summary,
            FAMILY_SPECS,
            figures_dir / f"arousal_controls__{AGGREGATION_MODE}__{output_name}.png",
            selection_label,
            "Nonsocial family control panel",
        )
        plot_panel(
            df,
            component_summary,
            COMPONENT_SPECS,
            figures_dir / f"arousal_control_components__{AGGREGATION_MODE}__{output_name}.png",
            selection_label,
            "Nonsocial component panel",
        )
        write_markdown(output_name, selection_label, docs_dir, family_summary, component_summary)


if __name__ == "__main__":
    main()

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PARENT = Path(__file__).resolve().parents[1]
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from _plot_helpers import DCZ_COLOR, VEHICLE_COLOR, exact_slope_permutation_p, fit_line, style_axis  # noqa: E402
from data_selection import load_all_branch_tables  # noqa: E402
from reorg_common import DATA_SELECTIONS, add_data_selection_and_mode_header, canonical_selection_name, ensure_output_dirs, exact_label_permutation_p  # noqa: E402


AGGREGATION_MODE = "across_session_temporal_dependence"
AGGREGATION_LABEL = "across_session_temporal_dependence"

PRETTY = {
    "groom_give_pct_selected": "Groom give (% selected time)",
    "groom_receive_pct_selected": "Groom receive (% selected time)",
    "mount_give_pct_selected": "Mount give (% selected time)",
    "groom_give_duration_s_selected": "Groom give duration (s)",
    "groom_receive_duration_s_selected": "Groom receive duration (s)",
    "mount_give_duration_s_selected": "Mount give duration (s)",
    "groom_give_bouts_selected": "Groom give bouts",
    "groom_receive_bouts_selected": "Groom receive bouts",
    "groom_bout_net_selected": "Net grooming bouts",
    "groom_bout_reciprocity_selected": "Grooming bout reciprocity (0 to 1)",
}


def analyze_metric(df: pd.DataFrame, metric: str) -> dict[str, object]:
    sub = df[["condition", "session_index", metric]].copy()
    sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
    sub = sub.dropna(subset=[metric]).reset_index(drop=True)
    y = sub[metric].to_numpy(dtype=float)
    raw_effect, raw_p = exact_label_permutation_p(y, sub["condition"].to_numpy())
    rows = {
        "metric": metric,
        "pretty_metric": PRETTY[metric],
        "raw_condition_effect": raw_effect,
        "raw_condition_permutation_p_two_sided": raw_p,
    }
    for condition in ["vehicle", "DCZ"]:
        cond_sub = sub.loc[sub["condition"] == condition]
        x = cond_sub["session_index"].to_numpy(dtype=float)
        values = cond_sub[metric].to_numpy(dtype=float)
        intercept, slope = fit_line(x, values)
        rows[f"{condition}_intercept_at_mean_session"] = intercept
        rows[f"{condition}_slope_per_session"] = slope
        rows[f"{condition}_slope_permutation_p_two_sided"] = exact_slope_permutation_p(x, values)
    return rows


def plot_metric(ax: plt.Axes, df: pd.DataFrame, metric: str, title: str) -> None:
    sub = df[["condition", "session_index", metric]].copy()
    sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
    sub = sub.dropna(subset=[metric]).reset_index(drop=True)
    for condition, color in [("vehicle", VEHICLE_COLOR), ("DCZ", DCZ_COLOR)]:
        cond_sub = sub.loc[sub["condition"] == condition]
        x = cond_sub["session_index"].to_numpy(dtype=float)
        y = cond_sub[metric].to_numpy(dtype=float)
        ax.scatter(x, y, color=color, s=38, zorder=3)
        x_line = np.linspace(x.min(), x.max(), 200)
        intercept, slope = fit_line(x, y)
        ax.plot(x_line, intercept + slope * (x_line - x.mean()), color=color, linewidth=2.0)
        p_value = exact_slope_permutation_p(x, y)
        y_text = 0.95 if condition == "vehicle" else 0.84
        ax.text(
            0.02,
            y_text,
            f"{condition.capitalize()} slope p = {p_value:.4f}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9.0,
            color=color,
            fontweight="bold" if p_value < 0.05 else "normal",
        )
    ax.set_title(title, fontsize=12, loc="left")
    ax.set_xlabel("Session order", fontsize=10.5)
    style_axis(ax)


def write_markdown(docs_dir: Path, data_selection: str, selection_label: str, duration_summary: pd.DataFrame, bout_summary: pd.DataFrame | None) -> None:
    lines = [
        "# Across-Session Temporal Dependence",
        "",
    ]
    add_data_selection_and_mode_header(lines, selection_label, AGGREGATION_LABEL)
    lines.extend(["## Duration metrics", ""])
    for row in duration_summary.itertuples(index=False):
        lines.extend(
            [
                f"### {row.pretty_metric}",
                f"- Raw condition effect: `{row.raw_condition_effect:.3f}`, exact permutation `p = {row.raw_condition_permutation_p_two_sided:.4f}`.",
                f"- Vehicle slope: `{row.vehicle_slope_per_session:.3f}` per session, slope permutation `p = {row.vehicle_slope_permutation_p_two_sided:.4f}`.",
                f"- DCZ slope: `{row.DCZ_slope_per_session:.3f}` per session, slope permutation `p = {row.DCZ_slope_permutation_p_two_sided:.4f}`.",
                "",
            ]
        )
    if bout_summary is not None and not bout_summary.empty:
        lines.extend(["## Bout metrics", ""])
        for row in bout_summary.itertuples(index=False):
            lines.extend(
                [
                    f"### {row.pretty_metric}",
                    f"- Raw condition effect: `{row.raw_condition_effect:.3f}`, exact permutation `p = {row.raw_condition_permutation_p_two_sided:.4f}`.",
                    f"- Vehicle slope: `{row.vehicle_slope_per_session:.3f}` per session, slope permutation `p = {row.vehicle_slope_permutation_p_two_sided:.4f}`.",
                    f"- DCZ slope: `{row.DCZ_slope_per_session:.3f}` per session, slope permutation `p = {row.DCZ_slope_permutation_p_two_sided:.4f}`.",
                    "",
                ]
            )
    (docs_dir / f"temporal_dependence__{AGGREGATION_MODE}__{data_selection}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    branch_tables = load_all_branch_tables()
    duration_metrics = [
        "groom_give_pct_selected",
        "groom_receive_pct_selected",
        "mount_give_pct_selected",
        "groom_give_duration_s_selected",
        "groom_receive_duration_s_selected",
        "mount_give_duration_s_selected",
    ]
    bout_metrics = [
        "groom_give_bouts_selected",
        "groom_receive_bouts_selected",
        "groom_bout_net_selected",
        "groom_bout_reciprocity_selected",
    ]
    for data_selection, selection_label in DATA_SELECTIONS:
        output_name = canonical_selection_name(data_selection)
        df = branch_tables[data_selection].copy()
        figures_dir, tables_dir, docs_dir = ensure_output_dirs(data_selection, AGGREGATION_MODE)
        df.to_csv(tables_dir / f"session_metrics__{AGGREGATION_MODE}__{output_name}.csv", index=False)

        duration_summary = pd.DataFrame([analyze_metric(df, metric) for metric in duration_metrics])
        duration_summary.to_csv(tables_dir / f"duration_temporal_stats__{AGGREGATION_MODE}__{output_name}.csv", index=False)

        fig, axes = plt.subplots(2, 3, figsize=(11.5, 6.4))
        titles = [
            "Groom give (% selected time)",
            "Groom receive (% selected time)",
            "Mount give (% selected time)",
            "Groom give duration (s)",
            "Groom receive duration (s)",
            "Mount give duration (s)",
        ]
        for ax, metric, title in zip(axes.ravel(), duration_metrics, titles):
            plot_metric(ax, df, metric, title)
        fig.suptitle(f"Duration temporal dependence: {selection_label}", fontsize=13, x=0.05, ha="left")
        fig.tight_layout(rect=(0, 0, 1, 0.94), w_pad=0.9, h_pad=1.0)
        fig.savefig(figures_dir / f"duration_temporal_dependence__{AGGREGATION_MODE}__{output_name}.png", dpi=220, bbox_inches="tight")
        plt.close(fig)

        bout_summary = None
        if df["groom_give_bouts_selected"].notna().any():
            bout_summary = pd.DataFrame([analyze_metric(df, metric) for metric in bout_metrics])
            bout_summary.to_csv(tables_dir / f"bout_temporal_stats__{AGGREGATION_MODE}__{output_name}.csv", index=False)
            fig, axes = plt.subplots(2, 2, figsize=(8.6, 6.4))
            bout_titles = [
                "Groom give bouts",
                "Groom receive bouts",
                "Net grooming bouts",
                "Grooming bout reciprocity",
            ]
            for ax, metric, title in zip(axes.ravel(), bout_metrics, bout_titles):
                plot_metric(ax, df, metric, title)
            fig.suptitle(f"Bout temporal dependence: {selection_label}", fontsize=13, x=0.05, ha="left")
            fig.tight_layout(rect=(0, 0, 1, 0.94), w_pad=0.9, h_pad=1.0)
            fig.savefig(figures_dir / f"bout_temporal_dependence__{AGGREGATION_MODE}__{output_name}.png", dpi=220, bbox_inches="tight")
            plt.close(fig)

        write_markdown(docs_dir, output_name, selection_label, duration_summary, bout_summary)


if __name__ == "__main__":
    main()

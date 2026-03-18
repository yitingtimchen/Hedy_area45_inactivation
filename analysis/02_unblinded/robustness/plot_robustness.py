from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PARENT = Path(__file__).resolve().parents[1]
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from _plot_helpers import (  # noqa: E402
    DCZ_COLOR,
    TITLE_SIZE,
    VEHICLE_COLOR,
    exact_slope_permutation_p,
    fit_line,
    p_style,
    paired_strip,
    style_axis,
)


ROOT = Path(__file__).resolve().parents[3]
UNBLINDED_ROOT = ROOT / "results" / "unblinded"

COHORTS = [
    ("full", "Full session set"),
    ("quiet_mask", "Quiet-mask sensitivity session set"),
    ("exclude_vet_entry", "Excluding vet-entry session"),
]

TEMPORAL_METRICS = [
    "groom_duration_net_receive_minus_give_pct_session",
    "groom_duration_reciprocity_0to1",
    "groom_bout_net_receive_minus_give",
    "groom_bout_reciprocity_0to1",
]

TEMPORAL_LABELS = {
    "groom_duration_net_receive_minus_give_pct_session": "Net grooming (% session)\n(receive - give)",
    "groom_duration_reciprocity_0to1": "Reciprocity (0 to 1)",
    "groom_bout_net_receive_minus_give": "Net grooming bouts\n(receive - give)",
    "groom_bout_reciprocity_0to1": "Bout reciprocity (0 to 1)",
}

TEMPORAL_TITLES = {
    "groom_duration_net_receive_minus_give_pct_session": "Net grooming duration over session order",
    "groom_duration_reciprocity_0to1": "Grooming reciprocity (duration) over session order",
    "groom_bout_net_receive_minus_give": "Net grooming bouts over session order",
    "groom_bout_reciprocity_0to1": "Grooming reciprocity (bouts) over session order",
}


def plot_temporal_metric(ax: plt.Axes, df: pd.DataFrame, metric: str, summary_row: pd.Series) -> None:
    ordered = df.sort_values("session_index").reset_index(drop=True)
    for condition, color, slope_col, p_col in [
        ("vehicle", VEHICLE_COLOR, "vehicle_slope_per_session", "vehicle_slope_permutation_p_two_sided"),
        ("DCZ", DCZ_COLOR, "dcz_slope_per_session", "dcz_slope_permutation_p_two_sided"),
    ]:
        sub = ordered[ordered["condition"] == condition]
        ax.scatter(sub["session_index"], sub[metric], color=color, s=46, zorder=3, label=condition.capitalize())
        ax.plot(sub["session_index"], sub[metric], color=color, linewidth=1.5, alpha=0.9, zorder=2)
        intercept, slope = fit_line(sub["session_index"].to_numpy(dtype=float), sub[metric].to_numpy(dtype=float))
        xgrid = np.linspace(sub["session_index"].min(), sub["session_index"].max(), 200)
        ygrid = intercept + slope * (xgrid - sub["session_index"].mean())
        ax.plot(xgrid, ygrid, color=color, linewidth=2.1, linestyle="--", zorder=4)
        label = p_style(float(summary_row[p_col]))
        xpos = 0.03 if condition == "vehicle" else 0.53
        ax.text(
            xpos,
            0.97,
            f"{condition.capitalize()} slope = {summary_row[slope_col]:.3f}\n{label['text']}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9.4,
            color=label["color"],
            fontweight=label["fontweight"],
        )
    if metric == "groom_duration_net_receive_minus_give_pct_session":
        ax.axhline(0, color="#7F7F7F", linewidth=1.0, linestyle=":")
        ax.set_ylim(-50, 20)
    elif metric == "groom_bout_net_receive_minus_give":
        ax.axhline(0, color="#7F7F7F", linewidth=1.0, linestyle=":")
    else:
        ax.set_ylim(0, 1.05)
    ax.set_title(TEMPORAL_TITLES[metric], fontsize=TITLE_SIZE, loc="left")
    ax.set_xlabel("Session order", fontsize=10.5)
    ax.set_ylabel(TEMPORAL_LABELS[metric], fontsize=10.5)
    style_axis(ax)


def plot_temporal_panel(cohort_name: str, cohort_label: str) -> None:
    tables_dir = UNBLINDED_ROOT / cohort_name / "tables"
    figures_dir = UNBLINDED_ROOT / cohort_name / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    decision = pd.read_csv(tables_dir / "unblinded_decision_table.csv", dtype={"session_id": str})
    summary = pd.read_csv(tables_dir / "temporal_dependence_summary.csv").set_index("metric")

    fig, axes = plt.subplots(2, 2, figsize=(9.6, 7.2))
    axes_arr = axes.ravel()
    for ax, metric in zip(axes_arr, TEMPORAL_METRICS):
        plot_temporal_metric(ax, decision, metric, summary.loc[metric])

    axes_arr[0].legend(frameon=False, loc="lower left", fontsize=9.6)
    fig.suptitle(f"Temporal dependence check: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94), w_pad=1.0, h_pad=1.0)
    fig.savefig(figures_dir / "temporal_dependence.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_temporal_quiet_metric(ax: plt.Axes, decision: pd.DataFrame, metric: str, ylabel: str, title: str) -> None:
    ordered = decision.sort_values("session_index").reset_index(drop=True)
    for condition, color, xpos in [("vehicle", VEHICLE_COLOR, 0.03), ("DCZ", DCZ_COLOR, 0.53)]:
        sub = ordered[ordered["condition"] == condition]
        x = sub["session_index"].to_numpy(dtype=float)
        y = sub[metric].to_numpy(dtype=float)
        intercept, slope = fit_line(x, y)
        p_value = exact_slope_permutation_p(x, y)
        xgrid = np.linspace(x.min(), x.max(), 200)
        ygrid = intercept + slope * (xgrid - x.mean())
        ax.scatter(x, y, color=color, s=40, zorder=3)
        ax.plot(x, y, color=color, linewidth=1.3, alpha=0.9, zorder=2)
        ax.plot(xgrid, ygrid, color=color, linewidth=1.8, linestyle="--", zorder=4)
        label = p_style(p_value)
        ax.text(
            xpos,
            0.97,
            f"{condition.capitalize()} slope = {slope:.3f}\n{label['text']}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=8.6,
            color=label["color"],
            fontweight=label["fontweight"],
        )
    ax.set_title(title, fontsize=11, loc="left")
    ax.set_xlabel("Session order", fontsize=10.0)
    ax.set_ylabel(ylabel, fontsize=10.0)
    style_axis(ax, tick_size=9.0)


def plot_quiet_mask_supplementary(decision: pd.DataFrame, figures_dir: Path, tables_dir: Path) -> None:
    primary = pd.read_csv(tables_dir / "condition_comparison_primary.csv")
    secondary = pd.read_csv(tables_dir / "condition_comparison_secondary.csv")
    exploratory = pd.read_csv(tables_dir / "condition_comparison_exploratory.csv")
    exploratory_df = pd.read_csv(tables_dir / "unblinded_exploratory_nonsocial_table.csv", dtype={"session_id": str})

    fig, axes = plt.subplots(3, 3, figsize=(11.0, 8.4))
    axes = axes.ravel()
    strip_specs = [
        ("groom_duration_net_receive_minus_give_pct_session", "Primary net grooming\n(% session)", primary, axes[0], True, None),
        ("groom_duration_reciprocity_0to1", "Primary reciprocity\n(0 to 1)", primary, axes[1], False, (0.0, 1.05)),
        ("groom_duration_net_receive_minus_give_pct_session", "Quiet-mask net grooming\n(% session)", primary, axes[2], True, None),
        ("groom_duration_reciprocity_0to1", "Quiet-mask reciprocity\n(0 to 1)", primary, axes[3], False, (0.0, 1.05)),
        ("groom_total_pct_session", "Total grooming\n(% session)", secondary, axes[4], False, None),
        ("social_engaged_pct_session", "Social engagement\n(% session)", secondary, axes[5], False, None),
        ("rest_stationary_resolved_pct_session", "Rest / stationary\n(% session)", exploratory, axes[6], False, None),
    ]
    for metric, ylabel, stats_df, ax, zero_line, y_limits in strip_specs:
        p_value = float(stats_df.loc[stats_df["metric"] == metric, "exact_permutation_p_two_sided"].iloc[0])
        source_df = exploratory_df if metric == "rest_stationary_resolved_pct_session" else decision
        paired_strip(ax, source_df, metric, ylabel, ylabel.split("\n")[0], p_value, y_limits=y_limits)
        if zero_line:
            ax.axhline(0, color="#7F7F7F", linewidth=1.0, linestyle="--")

    plot_temporal_quiet_metric(
        axes[7],
        decision,
        "groom_duration_net_receive_minus_give_pct_session",
        "Quiet-mask net grooming\n(% session)",
        "Quiet-mask net grooming duration slope",
    )
    plot_temporal_quiet_metric(
        axes[8],
        decision,
        "groom_duration_reciprocity_0to1",
        "Quiet-mask reciprocity\n(0 to 1)",
        "Quiet-mask grooming reciprocity (duration) slope",
    )
    axes[8].set_ylim(0, 1.05)

    fig.suptitle("Supplementary quiet-mask sensitivity summary", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95), w_pad=0.8, h_pad=0.9)
    fig.savefig(figures_dir / "quiet_mask_supplementary.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    for cohort_name, cohort_label in COHORTS:
        plot_temporal_panel(cohort_name, cohort_label)
        if cohort_name == "quiet_mask":
            tables_dir = UNBLINDED_ROOT / cohort_name / "tables"
            decision = pd.read_csv(tables_dir / "unblinded_decision_table.csv", dtype={"session_id": str})
            plot_quiet_mask_supplementary(decision, UNBLINDED_ROOT / cohort_name / "figures", tables_dir)


if __name__ == "__main__":
    main()

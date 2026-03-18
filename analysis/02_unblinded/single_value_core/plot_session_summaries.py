from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PARENT = Path(__file__).resolve().parents[1]
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from _plot_helpers import paired_strip  # noqa: E402


ROOT = Path(__file__).resolve().parents[3]
UNBLINDED_ROOT = ROOT / "results" / "unblinded"

COHORTS = [
    ("full", "Full session set"),
    ("quiet_mask", "Quiet-mask sensitivity session set"),
    ("exclude_vet_entry", "Excluding vet-entry session"),
]


def plot_raw_session_summary(decision: pd.DataFrame, component_stats: pd.DataFrame, figures_dir: Path, cohort_label: str) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(9.0, 3.8))
    specs = [
        ("groom_give_pct_session", "Groom given\n(% session)", "Groom duration given"),
        ("groom_receive_pct_session", "Groom received\n(% session)", "Groom duration received"),
        ("groom_total_pct_session", "Total grooming\n(% session)", "Total grooming duration"),
    ]
    for ax, (metric, ylabel, title) in zip(axes, specs):
        p_value = float(component_stats.loc[component_stats["metric"] == metric, "exact_permutation_p_two_sided"].iloc[0])
        paired_strip(ax, decision, metric, ylabel, title, p_value, y_limits=(0.0, 100.0))

    fig.suptitle(f"Raw session summaries: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92), w_pad=0.8)
    fig.savefig(figures_dir / "groom_duration_session_summary.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_groom_bout_session_summary(decision: pd.DataFrame, bout_component_stats: pd.DataFrame, figures_dir: Path, cohort_label: str) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(9.0, 3.8))
    specs = [
        ("groom_give_resolved_bouts", "Groom give bouts\n(per session)", "Groom give bouts"),
        ("groom_receive_resolved_bouts", "Groom receive bouts\n(per session)", "Groom receive bouts"),
        ("groom_total_resolved_bouts", "Total grooming bouts\n(per session)", "Total grooming bouts"),
    ]
    for ax, (metric, ylabel, title) in zip(axes, specs):
        p_value = float(bout_component_stats.loc[bout_component_stats["metric"] == metric, "exact_permutation_p_two_sided"].iloc[0])
        paired_strip(ax, decision, metric, ylabel, title, p_value)

    fig.suptitle(f"Groom bout session summaries: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92), w_pad=0.8)
    fig.savefig(figures_dir / "groom_bout_session_summary.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_composite_session_summary(decision: pd.DataFrame, primary_stats: pd.DataFrame, figures_dir: Path, cohort_label: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.8))
    specs = [
        (
            "groom_duration_net_receive_minus_give_pct_session",
            "Net grooming (% session)\n(receive - give)",
            "Net grooming duration",
        ),
        (
            "groom_duration_reciprocity_0to1",
            "Reciprocity (0 to 1)",
            "Grooming reciprocity (duration)",
        ),
    ]
    for ax, (metric, ylabel, title) in zip(axes, specs):
        p_value = float(primary_stats.loc[primary_stats["metric"] == metric, "exact_permutation_p_two_sided"].iloc[0])
        y_limits = None if metric.endswith("pct_session") else (0.0, 1.05)
        paired_strip(ax, decision, metric, ylabel, title, p_value, y_limits=y_limits)
        if metric == "groom_duration_net_receive_minus_give_pct_session":
            ax.axhline(0, color="#7F7F7F", linewidth=1.0, linestyle="--")

    fig.suptitle(f"Composite session summaries: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92), w_pad=0.9)
    fig.savefig(figures_dir / "groom_composite_session_summary.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_groom_bout_composite_summary(decision: pd.DataFrame, secondary_stats: pd.DataFrame, figures_dir: Path, cohort_label: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.8))
    specs = [
        (
            "groom_bout_net_receive_minus_give",
            "Net grooming bouts\n(receive - give)",
            "Net grooming bouts",
        ),
        (
            "groom_bout_reciprocity_0to1",
            "Bout reciprocity (0 to 1)",
            "Grooming bout reciprocity",
        ),
    ]
    for ax, (metric, ylabel, title) in zip(axes, specs):
        p_value = float(secondary_stats.loc[secondary_stats["metric"] == metric, "exact_permutation_p_two_sided"].iloc[0])
        y_limits = None if metric.endswith("minus_give") else (0.0, 1.05)
        paired_strip(ax, decision, metric, ylabel, title, p_value, y_limits=y_limits)
        if metric == "groom_bout_net_receive_minus_give":
            ax.axhline(0, color="#7F7F7F", linewidth=1.0, linestyle="--")

    fig.suptitle(f"Groom bout composite summaries: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92), w_pad=0.9)
    fig.savefig(figures_dir / "groom_bout_composite_session_summary.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_exploratory_panel(exploratory: pd.DataFrame, exploratory_stats: pd.DataFrame, figures_dir: Path, cohort_label: str) -> None:
    chosen = [
        "rest_stationary_resolved_pct_session",
        "travel_resolved_pct_session",
        "attention_to_outside_agents_resolved_pct_session",
        "scratch_resolved_pct_session",
        "hiccups_resolved_pct_session",
        "inferred_leave_per_hour",
    ]
    labels = {
        "rest_stationary_resolved_pct_session": "Rest / stationary\n(% session)",
        "travel_resolved_pct_session": "Travel\n(% session)",
        "attention_to_outside_agents_resolved_pct_session": "Attention outside\n(% session)",
        "scratch_resolved_pct_session": "Scratch\n(% session)",
        "hiccups_resolved_pct_session": "Hiccups\n(% session)",
        "inferred_leave_per_hour": "Inferred leaves\n(per hour)",
    }

    fig, axes = plt.subplots(2, 3, figsize=(9.2, 5.6))
    axes = axes.ravel()
    for ax, metric in zip(axes, chosen):
        sub = exploratory[["condition", metric]].copy()
        p_row = exploratory_stats.loc[exploratory_stats["metric"] == metric]
        p_value = float(p_row["exact_permutation_p_two_sided"].iloc[0]) if not p_row.empty else None
        paired_strip(ax, sub, metric, labels[metric], labels[metric].split("\n")[0], p_value)

    fig.suptitle(f"Exploratory contextual measures: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94), w_pad=0.8, h_pad=0.8)
    fig.savefig(figures_dir / "contextual_behavior_session_summary.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    for cohort_name, cohort_label in COHORTS:
        tables_dir = UNBLINDED_ROOT / cohort_name / "tables"
        figures_dir = UNBLINDED_ROOT / cohort_name / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)

        decision = pd.read_csv(tables_dir / "unblinded_decision_table.csv", dtype={"session_id": str})
        exploratory = pd.read_csv(tables_dir / "unblinded_exploratory_nonsocial_table.csv", dtype={"session_id": str})
        component_stats = pd.read_csv(tables_dir / "condition_comparison_groom_components.csv")
        bout_component_stats = pd.read_csv(tables_dir / "condition_comparison_groom_bout_components.csv")
        primary_stats = pd.read_csv(tables_dir / "condition_comparison_primary.csv")
        secondary_stats = pd.read_csv(tables_dir / "condition_comparison_secondary.csv")
        exploratory_stats = pd.read_csv(tables_dir / "condition_comparison_exploratory.csv")

        plot_raw_session_summary(decision, component_stats, figures_dir, cohort_label)
        plot_groom_bout_session_summary(decision, bout_component_stats, figures_dir, cohort_label)
        plot_composite_session_summary(decision, primary_stats, figures_dir, cohort_label)
        plot_groom_bout_composite_summary(decision, secondary_stats, figures_dir, cohort_label)
        plot_exploratory_panel(exploratory, exploratory_stats, figures_dir, cohort_label)


if __name__ == "__main__":
    main()

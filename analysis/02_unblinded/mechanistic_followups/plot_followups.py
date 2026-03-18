from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PARENT = Path(__file__).resolve().parents[1]
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from _plot_helpers import DCZ_COLOR, VEHICLE_COLOR, paired_strip, style_axis  # noqa: E402


ROOT = Path(__file__).resolve().parents[3]
UNBLINDED_ROOT = ROOT / "results" / "unblinded"

COHORTS = [
    ("full", "Full session set"),
    ("quiet_mask", "Quiet-mask sensitivity session set"),
    ("exclude_vet_entry", "Excluding vet-entry session"),
]

CELL_SPECS = [
    ("is_give_reciprocated", "give_reciprocated_share_of_all_episodes", "Hedy grooms first,\nHooke reciprocates"),
    ("is_give_unreciprocated", "give_unreciprocated_share_of_all_episodes", "Hedy grooms first,\nHooke does not reciprocate"),
    ("is_receive_reciprocated", "receive_reciprocated_share_of_all_episodes", "Hooke grooms first,\nHedy reciprocates"),
    ("is_receive_unreciprocated", "receive_unreciprocated_share_of_all_episodes", "Hooke grooms first,\nHedy does not reciprocate"),
]

CELL_COLORS = ["#3E6FB2", "#9DB7D5", "#D97C4A", "#E8B79B"]


def plot_cumulative_episode_counts(ax: plt.Axes, episode_df: pd.DataFrame, indicator_col: str, title: str, ylabel: str) -> None:
    grid = np.linspace(0.0, 1.0, 21)
    x_pct = 100.0 * grid
    for condition, color in [("vehicle", VEHICLE_COLOR), ("DCZ", DCZ_COLOR)]:
        sub = episode_df.loc[episode_df["condition"] == condition].copy()
        if sub.empty:
            continue
        curves = []
        for _, sess in sub.groupby("session_id", sort=False):
            sess = sess.sort_values("episode_mid_frac_session").reset_index(drop=True)
            x = sess["episode_mid_frac_session"].to_numpy(dtype=float)
            y = sess[indicator_col].to_numpy(dtype=float)
            curves.append(np.array([y[x <= frac].sum() for frac in grid], dtype=float))
        arr = np.vstack(curves)
        mean_curve = arr.mean(axis=0)
        sem_curve = arr.std(axis=0, ddof=1) / np.sqrt(arr.shape[0]) if arr.shape[0] > 1 else np.zeros_like(mean_curve)
        ax.fill_between(x_pct, mean_curve - sem_curve, mean_curve + sem_curve, color=color, alpha=0.15, linewidth=0)
        ax.plot(x_pct, mean_curve, color=color, linewidth=2.0, label=condition.capitalize())

    ax.set_title(title, fontsize=11, loc="left")
    ax.set_xlabel("% of session elapsed")
    ax.set_ylabel(ylabel)
    style_axis(ax)


def plot_generic_followups(session_df: pd.DataFrame, summary: pd.DataFrame, figures_dir: Path, cohort_label: str) -> None:
    p_map = dict(zip(summary["metric"], summary["exact_permutation_p_two_sided"]))
    fig, axes = plt.subplots(2, 2, figsize=(8.0, 5.6))
    axes = axes.ravel()
    specs = [
        ("episode_turn_taking_prob", "Probability", "Episode-level turn taking probability", False),
        ("episode_turn_taking_latency_median_s", "Seconds", "Episode turn-taking latency duration", True),
        ("groom_to_nonsocial_prob", "Probability", "Groom-duration to nonsocial activity probability", False),
        ("nonsocial_to_groom_prob", "Probability", "Nonsocial activity to groom-duration probability", False),
    ]
    for ax, (metric, ylabel, title, log_scale) in zip(axes, specs):
        paired_strip(ax, session_df, metric, ylabel, title, float(p_map[metric]), log_scale=log_scale)
    fig.suptitle(f"Exploratory grooming follow-up metrics: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94), w_pad=0.8, h_pad=0.8)
    fig.savefig(figures_dir / "groom_transition_followup_panel.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_directional_followups(session_df: pd.DataFrame, summary: pd.DataFrame, figures_dir: Path, cohort_label: str) -> None:
    p_map = dict(zip(summary["metric"], summary["exact_permutation_p_two_sided"]))
    fig, axes = plt.subplots(2, 3, figsize=(9.6, 5.8))
    axes = axes.ravel()
    specs = [
        ("give_initiated_episode_count", "Episodes per session", "Hedy start episodes", False),
        ("receive_initiated_episode_count", "Episodes per session", "Hooke start episodes", False),
        ("give_to_receive_prob_same_episode", "Probability", "Hedy start -> Hooke reciprocates", False),
        ("receive_to_give_prob_same_episode", "Probability", "Hooke start -> Hedy reciprocates", False),
        ("episode_give_to_receive_latency_median_s", "Seconds", "Time until Hooke reciprocates duration", True),
        ("episode_receive_to_give_latency_median_s", "Seconds", "Time until Hedy reciprocates duration", True),
    ]
    for ax, (metric, ylabel, title, log_scale) in zip(axes, specs):
        paired_strip(ax, session_df, metric, ylabel, title, float(p_map[metric]), log_scale=log_scale)
    fig.suptitle(f"Directional grooming follow-up: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94), w_pad=0.8, h_pad=0.8)
    fig.savefig(figures_dir / "groom_directional_followup.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_episode_class_summary(session_df: pd.DataFrame, summary: pd.DataFrame, figures_dir: Path, cohort_label: str) -> None:
    p_map = dict(zip(summary["metric"], summary["exact_permutation_p_two_sided"]))
    means = []
    for condition in ["vehicle", "DCZ"]:
        row = {"condition": condition}
        for _, share_metric, _ in CELL_SPECS:
            values = pd.to_numeric(
                session_df.loc[session_df["condition"] == condition, share_metric],
                errors="coerce",
            ).dropna()
            row[share_metric] = float(values.mean()) if len(values) else 0.0
        means.append(row)
    means_df = pd.DataFrame(means)

    fig, stack_ax = plt.subplots(1, 1, figsize=(5.8, 5.2))
    bottoms = np.zeros(2, dtype=float)
    x = np.arange(2, dtype=float)
    for color, (_, share_metric, label) in zip(CELL_COLORS, CELL_SPECS):
        heights = means_df[share_metric].to_numpy(dtype=float)
        stack_ax.bar(x, heights, bottom=bottoms, color=color, width=0.62, edgecolor="white", linewidth=0.7, label=label.replace("\n", " "))
        bottoms += heights
    stack_ax.set_xticks(x, ["Vehicle", "DCZ"])
    stack_ax.set_ylim(0.0, 1.0)
    stack_ax.set_ylabel("Mean share of all grooming episodes")
    stack_ax.set_title("Mean episode composition", fontsize=12, loc="left")
    style_axis(stack_ax)
    stack_ax.legend(
        frameon=False,
        fontsize=8.8,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=1,
    )
    fig.suptitle(f"Episode-class mean composition: {cohort_label}", fontsize=13, x=0.07, ha="left")
    fig.tight_layout(rect=(0, 0.12, 1, 0.93))
    fig.savefig(figures_dir / "groom_episode_class_mean_composition.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 4, figsize=(11.8, 3.8))
    for ax, (_, share_metric, column_label) in zip(axes, CELL_SPECS):
        paired_strip(
            ax,
            session_df,
            share_metric,
            "Share of all grooming episodes",
            column_label,
            float(p_map[share_metric]),
            y_limits=(0.0, 1.0),
        )
    fig.suptitle(f"Episode-class session summaries: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.88), w_pad=0.9)
    fig.savefig(figures_dir / "groom_episode_class_session_summary.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_feedback_dynamics(session_df: pd.DataFrame, episode_df: pd.DataFrame, summary: pd.DataFrame, figures_dir: Path, cohort_label: str) -> None:
    fig, axes = plt.subplots(1, 4, figsize=(12.6, 3.7), sharey=True)
    for ax, (indicator_col, _, column_label) in zip(axes, CELL_SPECS):
        plot_cumulative_episode_counts(ax, episode_df, indicator_col, column_label, "Episodes")
        ax.set_ylim(0.0, 5.0)
    axes[0].legend(frameon=False, loc="upper left")
    fig.suptitle(f"Groom feedback dynamics: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.88), w_pad=1.0)
    fig.savefig(figures_dir / "groom_feedback_dynamics_panel.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    for cohort_name, cohort_label in COHORTS:
        tables_dir = UNBLINDED_ROOT / cohort_name / "tables"
        figures_dir = UNBLINDED_ROOT / cohort_name / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)

        session_df = pd.read_csv(tables_dir / "groom_followup_metrics_by_session.csv", dtype={"session_id": str})
        summary = pd.read_csv(tables_dir / "groom_followup_condition_comparison.csv")
        directional_session_df = pd.read_csv(tables_dir / "groom_directional_followup_metrics_by_session.csv", dtype={"session_id": str})
        directional_summary = pd.read_csv(tables_dir / "groom_directional_followup_condition_comparison.csv")
        feedback_session_df = pd.read_csv(tables_dir / "groom_feedback_dynamics_metrics_by_session.csv", dtype={"session_id": str})
        feedback_episode_df = pd.read_csv(tables_dir / "groom_feedback_episode_table.csv", dtype={"session_id": str})
        feedback_summary = pd.read_csv(tables_dir / "groom_feedback_dynamics_condition_comparison.csv")

        plot_generic_followups(session_df, summary, figures_dir, cohort_label)
        plot_episode_class_summary(feedback_session_df, feedback_summary, figures_dir, cohort_label)
        plot_directional_followups(directional_session_df, directional_summary, figures_dir, cohort_label)
        plot_feedback_dynamics(feedback_session_df, feedback_episode_df, feedback_summary, figures_dir, cohort_label)


if __name__ == "__main__":
    main()

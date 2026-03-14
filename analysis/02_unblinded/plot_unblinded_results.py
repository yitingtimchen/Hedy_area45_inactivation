from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
UNBLINDED_ROOT = ROOT / "results" / "unblinded"

VEHICLE_COLOR = "#A9B7C9"
DCZ_COLOR = "#1F4AA8"
LINE_COLOR = "#7A7A7A"
TEXT_COLOR = "#111111"


def main() -> None:
    for cohort_name, cohort_label in [("full", "Full session set"), ("exclude_vet_entry", "Excluding vet-entry session")]:
        tables_dir = UNBLINDED_ROOT / cohort_name / "tables"
        figures_dir = UNBLINDED_ROOT / cohort_name / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)

        decision = pd.read_csv(tables_dir / "unblinded_decision_table.csv", dtype={"session_id": str})
        exploratory = pd.read_csv(tables_dir / "unblinded_exploratory_nonsocial_table.csv", dtype={"session_id": str})
        primary_stats = pd.read_csv(tables_dir / "condition_comparison_primary.csv")
        secondary_stats = pd.read_csv(tables_dir / "condition_comparison_secondary.csv")
        sensitivity_stats = pd.read_csv(tables_dir / "condition_comparison_quiet_mask_sensitivity.csv")
        exploratory_stats = pd.read_csv(tables_dir / "condition_comparison_exploratory.csv")

        plot_primary_condition_comparison(decision, primary_stats, secondary_stats, figures_dir, cohort_label)
        plot_primary_sensitivity(decision, sensitivity_stats, figures_dir, cohort_label)
        plot_primary_timecourse(decision, figures_dir, cohort_label)
        plot_exploratory_panel(exploratory, exploratory_stats, figures_dir, cohort_label)


def paired_strip(ax: plt.Axes, df: pd.DataFrame, vehicle_col: str, dcz_col: str, ylabel: str, title: str, p_text: str | None = None) -> None:
    ordered = df.sort_values(["date", "session_id"]).reset_index(drop=True)
    x_positions = np.array([0, 1])

    vehicle = ordered.loc[ordered["condition"] == "vehicle", vehicle_col].to_numpy(dtype=float)
    dcz = ordered.loc[ordered["condition"] == "DCZ", dcz_col].to_numpy(dtype=float)

    rng = np.random.default_rng(4)
    veh_jitter = rng.uniform(-0.06, 0.06, size=len(vehicle))
    dcz_jitter = rng.uniform(-0.06, 0.06, size=len(dcz))

    ax.scatter(np.full(len(vehicle), 0) + veh_jitter, vehicle, color=VEHICLE_COLOR, s=40, zorder=3)
    ax.scatter(np.full(len(dcz), 1) + dcz_jitter, dcz, color=DCZ_COLOR, s=40, zorder=3)

    for x, values, color in [(0, vehicle, VEHICLE_COLOR), (1, dcz, DCZ_COLOR)]:
        mean_value = float(np.mean(values))
        ax.plot([x - 0.18, x + 0.18], [mean_value, mean_value], color=color, linewidth=3.0, zorder=4)

    ax.set_xticks([0, 1], ["Vehicle", "DCZ"])
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=11, loc="left")
    if p_text:
        ax.text(0.02, 0.97, p_text, transform=ax.transAxes, ha="left", va="top", fontsize=9, color=TEXT_COLOR)
    style_axis(ax)


def plot_primary_condition_comparison(
    decision: pd.DataFrame,
    primary_stats: pd.DataFrame,
    secondary_stats: pd.DataFrame,
    figures_dir: Path,
    cohort_label: str,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(9.4, 7.2))
    axes = axes.ravel()

    p_net = primary_stats.loc[
        primary_stats["metric"] == "groom_duration_net_receive_minus_give_pct_session",
        "exact_permutation_p_two_sided",
    ].iloc[0]
    p_recip = primary_stats.loc[
        primary_stats["metric"] == "groom_duration_reciprocity_0to1",
        "exact_permutation_p_two_sided",
    ].iloc[0]
    p_total = secondary_stats.loc[
        secondary_stats["metric"] == "groom_total_pct_session",
        "exact_permutation_p_two_sided",
    ].iloc[0]
    p_social = secondary_stats.loc[
        secondary_stats["metric"] == "social_engaged_pct_session",
        "exact_permutation_p_two_sided",
    ].iloc[0]

    paired_strip(
        axes[0],
        decision,
        "groom_duration_net_receive_minus_give_pct_session",
        "groom_duration_net_receive_minus_give_pct_session",
        "Net grooming (% session)\n(receive - give)",
        "Primary: net grooming balance",
        f"Exact permutation p = {p_net:.4f}",
    )
    axes[0].axhline(0, color="#7F7F7F", linewidth=1.0, linestyle="--")

    paired_strip(
        axes[1],
        decision,
        "groom_duration_reciprocity_0to1",
        "groom_duration_reciprocity_0to1",
        "Reciprocity (0 to 1)",
        "Primary: grooming reciprocity",
        f"Exact permutation p = {p_recip:.4f}",
    )
    axes[1].set_ylim(0, 1.05)

    paired_strip(
        axes[2],
        decision,
        "groom_total_pct_session",
        "groom_total_pct_session",
        "Grooming (% session)",
        "Secondary: total grooming",
        f"Exact permutation p = {p_total:.4f}",
    )

    paired_strip(
        axes[3],
        decision,
        "social_engaged_pct_session",
        "social_engaged_pct_session",
        "Social engagement (% session)",
        "Secondary: social engagement",
        f"Exact permutation p = {p_social:.4f}",
    )

    fig.suptitle(f"Unblinded condition comparison: {cohort_label}", fontsize=12, x=0.06, ha="left")
    fig.tight_layout()
    fig.savefig(figures_dir / "unblinded_primary_condition_comparison.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_primary_sensitivity(decision: pd.DataFrame, sensitivity_stats: pd.DataFrame, figures_dir: Path, cohort_label: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.9))

    p_net = sensitivity_stats.loc[
        sensitivity_stats["metric"] == "groom_duration_net_receive_minus_give_pct_quiet_masked_p90",
        "exact_permutation_p_two_sided",
    ].iloc[0]
    p_recip = sensitivity_stats.loc[
        sensitivity_stats["metric"] == "groom_duration_reciprocity_0to1_quiet_masked_p90",
        "exact_permutation_p_two_sided",
    ].iloc[0]

    paired_strip(
        axes[0],
        decision,
        "groom_duration_net_receive_minus_give_pct_quiet_masked_p90",
        "groom_duration_net_receive_minus_give_pct_quiet_masked_p90",
        "Net grooming (% session)\n(receive - give)",
        "Quiet-masked primary endpoint",
        f"Exact permutation p = {p_net:.4f}",
    )
    axes[0].axhline(0, color="#7F7F7F", linewidth=1.0, linestyle="--")

    paired_strip(
        axes[1],
        decision,
        "groom_duration_reciprocity_0to1_quiet_masked_p90",
        "groom_duration_reciprocity_0to1_quiet_masked_p90",
        "Reciprocity (0 to 1)",
        "Quiet-masked reciprocity",
        f"Exact permutation p = {p_recip:.4f}",
    )
    axes[1].set_ylim(0, 1.05)

    fig.suptitle(f"Quiet-mask sensitivity: {cohort_label}", fontsize=12, x=0.06, ha="left")
    fig.tight_layout()
    fig.savefig(figures_dir / "unblinded_primary_quiet_mask_sensitivity.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_primary_timecourse(decision: pd.DataFrame, figures_dir: Path, cohort_label: str) -> None:
    ordered = decision.sort_values("date").reset_index(drop=True)
    fig, axes = plt.subplots(2, 1, figsize=(9.2, 5.5), sharex=True)

    for condition, color in [("vehicle", VEHICLE_COLOR), ("DCZ", DCZ_COLOR)]:
        sub = ordered[ordered["condition"] == condition]
        axes[0].plot(sub["session_index"], sub["groom_duration_net_receive_minus_give_pct_session"], marker="o", color=color, linewidth=1.6, label=condition.capitalize())
        axes[1].plot(sub["session_index"], sub["groom_duration_reciprocity_0to1"], marker="o", color=color, linewidth=1.6, label=condition.capitalize())

    axes[0].axhline(0, color="#7F7F7F", linewidth=1.0, linestyle="--")
    axes[0].set_ylabel("Net grooming (% session)\n(receive - give)")
    axes[0].set_title(f"Session progression after unblinding: {cohort_label}", fontsize=11, loc="left")
    axes[1].set_ylabel("Reciprocity (0 to 1)")
    axes[1].set_xlabel("Session order")
    axes[1].set_ylim(0, 1.05)
    axes[0].legend(frameon=False, loc="upper right")
    for ax in axes:
        style_axis(ax)

    fig.tight_layout()
    fig.savefig(figures_dir / "unblinded_primary_by_session_order.png", dpi=220, bbox_inches="tight")
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

    fig, axes = plt.subplots(2, 3, figsize=(11.0, 6.8))
    axes = axes.ravel()

    for ax, metric in zip(axes, chosen):
        sub = exploratory[["condition", "date", "session_id", metric]].copy()
        sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
        sub = sub.dropna(subset=[metric]).reset_index(drop=True)
        stat_row = exploratory_stats.loc[exploratory_stats["metric"] == metric].iloc[0]
        p_text = f"p = {stat_row['exact_permutation_p_two_sided']:.4f}" if pd.notna(stat_row["exact_permutation_p_two_sided"]) else "p = NA"
        paired_strip(ax, sub, metric, metric, labels[metric], labels[metric].split("\n")[0], p_text)

    fig.suptitle(f"Exploratory contextual measures: {cohort_label}", fontsize=12, x=0.06, ha="left")
    fig.tight_layout()
    fig.savefig(figures_dir / "unblinded_exploratory_panel.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def style_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.tick_params(length=3.5, width=0.8)


if __name__ == "__main__":
    main()

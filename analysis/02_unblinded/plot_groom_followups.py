from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
UNBLINDED_ROOT = ROOT / "results" / "unblinded"

VEHICLE_COLOR = "#A9B7C9"
DCZ_COLOR = "#1F4AA8"


def style_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.tick_params(length=3.5, width=0.8)


def strip_by_condition(
    ax: plt.Axes,
    df: pd.DataFrame,
    metric: str,
    ylabel: str,
    title: str,
    p_value: float,
    log_scale: bool = False,
) -> None:
    sub = df[["condition", metric]].copy()
    sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
    sub = sub.dropna(subset=[metric]).reset_index(drop=True)

    vehicle = sub.loc[sub["condition"] == "vehicle", metric].to_numpy(dtype=float)
    dcz = sub.loc[sub["condition"] == "DCZ", metric].to_numpy(dtype=float)
    rng = np.random.default_rng(12)

    ax.scatter(np.full(len(vehicle), 0) + rng.uniform(-0.06, 0.06, len(vehicle)), vehicle, color=VEHICLE_COLOR, s=40, zorder=3)
    ax.scatter(np.full(len(dcz), 1) + rng.uniform(-0.06, 0.06, len(dcz)), dcz, color=DCZ_COLOR, s=40, zorder=3)
    for x, values, color in [(0, vehicle, VEHICLE_COLOR), (1, dcz, DCZ_COLOR)]:
        if len(values):
            mean_value = float(np.mean(values))
            ax.plot([x - 0.18, x + 0.18], [mean_value, mean_value], color=color, linewidth=3.0, zorder=4)

    ax.set_xticks([0, 1], ["Vehicle", "DCZ"])
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=11, loc="left")
    ax.text(0.02, 0.97, f"p = {p_value:.4f}", transform=ax.transAxes, ha="left", va="top", fontsize=9, color="#111111")
    if log_scale:
        ax.set_yscale("log")
    style_axis(ax)


def main() -> None:
    for cohort_name, cohort_label in [("full", "Full session set"), ("exclude_vet_entry", "Excluding vet-entry session")]:
        tables_dir = UNBLINDED_ROOT / cohort_name / "tables"
        figures_dir = UNBLINDED_ROOT / cohort_name / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)

        session_df = pd.read_csv(tables_dir / "groom_followup_metrics_by_session.csv", dtype={"session_id": str})
        summary = pd.read_csv(tables_dir / "groom_followup_condition_comparison.csv")
        p_map = dict(zip(summary["metric"], summary["exact_permutation_p_two_sided"]))

        fig, axes = plt.subplots(2, 2, figsize=(9.6, 6.8))
        axes = axes.ravel()

        strip_by_condition(
            axes[0],
            session_df,
            "episode_turn_taking_prob",
            "Probability",
            "Episode-level turn taking",
            p_map["episode_turn_taking_prob"],
        )
        strip_by_condition(
            axes[1],
            session_df,
            "episode_turn_taking_latency_median_s",
            "Seconds",
            "Median episode turn-taking latency",
            p_map["episode_turn_taking_latency_median_s"],
            log_scale=True,
        )
        strip_by_condition(
            axes[2],
            session_df,
            "groom_to_nonsocial_prob",
            "Probability",
            "Groom to nonsocial activity",
            p_map["groom_to_nonsocial_prob"],
        )
        strip_by_condition(
            axes[3],
            session_df,
            "nonsocial_to_groom_prob",
            "Probability",
            "Nonsocial activity to groom",
            p_map["nonsocial_to_groom_prob"],
        )

        fig.suptitle(f"Unblinded grooming follow-up metrics: {cohort_label}", fontsize=12, x=0.06, ha="left")
        fig.tight_layout()
        fig.savefig(figures_dir / "unblinded_groom_followup_panel.png", dpi=220, bbox_inches="tight")
        plt.close(fig)


if __name__ == "__main__":
    main()

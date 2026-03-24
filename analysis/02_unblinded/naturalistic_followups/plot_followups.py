from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PARENT = Path(__file__).resolve().parents[1]
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from _plot_helpers import paired_strip  # noqa: E402
from naturalistic_followups.common import ensure_full_output_dirs  # noqa: E402


LEDGER_MAIN_PANEL_SPECS = [
    ("give_to_receive_prob_120s", "Probability", "Hedy grooms first:\nHooke returns within 120 s", False, (0.0, 1.0)),
    ("receive_to_give_prob_120s", "Probability", "Hooke grooms first:\nHedy returns within 120 s", False, (0.0, 1.0)),
    ("give_to_receive_latency_median_s", "Seconds", "Hooke return latency", True, None),
    ("receive_to_give_latency_median_s", "Seconds", "Hedy return latency", True, None),
]

LEDGER_SHUFFLE_PANEL_SPECS = [
    ("give_to_receive_prob_120s_minus_shuffle", "Observed - shuffled", "Hedy grooms first:\nreturn above shuffled baseline", False, None),
    ("receive_to_give_prob_120s_minus_shuffle", "Observed - shuffled", "Hooke grooms first:\nreturn above shuffled baseline", False, None),
]

REPAIR_PANEL_SPECS = [
    ("affiliative_repair_prob_120s", "Probability", "Affiliative repair within 120 s", False, (0.0, 1.0)),
    ("groom_repair_prob_120s", "Probability", "Groom repair within 120 s", False, (0.0, 1.0)),
    ("travel_disengage_prob_120s", "Probability", "Travel disengagement within 120 s", False, (0.0, 1.0)),
    ("repair_before_travel_prob", "Probability", "Repair occurs before travel", False, (0.0, 1.0)),
    ("affiliative_repair_latency_median_s", "Seconds", "Latency to affiliative repair", True, None),
    ("travel_disengage_latency_median_s", "Seconds", "Latency to travel disengagement", True, None),
]

BUFFERING_PANEL_SPECS = [
    ("alertness_delta_60s_after_grooming", "Post - pre fraction", "Alertness after grooming onset", False, None),
    ("outside_attention_delta_60s_after_grooming", "Post - pre fraction", "Outside attention after grooming onset", False, None),
    ("total_arousal_delta_120s_after_grooming", "Post - pre fraction", "Total arousal-like load after grooming onset", False, None),
    ("alertness_delta_60s_after_affiliative_social", "Post - pre fraction", "Alertness after affiliative social onset", False, None),
    ("outside_attention_delta_60s_after_affiliative_social", "Post - pre fraction", "Outside attention after affiliative social onset", False, None),
    ("total_arousal_delta_120s_after_affiliative_social", "Post - pre fraction", "Total arousal-like load after affiliative social onset", False, None),
]


def metric_p_map(summary: pd.DataFrame) -> dict[str, float]:
    return {str(row.metric): float(row.exact_permutation_p_two_sided) for row in summary.itertuples(index=False)}


def draw_panel(
    session_df: pd.DataFrame,
    summary: pd.DataFrame,
    specs: list[tuple[str, str, str, bool, tuple[float, float] | None]],
    output_path: Path,
    title: str,
) -> None:
    p_map = metric_p_map(summary)
    fig, axes = plt.subplots(2, 3, figsize=(10.2, 5.9))
    axes = axes.ravel()
    for ax, (metric, ylabel, panel_title, log_scale, y_limits) in zip(axes, specs):
        paired_strip(
            ax,
            session_df,
            metric,
            ylabel,
            panel_title,
            p_map.get(metric),
            y_limits=y_limits,
            log_scale=log_scale,
        )
    fig.suptitle(title, fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94), w_pad=0.85, h_pad=0.9)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def draw_ledger_main_panel(
    session_df: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> None:
    p_map = metric_p_map(summary)
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 7.0))
    axes = axes.ravel()
    for ax, (metric, ylabel, panel_title, log_scale, y_limits) in zip(axes, LEDGER_MAIN_PANEL_SPECS):
        paired_strip(
            ax,
            session_df,
            metric,
            ylabel,
            panel_title,
            p_map.get(metric),
            y_limits=y_limits,
            log_scale=log_scale,
        )
    fig.suptitle("Grooming ledger follow-up", fontsize=14, x=0.07, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95), w_pad=1.0, h_pad=1.0)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def draw_ledger_shuffle_panel(
    session_df: pd.DataFrame,
    summary: pd.DataFrame,
    output_path: Path,
) -> None:
    p_map = metric_p_map(summary)
    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.8))
    axes = axes.ravel()
    for ax, (metric, ylabel, panel_title, log_scale, y_limits) in zip(axes, LEDGER_SHUFFLE_PANEL_SPECS):
        paired_strip(
            ax,
            session_df,
            metric,
            ylabel,
            panel_title,
            p_map.get(metric),
            y_limits=y_limits,
            log_scale=log_scale,
        )
    fig.suptitle("Grooming ledger shuffled-baseline check", fontsize=13, x=0.07, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.93), w_pad=1.0)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    tables_dir, figures_dir, _ = ensure_full_output_dirs()
    ledger_session_df = pd.read_csv(tables_dir / "grooming_ledger_metrics_by_session.csv", dtype={"session_id": str})
    repair_session_df = pd.read_csv(tables_dir / "post_conflict_repair_metrics_by_session.csv", dtype={"session_id": str})
    buffering_session_df = pd.read_csv(tables_dir / "social_buffering_metrics_by_session.csv", dtype={"session_id": str})
    ledger_summary = pd.read_csv(tables_dir / "grooming_ledger_condition_comparison.csv")
    repair_summary = pd.read_csv(tables_dir / "post_conflict_repair_condition_comparison.csv")
    buffering_summary = pd.read_csv(tables_dir / "social_buffering_condition_comparison.csv")

    draw_ledger_main_panel(
        ledger_session_df,
        ledger_summary,
        figures_dir / "grooming_ledger_followup.png",
    )
    draw_ledger_shuffle_panel(
        ledger_session_df,
        ledger_summary,
        figures_dir / "grooming_ledger_shuffle_check.png",
    )
    draw_panel(
        repair_session_df,
        repair_summary,
        REPAIR_PANEL_SPECS,
        figures_dir / "post_conflict_repair_followup.png",
        "Post-conflict repair follow-up: full session set",
    )
    draw_panel(
        buffering_session_df,
        buffering_summary,
        BUFFERING_PANEL_SPECS,
        figures_dir / "social_buffering_followup.png",
        "Social buffering follow-up: full session set",
    )


if __name__ == "__main__":
    main()

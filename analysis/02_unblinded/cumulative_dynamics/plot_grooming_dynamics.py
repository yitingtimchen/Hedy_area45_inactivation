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
    FONT_SIZE,
    SESSION_FRACTION_GRID,
    TITLE_SIZE,
    VEHICLE_COLOR,
    interpolate_session_curve,
    round_up_abs_limit,
    style_axis,
)
from output_layout import results_figures_dir, results_tables_dir  # noqa: E402


ROOT = Path(__file__).resolve().parents[3]
UNBLINDED_ROOT = ROOT / "results" / "unblinded"
BLINDED_TABLES_DIR = ROOT / "results" / "blinded" / "tables"

COHORTS = [
    ("full", "Full session set"),
    ("quiet_mask", "Quiet-mask sensitivity session set"),
    ("exclude_vet_entry", "Excluding vet-entry session"),
]


def compute_timecourse_net_limit() -> float:
    max_abs = 0.0
    for cohort_name, _ in COHORTS:
        decision = pd.read_csv(
            results_tables_dir(cohort_name, "single_value_core") / "unblinded_decision_table.csv",
            dtype={"session_id": str},
        )
        timecourse = pd.read_csv(BLINDED_TABLES_DIR / "blinded_grooming_timecourse.csv", dtype={"session_id": str})
        merged = decision[["session_id", "session_duration_min"]].merge(timecourse, on="session_id", how="inner")
        duration_s = merged["session_duration_min"].to_numpy(dtype=float) * 60.0
        net_pct = np.where(
            duration_s > 0,
            100.0 * merged["cum_net_duration_receive_minus_give_s"].to_numpy(dtype=float) / duration_s,
            np.nan,
        )
        max_abs = max(max_abs, float(np.nanmax(np.abs(net_pct))))
    return round_up_abs_limit(max_abs, 5.0)


def build_curves(merged: pd.DataFrame, metric: str, is_signed: bool) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    curves_by_condition: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for condition in ["vehicle", "DCZ"]:
        sub = merged.loc[merged["condition"] == condition].copy()
        curves = []
        for _, sess in sub.groupby("session_id", sort=False):
            duration_s = float(sess["session_duration_min"].iloc[0]) * 60.0
            if duration_s <= 0:
                continue
            curves.append(interpolate_session_curve(sess, metric, duration_s, is_signed))
        if not curves:
            continue
        arr = np.vstack(curves)
        mean_curve = np.nanmean(arr, axis=0)
        sem_curve = np.nanstd(arr, axis=0, ddof=1) / np.sqrt(arr.shape[0]) if arr.shape[0] > 1 else np.zeros_like(mean_curve)
        curves_by_condition[condition] = (mean_curve, sem_curve)
    return curves_by_condition


def draw_curve_panel(ax: plt.Axes, curves: dict[str, tuple[np.ndarray, np.ndarray]], ylabel: str, title: str, signed_limit: float | None = None) -> None:
    x_pct = 100.0 * SESSION_FRACTION_GRID
    for condition, color in [("vehicle", VEHICLE_COLOR), ("DCZ", DCZ_COLOR)]:
        if condition not in curves:
            continue
        mean_curve, sem_curve = curves[condition]
        ax.fill_between(x_pct, mean_curve - sem_curve, mean_curve + sem_curve, color=color, alpha=0.14, linewidth=0)
        ax.plot(x_pct, mean_curve, color=color, linewidth=2.0, label=condition.capitalize())

    if signed_limit is None:
        ax.set_ylim(0.0, 100.0)
    else:
        ax.axhline(0, color="#7F7F7F", linewidth=1.0, linestyle="--")
        ax.set_ylim(-signed_limit, signed_limit)
    ax.set_title(title, fontsize=TITLE_SIZE, loc="left")
    ax.set_xlabel("% of session elapsed", fontsize=FONT_SIZE)
    ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
    style_axis(ax)


def plot_grooming_dynamics(decision: pd.DataFrame, figures_dir: Path, cohort_label: str, net_limit: float) -> None:
    timecourse = pd.read_csv(BLINDED_TABLES_DIR / "blinded_grooming_timecourse.csv", dtype={"session_id": str})
    merged = decision[["session_id", "condition", "session_duration_min"]].merge(timecourse, on="session_id", how="inner")

    raw_specs = [
        ("cum_groom_give_s", "Cumulative groom given\n(% session)", "Cumulative grooming duration given", False),
        ("cum_groom_receive_s", "Cumulative groom received\n(% session)", "Cumulative grooming duration received", False),
        ("cum_groom_total_s", "Cumulative total grooming\n(% session)", "Cumulative total grooming duration", False),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(10.0, 3.9), sharex=True)
    for ax, (metric, ylabel, title, is_signed) in zip(axes, raw_specs):
        draw_curve_panel(ax, build_curves(merged, metric, is_signed), ylabel, title)
    axes[0].legend(frameon=False, loc="upper left")
    fig.suptitle(f"Cumulative raw grooming dynamics: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92), w_pad=0.9)
    fig.savefig(figures_dir / "groom_duration_cumulative_dynamics.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(1, 1, figsize=(5.0, 3.9), sharex=True)
    draw_curve_panel(
        ax,
        build_curves(merged, "cum_net_duration_receive_minus_give_s", True),
        "Cumulative net grooming\n(% session)",
        "Cumulative net grooming duration",
        signed_limit=net_limit,
    )
    ax.legend(frameon=False, loc="upper left")
    fig.suptitle(f"Cumulative composite grooming dynamics: {cohort_label}", fontsize=13, x=0.06, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(figures_dir / "groom_composite_cumulative_dynamics.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

def main() -> None:
    net_limit = compute_timecourse_net_limit()
    for cohort_name, cohort_label in COHORTS:
        tables_dir = results_tables_dir(cohort_name, "single_value_core")
        figures_dir = results_figures_dir(cohort_name, "within_session_dynamics_minutes")
        decision = pd.read_csv(tables_dir / "unblinded_decision_table.csv", dtype={"session_id": str})
        plot_grooming_dynamics(decision, figures_dir, cohort_label, net_limit)


if __name__ == "__main__":
    main()

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PARENT = Path(__file__).resolve().parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from _plot_helpers import DCZ_COLOR, VEHICLE_COLOR, exact_slope_permutation_p, fit_line, paired_strip, p_style, style_axis  # noqa: E402
from data_selection import load_all_branch_tables  # noqa: E402
from reorg_common import canonical_selection_name, ensure_output_dirs, format_summary_line, summarize_by_condition  # noqa: E402


DATA_SELECTION = "include_smoothed_loud_epochs_only"
OUTPUT_NAME = canonical_selection_name(DATA_SELECTION)
SELECTION_LABEL = "Include smoothed loud epochs only"
RAW_MODE = "raw_total_duration"
NORM_MODE = "normalized_total_duration"
TEMP_MODE = "across_session_temporal_dependence"
METRIC_RAW = "loud_stress_composite_duration_s_selected"
METRIC_NORM = "loud_stress_composite_pct_selected"
METRIC_LABEL_RAW = "Loud/stress composite duration (s)"
METRIC_LABEL_NORM = "Loud/stress composite (% selected time)"


def plot_raw(df: pd.DataFrame) -> pd.DataFrame:
    figures_dir, tables_dir, docs_dir = ensure_output_dirs(DATA_SELECTION, RAW_MODE)
    summary = summarize_by_condition(df, [METRIC_RAW])
    fig, ax = plt.subplots(1, 1, figsize=(4.8, 3.8))
    p_value = float(summary.loc[summary["metric"] == METRIC_RAW, "exact_permutation_p_two_sided"].iloc[0])
    paired_strip(ax, df, METRIC_RAW, "Seconds", "Loud/stress composite duration", p_value)
    fig.suptitle(SELECTION_LABEL, fontsize=13, x=0.08, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(figures_dir / f"loud_stress_composite__{RAW_MODE}__{OUTPUT_NAME}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    summary.to_csv(tables_dir / f"loud_stress_composite__{RAW_MODE}__{OUTPUT_NAME}.csv", index=False)
    lines = ["# Loud-Only Stress Summary", "", format_summary_line(summary.iloc[0], METRIC_LABEL_RAW), ""]
    (docs_dir / f"loud_stress_composite__{RAW_MODE}__{OUTPUT_NAME}.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def plot_norm(df: pd.DataFrame) -> pd.DataFrame:
    figures_dir, tables_dir, docs_dir = ensure_output_dirs(DATA_SELECTION, NORM_MODE)
    summary = summarize_by_condition(df, [METRIC_NORM])
    fig, ax = plt.subplots(1, 1, figsize=(4.8, 3.8))
    p_value = float(summary.loc[summary["metric"] == METRIC_NORM, "exact_permutation_p_two_sided"].iloc[0])
    paired_strip(ax, df, METRIC_NORM, "% selected time", "Loud/stress composite", p_value)
    fig.suptitle(SELECTION_LABEL, fontsize=13, x=0.08, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(figures_dir / f"loud_stress_composite__{NORM_MODE}__{OUTPUT_NAME}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    summary.to_csv(tables_dir / f"loud_stress_composite__{NORM_MODE}__{OUTPUT_NAME}.csv", index=False)
    lines = ["# Loud-Only Stress Summary", "", format_summary_line(summary.iloc[0], METRIC_LABEL_NORM), ""]
    (docs_dir / f"loud_stress_composite__{NORM_MODE}__{OUTPUT_NAME}.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def analyze_temporal(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    values = pd.to_numeric(df[METRIC_NORM], errors="coerce")
    for condition in ["vehicle", "DCZ"]:
        sub = df.loc[df["condition"] == condition, ["session_index", METRIC_NORM]].copy()
        sub[METRIC_NORM] = pd.to_numeric(sub[METRIC_NORM], errors="coerce")
        sub = sub.dropna()
        x = sub["session_index"].to_numpy(dtype=float)
        y = sub[METRIC_NORM].to_numpy(dtype=float)
        intercept, slope = fit_line(x, y)
        rows.append(
            {
                "condition": condition,
                "intercept_at_mean_session": intercept,
                "slope_per_session": slope,
                "slope_permutation_p_two_sided": exact_slope_permutation_p(x, y),
            }
        )
    return pd.DataFrame(rows)


def plot_temporal(df: pd.DataFrame) -> pd.DataFrame:
    figures_dir, tables_dir, docs_dir = ensure_output_dirs(DATA_SELECTION, TEMP_MODE)
    summary = analyze_temporal(df)
    fig, ax = plt.subplots(1, 1, figsize=(5.0, 4.0))
    for condition, color in [("vehicle", VEHICLE_COLOR), ("DCZ", DCZ_COLOR)]:
        sub = df.loc[df["condition"] == condition, ["session_index", METRIC_NORM]].copy()
        sub[METRIC_NORM] = pd.to_numeric(sub[METRIC_NORM], errors="coerce")
        sub = sub.dropna()
        x = sub["session_index"].to_numpy(dtype=float)
        y = sub[METRIC_NORM].to_numpy(dtype=float)
        ax.scatter(x, y, color=color, s=42, zorder=3)
        intercept, slope = fit_line(x, y)
        x_line = np.linspace(x.min(), x.max(), 200)
        ax.plot(x_line, intercept + slope * (x_line - x.mean()), color=color, linewidth=2.0)
        row = summary.loc[summary["condition"] == condition].iloc[0]
        label = p_style(float(row["slope_permutation_p_two_sided"]))
        ypos = 0.97 if condition == "vehicle" else 0.86
        ax.text(0.03, ypos, f"{condition.capitalize()} slope = {row['slope_per_session']:.3f}\n{label['text']}", transform=ax.transAxes, ha="left", va="top", fontsize=9.0, color=label["color"], fontweight=label["fontweight"])
    ax.set_title("Loud/stress composite over session order", fontsize=12, loc="left")
    ax.set_xlabel("Session order", fontsize=10.5)
    ax.set_ylabel("% selected time", fontsize=10.5)
    style_axis(ax)
    fig.suptitle(SELECTION_LABEL, fontsize=13, x=0.08, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(figures_dir / f"loud_stress_composite__{TEMP_MODE}__{OUTPUT_NAME}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    summary.to_csv(tables_dir / f"loud_stress_composite__{TEMP_MODE}__{OUTPUT_NAME}.csv", index=False)
    lines = ["# Loud-Only Stress Temporal Dependence", ""]
    for row in summary.itertuples(index=False):
        lines.append(f"- {row.condition.capitalize()} slope: `{row.slope_per_session:.3f}` per session, permutation `p = {row.slope_permutation_p_two_sided:.4f}`.")
    lines.append("")
    (docs_dir / f"loud_stress_composite__{TEMP_MODE}__{OUTPUT_NAME}.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def main() -> None:
    df = load_all_branch_tables()[DATA_SELECTION].copy()
    plot_raw(df)
    plot_norm(df)
    plot_temporal(df)


if __name__ == "__main__":
    main()

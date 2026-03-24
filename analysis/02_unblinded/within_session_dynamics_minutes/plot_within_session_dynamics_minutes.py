from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PARENT = Path(__file__).resolve().parents[1]
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from _plot_helpers import DCZ_COLOR, FONT_SIZE, TITLE_SIZE, VEHICLE_COLOR, style_axis  # noqa: E402
from data_selection import build_minute_timecourse, load_all_branch_tables  # noqa: E402
from reorg_common import DATA_SELECTIONS, add_data_selection_and_mode_header, canonical_selection_name, ensure_output_dirs  # noqa: E402


AGGREGATION_MODE = "within_session_dynamics_minutes"
AGGREGATION_LABEL = "within_session_dynamics_minutes"


def summarize_curves(timecourse: pd.DataFrame, metric: str) -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    out: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for condition in ["vehicle", "DCZ"]:
        sub = timecourse.loc[timecourse["condition"] == condition].copy()
        if sub.empty:
            continue
        pivot = sub.pivot_table(index="session_id", columns="elapsed_min", values=metric, aggfunc="last")
        x = pivot.columns.to_numpy(dtype=float)
        arr = pivot.to_numpy(dtype=float)
        mean = np.nanmean(arr, axis=0)
        valid_counts = np.sum(np.isfinite(arr), axis=0)
        sem = np.zeros_like(mean)
        for idx, n_valid in enumerate(valid_counts):
            if n_valid > 1:
                sem[idx] = float(np.nanstd(arr[:, idx], ddof=1) / np.sqrt(n_valid))
        out[condition] = (x, mean, sem)
    return out


def draw_panel(ax: plt.Axes, curves: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]], ylabel: str, title: str, signed: bool = False) -> None:
    for condition, color in [("vehicle", VEHICLE_COLOR), ("DCZ", DCZ_COLOR)]:
        if condition not in curves:
            continue
        x, mean, sem = curves[condition]
        ax.fill_between(x, mean - sem, mean + sem, color=color, alpha=0.14, linewidth=0)
        ax.plot(x, mean, color=color, linewidth=2.0, label=condition.capitalize())
    if signed:
        ax.axhline(0, color="#7F7F7F", linewidth=1.0, linestyle="--")
    ax.set_xlabel("Elapsed minutes", fontsize=FONT_SIZE)
    ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
    ax.set_title(title, fontsize=TITLE_SIZE, loc="left")
    style_axis(ax)


def write_markdown(docs_dir: Path, data_selection: str, selection_label: str, max_min: float) -> None:
    lines = [
        "# Within-Session Dynamics in Minutes",
        "",
    ]
    add_data_selection_and_mode_header(lines, selection_label, AGGREGATION_LABEL)
    lines.extend(
        [
            "- X-axis is elapsed minutes from session start within the original analyzed session window.",
            "- For excluded-loud and loud-only branches, curves retain original clock time and accumulate only over included bins.",
            f"- Maximum plotted elapsed minute in this branch: `{max_min:.1f}`.",
            "",
        ]
    )
    (docs_dir / f"grooming__{AGGREGATION_MODE}__{data_selection}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    branch_tables = load_all_branch_tables()
    for data_selection, selection_label in DATA_SELECTIONS:
        output_name = canonical_selection_name(data_selection)
        figures_dir, tables_dir, docs_dir = ensure_output_dirs(data_selection, AGGREGATION_MODE)
        session_df = branch_tables[data_selection][["session_id", "condition", "selected_duration_min"]].copy()
        session_df.to_csv(tables_dir / f"session_metrics__{AGGREGATION_MODE}__{output_name}.csv", index=False)
        timecourse = build_minute_timecourse(data_selection)
        timecourse.to_csv(tables_dir / f"grooming_timecourse__{AGGREGATION_MODE}__{output_name}.csv", index=False)

        fig, axes = plt.subplots(1, 4, figsize=(14.0, 3.8), sharex=True)
        specs = [
            ("cum_groom_give_duration_s", "Seconds", "Cumulative groom give duration", False),
            ("cum_groom_receive_duration_s", "Seconds", "Cumulative groom receive duration", False),
            ("cum_groom_total_duration_s", "Seconds", "Cumulative total grooming duration", False),
            ("cum_groom_net_duration_s", "Seconds", "Cumulative net grooming duration", True),
        ]
        for ax, (metric, ylabel, title, signed) in zip(axes, specs):
            draw_panel(ax, summarize_curves(timecourse, metric), ylabel, title, signed=signed)
        axes[0].legend(frameon=False, loc="upper left")
        fig.suptitle(f"Grooming dynamics by elapsed minute: {selection_label}", fontsize=13, x=0.05, ha="left")
        fig.tight_layout(rect=(0, 0, 1, 0.92), w_pad=0.8)
        fig.savefig(figures_dir / f"grooming__{AGGREGATION_MODE}__{output_name}.png", dpi=220, bbox_inches="tight")
        plt.close(fig)

        max_min = float(timecourse["elapsed_min"].max()) if not timecourse.empty else 0.0
        write_markdown(docs_dir, output_name, selection_label, max_min)


if __name__ == "__main__":
    main()

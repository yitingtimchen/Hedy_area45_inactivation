from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SUMMARY_DIR = ROOT / "results" / "blinded" / "tables"
INTERVALS_DIR = ROOT / "data" / "derived" / "behavior" / "cleaned_intervals"
DERIVED_AUDIO_DIR = ROOT / "data" / "derived" / "audio"
BORIS_DIR = ROOT / "data" / "raw" / "boris"
FIGURES_DIR = ROOT / "results" / "blinded" / "figures"

GIVE_COLOR = "#4DD9E8"
RECEIVE_COLOR = "#1F4AA8"
BASELINE_COLOR = "#CFCFCF"
TRACE_COLOR = "#111111"
SHADE_COLOR = "#BDBDBD"
MASK_BASELINE_COLOR = "#D9D9D9"
MASK_EXCLUDED_COLOR = "#C0392B"
MOUNT_GIVE_COLOR = "#D97C4A"
MOUNT_ATTEMPT_COLOR = "#F0B173"
MOUNT_RECEIVE_COLOR = "#F6D5A4"

SMOOTH_WINDOW_BINS = 5
MAX_QUIET_GAP_BINS = 2
MIN_LOUD_RUN_BINS = 3


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    timecourse = pd.read_csv(SUMMARY_DIR / "blinded_grooming_timecourse.csv")
    summary = pd.read_csv(SUMMARY_DIR / "blinded_session_summary.csv").sort_values("session_id")
    audio = pd.read_csv(DERIVED_AUDIO_DIR / "blinded_audio_features_1s_labeled.csv", dtype={"session_id": str})

    for session_id in summary["session_id"].astype(str):
        timeline = pd.read_csv(INTERVALS_DIR / f"{session_id}_layered_timeline.csv")
        session_tc = timecourse[timecourse["session_id"].astype(str) == session_id].copy()
        session_audio = audio[audio["session_id"].astype(str) == session_id].copy()
        plot_session_panel(session_id, timeline, session_tc, session_audio)

    plot_gallery(timecourse, summary)
    plot_average_net_trace(timecourse)
    plot_session_reciprocity(summary)


def _fill_short_false_gaps(mask: np.ndarray, max_gap: int) -> np.ndarray:
    out = mask.copy()
    n = len(out)
    i = 0
    while i < n:
        if out[i]:
            i += 1
            continue
        start = i
        while i < n and not out[i]:
            i += 1
        end = i
        if start > 0 and end < n and out[start - 1] and out[end] and (end - start) <= max_gap:
            out[start:end] = True
    return out


def _remove_short_true_runs(mask: np.ndarray, min_run: int) -> np.ndarray:
    out = mask.copy()
    n = len(out)
    i = 0
    while i < n:
        if not out[i]:
            i += 1
            continue
        start = i
        while i < n and out[i]:
            i += 1
        end = i
        if (end - start) < min_run:
            out[start:end] = False
    return out


def compute_smoothed_loud_mask(audio_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    ordered = audio_df.sort_values("bin_start_s").reset_index(drop=True)
    smoothed_rms = (
        ordered["rms_dbfs"]
        .rolling(window=SMOOTH_WINDOW_BINS, center=True, min_periods=1)
        .mean()
        .to_numpy(dtype=float)
    )
    threshold = float(np.quantile(smoothed_rms, 0.90))
    loud_mask = smoothed_rms >= threshold
    loud_mask = _fill_short_false_gaps(loud_mask, MAX_QUIET_GAP_BINS)
    loud_mask = _remove_short_true_runs(loud_mask, MIN_LOUD_RUN_BINS)
    return loud_mask, smoothed_rms


def plot_session_panel(session_id: str, timeline: pd.DataFrame, timecourse: pd.DataFrame, audio_df: pd.DataFrame) -> None:
    sexual_intervals = extract_sexual_intervals(session_id, timeline)
    fig, axes = plt.subplots(
        5,
        1,
        figsize=(8.8, 7.6),
        sharex=True,
        gridspec_kw={"height_ratios": [0.9, 0.9, 0.7, 1.15, 1.15]},
    )

    draw_groom_strip(axes[0], timeline)
    draw_sexual_strip(axes[1], timeline, sexual_intervals)
    draw_loud_mask_strip(axes[2], audio_df)
    draw_cumulative_trace(
        axes[3],
        timecourse,
        "cum_net_duration_receive_minus_give_s",
        "Received - given (s)",
    )
    draw_cumulative_trace(
        axes[4],
        timecourse,
        "cum_net_bouts_receive_minus_give",
        "Received - given bouts",
    )

    axes[0].set_title(f"Blinded session {session_id}", fontsize=11, loc="left")
    axes[4].set_xlabel("Minutes from pairing start")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"{session_id}_paperstyle_social_panel.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def draw_groom_strip(ax: plt.Axes, timeline: pd.DataFrame) -> None:
    t = timeline.copy()
    session_start = float(t["start_s"].min())
    session_end = float(t["end_s"].max())
    xmin = 0.0
    xmax = (session_end - session_start) / 60.0

    ax.axhspan(-0.42, 0.42, color=BASELINE_COLOR, zorder=0)
    for row in t.itertuples(index=False):
        if row.social_state not in {"Groom give", "Groom receive"}:
            continue
        start_min = (float(row.start_s) - session_start) / 60.0
        width_min = float(row.duration_s) / 60.0
        color = GIVE_COLOR if row.social_state == "Groom give" else RECEIVE_COLOR
        ax.broken_barh([(start_min, width_min)], (-0.42, 0.84), facecolors=color, edgecolors="none", zorder=2)

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(-0.7, 0.7)
    ax.set_yticks([])
    ax.set_ylabel("Grooming", rotation=0, labelpad=28, va="center")
    style_axis(ax, keep_bottom=False)


def draw_loud_mask_strip(ax: plt.Axes, audio_df: pd.DataFrame) -> None:
    ordered = audio_df.sort_values("bin_start_s").reset_index(drop=True)
    session_start = float(ordered["elapsed_start_s"].min())
    session_end = float((ordered["elapsed_start_s"] + ordered["bin_duration_s"]).max())
    loud_mask, _ = compute_smoothed_loud_mask(ordered)

    ax.axhspan(-0.42, 0.42, color=MASK_BASELINE_COLOR, zorder=0)
    for row, is_loud in zip(ordered.itertuples(index=False), loud_mask):
        if not is_loud:
            continue
        start_min = (float(row.elapsed_start_s) - session_start) / 60.0
        width_min = float(row.bin_duration_s) / 60.0
        ax.broken_barh([(start_min, width_min)], (-0.42, 0.84), facecolors=MASK_EXCLUDED_COLOR, edgecolors="none", zorder=2)

    ax.set_xlim(0.0, (session_end - session_start) / 60.0)
    ax.set_ylim(-0.7, 0.7)
    ax.set_yticks([])
    ax.set_ylabel("Loud mask", rotation=0, labelpad=30, va="center")
    ax.text(
        0.01,
        0.84,
        "Red = excluded loud epochs",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=8.5,
        color=MASK_EXCLUDED_COLOR,
        fontweight="bold",
    )
    style_axis(ax, keep_bottom=False)


def extract_sexual_intervals(session_id: str, timeline: pd.DataFrame) -> pd.DataFrame:
    events = pd.read_pickle(BORIS_DIR / f"{session_id}.pkl").sort_values("Time").reset_index(drop=True)
    session_start = float(timeline["start_s"].min())
    session_end = float(timeline["end_s"].max())
    wanted = {"Mount give", "Mount attempt", "Mount receive"}
    starts: dict[str, list[float]] = {}
    rows: list[dict[str, float | str]] = []
    state_events = events[events["Behavior type"].isin(["START", "STOP"])].copy()
    for _, row in state_events.iterrows():
        behavior = str(row["Behavior"])
        if behavior not in wanted:
            continue
        event_type = str(row["Behavior type"])
        event_time = float(row["Time"])
        if event_type == "START":
            starts.setdefault(behavior, []).append(event_time)
            continue
        if behavior not in starts or not starts[behavior]:
            continue
        start_time = starts[behavior].pop(0)
        clip_start = max(start_time, session_start)
        clip_end = min(event_time, session_end)
        if clip_end <= clip_start:
            continue
        rows.append({"behavior": behavior, "start_s": clip_start, "end_s": clip_end, "duration_s": clip_end - clip_start})
    return pd.DataFrame(rows)


def draw_sexual_strip(ax: plt.Axes, timeline: pd.DataFrame, sexual_intervals: pd.DataFrame) -> None:
    session_start = float(timeline["start_s"].min())
    session_end = float(timeline["end_s"].max())
    color_map = {
        "Mount give": MOUNT_GIVE_COLOR,
        "Mount attempt": MOUNT_ATTEMPT_COLOR,
        "Mount receive": MOUNT_RECEIVE_COLOR,
    }
    ax.axhspan(-0.42, 0.42, color=BASELINE_COLOR, zorder=0)
    if not sexual_intervals.empty:
        for row in sexual_intervals.itertuples(index=False):
            start_min = (float(row.start_s) - session_start) / 60.0
            width_min = float(row.duration_s) / 60.0
            ax.broken_barh([(start_min, width_min)], (-0.42, 0.84), facecolors=color_map[row.behavior], edgecolors="none", zorder=2)

    ax.set_xlim(0.0, (session_end - session_start) / 60.0)
    ax.set_ylim(-0.7, 0.7)
    ax.set_yticks([])
    ax.set_ylabel("Sexual\nfamily", rotation=0, labelpad=22, va="center")
    ax.text(0.01, 0.84, "Give / attempt / receive", transform=ax.transAxes, ha="left", va="center", fontsize=8.3, color=TRACE_COLOR)
    style_axis(ax, keep_bottom=False)


def draw_cumulative_trace(ax: plt.Axes, timecourse: pd.DataFrame, y_col: str, y_label: str) -> None:
    x = timecourse["elapsed_min"].to_numpy()
    y = timecourse[y_col].to_numpy()
    ax.plot(x, y, color=TRACE_COLOR, linewidth=2.2)
    ax.axhline(0, color="#7F7F7F", linewidth=1.0, linestyle="--")
    ax.set_ylabel(y_label)
    ax.grid(False)
    style_axis(ax, keep_bottom=True)


def plot_gallery(timecourse: pd.DataFrame, summary: pd.DataFrame) -> None:
    sessions = summary["session_id"].astype(str).tolist()
    fig, axes = plt.subplots(4, 4, figsize=(12.5, 9.5), sharex=True, sharey=True)
    axes = axes.ravel()

    y_min = float(timecourse["cum_net_duration_receive_minus_give_s"].min())
    y_max = float(timecourse["cum_net_duration_receive_minus_give_s"].max())
    pad = max(15.0, 0.04 * max(abs(y_min), abs(y_max)))

    for ax, session_id in zip(axes, sessions):
        sub = timecourse[timecourse["session_id"].astype(str) == session_id].copy()
        ax.plot(sub["elapsed_min"], sub["cum_net_duration_receive_minus_give_s"], color=TRACE_COLOR, linewidth=1.6)
        ax.axhline(0, color="#7F7F7F", linewidth=0.8, linestyle="--")
        ax.set_title(session_id, fontsize=9, loc="left")
        ax.set_ylim(y_min - pad, y_max + pad)
        style_axis(ax, keep_bottom=True)

    for ax in axes[len(sessions):]:
        ax.axis("off")

    fig.supxlabel("Minutes from pairing start")
    fig.supylabel("Cumulative net duration (received - given, s)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "blinded_grooming_net_duration_gallery.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_average_net_trace(timecourse: pd.DataFrame) -> None:
    aligned = (
        timecourse.groupby("elapsed_min", as_index=False)["cum_net_duration_receive_minus_give_s"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={"mean": "mean_value", "std": "std_value", "count": "n"})
    )
    sem = aligned["std_value"].fillna(0) / np.sqrt(aligned["n"].clip(lower=1))

    fig, ax = plt.subplots(figsize=(7.8, 4.3))
    ax.fill_between(
        aligned["elapsed_min"],
        aligned["mean_value"] - sem,
        aligned["mean_value"] + sem,
        color=SHADE_COLOR,
        alpha=0.55,
        linewidth=0,
    )
    ax.plot(aligned["elapsed_min"], aligned["mean_value"], color=TRACE_COLOR, linewidth=2.4)
    ax.axhline(0, color="#7F7F7F", linewidth=1.0, linestyle="--")
    ax.set_xlabel("Minutes from pairing start")
    ax.set_ylabel("Net duration\n(received - given, s)")
    ax.set_title("Blinded average cumulative net grooming duration", fontsize=11, loc="left")
    style_axis(ax, keep_bottom=True)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "blinded_grooming_net_duration_average.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_session_reciprocity(summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ordered = summary.copy()
    colors = np.where(ordered["groom_duration_net_receive_minus_give_s"] >= 0, RECEIVE_COLOR, GIVE_COLOR)
    ax.bar(ordered["session_id"].astype(str), ordered["groom_duration_reciprocity_0to1"], color=colors, width=0.8)
    ax.set_xlabel("Blinded session ID")
    ax.set_ylabel("Session reciprocity\n(1 = reciprocal)")
    ax.set_ylim(0, 1.05)
    ax.set_title("Blinded session-level grooming reciprocity (duration)", fontsize=11, loc="left")
    ax.tick_params(axis="x", rotation=45)
    style_axis(ax, keep_bottom=True)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "blinded_session_groom_reciprocity_0to1.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def style_axis(ax: plt.Axes, keep_bottom: bool) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)
    if not keep_bottom:
        ax.spines["bottom"].set_visible(False)
        ax.tick_params(axis="x", bottom=False, labelbottom=False)
    ax.tick_params(length=3.5, width=0.8)


if __name__ == "__main__":
    main()

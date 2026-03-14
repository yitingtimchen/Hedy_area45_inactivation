from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DERIVED_AUDIO_DIR = ROOT / "data" / "derived" / "audio"
BLINDED_TABLES_DIR = ROOT / "results" / "blinded" / "tables"
FIGURES_DIR = ROOT / "results" / "blinded" / "figures"

TRACE_COLOR = "#4C566A"
MASK_COLOR = "#C0392B"
THRESH_COLOR = "#7D3C98"
FULL_COLOR = "#9FB3C8"
MASKED_COLOR = "#1F4AA8"
DELTA_COLOR = "#111111"


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    features = pd.read_csv(DERIVED_AUDIO_DIR / "blinded_audio_features_1s_labeled.csv", dtype={"session_id": str})
    decision = pd.read_csv(BLINDED_TABLES_DIR / "blinded_decision_table.csv", dtype={"session_id": str}).sort_values("session_id")

    plot_loudness_trace_gallery(features, decision["session_id"].tolist())
    plot_loudness_distribution_gallery(features, decision["session_id"].tolist())
    plot_endpoint_pairs(decision)
    plot_mask_delta_summary(decision)


def plot_loudness_trace_gallery(features: pd.DataFrame, sessions: list[str]) -> None:
    fig, axes = plt.subplots(4, 4, figsize=(13.0, 10.0), sharex=True, sharey=True)
    axes = axes.ravel()

    y_min = float(features["rms_dbfs"].min())
    y_max = float(features["rms_dbfs"].max())
    y_pad = 1.5

    for ax, session_id in zip(axes, sessions):
        sub = features[features["session_id"] == session_id].sort_values("elapsed_mid_min").copy()
        x = sub["elapsed_mid_min"].to_numpy()
        y = sub["rms_dbfs"].to_numpy()
        threshold = float(sub["session_rms_dbfs_p90"].iloc[0])
        masked = sub["rms_dbfs"] >= threshold

        ax.plot(x, y, color=TRACE_COLOR, linewidth=0.8, alpha=0.85)
        if masked.any():
            ax.scatter(
                sub.loc[masked, "elapsed_mid_min"],
                sub.loc[masked, "rms_dbfs"],
                s=4,
                color=MASK_COLOR,
                alpha=0.85,
                rasterized=True,
            )
        ax.axhline(threshold, color=THRESH_COLOR, linewidth=1.0, linestyle="--")
        ax.set_title(session_id, fontsize=9, loc="left")
        ax.set_ylim(y_min - y_pad, y_max + y_pad)
        style_axis(ax)

    for ax in axes[len(sessions):]:
        ax.axis("off")

    fig.supxlabel("Minutes from trimmed pairing start")
    fig.supylabel("RMS (dBFS)")
    fig.suptitle("Audio mask QC: loudness traces and masked bins", fontsize=12, x=0.06, ha="left")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "blinded_audio_mask_trace_gallery.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_loudness_distribution_gallery(features: pd.DataFrame, sessions: list[str]) -> None:
    fig, axes = plt.subplots(4, 4, figsize=(13.0, 10.0), sharex=True, sharey=True)
    axes = axes.ravel()

    x_min = float(features["rms_dbfs"].min())
    x_max = float(features["rms_dbfs"].max())
    bins = np.linspace(x_min, x_max, 36)

    for ax, session_id in zip(axes, sessions):
        sub = features[features["session_id"] == session_id].copy()
        threshold = float(sub["session_rms_dbfs_p90"].iloc[0])
        ax.hist(sub["rms_dbfs"], bins=bins, color=FULL_COLOR, alpha=0.9, edgecolor="white", linewidth=0.35)
        ax.axvline(threshold, color=THRESH_COLOR, linewidth=1.0, linestyle="--")
        ax.axvspan(threshold, x_max, color=MASK_COLOR, alpha=0.12)
        ax.set_title(session_id, fontsize=9, loc="left")
        style_axis(ax)

    for ax in axes[len(sessions):]:
        ax.axis("off")

    fig.supxlabel("RMS (dBFS)")
    fig.supylabel("1 s bins")
    fig.suptitle("Audio mask QC: per-session loudness distributions", fontsize=12, x=0.06, ha="left")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "blinded_audio_mask_distribution_gallery.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_endpoint_pairs(decision: pd.DataFrame) -> None:
    metric_specs = [
        (
            "groom_duration_net_receive_minus_give_pct_session",
            "groom_duration_net_receive_minus_give_pct_quiet_masked_p90",
            "Net grooming\n(receive - give, % session)",
        ),
        (
            "groom_duration_reciprocity_0to1",
            "groom_duration_reciprocity_0to1_quiet_masked_p90",
            "Groom reciprocity\n(0 to 1)",
        ),
        (
            "groom_total_pct_session",
            "groom_total_pct_quiet_masked_p90",
            "Grooming\n(% session)",
        ),
        (
            "attention_to_outside_agents_resolved_pct_session",
            "attention_outside_pct_quiet_masked_p90",
            "Attention outside\n(% session)",
        ),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(9.2, 7.0))
    axes = axes.ravel()

    for ax, (full_col, masked_col, label) in zip(axes, metric_specs):
        full = decision[full_col].to_numpy(dtype=float)
        masked = decision[masked_col].to_numpy(dtype=float)
        x_positions = np.array([0, 1])

        for f, m in zip(full, masked):
            ax.plot(x_positions, [f, m], color="#B0B0B0", linewidth=1.0, alpha=0.9, zorder=1)
            ax.scatter([0], [f], color=FULL_COLOR, s=28, zorder=2)
            ax.scatter([1], [m], color=MASKED_COLOR, s=28, zorder=2)

        ax.set_xticks([0, 1], ["Full\ntrimmed", "Quiet-masked\np90"])
        ax.set_ylabel(label)
        style_axis(ax)

    fig.suptitle("Audio mask sensitivity: paired session-level endpoints", fontsize=12, x=0.06, ha="left")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "blinded_audio_mask_endpoint_pairs.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_mask_delta_summary(decision: pd.DataFrame) -> None:
    delta_specs = [
        ("groom_duration_net_receive_minus_give_pct_delta_quiet_minus_full", "Net grooming\n(% session)"),
        ("groom_duration_reciprocity_0to1_delta_quiet_minus_full", "Groom reciprocity"),
        ("groom_total_pct_quiet_masked_p90", None),
        ("social_engaged_pct_delta_quiet_minus_full", "Social engaged\n(% session)"),
        ("attention_outside_pct_delta_quiet_minus_full", "Attention outside\n(% session)"),
        ("hiccups_pct_delta_quiet_minus_full", "Hiccups\n(% session)"),
    ]

    rows: list[dict[str, float | str]] = []
    for delta_col, label in delta_specs:
        if delta_col == "groom_total_pct_quiet_masked_p90":
            values = (
                decision["groom_total_pct_quiet_masked_p90"].to_numpy(dtype=float)
                - decision["groom_total_pct_session"].to_numpy(dtype=float)
            )
            label = "Groom total\n(% session)"
        else:
            values = decision[delta_col].to_numpy(dtype=float)
        for value in values:
            rows.append({"metric": label, "delta": value})
    plot_df = pd.DataFrame(rows)

    metric_order = [
        "Net grooming\n(% session)",
        "Groom reciprocity",
        "Groom total\n(% session)",
        "Social engaged\n(% session)",
        "Attention outside\n(% session)",
        "Hiccups\n(% session)",
    ]

    rng = np.random.default_rng(12)
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    for idx, metric in enumerate(metric_order):
        values = plot_df.loc[plot_df["metric"] == metric, "delta"].to_numpy(dtype=float)
        jitter = rng.uniform(-0.09, 0.09, size=len(values))
        ax.scatter(values, np.full(len(values), idx) + jitter, s=26, color=DELTA_COLOR, alpha=0.9)
        mean_value = float(np.mean(values))
        ax.plot([mean_value, mean_value], [idx - 0.18, idx + 0.18], color=MASKED_COLOR, linewidth=2.8)

    ax.axvline(0, color="#7F7F7F", linewidth=1.0, linestyle="--")
    ax.set_yticks(range(len(metric_order)), metric_order)
    ax.set_xlabel("Quiet-masked minus full trimmed")
    ax.set_title("Audio mask sensitivity: change after masking", fontsize=12, loc="left")
    style_axis(ax)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "blinded_audio_mask_delta_summary.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def style_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.tick_params(length=3.5, width=0.8)


if __name__ == "__main__":
    main()

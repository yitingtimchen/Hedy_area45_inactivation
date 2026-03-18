from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
UNBLINDED_ROOT = ROOT / "results" / "unblinded"
OUT_DIR = ROOT / "results" / "slides" / "assets"

VEHICLE_COLOR = "#A9B7C9"
DCZ_COLOR = "#1F4AA8"
TEXT_COLOR = "#111111"
REF_COLOR = "#8A8A8A"
TREND_COLOR = "#333333"
BG_COLOR = "#FFFFFF"


plt.rcParams.update(
    {
        "font.size": 16,
        "axes.titlesize": 18,
        "axes.labelsize": 18,
        "xtick.labelsize": 16,
        "ytick.labelsize": 16,
        "font.family": "DejaVu Sans",
    }
)


def style_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.2)
    ax.spines["bottom"].set_linewidth(1.2)
    ax.tick_params(length=4, width=1.0)
    ax.set_facecolor(BG_COLOR)


def condition_stripplot(
    ax: plt.Axes,
    vehicle: np.ndarray,
    dcz: np.ndarray,
    ylabel: str,
    p_text: str,
    note_text: str | None = None,
    zero_line: bool = False,
    ylim: tuple[float, float] | None = None,
) -> None:
    rng = np.random.default_rng(4)
    veh_jitter = rng.uniform(-0.07, 0.07, size=len(vehicle))
    dcz_jitter = rng.uniform(-0.07, 0.07, size=len(dcz))

    ax.scatter(np.full(len(vehicle), 0.0) + veh_jitter, vehicle, color=VEHICLE_COLOR, s=140, zorder=3)
    ax.scatter(np.full(len(dcz), 1.0) + dcz_jitter, dcz, color=DCZ_COLOR, s=140, zorder=3)

    for x, values, color in [(0.0, vehicle, VEHICLE_COLOR), (1.0, dcz, DCZ_COLOR)]:
        mean_value = float(np.mean(values))
        ax.plot([x - 0.22, x + 0.22], [mean_value, mean_value], color=color, linewidth=4.0, zorder=4)

    if zero_line:
        ax.axhline(0, color=REF_COLOR, linewidth=1.5, linestyle="--", zorder=1)

    ax.set_xticks([0, 1], ["Vehicle", "DCZ"])
    ax.set_ylabel(ylabel)
    if ylim is not None:
        ax.set_ylim(*ylim)

    ax.text(0.03, 0.97, p_text, transform=ax.transAxes, ha="left", va="top", fontsize=16, color=TEXT_COLOR)
    if note_text:
        ax.text(0.97, 0.05, note_text, transform=ax.transAxes, ha="right", va="bottom", fontsize=14, color="#555555")
    style_axis(ax)


def get_p(stats: pd.DataFrame, metric: str) -> float:
    return float(stats.loc[stats["metric"] == metric, "exact_permutation_p_two_sided"].iloc[0])


def read_metric_arrays(df: pd.DataFrame, metric: str) -> tuple[np.ndarray, np.ndarray]:
    vehicle = pd.to_numeric(df.loc[df["condition"] == "vehicle", metric], errors="coerce").dropna().to_numpy(dtype=float)
    dcz = pd.to_numeric(df.loc[df["condition"] == "DCZ", metric], errors="coerce").dropna().to_numpy(dtype=float)
    return vehicle, dcz


def plot_primary_single_metric(
    decision: pd.DataFrame,
    stats: pd.DataFrame,
    metric: str,
    ylabel: str,
    p_fmt: str,
    out_name: str,
    note_text: str | None = None,
    zero_line: bool = False,
    ylim: tuple[float, float] | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    vehicle, dcz = read_metric_arrays(decision, metric)
    condition_stripplot(
        ax,
        vehicle,
        dcz,
        ylabel,
        f"Exact permutation p = {get_p(stats, metric):{p_fmt}}",
        note_text=note_text,
        zero_line=zero_line,
        ylim=ylim,
    )
    fig.tight_layout()
    fig.savefig(OUT_DIR / out_name, dpi=260, bbox_inches="tight")
    plt.close(fig)


def robustness_rows() -> list[dict[str, object]]:
    variants = [
        (
            "Full",
            UNBLINDED_ROOT / "full" / "tables" / "condition_comparison_primary.csv",
            {
                "groom_duration_net_receive_minus_give_pct_session": "groom_duration_net_receive_minus_give_pct_session",
                "groom_duration_reciprocity_0to1": "groom_duration_reciprocity_0to1",
            },
        ),
        (
            "Quiet mask",
            UNBLINDED_ROOT / "quiet_mask" / "tables" / "condition_comparison_primary.csv",
            {
                "groom_duration_net_receive_minus_give_pct_session": "groom_duration_net_receive_minus_give_pct_session",
                "groom_duration_reciprocity_0to1": "groom_duration_reciprocity_0to1",
            },
        ),
        (
            "Exclude vet",
            UNBLINDED_ROOT / "exclude_vet_entry" / "tables" / "condition_comparison_primary.csv",
            {
                "groom_duration_net_receive_minus_give_pct_session": "groom_duration_net_receive_minus_give_pct_session",
                "groom_duration_reciprocity_0to1": "groom_duration_reciprocity_0to1",
            },
        ),
        (
            "Exclude vet + quiet mask",
            UNBLINDED_ROOT / "exclude_vet_entry" / "tables" / "condition_comparison_quiet_mask_sensitivity.csv",
            {
                "groom_duration_net_receive_minus_give_pct_session": "groom_duration_net_receive_minus_give_pct_quiet_masked_p90",
                "groom_duration_reciprocity_0to1": "groom_duration_reciprocity_0to1_quiet_masked_p90",
            },
        ),
    ]

    rows: list[dict[str, object]] = []
    for label, csv_path, metric_map in variants:
        df = pd.read_csv(csv_path)
        for canonical_metric, csv_metric in metric_map.items():
            row = df.loc[df["metric"] == csv_metric].iloc[0]
            rows.append(
                {
                    "variant": label,
                    "metric": canonical_metric,
                    "effect": float(row["mean_diff_DCZ_minus_vehicle"]),
                    "ci_low": float(row["bootstrap_ci95_low"]),
                    "ci_high": float(row["bootstrap_ci95_high"]),
                    "p_value": float(row["exact_permutation_p_two_sided"]),
                }
            )
    return rows


def plot_robustness_summary() -> None:
    rows = pd.DataFrame(robustness_rows())
    metric_specs = [
        (
            "groom_duration_net_receive_minus_give_pct_session",
            "DCZ - Vehicle difference\nin net groom duration (% session)",
        ),
        (
            "groom_duration_reciprocity_0to1",
            "DCZ - Vehicle difference\nin grooming reciprocity",
        ),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(13.6, 6.2))
    order = ["Full", "Quiet mask", "Exclude vet", "Exclude vet + quiet mask"]
    x_positions = np.arange(len(order))

    for ax, (metric, xlabel) in zip(axes, metric_specs):
        sub = rows.loc[rows["metric"] == metric].copy()
        sub = sub.set_index("variant").loc[order].reset_index()

        ax.axhline(0, color=REF_COLOR, linestyle="--", linewidth=1.5, zorder=1)
        y_min = float(sub["ci_low"].min())
        y_max = float(sub["ci_high"].max())
        y_span = y_max - y_min

        for x, (_, row) in zip(x_positions, sub.iterrows()):
            ax.vlines(x, row["ci_low"], row["ci_high"], color=DCZ_COLOR, linewidth=4, zorder=2)
            ax.scatter(x, row["effect"], s=140, color=DCZ_COLOR, zorder=3)
            ax.text(
                x,
                row["ci_high"] + 0.07 * y_span,
                f"p = {row['p_value']:.4f}",
                va="bottom",
                ha="center",
                fontsize=14,
                color=TEXT_COLOR,
            )

        ax.set_xticks(x_positions, ["Full", "Quiet mask", "Exclude vet", "Exclude vet\n+ quiet mask"])
        ax.set_ylabel(xlabel)
        ax.set_xlim(-0.6, len(order) - 0.4)
        ax.set_ylim(y_min - 0.1 * y_span, y_max + 0.2 * y_span)
        style_axis(ax)

    fig.tight_layout(w_pad=2.6)
    fig.savefig(OUT_DIR / "presentation_primary_robustness.png", dpi=260, bbox_inches="tight")
    plt.close(fig)


def plot_secondary_outcomes(decision: pd.DataFrame, secondary_stats: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.2))

    vehicle, dcz = read_metric_arrays(decision, "groom_total_pct_session")
    condition_stripplot(
        axes[0],
        vehicle,
        dcz,
        "Total groom duration\n(% of session)",
        f"Exact permutation p = {get_p(secondary_stats, 'groom_total_pct_session'):.4f}",
    )

    vehicle, dcz = read_metric_arrays(decision, "social_engaged_pct_session")
    condition_stripplot(
        axes[1],
        vehicle,
        dcz,
        "Social engagement\n(% of session)",
        f"Exact permutation p = {get_p(secondary_stats, 'social_engaged_pct_session'):.4f}",
    )

    fig.tight_layout()
    fig.savefig(OUT_DIR / "presentation_secondary_outcomes.png", dpi=260, bbox_inches="tight")
    plt.close(fig)


def plot_temporal_dependence(decision: pd.DataFrame, temporal_summary: pd.DataFrame) -> None:
    ordered = decision.sort_values("session_index").copy()

    specs = [
        (
            "groom_duration_net_receive_minus_give_pct_session",
            "Net groom duration\n(% of session; received - given)",
            float(
                temporal_summary.loc[
                    temporal_summary["metric"] == "groom_duration_net_receive_minus_give_pct_session",
                    "vehicle_slope_permutation_p_two_sided",
                ].iloc[0]
            ),
            float(
                temporal_summary.loc[
                    temporal_summary["metric"] == "groom_duration_net_receive_minus_give_pct_session",
                    "dcz_slope_permutation_p_two_sided",
                ].iloc[0]
            ),
            True,
            None,
        ),
        (
            "groom_duration_reciprocity_0to1",
            "Grooming reciprocity\n(0 to 1)",
            float(
                temporal_summary.loc[
                    temporal_summary["metric"] == "groom_duration_reciprocity_0to1",
                    "vehicle_slope_permutation_p_two_sided",
                ].iloc[0]
            ),
            float(
                temporal_summary.loc[
                    temporal_summary["metric"] == "groom_duration_reciprocity_0to1",
                    "dcz_slope_permutation_p_two_sided",
                ].iloc[0]
            ),
            False,
            (0, 1.05),
        ),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.8))
    for ax, (metric, ylabel, p_vehicle, p_dcz, zero_line, ylim) in zip(axes, specs):
        vehicle = ordered.loc[ordered["condition"] == "vehicle"]
        dcz = ordered.loc[ordered["condition"] == "DCZ"]

        vehicle_scatter = ax.scatter(
            vehicle["session_index"],
            vehicle[metric],
            color=VEHICLE_COLOR,
            edgecolor="#7A8796",
            linewidth=0.9,
            marker="o",
            s=130,
            zorder=3,
            label="Vehicle (n = 8)",
        )
        dcz_scatter = ax.scatter(
            dcz["session_index"],
            dcz[metric],
            color=DCZ_COLOR,
            edgecolor="#17356F",
            linewidth=0.9,
            marker="s",
            s=125,
            zorder=3,
            label="DCZ (n = 8)",
        )
        for sub, color in [(vehicle, VEHICLE_COLOR), (dcz, DCZ_COLOR)]:
            x = sub["session_index"].to_numpy(dtype=float)
            y = sub[metric].to_numpy(dtype=float)
            coef = np.polyfit(x, y, deg=1)
            x_line = np.linspace(x.min(), x.max(), 200)
            y_line = np.polyval(coef, x_line)
            ax.plot(x_line, y_line, color=color, linestyle="--", linewidth=2.2, zorder=2)

        if zero_line:
            ax.axhline(0, color=REF_COLOR, linestyle=":", linewidth=1.4, zorder=1)
        if ylim is not None:
            ax.set_ylim(*ylim)
        elif metric == "groom_duration_net_receive_minus_give_pct_session":
            ax.set_ylim(-50, 20)

        ax.set_xlabel("Session order")
        ax.set_ylabel(ylabel)
        ax.set_xticks([4, 8, 12, 16])
        ax.text(
            0.03,
            0.97,
            f"Vehicle slope p = {p_vehicle:.4f}\nDCZ slope p = {p_dcz:.4f}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=15,
            color=TEXT_COLOR,
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "none", "alpha": 0},
        )
        style_axis(ax)

    axes[1].legend(
        handles=[vehicle_scatter, dcz_scatter],
        labels=["Vehicle (n = 8)", "DCZ (n = 8)"],
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
        ncol=2,
        fontsize=15,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(OUT_DIR / "presentation_temporal_dependence.png", dpi=260, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    decision = pd.read_csv(UNBLINDED_ROOT / "full" / "tables" / "unblinded_decision_table.csv", dtype={"session_id": str})
    primary_stats = pd.read_csv(UNBLINDED_ROOT / "full" / "tables" / "condition_comparison_primary.csv")
    secondary_stats = pd.read_csv(UNBLINDED_ROOT / "full" / "tables" / "condition_comparison_secondary.csv")
    temporal_summary = pd.read_csv(UNBLINDED_ROOT / "full" / "tables" / "temporal_dependence_summary.csv")

    plot_primary_single_metric(
        decision,
        primary_stats,
        "groom_duration_net_receive_minus_give_pct_session",
        "Net groom duration\n(% of session; received - given)",
        ".4f",
        "presentation_primary_net_grooming.png",
        note_text="0 = balanced",
        zero_line=True,
    )
    plot_primary_single_metric(
        decision,
        primary_stats,
        "groom_duration_reciprocity_0to1",
        "Grooming reciprocity\n(0 to 1)",
        ".4f",
        "presentation_primary_reciprocity.png",
        note_text="1 = perfectly reciprocal",
        ylim=(0, 1.05),
    )
    plot_secondary_outcomes(decision, secondary_stats)
    plot_robustness_summary()
    plot_temporal_dependence(decision, temporal_summary)


if __name__ == "__main__":
    main()

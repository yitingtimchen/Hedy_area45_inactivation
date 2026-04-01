from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
from matplotlib.patches import Patch
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
INTERVALS_DIR = ROOT / "data" / "derived" / "behavior" / "cleaned_intervals"
BLINDED_TABLES_DIR = ROOT / "results" / "blinded" / "tables"
BORIS_ETHOGRAM_PATH = ROOT / "data" / "raw" / "ethogram" / "Hedy_area45_inactivation.boris"
RESULTS_ROOT = ROOT / "results" / "blinded" / "session_qc"
DOCS_ROOT = ROOT / "docs" / "blinded" / "session_qc"
FIGURES_DIR = RESULTS_ROOT / "figures"
TABLES_DIR = RESULTS_ROOT / "tables"


UNSCORED_BRIDGE_S = 3.0
FAMILY_ORDER = [
    "affiliative",
    "aggressive",
    "sexual",
    "feeding",
    "locomotion",
    "attention",
    "maintenance",
    "atypical",
    "unscored",
]
FAMILY_COLORS = {
    "affiliative": "#6BAED6",
    "aggressive": "#E15759",
    "sexual": "#EDC948",
    "feeding": "#59A14F",
    "locomotion": "#F28E2B",
    "attention": "#9C755F",
    "maintenance": "#76B7B2",
    "atypical": "#B07AA1",
    "unscored": "#D7D7D7",
}
STREAM_SPECS = [
    ("social_state", "Social"),
    ("activity_state", "Activity"),
    ("attention_state", "Attention"),
    ("atypical_state", "Atypical"),
]
CATEGORY_TO_FAMILY = {
    "Affiliative": "affiliative",
    "Aggression": "aggressive",
    "Sexual": "sexual",
    "Feeding": "feeding",
    "Locomotion": "locomotion",
    "Attention": "attention",
    "Maintenance": "maintenance",
    "Atypical": "atypical",
    "Other": "atypical",
    "Unscored": "unscored",
}


def ensure_dirs() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)


def style_axis(ax: plt.Axes, tick_size: float = 9) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="x", labelsize=tick_size)


def load_behavior_category_map() -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for path in sorted(INTERVALS_DIR.glob("*_behavior_intervals.csv")):
        df = pd.read_csv(path, usecols=["behavior", "category"])
        rows.append(df.dropna(subset=["behavior"]).drop_duplicates())
    if not rows:
        return pd.DataFrame(columns=["behavior", "category"])
    return (
        pd.concat(rows, ignore_index=True)
        .drop_duplicates()
        .sort_values(["category", "behavior"])
        .reset_index(drop=True)
    )


def behavior_category_lookup(category_map: pd.DataFrame) -> dict[str, str]:
    lookup = dict(zip(category_map["behavior"], category_map["category"]))
    lookup["Unscored"] = "Unscored"
    return lookup


def assign_primary_behavior(row: pd.Series) -> tuple[str, str]:
    if pd.notna(row["social_state"]) and str(row["social_state"]) != "":
        return str(row["social_state"]), "social"
    if pd.notna(row["activity_state"]) and str(row["activity_state"]) != "":
        return str(row["activity_state"]), "activity"
    if pd.notna(row["attention_state"]) and str(row["attention_state"]) != "":
        return str(row["attention_state"]), "attention"
    if pd.notna(row["atypical_state"]) and str(row["atypical_state"]) != "":
        return str(row["atypical_state"]), "atypical"
    return "Unscored", "unscored"


def collapse_primary_timeline(timeline: pd.DataFrame, category_lookup: dict[str, str]) -> pd.DataFrame:
    tl = timeline.copy()
    assigned = tl.apply(assign_primary_behavior, axis=1, result_type="expand")
    tl["behavior"] = assigned[0]
    tl["layer"] = assigned[1]
    tl["category"] = tl["behavior"].map(category_lookup).fillna("Other")
    tl["family"] = tl["category"].map(CATEGORY_TO_FAMILY).fillna("atypical")

    rows: list[dict[str, object]] = []
    current = tl.iloc[0].to_dict()
    for row in tl.iloc[1:].to_dict("records"):
        contiguous = abs(float(current["end_s"]) - float(row["start_s"])) < 1e-9
        if contiguous and current["behavior"] == row["behavior"]:
            current["end_s"] = row["end_s"]
            current["duration_s"] = float(current["end_s"]) - float(current["start_s"])
        else:
            rows.append(
                {
                    "start_s": float(current["start_s"]),
                    "end_s": float(current["end_s"]),
                    "duration_s": float(current["duration_s"]),
                    "behavior": str(current["behavior"]),
                    "layer": str(current["layer"]),
                    "category": str(current["category"]),
                    "family": str(current["family"]),
                }
            )
            current = row.copy()
    rows.append(
        {
            "start_s": float(current["start_s"]),
            "end_s": float(current["end_s"]),
            "duration_s": float(current["duration_s"]),
            "behavior": str(current["behavior"]),
            "layer": str(current["layer"]),
            "category": str(current["category"]),
            "family": str(current["family"]),
        }
    )
    return pd.DataFrame(rows)


def bridge_unscored_gaps(primary: pd.DataFrame, state_col: str, max_gap_s: float = UNSCORED_BRIDGE_S) -> pd.DataFrame:
    if primary.empty:
        return primary.copy()

    kept = primary[~((primary[state_col] == "Unscored") & (primary["duration_s"] <= max_gap_s))].copy().reset_index(drop=True)
    if kept.empty:
        return kept

    rows: list[dict[str, object]] = []
    current = kept.iloc[0].to_dict()
    for row in kept.iloc[1:].to_dict("records"):
        gap = float(row["start_s"]) - float(current["end_s"])
        if current[state_col] == row[state_col] and gap <= max_gap_s:
            current["end_s"] = row["end_s"]
            current["duration_s"] = float(current["end_s"]) - float(current["start_s"])
        else:
            rows.append(current.copy())
            current = row.copy()
    rows.append(current.copy())
    return pd.DataFrame(rows)


def build_family_timeline(primary: pd.DataFrame) -> pd.DataFrame:
    family_timeline = primary.loc[:, ["start_s", "end_s", "duration_s", "family"]].copy()
    if family_timeline.empty:
        return family_timeline
    rows: list[dict[str, object]] = []
    current = family_timeline.iloc[0].to_dict()
    for row in family_timeline.iloc[1:].to_dict("records"):
        contiguous = abs(float(current["end_s"]) - float(row["start_s"])) < 1e-9
        if contiguous and current["family"] == row["family"]:
            current["end_s"] = row["end_s"]
            current["duration_s"] = float(current["end_s"]) - float(current["start_s"])
        else:
            rows.append(current.copy())
            current = row.copy()
    rows.append(current.copy())
    return pd.DataFrame(rows)


def count_transitions(stream: pd.DataFrame, state_col: str) -> int:
    if stream.empty:
        return 0
    values = stream[state_col].astype(str).tolist()
    return sum(source != target for source, target in zip(values[:-1], values[1:]))


def summarize_session(session_id: str, category_lookup: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    timeline = pd.read_csv(INTERVALS_DIR / f"{session_id}_layered_timeline.csv")
    primary = collapse_primary_timeline(timeline, category_lookup)
    family_timeline = build_family_timeline(primary)
    session_duration_s = float(primary["duration_s"].sum())

    detailed_summary = (
        primary.groupby(["behavior", "category", "layer"], as_index=False)["duration_s"]
        .sum()
        .assign(
            session_id=session_id,
            pct_session=lambda df: np.where(session_duration_s > 0, 100.0 * df["duration_s"] / session_duration_s, np.nan),
            session_duration_s=session_duration_s,
        )
        .loc[:, ["session_id", "behavior", "category", "layer", "duration_s", "pct_session", "session_duration_s"]]
        .sort_values(["category", "behavior"])
        .reset_index(drop=True)
    )

    family_summary = (
        primary.groupby(["family"], as_index=False)["duration_s"]
        .sum()
        .assign(
            session_id=session_id,
            pct_session=lambda df: np.where(session_duration_s > 0, 100.0 * df["duration_s"] / session_duration_s, np.nan),
            session_duration_s=session_duration_s,
        )
        .loc[:, ["session_id", "family", "duration_s", "pct_session", "session_duration_s"]]
        .sort_values("family")
        .reset_index(drop=True)
    )

    primary_stream = bridge_unscored_gaps(primary.loc[:, ["start_s", "end_s", "duration_s", "behavior"]], "behavior")
    family_stream = bridge_unscored_gaps(build_family_timeline(primary), "family")

    metrics = {
        "session_id": session_id,
        "session_duration_s": session_duration_s,
        "resolved_state_transitions": count_transitions(primary_stream, "behavior"),
        "family_level_transitions": count_transitions(family_stream, "family"),
    }
    for family in FAMILY_ORDER:
        pct = family_summary.loc[family_summary["family"] == family, "pct_session"]
        metrics[f"{family}_pct_session"] = float(pct.iloc[0]) if not pct.empty else 0.0

    return primary, detailed_summary, family_summary, metrics


def behavior_color_map(behaviors: list[str], category_lookup: dict[str, str]) -> dict[str, str]:
    if BORIS_ETHOGRAM_PATH.exists():
        payload = json.loads(BORIS_ETHOGRAM_PATH.read_text(encoding="utf-8"))
        color_lookup = {
            str(row["code"]): str(row["color"])
            for row in payload.get("behaviors_conf", {}).values()
            if row.get("code") and row.get("color")
        }
        color_lookup["Unscored"] = FAMILY_COLORS["unscored"]
        return color_lookup

    cmap = plt.get_cmap("tab20")
    non_unscored = [behavior for behavior in behaviors if behavior != "Unscored"]
    colors = {
        behavior: mcolors.to_hex(cmap(idx % cmap.N))
        for idx, behavior in enumerate(non_unscored)
    }
    colors["Unscored"] = FAMILY_COLORS["unscored"]
    return colors


def clip_to_window(df: pd.DataFrame, start_s: float, end_s: float) -> pd.DataFrame:
    clipped = df.loc[(df["end_s"] > start_s) & (df["start_s"] < end_s)].copy()
    if clipped.empty:
        return clipped
    clipped["plot_start_s"] = clipped["start_s"].clip(lower=start_s) - start_s
    clipped["plot_end_s"] = clipped["end_s"].clip(upper=end_s) - start_s
    clipped["plot_duration_s"] = clipped["plot_end_s"] - clipped["plot_start_s"]
    return clipped.loc[clipped["plot_duration_s"] > 0].reset_index(drop=True)


def build_parallel_streams(timeline: pd.DataFrame) -> dict[str, pd.DataFrame]:
    streams: dict[str, pd.DataFrame] = {}
    for state_col, _label in STREAM_SPECS:
        sub = timeline.loc[
            timeline[state_col].notna() & (timeline[state_col].astype(str) != ""),
            ["start_s", "end_s", "duration_s", state_col],
        ].copy()
        if sub.empty:
            streams[state_col] = pd.DataFrame(columns=["start_s", "end_s", "duration_s", state_col])
            continue

        rows: list[dict[str, object]] = []
        current = sub.iloc[0].to_dict()
        for row in sub.iloc[1:].to_dict("records"):
            contiguous = abs(float(current["end_s"]) - float(row["start_s"])) < 1e-9
            if contiguous and current[state_col] == row[state_col]:
                current["end_s"] = row["end_s"]
                current["duration_s"] = float(current["end_s"]) - float(current["start_s"])
            else:
                rows.append(current.copy())
                current = row.copy()
        rows.append(current.copy())
        streams[state_col] = pd.DataFrame(rows)
    return streams


def summarize_parallel_metrics(timeline: pd.DataFrame, session_duration_s: float) -> dict[str, float]:
    parallel_streams = build_parallel_streams(timeline)
    metrics: dict[str, float] = {}
    for state_col, label in STREAM_SPECS:
        metric_prefix = f"{label.lower()}_stream"
        active = timeline[state_col].notna() & (timeline[state_col].astype(str) != "")
        metrics[f"{metric_prefix}_pct_session"] = 100.0 * float(timeline.loc[active, "duration_s"].sum()) / session_duration_s if session_duration_s > 0 else np.nan
        metrics[f"{metric_prefix}_transitions"] = count_transitions(parallel_streams[state_col], state_col)
    metrics["unscored_pct_session"] = (
        100.0
        * float(
            timeline.loc[
                timeline[["social_state", "activity_state", "attention_state", "atypical_state"]].isna().all(axis=1),
                "duration_s",
            ].sum()
        )
        / session_duration_s
        if session_duration_s > 0
        else np.nan
    )
    return metrics


def draw_ethogram(ax: plt.Axes, df: pd.DataFrame, state_col: str, color_lookup: dict[str, str], title: str, duration_s: float) -> None:
    for row in df.itertuples(index=False):
        ax.broken_barh(
            [(float(row.plot_start_s), float(row.plot_duration_s))],
            (0, 1),
            facecolors=color_lookup.get(str(getattr(row, state_col)), "#999999"),
            edgecolors="none",
        )
    ax.set_ylim(0, 1)
    ax.set_xlim(0, duration_s if duration_s > 0 else 1.0)
    ax.set_yticks([])
    ax.set_title(title, loc="left", fontsize=11)
    style_axis(ax, tick_size=9)


def add_state_legend(ax: plt.Axes, states: list[str], color_lookup: dict[str, str]) -> None:
    if not states:
        return
    handles = [Patch(facecolor=color_lookup.get(state, "#999999"), label=state) for state in states]
    ax.legend(
        handles=handles,
        ncol=min(4, len(handles)),
        loc="upper center",
        bbox_to_anchor=(0.5, -0.26),
        frameon=False,
        fontsize=7,
        handlelength=1.0,
        columnspacing=0.8,
    )


def plot_session_ethogram(
    session_id: str,
    parallel_streams: dict[str, pd.DataFrame],
    family_timeline: pd.DataFrame,
    behavior_colors: dict[str, str],
    pairing_start_s: float,
    pairing_end_s: float,
) -> None:
    family_plot = clip_to_window(family_timeline, pairing_start_s, pairing_end_s)
    duration_s = max(pairing_end_s - pairing_start_s, 0.0)
    fig, axes = plt.subplots(5, 1, figsize=(12.0, 6.6), sharex=True, height_ratios=[1.0, 1.0, 1.0, 1.0, 0.9])
    for ax, (state_col, label) in zip(axes[:4], STREAM_SPECS):
        stream_plot = clip_to_window(parallel_streams[state_col], pairing_start_s, pairing_end_s)
        draw_ethogram(ax, stream_plot, state_col, behavior_colors, f"{label} stream", duration_s)
        ax.text(-0.01, 0.5, label, transform=ax.transAxes, ha="right", va="center", fontsize=9)
        observed_states = list(dict.fromkeys(stream_plot[state_col].astype(str).tolist()))
        add_state_legend(ax, observed_states, behavior_colors)
    axes[0].set_title(f"Session {session_id}: parallel ethogram streams", loc="left", fontsize=11)
    draw_ethogram(axes[4], family_plot, "family", FAMILY_COLORS, "Collapsed family trace", duration_s)
    axes[4].text(-0.01, 0.5, "Family", transform=axes[4].transAxes, ha="right", va="center", fontsize=9)
    family_states = [family for family in FAMILY_ORDER if family in set(family_plot["family"])]
    add_state_legend(axes[4], family_states, FAMILY_COLORS)
    axes[4].set_xlabel("Time since pairing start (s)", fontsize=10)
    fig.subplots_adjust(left=0.08, right=0.995, top=0.95, bottom=0.10, hspace=1.25)
    fig.savefig(FIGURES_DIR / f"{session_id}_ethogram_trace.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_family_gallery(family_timelines: dict[str, pd.DataFrame], qc_table: pd.DataFrame, pairing_windows: dict[str, tuple[float, float]]) -> None:
    session_ids = list(qc_table["session_id"].astype(str))
    fig_height = max(5.5, 0.48 * len(session_ids) + 1.8)
    fig, axes = plt.subplots(len(session_ids), 1, figsize=(12.5, fig_height), sharex=False)
    if len(session_ids) == 1:
        axes = [axes]
    for ax, session_id in zip(axes, session_ids):
        family_timeline = family_timelines[session_id]
        pairing_start_s, pairing_end_s = pairing_windows[session_id]
        family_plot = clip_to_window(family_timeline, pairing_start_s, pairing_end_s)
        duration_s = max(pairing_end_s - pairing_start_s, 0.0)
        draw_ethogram(ax, family_plot, "family", FAMILY_COLORS, "", duration_s)
        flag_count = int(qc_table.loc[qc_table["session_id"] == session_id, "n_review_flags"].iloc[0])
        label = f"{session_id} | flags {flag_count}"
        ax.text(-0.01, 0.5, label, transform=ax.transAxes, ha="right", va="center", fontsize=9)
        ax.set_title("")
    axes[0].set_title("Blinded all-session QC sheet: collapsed family ethograms", loc="left", fontsize=13)
    axes[-1].set_xlabel("Time since pairing start (s)", fontsize=10)
    handles = [Patch(facecolor=FAMILY_COLORS[family], label=family) for family in FAMILY_ORDER]
    fig.legend(handles=handles, ncol=5, loc="upper center", bbox_to_anchor=(0.5, 0.995), frameon=False, fontsize=9)
    fig.tight_layout(rect=(0.08, 0.03, 0.995, 0.96))
    fig.savefig(FIGURES_DIR / "blinded_session_family_qc_gallery.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_qc_flag_summary(qc_table: pd.DataFrame, thresholds: pd.DataFrame) -> None:
    metric_cols = [
        "unscored_pct_session",
        "social_stream_pct_session",
        "activity_stream_pct_session",
        "attention_stream_pct_session",
    ]
    metric_titles = {
        "unscored_pct_session": "Unscored",
        "social_stream_pct_session": "Social",
        "activity_stream_pct_session": "Activity",
        "attention_stream_pct_session": "Attention",
    }
    threshold_lookup = thresholds.set_index("metric").to_dict("index") if not thresholds.empty else {}

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.2))
    axes_flat = axes.ravel()
    x = np.arange(len(qc_table))
    flagged_sessions = qc_table.loc[qc_table["is_review_target"], "session_id"].astype(str).tolist()

    for ax, metric in zip(axes_flat, metric_cols):
        vals = pd.to_numeric(qc_table[metric], errors="coerce").to_numpy(dtype=float)
        ax.scatter(x, vals, s=42, color="#9AA5B1", alpha=0.9, zorder=2)
        flagged = qc_table["is_review_target"].to_numpy(dtype=bool)
        ax.scatter(x[flagged], vals[flagged], s=58, color="#C53A2F", zorder=3)
        if metric in threshold_lookup:
            upper = float(threshold_lookup[metric]["upper_bound"])
            lower = float(threshold_lookup[metric]["lower_bound"])
            ax.axhline(upper, color="#C53A2F", linestyle="--", linewidth=1.4, zorder=1)
            ax.axhline(lower, color="#C53A2F", linestyle=":", linewidth=1.0, zorder=1)
        for idx, row in qc_table.loc[qc_table["is_review_target"]].reset_index().iterrows():
            y = float(row[metric])
            ax.text(row["index"], y, str(row["session_id"]), fontsize=8, ha="left", va="bottom", color="#7F1D1D")
        ax.set_title(f"{metric_titles[metric]} occupancy QC", loc="left", fontsize=11)
        ax.set_ylabel("Percent of pairing window", fontsize=9)
        ax.set_xticks(x, qc_table["session_id"].astype(str), rotation=75, ha="right", fontsize=7)
        style_axis(ax, tick_size=8)

    fig.suptitle(
        f"Blinded QC occupancy flags ({len(flagged_sessions)} flagged session{'s' if len(flagged_sessions) != 1 else ''})",
        fontsize=13,
        x=0.06,
        ha="left",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95), h_pad=1.0, w_pad=1.0)
    fig.savefig(FIGURES_DIR / "blinded_session_qc_flag_summary.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def iqr_flag_table(qc_table: pd.DataFrame, metric_cols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    thresholds: list[dict[str, object]] = []
    flagged = qc_table.copy()
    stale_cols = [
        col
        for col in flagged.columns
        if col.endswith("_review_flag") or col.endswith("_review_reason") or col in {"review_flag_reasons", "n_review_flags", "is_review_target"}
    ]
    if stale_cols:
        flagged = flagged.drop(columns=stale_cols)
    review_cols: list[str] = []
    for metric in metric_cols:
        values = pd.to_numeric(flagged[metric], errors="coerce").dropna()
        if values.empty:
            continue
        q1 = float(values.quantile(0.25))
        q3 = float(values.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        flag_col = f"{metric}_review_flag"
        flagged[flag_col] = (pd.to_numeric(flagged[metric], errors="coerce") < lower) | (pd.to_numeric(flagged[metric], errors="coerce") > upper)
        review_cols.append(flag_col)
        thresholds.append(
            {
                "metric": metric,
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "lower_bound": lower,
                "upper_bound": upper,
                "n_flagged": int(flagged[flag_col].sum()),
            }
        )

    reason_cols = []
    for metric in metric_cols:
        flag_col = f"{metric}_review_flag"
        if flag_col not in flagged.columns:
            continue
        reason_col = f"{metric}_review_reason"
        metric_vals = pd.to_numeric(flagged[metric], errors="coerce")
        lower = float(next(row["lower_bound"] for row in thresholds if row["metric"] == metric))
        upper = float(next(row["upper_bound"] for row in thresholds if row["metric"] == metric))
        flagged[reason_col] = np.where(
            ~flagged[flag_col],
            "",
            np.where(metric_vals < lower, f"{metric} below blinded IQR bound", f"{metric} above blinded IQR bound"),
        )
        reason_cols.append(reason_col)

    flagged["review_flag_reasons"] = flagged[reason_cols].apply(lambda row: "; ".join([value for value in row if value]), axis=1) if reason_cols else ""
    flagged["n_review_flags"] = flagged[review_cols].sum(axis=1).astype(int) if review_cols else 0
    flagged["is_review_target"] = flagged["n_review_flags"] > 0
    return flagged, pd.DataFrame(thresholds)


def write_markdown(qc_table: pd.DataFrame, thresholds: pd.DataFrame) -> None:
    flagged = qc_table.loc[qc_table["is_review_target"]].copy()
    lines = [
        "# Blinded Session QC",
        "",
        "This blinded QC layer adds resolved-behavior ethogram traces, collapsed family traces, and rule-based review flags for session follow-up.",
        "",
        "## Outputs",
        "",
        "- Per-session detailed plus collapsed ethogram traces are saved under `results/blinded/session_qc/figures/`.",
        "- The quick-review gallery is `blinded_session_family_qc_gallery.png`.",
        "- Session composition tables are provided at both the resolved-label and collapsed-family levels.",
        "- Review flags are blinded IQR-rule targets for manual follow-up, not automatic exclusions.",
        "- The occupancy-flag summary figure is `blinded_session_qc_flag_summary.png` and labels flagged session IDs directly.",
        "",
        "## Family collapse",
        "",
        "- Families shown in the QC traces are `affiliative`, `aggressive`, `sexual`, `feeding`, `locomotion`, `attention`, `maintenance`, `atypical`, and `unscored`.",
        "- Source labels in the original `Other` category are grouped into `atypical` for this blinded QC collapse so every resolved second lands in a review family.",
        "",
        "## Flag basis",
        "",
        "- Flags are now based on the parallel annotation streams rather than the single precedence-resolved display stream.",
        "- Stream occupancy metrics used for QC are `social_stream_pct_session`, `activity_stream_pct_session`, `attention_stream_pct_session`, plus `unscored_pct_session`.",
        "- The atypical lane remains visible in the plots and tables, but it does not drive QC flags.",
        "- Transition metrics are excluded from QC because their construction is still exploratory.",
        "",
        "## Flag rules",
        "",
    ]
    for row in thresholds.itertuples(index=False):
        lines.append(
            f"- `{row.metric}` flagged outside blinded Tukey bounds `[ {row.lower_bound:.2f}, {row.upper_bound:.2f} ]`; `{row.n_flagged}` sessions flagged."
        )
    lines.extend(["", "## Review targets", ""])
    if flagged.empty:
        lines.append("- No sessions crossed the blinded outlier rules.")
    else:
        for row in flagged.itertuples(index=False):
            lines.append(f"- Session `{row.session_id}`: {row.review_flag_reasons}.")
    lines.append("")
    (DOCS_ROOT / "session_qc.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    session_summary = pd.read_csv(BLINDED_TABLES_DIR / "blinded_session_summary.csv", dtype={"session_id": str})
    session_summary = session_summary.sort_values("session_id").reset_index(drop=True)
    pairing_windows = {
        str(row.session_id): (float(row.marker_start_s), float(row.marker_end_s))
        for row in session_summary.itertuples(index=False)
    }
    category_lookup = behavior_category_lookup(load_behavior_category_map())
    behaviors = sorted(category_lookup)
    behavior_colors = behavior_color_map(behaviors, category_lookup)

    primary_rows: list[pd.DataFrame] = []
    detailed_rows: list[pd.DataFrame] = []
    family_rows: list[pd.DataFrame] = []
    qc_metrics: list[dict[str, object]] = []
    family_timelines: dict[str, pd.DataFrame] = {}

    for session_id in session_summary["session_id"].astype(str):
        primary, detailed_summary, family_summary, metrics = summarize_session(session_id, category_lookup)
        timeline = pd.read_csv(INTERVALS_DIR / f"{session_id}_layered_timeline.csv")
        parallel_streams = build_parallel_streams(timeline)
        parallel_metrics = summarize_parallel_metrics(timeline, float(metrics["session_duration_s"]))
        family_timeline = build_family_timeline(primary)
        primary_rows.append(primary.assign(session_id=session_id))
        detailed_rows.append(detailed_summary)
        family_rows.append(family_summary)
        qc_metrics.append({**metrics, **parallel_metrics})
        family_timelines[session_id] = family_timeline
        pairing_start_s, pairing_end_s = pairing_windows[session_id]
        plot_session_ethogram(session_id, parallel_streams, family_timeline, behavior_colors, pairing_start_s, pairing_end_s)

    primary_df = pd.concat(primary_rows, ignore_index=True)
    detailed_df = pd.concat(detailed_rows, ignore_index=True)
    family_df = pd.concat(family_rows, ignore_index=True)
    qc_metrics_df = pd.DataFrame(qc_metrics)

    merge_cols = [
        "session_id",
        "exception_flag",
        "exception_note",
        "has_exception_note",
        "exception_timestamp",
        "session_duration_min",
    ]
    qc_table = session_summary[merge_cols].merge(qc_metrics_df, on="session_id", how="left")
    metric_cols = [
        "unscored_pct_session",
        "social_stream_pct_session",
        "activity_stream_pct_session",
        "attention_stream_pct_session",
    ]
    qc_table, thresholds = iqr_flag_table(qc_table, metric_cols)
    qc_table = qc_table.sort_values(["is_review_target", "n_review_flags", "session_id"], ascending=[False, False, True]).reset_index(drop=True)

    primary_df.to_csv(TABLES_DIR / "blinded_session_qc_primary_timeline_segments.csv", index=False)
    detailed_df.to_csv(TABLES_DIR / "blinded_session_qc_detailed_composition_by_session.csv", index=False)
    family_df.to_csv(TABLES_DIR / "blinded_session_qc_family_composition_by_session.csv", index=False)
    qc_table.to_csv(TABLES_DIR / "blinded_session_qc_table.csv", index=False)
    thresholds.to_csv(TABLES_DIR / "blinded_session_qc_flag_thresholds.csv", index=False)

    plot_family_gallery(family_timelines, qc_table, pairing_windows)
    plot_qc_flag_summary(qc_table, thresholds)
    write_markdown(qc_table, thresholds)


if __name__ == "__main__":
    main()

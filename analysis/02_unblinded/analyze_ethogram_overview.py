from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import re
import sys
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PARENT = Path(__file__).resolve().parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from _plot_helpers import style_axis  # noqa: E402
from output_layout import docs_section_dir, results_figures_dir, results_tables_dir  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
INTERVALS_DIR = ROOT / "data" / "derived" / "behavior" / "cleaned_intervals"
KEY_PATH = ROOT / "data" / "raw" / "session_key" / "Sessions name encoding.xlsx"

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
VET_ENTRY_SESSION_ID = "596273"
UNSCORED_BRIDGE_S = 3.0
TOP_BEHAVIOR_COUNT = 14
TRANSITION_ANNOTATE_THRESHOLD = 0.20
TRANSITION_SUMMARY_MIN_COUNT = 5
TRANSITION_MIN_COUNT_FOR_GRAPH = 3
TRANSITION_TOP_EDGES_PER_SOURCE = 2

VEHICLE_COLOR = "#A9B7C9"
DCZ_COLOR = "#1F4AA8"
BASE_FONT_SIZE = 19.0
TITLE_FONT_SIZE = 23.0
CATEGORY_TICK_FONT_SIZE = 17.0
NODE_LABEL_FONT_SIZE = 17.0
EDGE_LABEL_FONT_SIZE = 14.0
CATEGORY_COLORS = {
    "Affiliative": "#6BAED6",
    "Aggression": "#E15759",
    "Attention": "#9C755F",
    "Atypical": "#B07AA1",
    "Feeding": "#59A14F",
    "Locomotion": "#F28E2B",
    "Maintenance": "#76B7B2",
    "Other": "#BAB0AC",
    "Sexual": "#EDC948",
    "Unscored": "#D7D7D7",
}
CATEGORY_ORDER = [
    "Affiliative",
    "Sexual",
    "Aggression",
    "Maintenance",
    "Feeding",
    "Locomotion",
    "Attention",
    "Other",
    "Atypical",
    "Unscored",
]
SOCIAL_LAYER = "social"
RESTFUL_BEHAVIORS = {"Rest/Stationary", "Vigilant/Scan"}
AGGRESSIVE_CATEGORIES = {"Aggression"}
AFFILIATIVE_SOCIAL_CATEGORIES = {"Affiliative", "Sexual"}


def load_xlsx_sheet_rows(path: Path) -> pd.DataFrame:
    with ZipFile(path) as zf:
        shared_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        shared = [
            "".join(t.text or "" for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))
            for si in shared_root.findall("a:si", NS)
        ]
        sheet_root = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))

    rows: list[dict[str, str]] = []
    for row in sheet_root.findall(".//a:sheetData/a:row", NS):
        cells: dict[str, str] = {}
        for cell in row.findall("a:c", NS):
            ref = cell.get("r", "")
            col = re.sub(r"\d+", "", ref)
            cell_type = cell.get("t")
            value_node = cell.find("a:v", NS)
            value = ""
            if value_node is not None:
                value = value_node.text or ""
                if cell_type == "s":
                    value = shared[int(value)]
            cells[col] = value
        if cells.get("A") and cells.get("B") and cells.get("D"):
            rows.append(cells)
    return pd.DataFrame(rows)


def load_unblinding_map() -> pd.DataFrame:
    raw = load_xlsx_sheet_rows(KEY_PATH)
    mapping = raw.assign(
        session_id=raw["D"].str.extract(r"(\d+)_"),
        original_name=raw["A"],
        condition=raw["B"],
        date_str=raw["A"].str.extract(r"^(\d{8})_"),
    )
    mapping["date"] = pd.to_datetime(mapping["date_str"], format="%Y%m%d")
    mapping["condition"] = mapping["condition"].replace({"Saline": "vehicle", "Inactivation": "DCZ"})
    session_map = (
        mapping.groupby("session_id", as_index=False)
        .agg(original_name=("original_name", "first"), condition=("condition", "first"), date=("date", "first"))
        .sort_values("date")
        .reset_index(drop=True)
    )
    session_map["session_index"] = np.arange(1, len(session_map) + 1)
    return session_map


def load_behavior_category_map() -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for path in sorted(INTERVALS_DIR.glob("*_behavior_intervals.csv")):
        df = pd.read_csv(path, usecols=["behavior", "category"])
        rows.append(df.dropna(subset=["behavior"]).drop_duplicates())
    if not rows:
        return pd.DataFrame(columns=["behavior", "category"])
    combined = pd.concat(rows, ignore_index=True).drop_duplicates().sort_values(["category", "behavior"]).reset_index(drop=True)
    return combined


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


def collapse_primary_timeline(timeline: pd.DataFrame) -> pd.DataFrame:
    tl = timeline.copy()
    assigned = tl.apply(assign_primary_behavior, axis=1, result_type="expand")
    tl["behavior"] = assigned[0]
    tl["layer"] = assigned[1]

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
        }
    )
    return pd.DataFrame(rows)


def bridge_unscored_gaps(primary: pd.DataFrame, max_gap_s: float = UNSCORED_BRIDGE_S) -> pd.DataFrame:
    if primary.empty:
        return primary.copy()

    kept = primary[~((primary["behavior"] == "Unscored") & (primary["duration_s"] <= max_gap_s))].copy().reset_index(drop=True)
    if kept.empty:
        return kept

    rows: list[dict[str, object]] = []
    current = kept.iloc[0].to_dict()
    for row in kept.iloc[1:].to_dict("records"):
        gap = float(row["start_s"]) - float(current["end_s"])
        if current["behavior"] == row["behavior"] and gap <= max_gap_s:
            current["end_s"] = row["end_s"]
            current["duration_s"] = float(current["end_s"]) - float(current["start_s"])
        else:
            rows.append(current.copy())
            current = row.copy()
    rows.append(current.copy())
    return pd.DataFrame(rows)


def behavior_category_lookup(category_map: pd.DataFrame) -> dict[str, str]:
    lookup = dict(zip(category_map["behavior"], category_map["category"]))
    lookup["Unscored"] = "Unscored"
    return lookup


def summarize_session(session_id: str, category_lookup: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    timeline = pd.read_csv(INTERVALS_DIR / f"{session_id}_layered_timeline.csv")
    primary = collapse_primary_timeline(timeline)
    transition_stream = bridge_unscored_gaps(primary)
    session_duration_s = float(primary["duration_s"].sum())

    behavior_summary = (
        primary.groupby(["behavior", "layer"], as_index=False)["duration_s"]
        .sum()
        .assign(
            session_id=session_id,
            category=lambda df: df["behavior"].map(category_lookup).fillna("Other"),
            pct_session=lambda df: 100.0 * df["duration_s"] / session_duration_s if session_duration_s else np.nan,
            session_duration_s=session_duration_s,
        )
        .loc[:, ["session_id", "behavior", "category", "layer", "duration_s", "pct_session", "session_duration_s"]]
        .sort_values(["category", "behavior"])
        .reset_index(drop=True)
    )

    transition_rows: list[dict[str, object]] = []
    records = transition_stream.to_dict("records")
    for idx in range(len(records) - 1):
        source = str(records[idx]["behavior"])
        target = str(records[idx + 1]["behavior"])
        if source == target:
            continue
        transition_rows.append({"session_id": session_id, "source": source, "target": target, "count": 1})
    transition_df = pd.DataFrame(transition_rows)
    if transition_df.empty:
        transition_df = pd.DataFrame(columns=["session_id", "source", "target", "count"])
    else:
        transition_df = transition_df.groupby(["session_id", "source", "target"], as_index=False)["count"].sum()
    return behavior_summary, transition_df


def category_condition_summary(behavior_df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        behavior_df.groupby(["condition", "category"], as_index=False)
        .agg(
            mean_pct_session=("pct_session", "mean"),
            sd_pct_session=("pct_session", "std"),
            total_duration_s=("duration_s", "sum"),
            n_sessions=("session_id", "nunique"),
        )
    )
    return summary.sort_values(["condition", "category"]).reset_index(drop=True)


def behavior_condition_summary(behavior_df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        behavior_df.groupby(["condition", "behavior", "category"], as_index=False)
        .agg(
            mean_pct_session=("pct_session", "mean"),
            sd_pct_session=("pct_session", "std"),
            total_duration_s=("duration_s", "sum"),
            n_sessions_present=("session_id", "nunique"),
        )
    )
    return summary.sort_values(["condition", "mean_pct_session", "behavior"], ascending=[True, False, True]).reset_index(drop=True)


def overall_observed_behavior_table(behavior_df: pd.DataFrame) -> pd.DataFrame:
    return (
        behavior_df.groupby(["behavior", "category"], as_index=False)
        .agg(
            pooled_duration_s=("duration_s", "sum"),
            pooled_mean_pct_session=("pct_session", "mean"),
            sessions_present=("session_id", "nunique"),
        )
        .sort_values(["pooled_mean_pct_session", "pooled_duration_s", "behavior"], ascending=[False, False, True])
        .reset_index(drop=True)
    )


def build_condition_transition_summary(transition_df: pd.DataFrame) -> pd.DataFrame:
    if transition_df.empty:
        return pd.DataFrame(columns=["condition", "source", "target", "count", "prob"])

    merged = transition_df.copy()
    rows: list[dict[str, object]] = []
    for condition, sub in merged.groupby("condition", sort=False):
        grouped = sub.groupby(["source", "target"], as_index=False)["count"].sum()
        source_totals = grouped.groupby("source")["count"].sum().to_dict()
        for row in grouped.itertuples(index=False):
            rows.append(
                {
                    "condition": condition,
                    "source": row.source,
                    "target": row.target,
                    "count": int(row.count),
                    "prob": float(row.count / source_totals[row.source]) if source_totals.get(row.source, 0) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def build_pooled_transition_summary(transition_df: pd.DataFrame) -> pd.DataFrame:
    if transition_df.empty:
        return pd.DataFrame(columns=["source", "target", "count", "prob"])

    grouped = transition_df.groupby(["source", "target"], as_index=False)["count"].sum()
    source_totals = grouped.groupby("source")["count"].sum().to_dict()
    grouped["prob"] = grouped.apply(lambda row: row["count"] / source_totals[row["source"]] if source_totals.get(row["source"], 0) else np.nan, axis=1)
    return grouped.sort_values(["source", "target"]).reset_index(drop=True)


def top_behaviors_for_plot(overall_behavior: pd.DataFrame) -> list[str]:
    filtered = overall_behavior.loc[overall_behavior["behavior"] != "Unscored"].copy()
    return filtered.head(max(TOP_BEHAVIOR_COUNT, len(filtered)))["behavior"].tolist()


def pie_summary_table(behavior_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    df = behavior_df.copy()
    df["is_rest_vigilant"] = df["behavior"].isin(RESTFUL_BEHAVIORS)
    df["is_behaving"] = ~df["is_rest_vigilant"] & (df["behavior"] != "Unscored")
    df["is_social"] = df["layer"] == SOCIAL_LAYER
    df["is_asocial"] = (df["behavior"] != "Unscored") & ~df["is_social"]
    df["is_aggressive_social"] = df["is_social"] & df["category"].isin(AGGRESSIVE_CATEGORIES)
    df["is_affiliative_social"] = df["is_social"] & ~df["category"].isin(AGGRESSIVE_CATEGORIES)

    level1 = pd.DataFrame(
        [
            {"label": "Rest/Vigilant", "pct": float(df.loc[df["is_rest_vigilant"], "duration_s"].sum())},
            {"label": "Behaving", "pct": float(df.loc[df["is_behaving"], "duration_s"].sum())},
        ]
    )
    level1["pct"] = 100.0 * level1["pct"] / float(df["duration_s"].sum())

    behaving_total = float(df.loc[df["is_behaving"], "duration_s"].sum())
    level2 = pd.DataFrame(
        [
            {"label": "Social", "pct": float(df.loc[df["is_social"], "duration_s"].sum())},
            {"label": "Asocial", "pct": float(df.loc[df["is_asocial"], "duration_s"].sum())},
        ]
    )
    level2["pct"] = 100.0 * level2["pct"] / behaving_total if behaving_total else np.nan

    social_total = float(df.loc[df["is_social"], "duration_s"].sum())
    level3 = pd.DataFrame(
        [
            {"label": "Affiliative", "pct": float(df.loc[df["is_affiliative_social"], "duration_s"].sum())},
            {"label": "Aggressive", "pct": float(df.loc[df["is_aggressive_social"], "duration_s"].sum())},
        ]
    )
    level3["pct"] = 100.0 * level3["pct"] / social_total if social_total else np.nan
    return {"rest_vs_behaving": level1, "social_vs_asocial": level2, "affiliative_vs_aggressive": level3}


def draw_pie(ax: plt.Axes, pie_df: pd.DataFrame, colors: list[str], title: str) -> None:
    values = pie_df["pct"].fillna(0.0).to_numpy(dtype=float)
    labels = [f"{label}\n{value:.0f}%" for label, value in zip(pie_df["label"], values)]
    ax.pie(values, labels=labels, colors=colors, startangle=90, counterclock=False, textprops={"fontsize": BASE_FONT_SIZE})
    ax.set_title(title, loc="left", fontsize=TITLE_FONT_SIZE)


def pie_summary_for_condition(behavior_df: pd.DataFrame, condition: str) -> dict[str, pd.DataFrame]:
    return pie_summary_table(behavior_df.loc[behavior_df["condition"] == condition].reset_index(drop=True))


def plot_behavior_composition(behavior_df: pd.DataFrame, behavior_summary: pd.DataFrame, overall_behavior: pd.DataFrame, out_path: Path) -> None:
    top_behaviors = top_behaviors_for_plot(overall_behavior)
    fig = plt.figure(figsize=(18.0, 11.5))
    gs = fig.add_gridspec(2, 1, hspace=0.08)

    veh_ax = fig.add_subplot(gs[0, 0])
    dcz_ax = fig.add_subplot(gs[1, 0], sharex=veh_ax)
    plot_df = (
        behavior_summary.loc[behavior_summary["behavior"].isin(top_behaviors), ["condition", "behavior", "category", "mean_pct_session"]]
        .copy()
        .pivot(index="behavior", columns="condition", values="mean_pct_session")
        .reindex(top_behaviors)
    )
    category_lookup = overall_behavior.set_index("behavior")["category"].to_dict()
    x = np.arange(len(plot_df.index))
    vehicle_vals = plot_df["vehicle"].fillna(0.0).to_numpy(dtype=float) if "vehicle" in plot_df.columns else np.zeros(len(plot_df.index))
    dcz_vals = plot_df["DCZ"].fillna(0.0).to_numpy(dtype=float) if "DCZ" in plot_df.columns else np.zeros(len(plot_df.index))
    max_y = max(float(np.nanmax(vehicle_vals)) if len(vehicle_vals) else 0.0, float(np.nanmax(dcz_vals)) if len(dcz_vals) else 0.0)

    for ax, values, color, title in [
        (veh_ax, vehicle_vals, VEHICLE_COLOR, "Vehicle"),
        (dcz_ax, dcz_vals, DCZ_COLOR, "DCZ"),
    ]:
        bar_colors = [CATEGORY_COLORS.get(category_lookup.get(behavior, "Other"), color) for behavior in plot_df.index]
        ax.bar(x, values, width=0.72, color=bar_colors)
        ax.set_ylim(0.0, max_y * 1.12 if max_y > 0 else 1.0)
        ax.set_ylabel("Mean percent of session", fontsize=BASE_FONT_SIZE)
        ax.set_title(title, loc="left", fontsize=TITLE_FONT_SIZE)
        style_axis(ax, tick_size=CATEGORY_TICK_FONT_SIZE)

    veh_ax.tick_params(labelbottom=False)
    dcz_ax.set_xticks(x, list(plot_df.index), rotation=75, ha="right")
    for tick in dcz_ax.get_xticklabels():
        tick.set_color("#111111")
        tick.set_fontsize(CATEGORY_TICK_FONT_SIZE)
    dcz_ax.set_xlabel("Resolved behavior labels ordered by pooled frequency", fontsize=BASE_FONT_SIZE)

    observed_n = int((overall_behavior["behavior"] != "Unscored").sum())
    fig.suptitle(
        f"Ethogram overview: Figure 1c-style behavior summary ({observed_n} resolved behaviors observed)",
        fontsize=TITLE_FONT_SIZE + 1.0,
        x=0.05,
        ha="left",
    )
    fig.subplots_adjust(left=0.08, right=0.98, top=0.90, bottom=0.24, hspace=0.16)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_condition_pies(behavior_df: pd.DataFrame, out_path: Path) -> None:
    fig = plt.figure(figsize=(18.0, 10.0))
    gs = fig.add_gridspec(2, 3, hspace=0.36, wspace=0.28)
    specs = [
        ("vehicle", "Vehicle"),
        ("DCZ", "DCZ"),
    ]
    pie_titles = [
        ("rest_vs_behaving", ["#BDBDBD", "#4E79A7"], "Rest/Vigilant vs Behaving"),
        ("social_vs_asocial", ["#59A14F", "#F28E2B"], "Within Behaving: Social vs Asocial"),
        ("affiliative_vs_aggressive", ["#6BAED6", "#E15759"], "Within Social: Affiliative vs Aggressive"),
    ]
    for row_idx, (condition, label) in enumerate(specs):
        pies = pie_summary_for_condition(behavior_df, condition)
        for col_idx, (key, colors, title) in enumerate(pie_titles):
            ax = fig.add_subplot(gs[row_idx, col_idx])
            draw_pie(ax, pies[key], colors, f"{label}: {title}")
    fig.suptitle(
        "Ethogram overview: Figure 1c-style coarse composition pies by condition",
        fontsize=TITLE_FONT_SIZE + 1.0,
        x=0.05,
        ha="left",
    )
    fig.subplots_adjust(left=0.05, right=0.98, top=0.90, bottom=0.05, hspace=0.42, wspace=0.30)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def circular_layout(nodes: list[str]) -> dict[str, tuple[float, float]]:
    angles = np.linspace(np.pi / 2, np.pi / 2 + 2 * np.pi, len(nodes), endpoint=False)
    return {node: (float(np.cos(angle)), float(np.sin(angle))) for node, angle in zip(nodes, angles)}


def filtered_transition_graph(condition_transition: pd.DataFrame, condition: str) -> pd.DataFrame:
    sub = condition_transition.loc[(condition_transition["condition"] == condition) & (condition_transition["source"] != "Unscored") & (condition_transition["target"] != "Unscored")].copy()
    if sub.empty:
        return sub
    kept_rows = []
    for source, source_df in sub.groupby("source", sort=False):
        keep = source_df.loc[source_df["count"] >= TRANSITION_MIN_COUNT_FOR_GRAPH].sort_values(["prob", "count"], ascending=[False, False]).head(TRANSITION_TOP_EDGES_PER_SOURCE)
        kept_rows.append(keep)
    return pd.concat(kept_rows, ignore_index=True).drop_duplicates(subset=["source", "target"]).reset_index(drop=True)


def draw_transition_graph(ax: plt.Axes, graph_df: pd.DataFrame, node_stats: pd.DataFrame, title: str, nodes: list[str]) -> None:
    if graph_df.empty:
        ax.text(0.5, 0.5, "No transitions met plotting threshold", ha="center", va="center", fontsize=11)
        ax.set_title(title, loc="left", fontsize=12)
        ax.axis("off")
        return

    pos = circular_layout(nodes)
    node_lookup = node_stats.set_index("behavior")
    max_prob = float(graph_df["prob"].max())

    for row in graph_df.itertuples(index=False):
        x1, y1 = pos[row.source]
        x2, y2 = pos[row.target]
        rad = 0.18 if row.source < row.target else -0.18
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops={
                "arrowstyle": "-|>",
                "color": "#7D8793",
                "lw": 0.8 + 5.2 * (float(row.prob) / max_prob if max_prob else 0.0),
                "alpha": 0.55,
                "connectionstyle": f"arc3,rad={rad}",
                "shrinkA": 18,
                "shrinkB": 18,
            },
            zorder=1,
        )
        mid_x = 0.5 * (x1 + x2)
        mid_y = 0.5 * (y1 + y2) + (0.08 if rad > 0 else -0.08)
        ax.text(mid_x, mid_y, f"{100.0 * float(row.prob):.0f}", fontsize=EDGE_LABEL_FONT_SIZE, color="#555555", ha="center", va="center")

    for node in nodes:
        x, y = pos[node]
        category = node_lookup.loc[node, "category"] if node in node_lookup.index else "Other"
        node_size = 260 + 38 * float(node_lookup.loc[node, "pooled_mean_pct_session"]) if node in node_lookup.index else 260
        ax.scatter([x], [y], s=node_size, color=CATEGORY_COLORS.get(str(category), "#999999"), edgecolor="#2F2F2F", linewidth=0.8, zorder=3)
        ha = "left" if x >= 0 else "right"
        x_text = x + (0.09 if x >= 0 else -0.09)
        ax.text(x_text, y, node, ha=ha, va="center", fontsize=NODE_LABEL_FONT_SIZE)

    ax.set_title(title, loc="left", fontsize=TITLE_FONT_SIZE)
    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.3, 1.3)
    ax.axis("off")


def plot_transition_graphs(condition_transition: pd.DataFrame, overall_behavior: pd.DataFrame, out_path: Path) -> None:
    vehicle_graph = filtered_transition_graph(condition_transition, "vehicle")
    dcz_graph = filtered_transition_graph(condition_transition, "DCZ")
    node_lookup = overall_behavior.set_index("behavior")["pooled_mean_pct_session"].to_dict()
    vehicle_nodes = sorted(
        set(vehicle_graph["source"]).union(set(vehicle_graph["target"])),
        key=lambda name: (-float(node_lookup.get(name, 0.0)), name),
    )
    dcz_extra_nodes = [node for node in sorted(set(dcz_graph["source"]).union(set(dcz_graph["target"]))) if node not in vehicle_nodes]
    nodes = vehicle_nodes + dcz_extra_nodes
    fig, axes = plt.subplots(1, 2, figsize=(18.0, 9.5))
    draw_transition_graph(axes[0], vehicle_graph, overall_behavior, "Vehicle", nodes)
    draw_transition_graph(axes[1], dcz_graph, overall_behavior, "DCZ", nodes)
    fig.suptitle(
        "Ethogram overview: Figure 1d-style transition maps\nEdges show top outgoing transition probabilities per source behavior",
        fontsize=TITLE_FONT_SIZE + 1.0,
        x=0.05,
        ha="left",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95), w_pad=1.0)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_markdown(
    cohort_label: str,
    note: str | None,
    overall_behavior: pd.DataFrame,
    category_summary: pd.DataFrame,
    pooled_transition: pd.DataFrame,
) -> str:
    observed_behaviors = overall_behavior.loc[overall_behavior["behavior"] != "Unscored"].copy()
    top_behaviors = observed_behaviors.head(8)
    top_transitions = pooled_transition.loc[pooled_transition["count"] >= TRANSITION_SUMMARY_MIN_COUNT].copy()
    top_transitions = top_transitions.sort_values(["prob", "count"], ascending=[False, False]).head(8)
    category_lines = []
    for category in CATEGORY_ORDER:
        rows = category_summary.loc[category_summary["category"] == category]
        if rows.empty:
            continue
        vehicle = rows.loc[rows["condition"] == "vehicle", "mean_pct_session"]
        dcz = rows.loc[rows["condition"] == "DCZ", "mean_pct_session"]
        vehicle_text = f"{float(vehicle.iloc[0]):.2f}" if not vehicle.empty else "NA"
        dcz_text = f"{float(dcz.iloc[0]):.2f}" if not dcz.empty else "NA"
        category_lines.append(f"- {category}: vehicle `{vehicle_text}%`, DCZ `{dcz_text}%` mean session time.")

    lines = [
        "# Ethogram Overview",
        "",
        f"Cohort: {cohort_label}.",
    ]
    if note:
        lines.extend(["", note])
    lines.extend(
        [
            "",
            "This section adds a Figure 1c/1d-style behavioral overview using the repo's locked preprocessing choices:",
            "",
            "- Behavior composition uses the precedence-resolved layered timeline, so each second contributes to exactly one primary behavior state.",
            "- The Figure 1c-style pies are coarse summaries: `Rest/Vigilant` pools `Rest/Stationary` with `Vigilant/Scan`, `Behaving` is everything else except `Unscored`, and the final social pie folds sexual behavior into the non-aggressive side.",
            f"- Transition analyses remove `Unscored` gaps of duration `<= {UNSCORED_BRIDGE_S:.0f} s` before re-collapsing adjacent identical states.",
            "- Transition probabilities are computed from the resulting primary-state stream as `count(source -> target) / total outgoing transitions from source`.",
            f"- To keep the transition maps readable, each source behavior shows up to `{TRANSITION_TOP_EDGES_PER_SOURCE}` outgoing edges with count `>= {TRANSITION_MIN_COUNT_FOR_GRAPH}`.",
            "",
            "## Coverage",
            "",
            f"- Observed resolved behaviors: `{len(observed_behaviors)}`.",
            f"- Top resolved behavior by pooled mean session time: `{top_behaviors.iloc[0]['behavior']}` (`{top_behaviors.iloc[0]['pooled_mean_pct_session']:.2f}%`)." if not top_behaviors.empty else "- No observed resolved behaviors found.",
            "",
            "## Category-level composition",
            "",
        ]
    )
    lines.extend(category_lines)
    lines.extend(["", "## Top resolved behaviors", ""])
    for row in top_behaviors.itertuples(index=False):
        lines.append(
            f"- {row.behavior} ({row.category}): pooled mean `{row.pooled_mean_pct_session:.2f}%` of session, present in `{row.sessions_present}` sessions."
        )
    lines.extend(["", "## Strongest pooled transitions", ""])
    if top_transitions.empty:
        lines.append(f"- No pooled transitions met the summary threshold of at least `{TRANSITION_SUMMARY_MIN_COUNT}` counts.")
    else:
        for row in top_transitions.itertuples(index=False):
            lines.append(f"- {row.source} -> {row.target}: probability `{row.prob:.3f}` from `{row.count}` pooled transitions.")
    lines.append("")
    return "\n".join(lines)


def write_outputs(
    behavior_df: pd.DataFrame,
    transition_df: pd.DataFrame,
    cohort_name: str,
    cohort_label: str,
    note: str | None = None,
) -> None:
    tables_dir = results_tables_dir(cohort_name, "ethogram_overview")
    figures_dir = results_figures_dir(cohort_name, "ethogram_overview")
    docs_dir = docs_section_dir(cohort_name, "ethogram_overview")

    category_summary = category_condition_summary(behavior_df)
    behavior_summary = behavior_condition_summary(behavior_df)
    overall_behavior = overall_observed_behavior_table(behavior_df)
    pooled_transition = build_pooled_transition_summary(transition_df)
    condition_transition = build_condition_transition_summary(transition_df)

    behavior_df.to_csv(tables_dir / "resolved_behavior_by_session.csv", index=False)
    category_summary.to_csv(tables_dir / "resolved_category_condition_summary.csv", index=False)
    behavior_summary.to_csv(tables_dir / "resolved_behavior_condition_summary.csv", index=False)
    overall_behavior.to_csv(tables_dir / "resolved_behavior_overall_summary.csv", index=False)
    transition_df.to_csv(tables_dir / "resolved_transition_counts_by_session.csv", index=False)
    pooled_transition.to_csv(tables_dir / "resolved_transition_pooled_summary.csv", index=False)
    condition_transition.to_csv(tables_dir / "resolved_transition_condition_summary.csv", index=False)

    plot_behavior_composition(behavior_df, behavior_summary, overall_behavior, figures_dir / "ethogram_behavior_composition.png")
    plot_condition_pies(behavior_df, figures_dir / "ethogram_condition_pies.png")
    plot_transition_graphs(condition_transition, overall_behavior, figures_dir / "ethogram_transition_graphs.png")
    (docs_dir / "ethogram_overview.md").write_text(
        build_markdown(cohort_label, note, overall_behavior, category_summary, pooled_transition),
        encoding="utf-8",
    )


def main() -> None:
    category_map = load_behavior_category_map()
    category_lookup = behavior_category_lookup(category_map)
    session_map = load_unblinding_map()

    behavior_rows: list[pd.DataFrame] = []
    transition_rows: list[pd.DataFrame] = []
    for session_id in session_map["session_id"].astype(str):
        behavior_df, transition_df = summarize_session(session_id, category_lookup)
        behavior_rows.append(behavior_df)
        transition_rows.append(transition_df)

    behavior_df = pd.concat(behavior_rows, ignore_index=True)
    transition_df = pd.concat(transition_rows, ignore_index=True)
    behavior_df = session_map.merge(behavior_df, on="session_id", how="left").sort_values(["date", "behavior"]).reset_index(drop=True)
    transition_df = session_map.merge(transition_df, on="session_id", how="left").sort_values(["date", "source", "target"]).reset_index(drop=True)

    write_outputs(behavior_df, transition_df, "full", "full session set")
    write_outputs(
        behavior_df,
        transition_df,
        "quiet_mask",
        "quiet-mask sensitivity session set",
        note="Because this overview is built from the behavior timeline rather than the audio mask, the quiet-mask version currently matches the full session set.",
    )

    filtered_behavior = behavior_df.loc[behavior_df["session_id"] != VET_ENTRY_SESSION_ID].reset_index(drop=True)
    filtered_transition = transition_df.loc[transition_df["session_id"] != VET_ENTRY_SESSION_ID].reset_index(drop=True)
    write_outputs(
        filtered_behavior,
        filtered_transition,
        "exclude_vet_entry",
        "excluding known vet-entry session 596273",
    )


if __name__ == "__main__":
    main()

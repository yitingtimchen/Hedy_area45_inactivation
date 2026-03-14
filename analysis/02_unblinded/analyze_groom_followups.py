from __future__ import annotations

from itertools import combinations
from pathlib import Path
from zipfile import ZipFile
import re
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INTERVALS_DIR = ROOT / "data" / "derived" / "behavior" / "cleaned_intervals"
UNBLINDED_ROOT = ROOT / "results" / "unblinded"
DOCS_ROOT = ROOT / "docs" / "unblinded"
KEY_PATH = ROOT / "data" / "raw" / "session_key" / "Sessions name encoding.xlsx"

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

UNSCORED_BRIDGE_S = 3.0
VET_ENTRY_SESSION_ID = "596273"

GROOM_LABEL_MAP = {
    "Groom give": "groom_give",
    "Groom receive": "groom_receive",
}
GROOM_STATES = set(GROOM_LABEL_MAP.values())


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


def load_social_episodes(session_id: str) -> pd.DataFrame:
    return pd.read_csv(INTERVALS_DIR / f"{session_id}_social_bouts.csv")


def assign_transition_state(row: pd.Series) -> str:
    social_state = row["social_state"] if pd.notna(row["social_state"]) else ""
    if social_state in GROOM_LABEL_MAP:
        return GROOM_LABEL_MAP[social_state]
    if bool(row["social_engaged"]):
        return "other_social"
    if pd.notna(row["activity_state"]) and str(row["activity_state"]) != "":
        return "nonsocial_activity"
    if pd.notna(row["attention_state"]) and str(row["attention_state"]) != "":
        return "attention_only"
    if pd.notna(row["atypical_state"]) and str(row["atypical_state"]) != "":
        return "atypical_only"
    return "unscored"


def collapse_state_timeline(timeline: pd.DataFrame) -> pd.DataFrame:
    tl = timeline.copy()
    tl["transition_state"] = tl.apply(assign_transition_state, axis=1)

    rows: list[dict[str, object]] = []
    current = tl.iloc[0].to_dict()
    for row in tl.iloc[1:].to_dict("records"):
        contiguous = abs(float(current["end_s"]) - float(row["start_s"])) < 1e-9
        if contiguous and current["transition_state"] == row["transition_state"]:
            current["end_s"] = row["end_s"]
            current["duration_s"] = float(current["end_s"]) - float(current["start_s"])
        else:
            rows.append(
                {
                    "start_s": float(current["start_s"]),
                    "end_s": float(current["end_s"]),
                    "duration_s": float(current["duration_s"]),
                    "transition_state": current["transition_state"],
                }
            )
            current = row.copy()
    rows.append(
        {
            "start_s": float(current["start_s"]),
            "end_s": float(current["end_s"]),
            "duration_s": float(current["duration_s"]),
            "transition_state": current["transition_state"],
        }
    )
    return pd.DataFrame(rows)


def bridge_short_unscored_gaps(states: pd.DataFrame, max_gap_s: float = UNSCORED_BRIDGE_S) -> pd.DataFrame:
    if states.empty:
        return states.copy()

    kept = states[~((states["transition_state"] == "unscored") & (states["duration_s"] <= max_gap_s))].copy().reset_index(drop=True)
    if kept.empty:
        return kept

    rows: list[dict[str, object]] = []
    current = kept.iloc[0].to_dict()
    for row in kept.iloc[1:].to_dict("records"):
        gap = float(row["start_s"]) - float(current["end_s"])
        if current["transition_state"] == row["transition_state"] and gap <= max_gap_s:
            current["end_s"] = row["end_s"]
            current["duration_s"] = float(current["end_s"]) - float(current["start_s"])
        else:
            rows.append(current.copy())
            current = row.copy()
    rows.append(current.copy())
    return pd.DataFrame(rows)


def collapse_social_sequence_within_episode(timeline: pd.DataFrame, start_s: float, end_s: float) -> pd.DataFrame:
    social = timeline.loc[
        timeline["social_state"].notna() & (timeline["end_s"] > start_s) & (timeline["start_s"] < end_s),
        ["start_s", "end_s", "social_state"],
    ].copy()
    if social.empty:
        return pd.DataFrame(columns=["start_s", "end_s", "duration_s", "social_state"])

    social["start_s"] = social["start_s"].clip(lower=start_s)
    social["end_s"] = social["end_s"].clip(upper=end_s)
    social["duration_s"] = social["end_s"] - social["start_s"]
    social = social.loc[social["duration_s"] > 0].reset_index(drop=True)
    if social.empty:
        return pd.DataFrame(columns=["start_s", "end_s", "duration_s", "social_state"])

    rows: list[dict[str, object]] = []
    current = social.iloc[0].to_dict()
    for row in social.iloc[1:].to_dict("records"):
        contiguous = abs(float(current["end_s"]) - float(row["start_s"])) < 1e-9
        same_state = current["social_state"] == row["social_state"]
        if contiguous and same_state:
            current["end_s"] = row["end_s"]
            current["duration_s"] = float(current["end_s"]) - float(current["start_s"])
        else:
            rows.append(current.copy())
            current = row.copy()
    rows.append(current.copy())
    return pd.DataFrame(rows)


def safe_prob(num: int, den: int) -> float | None:
    if den == 0:
        return None
    return num / den


def safe_rate_per_hour(num: int, duration_s: float) -> float | None:
    if duration_s <= 0:
        return None
    return num / (duration_s / 3600.0)


def episode_turn_taking_metrics(timeline: pd.DataFrame, social_episodes: pd.DataFrame) -> dict[str, object]:
    grooming_episodes = 0
    turn_taking_episodes = 0
    latencies: list[float] = []
    give_to_receive_latencies: list[float] = []
    receive_to_give_latencies: list[float] = []

    for episode in social_episodes.itertuples(index=False):
        sequence = collapse_social_sequence_within_episode(timeline, float(episode.start_s), float(episode.end_s))
        if sequence.empty:
            continue

        groom_seq = sequence.loc[sequence["social_state"].isin(GROOM_LABEL_MAP.keys())].reset_index(drop=True)
        if groom_seq.empty:
            continue

        grooming_episodes += 1
        first = groom_seq.iloc[0]
        first_role = GROOM_LABEL_MAP[first["social_state"]]
        target_label = "Groom receive" if first_role == "groom_give" else "Groom give"
        later = groom_seq.loc[(groom_seq["start_s"] >= float(first["end_s"]) - 1e-9) & (groom_seq["social_state"] == target_label)]
        if later.empty:
            continue

        turn_taking_episodes += 1
        latency = float(later.iloc[0]["start_s"]) - float(first["end_s"])
        latencies.append(latency)
        if first_role == "groom_give":
            give_to_receive_latencies.append(latency)
        else:
            receive_to_give_latencies.append(latency)

    return {
        "grooming_social_episode_count": grooming_episodes,
        "turn_taking_social_episode_count": turn_taking_episodes,
        "episode_turn_taking_prob": safe_prob(turn_taking_episodes, grooming_episodes),
        "episode_turn_taking_latency_median_s": float(np.median(latencies)) if latencies else np.nan,
        "episode_give_to_receive_latency_median_s": float(np.median(give_to_receive_latencies)) if give_to_receive_latencies else np.nan,
        "episode_receive_to_give_latency_median_s": float(np.median(receive_to_give_latencies)) if receive_to_give_latencies else np.nan,
    }


def immediate_transition_metrics(states: pd.DataFrame) -> dict[str, object]:
    rows = states.to_dict("records")
    groom_known_next = 0
    groom_to_nonsocial = 0
    nonsocial_known_next = 0
    nonsocial_to_groom = 0

    for idx, row in enumerate(rows[:-1]):
        current = row["transition_state"]
        next_state = rows[idx + 1]["transition_state"]
        if next_state == "unscored":
            continue
        if current in GROOM_STATES:
            groom_known_next += 1
            if next_state == "nonsocial_activity":
                groom_to_nonsocial += 1
        if current == "nonsocial_activity":
            nonsocial_known_next += 1
            if next_state in GROOM_STATES:
                nonsocial_to_groom += 1

    return {
        "groom_bouts_with_known_next_state": groom_known_next,
        "groom_to_nonsocial_events": groom_to_nonsocial,
        "groom_to_nonsocial_prob": safe_prob(groom_to_nonsocial, groom_known_next),
        "nonsocial_bouts_with_known_next_state": nonsocial_known_next,
        "nonsocial_to_groom_events": nonsocial_to_groom,
        "nonsocial_to_groom_prob": safe_prob(nonsocial_to_groom, nonsocial_known_next),
    }


def summarize_session(session_id: str) -> dict[str, object]:
    timeline = pd.read_csv(INTERVALS_DIR / f"{session_id}_layered_timeline.csv")
    social_episodes = load_social_episodes(session_id)
    duration_s = float(timeline["duration_s"].sum())

    states = collapse_state_timeline(timeline)
    states = bridge_short_unscored_gaps(states)

    episode_turn_taking = episode_turn_taking_metrics(timeline, social_episodes)
    transitions = immediate_transition_metrics(states)

    return {
        "session_id": session_id,
        "trimmed_session_duration_s": duration_s,
        **episode_turn_taking,
        **transitions,
        "turn_taking_social_episodes_per_hour": safe_rate_per_hour(int(episode_turn_taking["turn_taking_social_episode_count"]), duration_s),
        "groom_to_nonsocial_events_per_hour": safe_rate_per_hour(int(transitions["groom_to_nonsocial_events"]), duration_s),
        "nonsocial_to_groom_events_per_hour": safe_rate_per_hour(int(transitions["nonsocial_to_groom_events"]), duration_s),
    }


def bootstrap_ci_for_mean_diff(dcz: np.ndarray, vehicle: np.ndarray, seed: int = 57, n_boot: int = 20000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    dcz_draws = rng.choice(dcz, size=(n_boot, len(dcz)), replace=True).mean(axis=1)
    veh_draws = rng.choice(vehicle, size=(n_boot, len(vehicle)), replace=True).mean(axis=1)
    diffs = dcz_draws - veh_draws
    low, high = np.percentile(diffs, [2.5, 97.5])
    return float(low), float(high)


def exact_label_permutation_p(values: np.ndarray, labels: np.ndarray) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    labels = np.asarray(labels)
    n = len(values)
    dcz_n = int(np.sum(labels == "DCZ"))
    observed = values[labels == "DCZ"].mean() - values[labels == "vehicle"].mean()
    diffs = []
    for idx in combinations(range(n), dcz_n):
        mask = np.zeros(n, dtype=bool)
        mask[list(idx)] = True
        diffs.append(values[mask].mean() - values[~mask].mean())
    diffs = np.asarray(diffs)
    return float(observed), float(np.mean(np.abs(diffs) >= abs(observed)))


def compare_conditions(df: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for metric in metrics:
        sub = df[["condition", metric]].copy()
        sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
        sub = sub.dropna(subset=[metric]).reset_index(drop=True)
        dcz = sub.loc[sub["condition"] == "DCZ", metric].to_numpy(dtype=float)
        vehicle = sub.loc[sub["condition"] == "vehicle", metric].to_numpy(dtype=float)
        if len(dcz) == 0 or len(vehicle) == 0:
            continue
        effect, p_value = exact_label_permutation_p(sub[metric].to_numpy(dtype=float), sub["condition"].to_numpy())
        ci_low, ci_high = bootstrap_ci_for_mean_diff(dcz, vehicle)
        rows.append(
            {
                "metric": metric,
                "vehicle_mean": float(np.mean(vehicle)),
                "vehicle_sd": float(np.std(vehicle, ddof=1)),
                "DCZ_mean": float(np.mean(dcz)),
                "DCZ_sd": float(np.std(dcz, ddof=1)),
                "mean_diff_DCZ_minus_vehicle": effect,
                "bootstrap_ci95_low": ci_low,
                "bootstrap_ci95_high": ci_high,
                "exact_permutation_p_two_sided": p_value,
                "n_vehicle": int(len(vehicle)),
                "n_DCZ": int(len(dcz)),
            }
        )
    return pd.DataFrame(rows)


def build_markdown(summary: pd.DataFrame, cohort_label: str) -> str:
    pretty = {
        "episode_turn_taking_prob": "Episode-level grooming turn-taking probability",
        "episode_turn_taking_latency_median_s": "Median episode-level turn-taking latency (s)",
        "groom_to_nonsocial_prob": "Groom to nonsocial-activity probability",
        "nonsocial_to_groom_prob": "Nonsocial-activity to groom probability",
    }
    lines = [
        "# Groom Follow-Up Analysis",
        "",
        f"Cohort: {cohort_label}.",
        "These exploratory follow-ups were designed to stay close to the main grooming result rather than mining the full transition matrix.",
        "",
        "## Definitions",
        "",
        "- Social episodes use the locked preprocessing definition in which `social_engaged` periods are merged across gaps `<= 2 s`.",
        f"- The transition stream for non-social entry and exit metrics collapses the cleaned layered timeline into `groom_give`, `groom_receive`, `other_social`, `nonsocial_activity`, `attention_only`, `atypical_only`, and `unscored`.",
        f"- Short `unscored` gaps of duration `<= {UNSCORED_BRIDGE_S:.0f} s` are removed before recollapsing adjacent identical states for the non-social entry and exit metrics.",
        "- `episode_turn_taking_prob`: among social episodes that contain grooming, the proportion in which the opposite grooming role appears later in the same social episode.",
        "- `episode_turn_taking_latency_median_s`: the median latency from the end of the first grooming role to the start of the opposite grooming role within that same social episode.",
        "- `groom_to_nonsocial_prob`: among grooming bouts with a known next state, the proportion whose next state is `nonsocial_activity`.",
        "- `nonsocial_to_groom_prob`: among `nonsocial_activity` bouts with a known next state, the proportion whose next state is grooming (`give` or `receive`).",
        "",
        "## Condition comparisons",
        "",
    ]
    for metric in [
        "episode_turn_taking_prob",
        "episode_turn_taking_latency_median_s",
        "groom_to_nonsocial_prob",
        "nonsocial_to_groom_prob",
    ]:
        row = summary.loc[summary["metric"] == metric]
        if row.empty:
            continue
        r = row.iloc[0]
        lines.append(
            f"- {pretty[metric]}: vehicle mean `{r['vehicle_mean']:.3f}`, DCZ mean `{r['DCZ_mean']:.3f}`, "
            f"mean difference `{r['mean_diff_DCZ_minus_vehicle']:.3f}`, 95% CI `[{r['bootstrap_ci95_low']:.3f}, {r['bootstrap_ci95_high']:.3f}]`, "
            f"exact permutation `p = {r['exact_permutation_p_two_sided']:.4f}`."
        )
    lines.append("")
    return "\n".join(lines)


def write_outputs(metrics_df: pd.DataFrame, cohort_name: str, cohort_label: str) -> None:
    tables_dir = UNBLINDED_ROOT / cohort_name / "tables"
    docs_dir = DOCS_ROOT / cohort_name
    tables_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    metrics_df.to_csv(tables_dir / "groom_followup_metrics_by_session.csv", index=False)
    summary = compare_conditions(
        metrics_df,
        [
            "episode_turn_taking_prob",
            "episode_turn_taking_latency_median_s",
            "groom_to_nonsocial_prob",
            "nonsocial_to_groom_prob",
        ],
    )
    summary.to_csv(tables_dir / "groom_followup_condition_comparison.csv", index=False)
    (docs_dir / "groom_followup_analysis.md").write_text(build_markdown(summary, cohort_label), encoding="utf-8")


def main() -> None:
    UNBLINDED_ROOT.mkdir(parents=True, exist_ok=True)
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)

    session_ids = sorted({path.name.split("_")[0] for path in INTERVALS_DIR.glob("*_layered_timeline.csv")})
    metrics_df = pd.DataFrame([summarize_session(session_id) for session_id in session_ids])
    session_map = load_unblinding_map()
    metrics_df = session_map.merge(metrics_df, on="session_id", how="left")

    write_outputs(metrics_df, "full", "full session set")
    filtered = metrics_df.loc[metrics_df["session_id"] != VET_ENTRY_SESSION_ID].reset_index(drop=True)
    write_outputs(filtered, "exclude_vet_entry", "excluding known vet-entry session 596273")


if __name__ == "__main__":
    main()

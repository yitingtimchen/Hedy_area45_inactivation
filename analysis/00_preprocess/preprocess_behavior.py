from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "data" / "raw" / "boris"
INTERVALS_DIR = ROOT / "data" / "derived" / "behavior" / "cleaned_intervals"
SUMMARIES_DIR = ROOT / "results" / "blinded" / "tables"
EXCEPTIONS_PATH = ROOT / "analysis" / "utils" / "session_exceptions.csv"

GAP_MERGE_S = 2.0
TIMECOURSE_STEP_S = 60
SOCIAL_BOUT_GAP_S = 2.0
LEAVE_RETURN_GAP_S = 3.0
EDGE_TRIM_S = 30.0

SOCIAL_LAYER = "social"
ACTIVITY_LAYER = "activity"
ATTENTION_LAYER = "attention"
ATYPICAL_LAYER = "atypical"

LAYER_ORDER = [SOCIAL_LAYER, ACTIVITY_LAYER, ATTENTION_LAYER, ATYPICAL_LAYER]

BEHAVIOR_LAYER = {
    "Approach (non-agonistic)": SOCIAL_LAYER,
    "Leave/Withdraw (non-agonistic)": SOCIAL_LAYER,
    "Proximity (<arm’s reach)": SOCIAL_LAYER,
    "Contact/Sit-with": SOCIAL_LAYER,
    "Affiliative touch": SOCIAL_LAYER,
    "Lip-smack": SOCIAL_LAYER,
    "Muzzle-muzzle contact": SOCIAL_LAYER,
    "Groom give": SOCIAL_LAYER,
    "Groom receive": SOCIAL_LAYER,
    "Groom solicit": SOCIAL_LAYER,
    "Sex present": SOCIAL_LAYER,
    "Mount attempt": SOCIAL_LAYER,
    "Mount give": SOCIAL_LAYER,
    "Mount receive": SOCIAL_LAYER,
    "Intromission": SOCIAL_LAYER,
    "Ejaculation": SOCIAL_LAYER,
    "Genital inspect": SOCIAL_LAYER,
    "Stare threat": SOCIAL_LAYER,
    "Open-mouth threat": SOCIAL_LAYER,
    "Head-bob threat": SOCIAL_LAYER,
    "Lunge/Charge": SOCIAL_LAYER,
    "Aggressive vocal": SOCIAL_LAYER,
    "Enlist/Recruit": SOCIAL_LAYER,
    "Slap ground": SOCIAL_LAYER,
    "Cage-shake display": SOCIAL_LAYER,
    "Displacement": SOCIAL_LAYER,
    "Grab attempt": SOCIAL_LAYER,
    "Grab": SOCIAL_LAYER,
    "Bite": SOCIAL_LAYER,
    "Chase": SOCIAL_LAYER,
    "Fight": SOCIAL_LAYER,
    "Redirected aggression": SOCIAL_LAYER,
    "Avoid": SOCIAL_LAYER,
    "Cower/Crouch": SOCIAL_LAYER,
    "Fear grimace": SOCIAL_LAYER,
    "Submissive present": SOCIAL_LAYER,
    "Scream": SOCIAL_LAYER,
    "Flee": SOCIAL_LAYER,
    "Freeze/Ignore": SOCIAL_LAYER,
    "Rest/Stationary": ACTIVITY_LAYER,
    "Sleep": ACTIVITY_LAYER,
    "Self-groom": ACTIVITY_LAYER,
    "Scratch": ACTIVITY_LAYER,
    "Stretch": ACTIVITY_LAYER,
    "Urinate": ACTIVITY_LAYER,
    "Defecate": ACTIVITY_LAYER,
    "Travel": ACTIVITY_LAYER,
    "Forage/Search": ACTIVITY_LAYER,
    "Eat": ACTIVITY_LAYER,
    "Drink": ACTIVITY_LAYER,
    "Chew non-food": ACTIVITY_LAYER,
    "Object manipulate": ACTIVITY_LAYER,
    "Out-of-view": ACTIVITY_LAYER,
    "Vigilant/Scan": ATTENTION_LAYER,
    "Attention to outside agents": ATTENTION_LAYER,
    "Alarm bark": ATTENTION_LAYER,
    "Hiccups": ATYPICAL_LAYER,
    "Pace": ATYPICAL_LAYER,
    "Bounce": ATYPICAL_LAYER,
    "Rock": ATYPICAL_LAYER,
    "Body flip": ATYPICAL_LAYER,
    "Salute/eye poke": ATYPICAL_LAYER,
    "Digit suck": ATYPICAL_LAYER,
    "Genital suck": ATYPICAL_LAYER,
    "Self-hair-pull": ATYPICAL_LAYER,
    "Self-grasp": ATYPICAL_LAYER,
    "Self-bite": ATYPICAL_LAYER,
    "Self-injury (wound)": ATYPICAL_LAYER,
    "Teeth grind": ATYPICAL_LAYER,
    "Head toss": ATYPICAL_LAYER,
    "Blow cheeks/noise": ATYPICAL_LAYER,
    "Coprophagy": ATYPICAL_LAYER,
    "Feces paint": ATYPICAL_LAYER,
    "Bizarre posture": ATYPICAL_LAYER,
    "Yawn": ATYPICAL_LAYER,
}

PRECEDENCE = {
    SOCIAL_LAYER: [
        "Fight",
        "Bite",
        "Grab",
        "Grab attempt",
        "Chase",
        "Lunge/Charge",
        "Displacement",
        "Redirected aggression",
        "Open-mouth threat",
        "Head-bob threat",
        "Stare threat",
        "Aggressive vocal",
        "Enlist/Recruit",
        "Cage-shake display",
        "Slap ground",
        "Mount give",
        "Mount receive",
        "Mount attempt",
        "Intromission",
        "Ejaculation",
        "Groom give",
        "Groom receive",
        "Groom solicit",
        "Contact/Sit-with",
        "Proximity (<arm’s reach)",
        "Approach (non-agonistic)",
        "Leave/Withdraw (non-agonistic)",
        "Affiliative touch",
        "Lip-smack",
        "Muzzle-muzzle contact",
        "Sex present",
        "Genital inspect",
        "Avoid",
        "Cower/Crouch",
        "Fear grimace",
        "Submissive present",
        "Scream",
        "Flee",
        "Freeze/Ignore",
    ],
    ACTIVITY_LAYER: [
        "Out-of-view",
        "Eat",
        "Drink",
        "Forage/Search",
        "Travel",
        "Self-groom",
        "Scratch",
        "Object manipulate",
        "Chew non-food",
        "Urinate",
        "Defecate",
        "Stretch",
        "Sleep",
        "Rest/Stationary",
    ],
    ATTENTION_LAYER: [
        "Attention to outside agents",
        "Alarm bark",
        "Vigilant/Scan",
    ],
    ATYPICAL_LAYER: [
        "Self-injury (wound)",
        "Self-bite",
        "Self-hair-pull",
        "Genital suck",
        "Digit suck",
        "Salute/eye poke",
        "Body flip",
        "Rock",
        "Bounce",
        "Pace",
        "Bizarre posture",
        "Teeth grind",
        "Head toss",
        "Blow cheeks/noise",
        "Coprophagy",
        "Feces paint",
        "Yawn",
        "Hiccups",
    ],
}


@dataclass
class SessionWindow:
    session_id: str
    marker_start_s: float
    marker_end_s: float
    start_s: float
    end_s: float

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


def layer_for_behavior(behavior: str) -> str:
    return BEHAVIOR_LAYER.get(behavior, ACTIVITY_LAYER)


def precedence_rank(layer: str, behavior: str) -> int:
    try:
        return PRECEDENCE[layer].index(behavior)
    except ValueError:
        return len(PRECEDENCE[layer]) + 1


def load_events(path: Path) -> tuple[pd.DataFrame, SessionWindow]:
    events = pd.read_pickle(path).sort_values("Time").reset_index(drop=True)
    marker_start_s = float(events.loc[events["Behavior"] == "Start pairing", "Time"].iloc[0])
    marker_end_s = float(events.loc[events["Behavior"] == "End pairing", "Time"].iloc[0])
    raw_duration = marker_end_s - marker_start_s
    trim_s = EDGE_TRIM_S if raw_duration > (2 * EDGE_TRIM_S) else 0.0
    start_s = marker_start_s + trim_s
    end_s = marker_end_s - trim_s
    return events, SessionWindow(path.stem, marker_start_s, marker_end_s, start_s, end_s)


def build_raw_intervals(events: pd.DataFrame, window: SessionWindow) -> pd.DataFrame:
    starts: dict[str, list[float]] = {}
    intervals: list[dict[str, float | str]] = []
    state_events = events[events["Behavior type"].isin(["START", "STOP"])].copy()

    for _, row in state_events.iterrows():
        behavior = row["Behavior"]
        event_type = row["Behavior type"]
        event_time = float(row["Time"])
        category = row["Behavioral category"]

        if event_type == "START":
            starts.setdefault(behavior, []).append(event_time)
            continue

        if behavior not in starts or not starts[behavior]:
            continue

        start_time = starts[behavior].pop(0)
        clip_start = max(start_time, window.start_s)
        clip_end = min(event_time, window.end_s)
        if clip_end <= clip_start:
            continue

        intervals.append(
            {
                "session_id": window.session_id,
                "behavior": behavior,
                "category": category,
                "start_s": clip_start,
                "end_s": clip_end,
                "duration_s": clip_end - clip_start,
                "layer": layer_for_behavior(behavior),
            }
        )

    if not intervals:
        return pd.DataFrame(columns=["session_id", "behavior", "category", "start_s", "end_s", "duration_s", "layer"])

    return pd.DataFrame(intervals).sort_values(["start_s", "end_s", "behavior"]).reset_index(drop=True)


def merge_same_behavior(intervals: pd.DataFrame, gap_s: float = GAP_MERGE_S) -> pd.DataFrame:
    if intervals.empty:
        return intervals.copy()

    merged_rows: list[dict[str, float | str]] = []
    for (_, behavior, layer), group in intervals.groupby(["session_id", "behavior", "layer"], sort=False):
        group = group.sort_values(["start_s", "end_s"]).reset_index(drop=True)
        current = group.iloc[0].to_dict()
        for row in group.iloc[1:].itertuples(index=False):
            if float(row.start_s) - float(current["end_s"]) <= gap_s:
                current["end_s"] = max(float(current["end_s"]), float(row.end_s))
                current["duration_s"] = float(current["end_s"]) - float(current["start_s"])
            else:
                merged_rows.append(current.copy())
                current = row._asdict()
        merged_rows.append(current.copy())
    merged = pd.DataFrame(merged_rows)
    return merged.sort_values(["start_s", "end_s", "behavior"]).reset_index(drop=True)


def choose_state(layer: str, active_behaviors: Iterable[str]) -> str | None:
    active_behaviors = list(active_behaviors)
    if not active_behaviors:
        return None
    return sorted(active_behaviors, key=lambda b: (precedence_rank(layer, b), b))[0]


def build_layered_timeline(intervals: pd.DataFrame, window: SessionWindow) -> pd.DataFrame:
    boundaries = {window.start_s, window.end_s}
    for row in intervals.itertuples(index=False):
        boundaries.add(float(row.start_s))
        boundaries.add(float(row.end_s))
    bounds = sorted(boundaries)

    if len(bounds) < 2:
        return pd.DataFrame()

    by_layer = {layer: intervals[intervals["layer"] == layer].copy() for layer in LAYER_ORDER}
    timeline_rows: list[dict[str, object]] = []

    for start_s, end_s in zip(bounds[:-1], bounds[1:]):
        if end_s <= start_s:
            continue

        row: dict[str, object] = {
            "session_id": window.session_id,
            "start_s": start_s,
            "end_s": end_s,
            "duration_s": end_s - start_s,
        }
        for layer in LAYER_ORDER:
            active = by_layer[layer]
            mask = (active["start_s"] < end_s) & (active["end_s"] > start_s)
            behaviors = sorted(active.loc[mask, "behavior"].unique().tolist())
            row[f"{layer}_state"] = choose_state(layer, behaviors)
            row[f"{layer}_active"] = "|".join(behaviors)

        social_state = row["social_state"]
        row["social_engaged"] = social_state in {
            "Proximity (<arm’s reach)",
            "Contact/Sit-with",
            "Groom give",
            "Groom receive",
            "Groom solicit",
            "Mount give",
            "Mount receive",
            "Mount attempt",
            "Affiliative touch",
            "Muzzle-muzzle contact",
        }
        row["physical_contact_implied"] = social_state in {
            "Contact/Sit-with",
            "Groom give",
            "Groom receive",
            "Mount give",
            "Mount receive",
            "Mount attempt",
            "Affiliative touch",
            "Muzzle-muzzle contact",
        }
        row["proximity_implied"] = row["social_engaged"]
        timeline_rows.append(row)

    timeline = pd.DataFrame(timeline_rows)
    timeline = timeline[timeline["duration_s"] > 0].reset_index(drop=True)
    return collapse_adjacent_timeline_rows(timeline)


def collapse_adjacent_timeline_rows(timeline: pd.DataFrame) -> pd.DataFrame:
    if timeline.empty:
        return timeline.copy()

    key_cols = [
        "social_state",
        "social_active",
        "activity_state",
        "activity_active",
        "attention_state",
        "attention_active",
        "atypical_state",
        "atypical_active",
        "social_engaged",
        "physical_contact_implied",
        "proximity_implied",
    ]

    rows: list[dict[str, object]] = []
    current = timeline.iloc[0].to_dict()
    for next_row in timeline.iloc[1:].to_dict("records"):
        same_profile = all(current[col] == next_row[col] for col in key_cols)
        contiguous = abs(float(current["end_s"]) - float(next_row["start_s"])) < 1e-9
        if same_profile and contiguous:
            current["end_s"] = next_row["end_s"]
            current["duration_s"] = float(current["end_s"]) - float(current["start_s"])
        else:
            rows.append(current.copy())
            current = next_row.copy()
    rows.append(current.copy())
    return pd.DataFrame(rows)


def state_intervals_from_timeline(timeline: pd.DataFrame, layer: str) -> pd.DataFrame:
    state_col = f"{layer}_state"
    if timeline.empty or state_col not in timeline.columns:
        return pd.DataFrame(columns=["behavior", "start_s", "end_s", "duration_s"])
    state_rows = timeline.loc[timeline[state_col].notna(), [state_col, "start_s", "end_s", "duration_s"]].copy()
    state_rows = state_rows.rename(columns={state_col: "behavior"}).reset_index(drop=True)
    return state_rows


def summarize_session(
    raw_intervals: pd.DataFrame,
    timeline: pd.DataFrame,
    window: SessionWindow,
) -> dict[str, object]:
    summary: dict[str, object] = {
        "session_id": window.session_id,
        "marker_start_s": window.marker_start_s,
        "marker_end_s": window.marker_end_s,
        "session_start_s": window.start_s,
        "session_end_s": window.end_s,
        "session_duration_s": window.duration_s,
        "session_duration_min": window.duration_s / 60.0,
        "edge_trim_s": EDGE_TRIM_S,
    }

    resolved_intervals = pd.concat(
        [state_intervals_from_timeline(timeline, layer) for layer in LAYER_ORDER],
        ignore_index=True,
    )
    duration_by_behavior = resolved_intervals.groupby("behavior")["duration_s"].sum()
    bouts_by_behavior = resolved_intervals.groupby("behavior").size()
    raw_duration_by_behavior = raw_intervals.groupby("behavior")["duration_s"].sum()

    for behavior, duration_s in duration_by_behavior.items():
        safe_name = sanitize_name(behavior)
        summary[f"{safe_name}_resolved_duration_s"] = duration_s
        summary[f"{safe_name}_resolved_pct_session"] = 100.0 * duration_s / window.duration_s
        summary[f"{safe_name}_raw_duration_s"] = float(raw_duration_by_behavior.get(behavior, 0.0))

    for behavior, bout_count in bouts_by_behavior.items():
        safe_name = sanitize_name(behavior)
        summary[f"{safe_name}_resolved_bouts"] = int(bout_count)
        summary[f"{safe_name}_resolved_bouts_per_hour"] = float(bout_count) / (window.duration_s / 3600.0)

    give_s = float(duration_by_behavior.get("Groom give", 0.0))
    receive_s = float(duration_by_behavior.get("Groom receive", 0.0))
    total_groom_s = give_s + receive_s
    give_bouts = int(bouts_by_behavior.get("Groom give", 0))
    receive_bouts = int(bouts_by_behavior.get("Groom receive", 0))
    total_groom_bouts = give_bouts + receive_bouts

    summary["groom_give_pct_session"] = 100.0 * give_s / window.duration_s
    summary["groom_receive_pct_session"] = 100.0 * receive_s / window.duration_s
    summary["groom_total_pct_session"] = 100.0 * total_groom_s / window.duration_s
    summary["groom_give_bouts_per_hour"] = give_bouts / (window.duration_s / 3600.0)
    summary["groom_receive_bouts_per_hour"] = receive_bouts / (window.duration_s / 3600.0)
    summary["groom_total_bouts_per_hour"] = total_groom_bouts / (window.duration_s / 3600.0)
    summary["groom_duration_net_receive_minus_give_s"] = receive_s - give_s
    summary["groom_duration_net_receive_minus_give_pct_session"] = 100.0 * (receive_s - give_s) / window.duration_s
    summary["groom_bout_net_receive_minus_give"] = receive_bouts - give_bouts
    summary["groom_duration_reciprocity_0to1"] = reciprocity_score(receive_s, give_s)
    summary["groom_bout_reciprocity_0to1"] = reciprocity_score(receive_bouts, give_bouts)

    summary["social_engaged_pct_session"] = 100.0 * timeline.loc[timeline["social_engaged"], "duration_s"].sum() / window.duration_s
    summary["physical_contact_implied_pct_session"] = 100.0 * timeline.loc[timeline["physical_contact_implied"], "duration_s"].sum() / window.duration_s
    summary["proximity_implied_pct_session"] = 100.0 * timeline.loc[timeline["proximity_implied"], "duration_s"].sum() / window.duration_s
    summary["unknown_pct_session"] = 100.0 * timeline.loc[
        timeline[["social_state", "activity_state", "attention_state", "atypical_state"]].isna().all(axis=1),
        "duration_s",
    ].sum() / window.duration_s
    return summary


def grooming_timecourse(timeline: pd.DataFrame, window: SessionWindow) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    social_intervals = state_intervals_from_timeline(timeline, SOCIAL_LAYER)
    give_intervals = social_intervals[social_intervals["behavior"] == "Groom give"]
    receive_intervals = social_intervals[social_intervals["behavior"] == "Groom receive"]
    sample_times = np.arange(window.start_s, window.end_s + TIMECOURSE_STEP_S, TIMECOURSE_STEP_S)
    if sample_times[-1] > window.end_s:
        sample_times[-1] = window.end_s
    if sample_times[-1] != window.end_s:
        sample_times = np.append(sample_times, window.end_s)

    for sample_s in sample_times:
        give_s = overlap_duration(give_intervals, window.start_s, sample_s)
        receive_s = overlap_duration(receive_intervals, window.start_s, sample_s)
        give_bouts = completed_bouts_by_time(give_intervals, sample_s)
        receive_bouts = completed_bouts_by_time(receive_intervals, sample_s)
        elapsed_s = sample_s - window.start_s
        recv_minus_give_duration = receive_s - give_s
        recv_minus_give_bouts = receive_bouts - give_bouts
        rows.append(
            {
                "session_id": window.session_id,
                "sample_s": sample_s,
                "elapsed_s": elapsed_s,
                "elapsed_min": elapsed_s / 60.0,
                "elapsed_frac_session": elapsed_s / window.duration_s if window.duration_s else np.nan,
                "cum_groom_give_s": give_s,
                "cum_groom_receive_s": receive_s,
                "cum_groom_total_s": give_s + receive_s,
                "cum_net_duration_receive_minus_give_s": recv_minus_give_duration,
                "cum_groom_give_bouts": give_bouts,
                "cum_groom_receive_bouts": receive_bouts,
                "cum_net_bouts_receive_minus_give": recv_minus_give_bouts,
                "duration_reciprocity_0to1": reciprocity_score(receive_s, give_s),
                "bout_reciprocity_0to1": reciprocity_score(receive_bouts, give_bouts),
            }
        )
    return pd.DataFrame(rows)


def overlap_duration(intervals: pd.DataFrame, start_s: float, end_s: float) -> float:
    if intervals.empty:
        return 0.0
    starts = intervals["start_s"].to_numpy(dtype=float)
    ends = intervals["end_s"].to_numpy(dtype=float)
    return float(np.maximum(0.0, np.minimum(ends, end_s) - np.maximum(starts, start_s)).sum())


def overlapping_bouts(intervals: pd.DataFrame, start_s: float, end_s: float) -> int:
    if intervals.empty:
        return 0
    mask = (intervals["start_s"] < end_s) & (intervals["end_s"] > start_s)
    return int(mask.sum())


def completed_bouts_by_time(intervals: pd.DataFrame, sample_s: float) -> int:
    if intervals.empty:
        return 0
    return int((intervals["start_s"] <= sample_s).sum())


def reciprocity_score(a: float, b: float) -> float | None:
    denom = a + b
    if denom == 0:
        return None
    return 1.0 - (abs(a - b) / denom)


def sanitize_name(value: str) -> str:
    cleaned = []
    for ch in value.lower():
        if ch.isalnum():
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned).strip("_").replace("__", "_")


def load_exceptions() -> pd.DataFrame:
    if not EXCEPTIONS_PATH.exists():
        return pd.DataFrame(columns=["session_id", "exception_timestamp", "exception_flag", "exception_note"])
    exceptions = pd.read_csv(EXCEPTIONS_PATH, dtype={"session_id": str})
    return exceptions


def infer_social_bouts(timeline: pd.DataFrame, window: SessionWindow) -> pd.DataFrame:
    social = timeline.loc[timeline["social_engaged"], ["session_id", "start_s", "end_s", "duration_s", "social_state"]].copy()
    if social.empty:
        return pd.DataFrame(columns=["session_id", "bout_id", "start_s", "end_s", "duration_s", "states"])

    rows = []
    current = social.iloc[0].to_dict()
    states = [current["social_state"]]
    bout_id = 1
    for row in social.iloc[1:].to_dict("records"):
        gap = float(row["start_s"]) - float(current["end_s"])
        if gap <= SOCIAL_BOUT_GAP_S:
            current["end_s"] = row["end_s"]
            current["duration_s"] = float(current["end_s"]) - float(current["start_s"])
            if row["social_state"] not in states:
                states.append(row["social_state"])
        else:
            rows.append(
                {
                    "session_id": window.session_id,
                    "bout_id": bout_id,
                    "start_s": current["start_s"],
                    "end_s": current["end_s"],
                    "duration_s": current["duration_s"],
                    "states": "|".join(states),
                }
            )
            bout_id += 1
            current = row.copy()
            states = [current["social_state"]]
    rows.append(
        {
            "session_id": window.session_id,
            "bout_id": bout_id,
            "start_s": current["start_s"],
            "end_s": current["end_s"],
            "duration_s": current["duration_s"],
            "states": "|".join(states),
        }
    )
    return pd.DataFrame(rows)


def infer_leave_events(timeline: pd.DataFrame, window: SessionWindow) -> pd.DataFrame:
    rows = []
    t = timeline.reset_index(drop=True)
    for idx, row in t.iterrows():
        if not bool(row["proximity_implied"]):
            continue
        if idx + 1 >= len(t):
            continue
        next_row = t.iloc[idx + 1]
        if float(next_row["start_s"]) - float(row["end_s"]) > 1e-9:
            continue
        if bool(next_row["proximity_implied"]):
            continue
        if next_row["activity_state"] != "Travel":
            continue

        return_window_end = min(float(next_row["end_s"]) + LEAVE_RETURN_GAP_S, window.end_s)
        future = t[(t["start_s"] < return_window_end) & (t["end_s"] > float(next_row["end_s"]))]
        returned = bool(future["proximity_implied"].fillna(False).any())
        if returned:
            continue

        rows.append(
            {
                "session_id": window.session_id,
                "leave_time_s": float(next_row["start_s"]),
                "preceding_social_state": row["social_state"],
                "travel_duration_s": float(next_row["duration_s"]),
            }
        )
    return pd.DataFrame(rows)


def summarize_social_bouts(social_bouts: pd.DataFrame, leave_events: pd.DataFrame, summary: dict[str, object]) -> dict[str, object]:
    if social_bouts.empty:
        summary["social_bout_count"] = 0
        summary["social_bouts_per_hour"] = 0.0
        summary["social_bout_median_s"] = np.nan
        summary["social_bout_mean_s"] = np.nan
    else:
        summary["social_bout_count"] = int(len(social_bouts))
        session_hours = summary["session_duration_s"] / 3600.0
        summary["social_bouts_per_hour"] = len(social_bouts) / session_hours if session_hours else np.nan
        summary["social_bout_median_s"] = float(social_bouts["duration_s"].median())
        summary["social_bout_mean_s"] = float(social_bouts["duration_s"].mean())

    summary["inferred_leave_count"] = int(len(leave_events))
    session_hours = summary["session_duration_s"] / 3600.0
    summary["inferred_leave_per_hour"] = len(leave_events) / session_hours if session_hours else np.nan
    return summary


def main() -> None:
    INTERVALS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    exceptions = load_exceptions()

    summary_rows: list[dict[str, object]] = []
    grooming_timeseries: list[pd.DataFrame] = []
    social_bout_tables: list[pd.DataFrame] = []
    leave_tables: list[pd.DataFrame] = []

    for table_path in sorted(TABLES_DIR.glob("*.pkl")):
        events, window = load_events(table_path)
        raw_intervals = build_raw_intervals(events, window)
        merged_intervals = merge_same_behavior(raw_intervals, GAP_MERGE_S)
        timeline = build_layered_timeline(merged_intervals, window)
        social_bouts = infer_social_bouts(timeline, window)
        leave_events = infer_leave_events(timeline, window)

        merged_intervals.to_csv(INTERVALS_DIR / f"{window.session_id}_behavior_intervals.csv", index=False)
        timeline.to_csv(INTERVALS_DIR / f"{window.session_id}_layered_timeline.csv", index=False)
        social_bouts.to_csv(INTERVALS_DIR / f"{window.session_id}_social_bouts.csv", index=False)
        leave_events.to_csv(INTERVALS_DIR / f"{window.session_id}_inferred_leaves.csv", index=False)

        summary = summarize_session(merged_intervals, timeline, window)
        summary_rows.append(summarize_social_bouts(social_bouts, leave_events, summary))
        grooming_timeseries.append(grooming_timecourse(timeline, window))
        social_bout_tables.append(social_bouts)
        leave_tables.append(leave_events)

    summary_df = pd.DataFrame(summary_rows)
    summary_df["session_id"] = summary_df["session_id"].astype(str)
    if not exceptions.empty:
        summary_df = summary_df.merge(exceptions, on="session_id", how="left")
        summary_df["has_exception_note"] = summary_df["exception_note"].notna()
    else:
        summary_df["exception_timestamp"] = pd.NA
        summary_df["exception_flag"] = pd.NA
        summary_df["exception_note"] = pd.NA
        summary_df["has_exception_note"] = False
    summary_df.sort_values("session_id").to_csv(SUMMARIES_DIR / "blinded_session_summary.csv", index=False)
    pd.concat(grooming_timeseries, ignore_index=True).sort_values(["session_id", "sample_s"]).to_csv(
        SUMMARIES_DIR / "blinded_grooming_timecourse.csv", index=False
    )
    pd.concat(social_bout_tables, ignore_index=True).to_csv(SUMMARIES_DIR / "blinded_social_bouts.csv", index=False)
    pd.concat(leave_tables, ignore_index=True).to_csv(SUMMARIES_DIR / "blinded_inferred_leaves.csv", index=False)


if __name__ == "__main__":
    main()

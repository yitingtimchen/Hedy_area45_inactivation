from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

PARENT = Path(__file__).resolve().parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from compute_quiet_mask_sensitivity import compute_smoothed_loud_mask  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
BORIS_DIR = ROOT / "data" / "raw" / "boris"
DERIVED_AUDIO_DIR = ROOT / "data" / "derived" / "audio"
BLINDED_TABLES_DIR = ROOT / "results" / "blinded" / "tables"

EDGE_TRIM_S = 30.0

SOCIAL_BEHAVIORS = [
    "Approach (non-agonistic)",
    "Proximity (<arm's reach)",
    "Groom solicit",
    "Mount attempt",
    "Mount give",
    "Mount receive",
    "Aggressive vocal",
    "Open-mouth threat",
    "Enlist/Recruit",
    "Cage-shake display",
]

FAMILY_MAP = {
    "affiliative_nongroom": [
        "Approach (non-agonistic)",
        "Proximity (<arm's reach)",
        "Groom solicit",
    ],
    "sexual": [
        "Mount attempt",
        "Mount give",
        "Mount receive",
    ],
    "aggression_display": [
        "Aggressive vocal",
        "Open-mouth threat",
        "Enlist/Recruit",
        "Cage-shake display",
    ],
}


def extract_behavior_intervals(events: pd.DataFrame, session_id: str) -> tuple[pd.DataFrame, float]:
    marker_start = float(events.loc[events["Behavior"] == "Start pairing", "Time"].iloc[0])
    marker_end = float(events.loc[events["Behavior"] == "End pairing", "Time"].iloc[0])
    raw_duration = marker_end - marker_start
    trim_s = EDGE_TRIM_S if raw_duration > (2 * EDGE_TRIM_S) else 0.0
    start_s = marker_start + trim_s
    end_s = marker_end - trim_s
    duration_s = end_s - start_s

    starts: dict[str, list[float]] = {}
    rows: list[dict[str, object]] = []
    state_events = events[events["Behavior type"].isin(["START", "STOP"])].copy()
    for _, row in state_events.iterrows():
        behavior = str(row["Behavior"])
        if behavior not in SOCIAL_BEHAVIORS:
            continue
        event_type = str(row["Behavior type"])
        event_time = float(row["Time"])
        if event_type == "START":
            starts.setdefault(behavior, []).append(event_time)
            continue
        if behavior not in starts or not starts[behavior]:
            continue
        start_time = starts[behavior].pop(0)
        clip_start = max(start_time, start_s)
        clip_end = min(event_time, end_s)
        if clip_end <= clip_start:
            continue
        rows.append(
            {
                "session_id": session_id,
                "behavior": behavior,
                "start_s": clip_start,
                "end_s": clip_end,
                "duration_s": clip_end - clip_start,
            }
        )
    return pd.DataFrame(rows), duration_s


def summarize_session(session_id: str) -> tuple[dict[str, object], pd.DataFrame]:
    events = pd.read_pickle(BORIS_DIR / f"{session_id}.pkl").sort_values("Time").reset_index(drop=True)
    intervals, session_duration_s = extract_behavior_intervals(events, session_id)
    row: dict[str, object] = {
        "session_id": session_id,
        "session_duration_s": session_duration_s,
    }

    for behavior in SOCIAL_BEHAVIORS:
        sub = intervals.loc[intervals["behavior"] == behavior]
        duration_s = float(sub["duration_s"].sum()) if not sub.empty else 0.0
        bouts = int(len(sub))
        row[f"{behavior}_duration_pct_session"] = 100.0 * duration_s / session_duration_s if session_duration_s > 0 else np.nan
        row[f"{behavior}_bout_count"] = bouts

    for family, members in FAMILY_MAP.items():
        sub = intervals.loc[intervals["behavior"].isin(members)]
        duration_s = float(sub["duration_s"].sum()) if not sub.empty else 0.0
        bouts = int(len(sub))
        row[f"{family}_duration_pct_session"] = 100.0 * duration_s / session_duration_s if session_duration_s > 0 else np.nan
        row[f"{family}_bout_count"] = bouts

    return row, intervals


def overlapped_duration(intervals: pd.DataFrame, quiet_bins: np.ndarray) -> float:
    if intervals.empty or quiet_bins.size == 0:
        return 0.0
    total = 0.0
    for interval in intervals.itertuples(index=False):
        start = float(interval.start_s)
        end = float(interval.end_s)
        overlap_start = np.maximum(start, quiet_bins[:, 0])
        overlap_end = np.minimum(end, quiet_bins[:, 1])
        total += float(np.clip(overlap_end - overlap_start, a_min=0.0, a_max=None).sum())
    return total


def summarize_session_quiet(intervals: pd.DataFrame, quiet_bins: np.ndarray, quiet_duration_s: float) -> dict[str, object]:
    row: dict[str, object] = {
        "session_duration_quiet_masked_s": quiet_duration_s,
    }
    for behavior in SOCIAL_BEHAVIORS:
        sub = intervals.loc[intervals["behavior"] == behavior]
        duration_s = overlapped_duration(sub, quiet_bins)
        row[f"{behavior}_duration_pct_quiet_masked_p90"] = 100.0 * duration_s / quiet_duration_s if quiet_duration_s > 0 else np.nan

    for family, members in FAMILY_MAP.items():
        sub = intervals.loc[intervals["behavior"].isin(members)]
        duration_s = overlapped_duration(sub, quiet_bins)
        row[f"{family}_duration_pct_quiet_masked_p90"] = 100.0 * duration_s / quiet_duration_s if quiet_duration_s > 0 else np.nan
    return row


def main() -> None:
    session_summary = pd.read_csv(BLINDED_TABLES_DIR / "blinded_session_summary.csv", dtype={"session_id": str})
    audio_features = pd.read_csv(DERIVED_AUDIO_DIR / "blinded_audio_features_1s_labeled.csv")
    session_ids = session_summary["session_id"].astype(str).tolist()

    session_rows = []
    interval_tables = []
    for session_id in session_ids:
        session_row, interval_df = summarize_session(session_id)
        audio_group = audio_features.loc[audio_features["session_id"].astype(str) == session_id].sort_values("bin_start_s").reset_index(drop=True)
        loud_mask, _, _ = compute_smoothed_loud_mask(audio_group)
        quiet_group = audio_group.loc[~loud_mask, ["bin_start_s", "bin_end_s"]].copy()
        quiet_bins = quiet_group.to_numpy(dtype=float) if not quiet_group.empty else np.empty((0, 2), dtype=float)
        session_row.update(summarize_session_quiet(interval_df, quiet_bins, float(quiet_group["bin_end_s"].sub(quiet_group["bin_start_s"]).sum())))
        session_rows.append(session_row)
        if not interval_df.empty:
            interval_tables.append(interval_df)

    metrics_df = pd.DataFrame(session_rows).sort_values("session_id").reset_index(drop=True)
    interval_df = pd.concat(interval_tables, ignore_index=True) if interval_tables else pd.DataFrame()

    BLINDED_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(BLINDED_TABLES_DIR / "blinded_social_nonprecedence_metrics_by_session.csv", index=False)
    if not interval_df.empty:
        interval_df.to_csv(BLINDED_TABLES_DIR / "blinded_social_nonprecedence_interval_table.csv", index=False)


if __name__ == "__main__":
    main()

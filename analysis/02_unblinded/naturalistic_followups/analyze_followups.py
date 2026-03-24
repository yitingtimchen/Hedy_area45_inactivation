from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PARENT = Path(__file__).resolve().parents[1]
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from naturalistic_followups.common import (  # noqa: E402
    compare_conditions,
    ensure_full_output_dirs,
    format_summary_line,
    load_behavior_intervals,
    load_timeline,
    load_unblinding_map,
    normalize_text,
    overlap_duration,
)


LAG_WINDOWS_S = [30.0, 120.0, 300.0, 600.0]
SHUFFLE_WINDOWS_S = [120.0, 600.0]
N_SHUFFLES = 2000

NEGATIVE_SOCIAL_BEHAVIORS = {
    "Aggressive vocal",
    "Open-mouth threat",
    "Head-bob threat",
    "Stare threat",
    "Enlist/Recruit",
    "Cage-shake display",
    "Lunge/Charge",
    "Displacement",
    "Grab attempt",
    "Grab",
    "Bite",
    "Chase",
    "Fight",
    "Redirected aggression",
    "Avoid",
    "Cower/Crouch",
    "Fear grimace",
    "Submissive present",
    "Scream",
    "Flee",
    "Freeze/Ignore",
}

AFFILIATIVE_REPAIR_BEHAVIORS = {
    "Approach (non-agonistic)",
    "Proximity (<arm's reach)",
    "Contact/Sit-with",
    "Affiliative touch",
    "Muzzle-muzzle contact",
    "Groom give",
    "Groom receive",
    "Groom solicit",
}

GROOM_BEHAVIORS = {"Groom give", "Groom receive"}
TRAVEL_BEHAVIORS = {"Travel"}
AFFILIATIVE_SOCIAL_ONSETS = AFFILIATIVE_REPAIR_BEHAVIORS

ATTENTION_ALERT_STATES = {"Vigilant/Scan", "Attention to outside agents"}

LEDGER_METRICS = [
    "give_to_receive_prob_120s",
    "receive_to_give_prob_120s",
    "give_to_receive_prob_600s",
    "receive_to_give_prob_600s",
    "give_to_receive_prob_120s_minus_shuffle",
    "receive_to_give_prob_120s_minus_shuffle",
    "give_to_receive_latency_median_s",
    "receive_to_give_latency_median_s",
]

REPAIR_METRICS = [
    "negative_trigger_count",
    "affiliative_repair_prob_120s",
    "groom_repair_prob_120s",
    "travel_disengage_prob_120s",
    "repair_before_travel_prob",
    "affiliative_repair_latency_median_s",
    "travel_disengage_latency_median_s",
]

BUFFERING_METRICS = [
    "alertness_delta_60s_after_grooming",
    "outside_attention_delta_60s_after_grooming",
    "total_arousal_delta_120s_after_grooming",
    "alertness_delta_60s_after_affiliative_social",
    "outside_attention_delta_60s_after_affiliative_social",
    "total_arousal_delta_120s_after_affiliative_social",
]

LEDGER_LABELS = {
    "give_to_receive_prob_120s": "Return-groom probability within 120 s after Hedy grooms Hooke",
    "receive_to_give_prob_120s": "Return-groom probability within 120 s after Hooke grooms Hedy",
    "give_to_receive_prob_600s": "Return-groom probability within 600 s after Hedy grooms Hooke",
    "receive_to_give_prob_600s": "Return-groom probability within 600 s after Hooke grooms Hedy",
    "give_to_receive_prob_120s_minus_shuffle": "Observed minus shuffled 120 s return probability after Hedy grooms Hooke",
    "receive_to_give_prob_120s_minus_shuffle": "Observed minus shuffled 120 s return probability after Hooke grooms Hedy",
    "give_to_receive_latency_median_s": "Median latency until Hooke returns grooming after Hedy grooms",
    "receive_to_give_latency_median_s": "Median latency until Hedy returns grooming after Hooke grooms",
}

REPAIR_LABELS = {
    "negative_trigger_count": "Negative social trigger count per session",
    "affiliative_repair_prob_120s": "Probability of affiliative repair within 120 s after a negative social event",
    "groom_repair_prob_120s": "Probability of grooming-based repair within 120 s after a negative social event",
    "travel_disengage_prob_120s": "Probability of travel disengagement within 120 s after a negative social event",
    "repair_before_travel_prob": "Probability that affiliative repair occurs before travel disengagement",
    "affiliative_repair_latency_median_s": "Median latency to affiliative repair after a negative social event",
    "travel_disengage_latency_median_s": "Median latency to travel disengagement after a negative social event",
}

BUFFERING_LABELS = {
    "alertness_delta_60s_after_grooming": "Post-minus-pre alertness load after grooming onset",
    "outside_attention_delta_60s_after_grooming": "Post-minus-pre outside-attention load after grooming onset",
    "total_arousal_delta_120s_after_grooming": "Post-minus-pre total arousal-like load after grooming onset",
    "alertness_delta_60s_after_affiliative_social": "Post-minus-pre alertness load after affiliative-social onset",
    "outside_attention_delta_60s_after_affiliative_social": "Post-minus-pre outside-attention load after affiliative-social onset",
    "total_arousal_delta_120s_after_affiliative_social": "Post-minus-pre total arousal-like load after affiliative-social onset",
}


def first_future_event(events: pd.DataFrame, anchor_s: float) -> pd.Series | None:
    future = events.loc[events["start_s"].to_numpy(dtype=float) >= (anchor_s - 1e-9)]
    if future.empty:
        return None
    return future.sort_values("start_s").iloc[0]


def build_ledger_events(session_id: str, intervals: pd.DataFrame, session_start_s: float, session_end_s: float) -> pd.DataFrame:
    groom = intervals.loc[intervals["behavior"].isin(GROOM_BEHAVIORS)].copy()
    groom = groom.sort_values(["start_s", "end_s"]).reset_index(drop=True)
    if groom.empty:
        return pd.DataFrame()

    rows: list[dict[str, object]] = []
    for row in groom.itertuples(index=False):
        trigger_behavior = normalize_text(row.behavior)
        trigger_end_s = float(row.end_s)
        opposite_behavior = "Groom receive" if trigger_behavior == "Groom give" else "Groom give"
        future_opposite = groom.loc[
            (groom["behavior"] == opposite_behavior) & (groom["start_s"].to_numpy(dtype=float) >= (trigger_end_s - 1e-9))
        ].sort_values("start_s")
        next_row = future_opposite.iloc[0] if not future_opposite.empty else None
        latency_s = float(next_row["start_s"] - trigger_end_s) if next_row is not None else np.nan
        event_row: dict[str, object] = {
            "session_id": session_id,
            "trigger_behavior": trigger_behavior,
            "trigger_start_s": float(row.start_s),
            "trigger_end_s": trigger_end_s,
            "trigger_duration_s": float(row.duration_s),
            "opposite_behavior": opposite_behavior,
            "return_latency_s": latency_s,
            "session_start_s": session_start_s,
            "session_end_s": session_end_s,
        }
        for window_s in LAG_WINDOWS_S:
            eligible = trigger_end_s + window_s <= session_end_s + 1e-9
            success = bool(eligible and np.isfinite(latency_s) and latency_s <= window_s)
            event_row[f"eligible_{int(window_s)}s"] = bool(eligible)
            event_row[f"returned_within_{int(window_s)}s"] = success
        rows.append(event_row)
    return pd.DataFrame(rows)


def shuffled_return_probability(
    trigger_ends: np.ndarray,
    opposite_starts: np.ndarray,
    session_start_s: float,
    session_end_s: float,
    window_s: float,
    seed: int,
) -> float | None:
    duration_s = session_end_s - session_start_s
    if duration_s <= window_s or len(trigger_ends) == 0 or len(opposite_starts) == 0:
        return None
    eligible = trigger_ends + window_s <= session_end_s + 1e-9
    if not np.any(eligible):
        return None

    trigger_rel = trigger_ends[eligible] - session_start_s
    opposite_rel = opposite_starts - session_start_s
    rng = np.random.default_rng(seed)
    probs = []
    for _ in range(N_SHUFFLES):
        shift = rng.uniform(0.0, duration_s)
        shifted = np.mod(opposite_rel + shift, duration_s)
        delta = shifted[None, :] - trigger_rel[:, None]
        delta[delta < 0.0] += duration_s
        success = ((delta > 1e-9) & (delta <= window_s)).any(axis=1)
        probs.append(float(success.mean()))
    return float(np.mean(np.asarray(probs, dtype=float)))


def summarize_ledger_session(event_df: pd.DataFrame) -> dict[str, object]:
    summary: dict[str, object] = {
        "give_trigger_count": 0,
        "receive_trigger_count": 0,
    }
    if event_df.empty:
        for metric in LEDGER_METRICS:
            summary[metric] = np.nan
        summary["give_to_receive_prob_600s_minus_shuffle"] = np.nan
        summary["receive_to_give_prob_600s_minus_shuffle"] = np.nan
        return summary

    session_start_s = float(event_df["session_start_s"].iloc[0])
    session_end_s = float(event_df["session_end_s"].iloc[0])
    for trigger_behavior, prefix in [("Groom give", "give_to_receive"), ("Groom receive", "receive_to_give")]:
        sub = event_df.loc[event_df["trigger_behavior"] == trigger_behavior].copy()
        summary["give_trigger_count" if prefix == "give_to_receive" else "receive_trigger_count"] = int(len(sub))
        if sub.empty:
            for window_s in LAG_WINDOWS_S:
                summary[f"{prefix}_prob_{int(window_s)}s"] = np.nan
            summary[f"{prefix}_latency_median_s"] = np.nan
            summary[f"{prefix}_prob_120s_minus_shuffle"] = np.nan
            summary[f"{prefix}_prob_600s_minus_shuffle"] = np.nan
            continue

        latencies = pd.to_numeric(sub["return_latency_s"], errors="coerce").dropna()
        summary[f"{prefix}_latency_median_s"] = float(latencies.median()) if not latencies.empty else np.nan

        trigger_ends = sub["trigger_end_s"].to_numpy(dtype=float)
        opposite_starts = event_df.loc[event_df["trigger_behavior"] != trigger_behavior, "trigger_start_s"].to_numpy(dtype=float)
        base_seed = int(sub["session_id"].iloc[0]) + (1 if trigger_behavior == "Groom give" else 7)

        for window_s in LAG_WINDOWS_S:
            eligible_col = f"eligible_{int(window_s)}s"
            success_col = f"returned_within_{int(window_s)}s"
            eligible = sub.loc[sub[eligible_col], success_col]
            summary[f"{prefix}_prob_{int(window_s)}s"] = float(eligible.mean()) if len(eligible) else np.nan
            if window_s in SHUFFLE_WINDOWS_S:
                shuffled = shuffled_return_probability(
                    trigger_ends,
                    opposite_starts,
                    session_start_s,
                    session_end_s,
                    window_s,
                    seed=base_seed + int(window_s),
                )
                observed = summary[f"{prefix}_prob_{int(window_s)}s"]
                summary[f"{prefix}_prob_{int(window_s)}s_minus_shuffle"] = (
                    observed - shuffled if shuffled is not None and np.isfinite(observed) else np.nan
                )
    return summary


def build_repair_events(session_id: str, intervals: pd.DataFrame, timeline: pd.DataFrame) -> pd.DataFrame:
    negative = intervals.loc[intervals["behavior"].isin(NEGATIVE_SOCIAL_BEHAVIORS)].copy()
    negative = negative.sort_values(["start_s", "end_s"]).reset_index(drop=True)
    if negative.empty:
        return pd.DataFrame()

    repair = intervals.loc[intervals["behavior"].isin(AFFILIATIVE_REPAIR_BEHAVIORS)].copy()
    grooming = intervals.loc[intervals["behavior"].isin(GROOM_BEHAVIORS)].copy()
    travel = intervals.loc[intervals["behavior"].isin(TRAVEL_BEHAVIORS)].copy()
    session_end_s = float(timeline["end_s"].max())

    rows: list[dict[str, object]] = []
    for row in negative.itertuples(index=False):
        trigger_end_s = float(row.end_s)
        repair_row = first_future_event(repair, trigger_end_s)
        groom_row = first_future_event(grooming, trigger_end_s)
        travel_row = first_future_event(travel, trigger_end_s)

        repair_latency = float(repair_row["start_s"] - trigger_end_s) if repair_row is not None else np.nan
        groom_latency = float(groom_row["start_s"] - trigger_end_s) if groom_row is not None else np.nan
        travel_latency = float(travel_row["start_s"] - trigger_end_s) if travel_row is not None else np.nan
        rows.append(
            {
                "session_id": session_id,
                "trigger_behavior": normalize_text(row.behavior),
                "trigger_start_s": float(row.start_s),
                "trigger_end_s": trigger_end_s,
                "trigger_duration_s": float(row.duration_s),
                "affiliative_repair_latency_s": repair_latency,
                "groom_repair_latency_s": groom_latency,
                "travel_disengage_latency_s": travel_latency,
                "repair_before_travel": bool(
                    np.isfinite(repair_latency) and (not np.isfinite(travel_latency) or repair_latency < travel_latency)
                ),
                "session_end_s": session_end_s,
            }
        )
    event_df = pd.DataFrame(rows)
    for window_s in [30.0, 120.0, 300.0]:
        event_df[f"eligible_{int(window_s)}s"] = event_df["trigger_end_s"] + window_s <= event_df["session_end_s"] + 1e-9
        event_df[f"affiliative_repair_within_{int(window_s)}s"] = (
            event_df[f"eligible_{int(window_s)}s"] & event_df["affiliative_repair_latency_s"].le(window_s)
        )
        event_df[f"groom_repair_within_{int(window_s)}s"] = (
            event_df[f"eligible_{int(window_s)}s"] & event_df["groom_repair_latency_s"].le(window_s)
        )
        event_df[f"travel_disengage_within_{int(window_s)}s"] = (
            event_df[f"eligible_{int(window_s)}s"] & event_df["travel_disengage_latency_s"].le(window_s)
        )
    return event_df


def summarize_repair_session(event_df: pd.DataFrame) -> dict[str, object]:
    summary = {
        "negative_trigger_count": int(len(event_df)),
        "affiliative_repair_prob_120s": np.nan,
        "groom_repair_prob_120s": np.nan,
        "travel_disengage_prob_120s": np.nan,
        "repair_before_travel_prob": np.nan,
        "affiliative_repair_latency_median_s": np.nan,
        "travel_disengage_latency_median_s": np.nan,
    }
    if event_df.empty:
        return summary

    eligible_120 = event_df.loc[event_df["eligible_120s"]]
    if not eligible_120.empty:
        summary["affiliative_repair_prob_120s"] = float(eligible_120["affiliative_repair_within_120s"].mean())
        summary["groom_repair_prob_120s"] = float(eligible_120["groom_repair_within_120s"].mean())
        summary["travel_disengage_prob_120s"] = float(eligible_120["travel_disengage_within_120s"].mean())
        summary["repair_before_travel_prob"] = float(eligible_120["repair_before_travel"].mean())

    repair_lat = pd.to_numeric(event_df["affiliative_repair_latency_s"], errors="coerce").dropna()
    travel_lat = pd.to_numeric(event_df["travel_disengage_latency_s"], errors="coerce").dropna()
    summary["affiliative_repair_latency_median_s"] = float(repair_lat.median()) if not repair_lat.empty else np.nan
    summary["travel_disengage_latency_median_s"] = float(travel_lat.median()) if not travel_lat.empty else np.nan
    return summary


def state_fraction(timeline: pd.DataFrame, start_s: float, end_s: float, state_kind: str) -> float:
    duration_s = end_s - start_s
    if duration_s <= 0:
        return np.nan

    if state_kind == "alertness":
        mask = timeline["attention_state"].isin(ATTENTION_ALERT_STATES)
    elif state_kind == "outside_attention":
        mask = timeline["attention_state"] == "Attention to outside agents"
    elif state_kind == "scratch_hiccups":
        mask = (timeline["activity_state"] == "Scratch") | (timeline["atypical_state"] == "Hiccups")
    elif state_kind == "total_arousal":
        mask = (
            timeline["attention_state"].isin(ATTENTION_ALERT_STATES)
            | (timeline["activity_state"] == "Scratch")
            | (timeline["atypical_state"] == "Hiccups")
        )
    else:
        raise KeyError(state_kind)

    overlap = overlap_duration(timeline.loc[mask, ["start_s", "end_s"]], start_s, end_s)
    return float(overlap / duration_s)


def build_buffering_events(session_id: str, intervals: pd.DataFrame, timeline: pd.DataFrame) -> pd.DataFrame:
    session_start_s = float(timeline["start_s"].min())
    session_end_s = float(timeline["end_s"].max())
    trigger_defs = {
        "grooming": intervals.loc[intervals["behavior"].isin(GROOM_BEHAVIORS)].copy(),
        "affiliative_social": intervals.loc[intervals["behavior"].isin(AFFILIATIVE_SOCIAL_ONSETS)].copy(),
    }
    rows: list[dict[str, object]] = []
    for trigger_type, trigger_df in trigger_defs.items():
        if trigger_df.empty:
            continue
        trigger_df = trigger_df.sort_values(["start_s", "end_s"]).reset_index(drop=True)
        for row in trigger_df.itertuples(index=False):
            trigger_start_s = float(row.start_s)
            if trigger_start_s - 120.0 < session_start_s - 1e-9 or trigger_start_s + 120.0 > session_end_s + 1e-9:
                continue
            record = {
                "session_id": session_id,
                "trigger_type": trigger_type,
                "trigger_behavior": normalize_text(row.behavior),
                "trigger_start_s": trigger_start_s,
            }
            for state_kind, window_s in [
                ("alertness", 60.0),
                ("outside_attention", 60.0),
                ("scratch_hiccups", 120.0),
                ("total_arousal", 120.0),
            ]:
                pre_value = state_fraction(timeline, trigger_start_s - window_s, trigger_start_s, state_kind)
                post_value = state_fraction(timeline, trigger_start_s, trigger_start_s + window_s, state_kind)
                record[f"{state_kind}_pre_{int(window_s)}s"] = pre_value
                record[f"{state_kind}_post_{int(window_s)}s"] = post_value
                record[f"{state_kind}_delta_{int(window_s)}s"] = post_value - pre_value
            rows.append(record)
    return pd.DataFrame(rows)


def summarize_buffering_session(event_df: pd.DataFrame) -> dict[str, object]:
    summary = {
        "grooming_trigger_count": 0,
        "affiliative_social_trigger_count": 0,
    }
    for metric in BUFFERING_METRICS:
        summary[metric] = np.nan
    if event_df.empty:
        return summary

    for trigger_type, prefix in [("grooming", "grooming"), ("affiliative_social", "affiliative_social")]:
        sub = event_df.loc[event_df["trigger_type"] == trigger_type].copy()
        summary[f"{prefix}_trigger_count"] = int(len(sub))
        if sub.empty:
            continue
        summary[f"alertness_delta_60s_after_{prefix}"] = float(sub["alertness_delta_60s"].mean())
        summary[f"outside_attention_delta_60s_after_{prefix}"] = float(sub["outside_attention_delta_60s"].mean())
        summary[f"total_arousal_delta_120s_after_{prefix}"] = float(sub["total_arousal_delta_120s"].mean())
    return summary


def build_ledger_markdown(summary: pd.DataFrame) -> str:
    lines = [
        "# Grooming Ledger Analysis",
        "",
        "This follow-up extends the same-episode grooming analysis to medium timescales by asking how often the opposite grooming direction appears within fixed lag windows after a grooming bout ends.",
        "",
        "## Definitions",
        "",
        "- Trigger bouts come from the cleaned merged social-behavior intervals.",
        "- `Groom give -> Groom receive` means Hedy grooms first and Hooke later returns grooming.",
        "- `Groom receive -> Groom give` is the symmetric reverse direction.",
        "- Window-based probabilities use only triggers with the full future window still observed inside the session.",
        "- The shuffled baseline circularly shifts the opposite-direction grooming starts within session to estimate a within-session chance expectation while preserving each session's event count.",
        "",
        "## Condition comparisons",
        "",
    ]
    for metric in LEDGER_METRICS:
        row = summary.loc[summary["metric"] == metric]
        if row.empty:
            continue
        lines.append(format_summary_line(row.iloc[0], LEDGER_LABELS[metric]))
    lines.append("")
    return "\n".join(lines)


def build_repair_markdown(summary: pd.DataFrame, event_df: pd.DataFrame) -> str:
    n_events = int(len(event_df))
    lines = [
        "# Post-Conflict Repair And Disengagement",
        "",
        "This follow-up treats threat- or disruption-like social events as triggers and asks whether the next short-horizon tendency is affiliative repair or behavioral disengagement.",
        "",
        "## Definitions",
        "",
        "- Negative triggers are aggressive, threat, or submission-family social events from the cleaned interval table.",
        "- `Affiliative repair` is the next occurrence of approach, proximity, contact, grooming, grooming solicitation, affiliative touch, or muzzle contact after the trigger ends.",
        "- `Travel disengagement` is the next occurrence of `Travel` after the trigger ends.",
        "- The primary comparison window is 120 s and uses only triggers with the full 120 s still visible in the session.",
        f"- Total negative trigger events in the full cohort: `{n_events}`.",
        "",
        "## Condition comparisons",
        "",
    ]
    for metric in REPAIR_METRICS:
        row = summary.loc[summary["metric"] == metric]
        if row.empty:
            continue
        lines.append(format_summary_line(row.iloc[0], REPAIR_LABELS[metric]))
    lines.append("")
    return "\n".join(lines)


def build_buffering_markdown(summary: pd.DataFrame) -> str:
    lines = [
        "# Social Buffering And Co-Regulation",
        "",
        "This follow-up asks whether affiliative onsets are followed by short-horizon decreases in alertness- or arousal-like states using only the existing behavior layers.",
        "",
        "## Definitions",
        "",
        "- `Alertness load` is the fraction of time spent in `Vigilant/Scan` or `Attention to outside agents`.",
        "- `Outside-attention load` isolates `Attention to outside agents` alone.",
        "- `Total arousal-like load` is the fraction of time spent in alertness states, `Scratch`, or `Hiccups`.",
        "- Each metric is computed as `post window - pre window` around event onset, so negative values indicate buffering-like reductions after the affiliative event begins.",
        "- Grooming and broader affiliative-social triggers require a full 120 s pre window and 120 s post window inside the observed session.",
        "",
        "## Condition comparisons",
        "",
    ]
    for metric in BUFFERING_METRICS:
        row = summary.loc[summary["metric"] == metric]
        if row.empty:
            continue
        lines.append(format_summary_line(row.iloc[0], BUFFERING_LABELS[metric]))
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    tables_dir, _, docs_dir = ensure_full_output_dirs()
    session_map = load_unblinding_map()

    ledger_session_rows: list[dict[str, object]] = []
    repair_session_rows: list[dict[str, object]] = []
    buffering_session_rows: list[dict[str, object]] = []
    ledger_events_all: list[pd.DataFrame] = []
    repair_events_all: list[pd.DataFrame] = []
    buffering_events_all: list[pd.DataFrame] = []

    for session_id in session_map["session_id"].astype(str):
        intervals = load_behavior_intervals(session_id)
        timeline = load_timeline(session_id)
        session_start_s = float(timeline["start_s"].min())
        session_end_s = float(timeline["end_s"].max())

        ledger_events = build_ledger_events(session_id, intervals, session_start_s, session_end_s)
        repair_events = build_repair_events(session_id, intervals, timeline)
        buffering_events = build_buffering_events(session_id, intervals, timeline)

        ledger_events_all.append(ledger_events)
        repair_events_all.append(repair_events)
        buffering_events_all.append(buffering_events)

        ledger_session_rows.append({"session_id": session_id, **summarize_ledger_session(ledger_events)})
        repair_session_rows.append({"session_id": session_id, **summarize_repair_session(repair_events)})
        buffering_session_rows.append({"session_id": session_id, **summarize_buffering_session(buffering_events)})

    ledger_events_df = pd.concat([df for df in ledger_events_all if not df.empty], ignore_index=True)
    repair_events_df = pd.concat([df for df in repair_events_all if not df.empty], ignore_index=True)
    buffering_events_df = pd.concat([df for df in buffering_events_all if not df.empty], ignore_index=True)

    ledger_session_df = session_map.merge(pd.DataFrame(ledger_session_rows), on="session_id", how="left").sort_values("date").reset_index(drop=True)
    repair_session_df = session_map.merge(pd.DataFrame(repair_session_rows), on="session_id", how="left").sort_values("date").reset_index(drop=True)
    buffering_session_df = session_map.merge(pd.DataFrame(buffering_session_rows), on="session_id", how="left").sort_values("date").reset_index(drop=True)

    if not ledger_events_df.empty:
        ledger_events_df = session_map.merge(ledger_events_df, on="session_id", how="right").sort_values(["date", "trigger_start_s"]).reset_index(drop=True)
    if not repair_events_df.empty:
        repair_events_df = session_map.merge(repair_events_df, on="session_id", how="right").sort_values(["date", "trigger_start_s"]).reset_index(drop=True)
    if not buffering_events_df.empty:
        buffering_events_df = session_map.merge(buffering_events_df, on="session_id", how="right").sort_values(["date", "trigger_start_s"]).reset_index(drop=True)

    ledger_summary = compare_conditions(ledger_session_df, LEDGER_METRICS)
    repair_summary = compare_conditions(repair_session_df, REPAIR_METRICS)
    buffering_summary = compare_conditions(buffering_session_df, BUFFERING_METRICS)

    ledger_session_df.to_csv(tables_dir / "grooming_ledger_metrics_by_session.csv", index=False)
    repair_session_df.to_csv(tables_dir / "post_conflict_repair_metrics_by_session.csv", index=False)
    buffering_session_df.to_csv(tables_dir / "social_buffering_metrics_by_session.csv", index=False)
    if not ledger_events_df.empty:
        ledger_events_df.to_csv(tables_dir / "grooming_ledger_event_table.csv", index=False)
    if not repair_events_df.empty:
        repair_events_df.to_csv(tables_dir / "post_conflict_repair_event_table.csv", index=False)
    if not buffering_events_df.empty:
        buffering_events_df.to_csv(tables_dir / "social_buffering_event_table.csv", index=False)

    ledger_summary.to_csv(tables_dir / "grooming_ledger_condition_comparison.csv", index=False)
    repair_summary.to_csv(tables_dir / "post_conflict_repair_condition_comparison.csv", index=False)
    buffering_summary.to_csv(tables_dir / "social_buffering_condition_comparison.csv", index=False)

    (docs_dir / "grooming_ledger_analysis.md").write_text(build_ledger_markdown(ledger_summary), encoding="utf-8")
    (docs_dir / "post_conflict_repair_analysis.md").write_text(
        build_repair_markdown(repair_summary, repair_events_df),
        encoding="utf-8",
    )
    (docs_dir / "social_buffering_analysis.md").write_text(
        build_buffering_markdown(buffering_summary),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

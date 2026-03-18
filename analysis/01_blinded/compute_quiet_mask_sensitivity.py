from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DERIVED_AUDIO_DIR = ROOT / "data" / "derived" / "audio"
BLINDED_TABLES_DIR = ROOT / "results" / "blinded" / "tables"

SMOOTH_WINDOW_BINS = 5
MAX_QUIET_GAP_BINS = 2
MIN_LOUD_RUN_BINS = 3


def reciprocity_score(a: float, b: float) -> float | None:
    denom = a + b
    if denom == 0:
        return None
    return 1.0 - (abs(a - b) / denom)


def count_bouts(series: pd.Series, target: str) -> int:
    active = series.eq(target).fillna(False).to_numpy(dtype=bool)
    if active.size == 0:
        return 0
    starts = active & np.concatenate(([True], ~active[:-1]))
    return int(starts.sum())


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


def compute_smoothed_loud_mask(group: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, float]:
    smoothed_rms = (
        group["rms_dbfs"]
        .rolling(window=SMOOTH_WINDOW_BINS, center=True, min_periods=1)
        .mean()
        .to_numpy(dtype=float)
    )
    threshold = float(np.quantile(smoothed_rms, 0.90))
    loud_mask = smoothed_rms >= threshold
    loud_mask = _fill_short_false_gaps(loud_mask, MAX_QUIET_GAP_BINS)
    loud_mask = _remove_short_true_runs(loud_mask, MIN_LOUD_RUN_BINS)
    return loud_mask, smoothed_rms, threshold


def summarize_subset(session_id: str, subset_name: str, subset: pd.DataFrame) -> dict[str, object]:
    n_seconds = len(subset)
    hours = n_seconds / 3600.0 if n_seconds else np.nan
    give_seconds = int((subset["social_state"] == "Groom give").sum())
    receive_seconds = int((subset["social_state"] == "Groom receive").sum())
    total_groom_seconds = give_seconds + receive_seconds
    give_bouts = count_bouts(subset["social_state"], "Groom give")
    receive_bouts = count_bouts(subset["social_state"], "Groom receive")

    return {
        "session_id": session_id,
        "analysis_subset": subset_name,
        "n_seconds": n_seconds,
        "duration_min": n_seconds / 60.0,
        "groom_give_pct": 100.0 * give_seconds / n_seconds if n_seconds else np.nan,
        "groom_receive_pct": 100.0 * receive_seconds / n_seconds if n_seconds else np.nan,
        "groom_total_pct": 100.0 * total_groom_seconds / n_seconds if n_seconds else np.nan,
        "groom_duration_net_receive_minus_give_s": receive_seconds - give_seconds,
        "groom_duration_net_receive_minus_give_pct": 100.0 * (receive_seconds - give_seconds) / n_seconds if n_seconds else np.nan,
        "groom_duration_reciprocity_0to1": reciprocity_score(receive_seconds, give_seconds),
        "groom_give_bouts": give_bouts,
        "groom_receive_bouts": receive_bouts,
        "groom_bout_net_receive_minus_give": receive_bouts - give_bouts,
        "groom_bout_reciprocity_0to1": reciprocity_score(receive_bouts, give_bouts),
        "groom_give_bouts_per_hour": give_bouts / hours if hours and not np.isnan(hours) else np.nan,
        "groom_receive_bouts_per_hour": receive_bouts / hours if hours and not np.isnan(hours) else np.nan,
        "social_engaged_pct": 100.0 * subset["social_engaged"].mean() if n_seconds else np.nan,
        "physical_contact_pct": 100.0 * subset["physical_contact_implied"].mean() if n_seconds else np.nan,
        "attention_outside_pct": 100.0 * (subset["attention_state"] == "Attention to outside agents").mean() if n_seconds else np.nan,
        "travel_pct": 100.0 * (subset["activity_state"] == "Travel").mean() if n_seconds else np.nan,
        "hiccups_pct": 100.0 * (subset["atypical_state"] == "Hiccups").mean() if n_seconds else np.nan,
        "mean_rms_dbfs": float(subset["rms_dbfs"].mean()) if n_seconds else np.nan,
    }


def build_wide_table(summary: pd.DataFrame) -> pd.DataFrame:
    full = summary[summary["analysis_subset"] == "full_trimmed"].copy().set_index("session_id")
    quiet = summary[summary["analysis_subset"] == "quiet_masked_p90"].copy().set_index("session_id")

    metric_cols = [c for c in summary.columns if c not in {"session_id", "analysis_subset"}]
    rows = []
    for session_id in sorted(summary["session_id"].astype(str).unique()):
        row = {"session_id": session_id}
        full_row = full.loc[session_id]
        quiet_row = quiet.loc[session_id]
        for col in metric_cols:
            row[f"{col}_full_trimmed"] = full_row[col]
            row[f"{col}_quiet_masked_p90"] = quiet_row[col]
            if pd.api.types.is_numeric_dtype(summary[col]):
                row[f"{col}_delta_quiet_minus_full"] = quiet_row[col] - full_row[col]
        rows.append(row)
    return pd.DataFrame(rows).sort_values("session_id").reset_index(drop=True)


def main() -> None:
    features = pd.read_csv(DERIVED_AUDIO_DIR / "blinded_audio_features_1s_labeled.csv")
    rows = []

    for session_id, group in features.groupby("session_id", sort=False):
        group = group.sort_values("bin_start_s").reset_index(drop=True)
        rows.append(summarize_subset(str(session_id), "full_trimmed", group))

        loud_mask, _, _ = compute_smoothed_loud_mask(group)
        quiet_mask = ~loud_mask
        quiet_subset = group.loc[quiet_mask].reset_index(drop=True)
        rows.append(summarize_subset(str(session_id), "quiet_masked_p90", quiet_subset))

    summary = pd.DataFrame(rows).sort_values(["session_id", "analysis_subset"]).reset_index(drop=True)
    summary.to_csv(BLINDED_TABLES_DIR / "blinded_quiet_mask_sensitivity_long.csv", index=False)

    wide = build_wide_table(summary)
    wide.to_csv(BLINDED_TABLES_DIR / "blinded_quiet_mask_sensitivity_wide.csv", index=False)


if __name__ == "__main__":
    main()

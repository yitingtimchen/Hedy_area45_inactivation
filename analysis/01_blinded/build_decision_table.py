from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
BLINDED_TABLES_DIR = ROOT / "results" / "blinded" / "tables"


def main() -> None:
    session_summary = pd.read_csv(BLINDED_TABLES_DIR / "blinded_session_summary.csv", dtype={"session_id": str})
    quiet = pd.read_csv(BLINDED_TABLES_DIR / "blinded_quiet_mask_sensitivity_wide.csv", dtype={"session_id": str})

    session_cols = [
        "session_id",
        "session_duration_min",
        "groom_give_pct_session",
        "groom_receive_pct_session",
        "groom_total_pct_session",
        "groom_give_resolved_bouts",
        "groom_receive_resolved_bouts",
        "groom_total_resolved_bouts",
        "groom_give_bouts_per_hour",
        "groom_receive_bouts_per_hour",
        "groom_total_bouts_per_hour",
        "groom_give_bout_mean_duration_s",
        "groom_receive_bout_mean_duration_s",
        "groom_total_bout_mean_duration_s",
        "groom_give_bout_median_duration_s",
        "groom_receive_bout_median_duration_s",
        "groom_total_bout_median_duration_s",
        "groom_duration_net_receive_minus_give_pct_session",
        "groom_bout_net_receive_minus_give",
        "groom_duration_reciprocity_0to1",
        "groom_bout_reciprocity_0to1",
        "social_engaged_pct_session",
        "attention_to_outside_agents_resolved_pct_session",
        "hiccups_resolved_pct_session",
        "inferred_leave_per_hour",
        "exception_flag",
        "exception_note",
        "has_exception_note",
    ]
    quiet_cols = [
        "session_id",
        "duration_min_quiet_masked_p90",
        "groom_give_pct_quiet_masked_p90",
        "groom_receive_pct_quiet_masked_p90",
        "groom_total_pct_quiet_masked_p90",
        "groom_duration_net_receive_minus_give_pct_quiet_masked_p90",
        "groom_duration_net_receive_minus_give_pct_delta_quiet_minus_full",
        "groom_give_bouts_quiet_masked_p90",
        "groom_receive_bouts_quiet_masked_p90",
        "groom_total_bouts_quiet_masked_p90",
        "groom_give_bout_mean_duration_s_quiet_masked_p90",
        "groom_receive_bout_mean_duration_s_quiet_masked_p90",
        "groom_total_bout_mean_duration_s_quiet_masked_p90",
        "groom_give_bout_median_duration_s_quiet_masked_p90",
        "groom_receive_bout_median_duration_s_quiet_masked_p90",
        "groom_total_bout_median_duration_s_quiet_masked_p90",
        "groom_bout_net_receive_minus_give_quiet_masked_p90",
        "groom_bout_net_receive_minus_give_delta_quiet_minus_full",
        "groom_duration_reciprocity_0to1_quiet_masked_p90",
        "groom_duration_reciprocity_0to1_delta_quiet_minus_full",
        "groom_bout_reciprocity_0to1_quiet_masked_p90",
        "groom_bout_reciprocity_0to1_delta_quiet_minus_full",
        "social_engaged_pct_quiet_masked_p90",
        "social_engaged_pct_delta_quiet_minus_full",
        "attention_outside_pct_quiet_masked_p90",
        "attention_outside_pct_delta_quiet_minus_full",
        "hiccups_pct_quiet_masked_p90",
        "hiccups_pct_delta_quiet_minus_full",
    ]

    decision = session_summary[session_cols].merge(quiet[quiet_cols], on="session_id", how="left")
    decision = decision.sort_values("session_id").reset_index(drop=True)
    decision.to_csv(BLINDED_TABLES_DIR / "blinded_decision_table.csv", index=False)


if __name__ == "__main__":
    main()

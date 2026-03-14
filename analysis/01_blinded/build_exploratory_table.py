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
        "travel_resolved_pct_session",
        "rest_stationary_resolved_pct_session",
        "vigilant_scan_resolved_pct_session",
        "attention_to_outside_agents_resolved_pct_session",
        "scratch_resolved_pct_session",
        "self_groom_resolved_pct_session",
        "hiccups_resolved_pct_session",
        "pace_resolved_pct_session",
        "forage_search_resolved_pct_session",
        "object_manipulate_resolved_pct_session",
        "exception_flag",
        "exception_note",
        "has_exception_note",
    ]
    quiet_cols = [
        "session_id",
        "travel_pct_quiet_masked_p90",
        "travel_pct_delta_quiet_minus_full",
        "attention_outside_pct_quiet_masked_p90",
        "attention_outside_pct_delta_quiet_minus_full",
        "hiccups_pct_quiet_masked_p90",
        "hiccups_pct_delta_quiet_minus_full",
        "social_engaged_pct_quiet_masked_p90",
        "social_engaged_pct_delta_quiet_minus_full",
    ]

    exploratory = session_summary[session_cols].merge(quiet[quiet_cols], on="session_id", how="left")
    exploratory = exploratory.sort_values("session_id").reset_index(drop=True)
    exploratory.to_csv(BLINDED_TABLES_DIR / "blinded_exploratory_nonsocial_table.csv", index=False)


if __name__ == "__main__":
    main()

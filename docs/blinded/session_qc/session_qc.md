# Blinded Session QC

This blinded QC layer adds resolved-behavior ethogram traces, collapsed family traces, and rule-based review flags for session follow-up.

## Outputs

- Per-session detailed plus collapsed ethogram traces are saved under `results/blinded/session_qc/figures/`.
- The quick-review gallery is `blinded_session_family_qc_gallery.png`.
- Session composition tables are provided at both the resolved-label and collapsed-family levels.
- Review flags are blinded IQR-rule targets for manual follow-up, not automatic exclusions.
- The occupancy-flag summary figure is `blinded_session_qc_flag_summary.png` and labels flagged session IDs directly.

## Family collapse

- Families shown in the QC traces are `affiliative`, `aggressive`, `sexual`, `feeding`, `locomotion`, `attention`, `maintenance`, `atypical`, and `unscored`.
- Source labels in the original `Other` category are grouped into `atypical` for this blinded QC collapse so every resolved second lands in a review family.

## Flag basis

- Flags are now based on the parallel annotation streams rather than the single precedence-resolved display stream.
- Stream occupancy metrics used for QC are `social_stream_pct_session`, `activity_stream_pct_session`, `attention_stream_pct_session`, plus `unscored_pct_session`.
- The atypical lane remains visible in the plots and tables, but it does not drive QC flags.
- Transition metrics are excluded from QC because their construction is still exploratory.

## Flag rules

- `unscored_pct_session` flagged outside blinded Tukey bounds `[ -0.64, 2.22 ]`; `0` sessions flagged.
- `social_stream_pct_session` flagged outside blinded Tukey bounds `[ 58.29, 106.92 ]`; `0` sessions flagged.
- `activity_stream_pct_session` flagged outside blinded Tukey bounds `[ -9.17, 37.34 ]`; `0` sessions flagged.
- `attention_stream_pct_session` flagged outside blinded Tukey bounds `[ -3.48, 14.69 ]`; `1` sessions flagged.

## Review targets

- Session `596273`: attention_stream_pct_session above blinded IQR bound.

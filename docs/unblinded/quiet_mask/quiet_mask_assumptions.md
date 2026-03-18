# Quiet-Mask Assumptions

- The quiet-mask branch is built from the same sessions as the full branch, but primary session-level metrics are recomputed after removing smoothed loud epochs.
- Loud epochs are defined from a centered 5 s rolling-average loudness trace within each session.
- Bins above the session-specific smoothed 90th-percentile threshold are marked as loud.
- Quiet gaps `<= 2 s` inside loud stretches are filled, and isolated loud blips `< 3 s` are removed from the mask.
- Metrics are recomputed on the retained 1 s bins after those loud epochs are removed.
- This is a robustness analysis for duration-based session summaries; it should not be interpreted as a perfect reconstruction of the original session timeline.
- Episode-level and macro-transition follow-up outputs in the quiet-mask branch are mirrored for organizational consistency and are not themselves re-derived from a time-preserving masked event stream.

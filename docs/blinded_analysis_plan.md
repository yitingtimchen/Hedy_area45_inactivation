# Blinded Analysis Plan

## Goal

Define and lock the core behavioral analysis before mapping blinded sessions back to drug condition.

## Analysis Principles

- Keep feature engineering blinded until the endpoint set is finalized.
- Use one primary behavioral preprocessing pipeline for all sessions.
- Treat audio as a sensitivity layer, not as a driver of the core behavioral definitions.
- Keep observed labels separate from inferred or derived variables.

## Primary Preprocessing Rules

- Analyze only the pairing window from `Start pairing` to `End pairing`.
- Trim the first 30 s and last 30 s of each pairing window from the primary analysis set to exclude experimenter entry/exit effects.
- Merge adjacent bouts of the same observed behavior across unlabeled gaps `<= 2 s`.
- Use a layered representation rather than forcing all labels into one stream.

### Layers

- `Social`: approach, proximity, grooming, mounting, aggression-related social acts.
- `Activity / maintenance`: rest, travel, forage, eat, drink, object manipulation, scratch, self-groom, stretch, urinate.
- `Attention`: vigilant/scan, attention to outside agents.
- `Atypical / somatic`: hiccups, pace, bounce, bizarre posture, yawn.

## Grooming Metrics

The grooming analysis separates direction from reciprocity.

### Net grooming

- `groom_duration_net_receive_minus_give_s = receive duration - give duration`
- `groom_duration_net_receive_minus_give_pct_session = 100 * (receive duration - give duration) / session duration`
- `groom_bout_net_receive_minus_give = receive bouts - give bouts`

The normalized session-level net duration metric is the preferred summary for across-session comparison because sessions are not exactly identical in length. Raw net seconds are retained for cumulative paper-style traces.

### Reciprocity

- `groom_duration_reciprocity_0to1 = 1 - abs(receive - give) / (receive + give)`
- `groom_bout_reciprocity_0to1 = 1 - abs(receive bouts - give bouts) / (receive bouts + give bouts)`

Interpretation:

- `1` = perfectly reciprocal
- `0` = fully one-sided

This metric is intentionally unsigned. Directionality is represented by the net grooming measures above.

## Endpoint Logic

### Primary endpoints

- `groom_duration_net_receive_minus_give_pct_session`
- `groom_duration_reciprocity_0to1`

Rationale:

- These directly capture the magnitude and direction of grooming imbalance plus the symmetry of exchange.
- Together they preserve the paper-style framing while remaining interpretable at the session level.

### Secondary endpoints

- `groom_total_pct_session`
- `groom_bout_net_receive_minus_give`
- `groom_bout_reciprocity_0to1`
- `social_engaged_pct_session`

Rationale:

- These support interpretation of the primary grooming results without replacing them.

### Exploratory / contextual endpoints

- `travel_resolved_pct_session`
- `rest_stationary_resolved_pct_session`
- `vigilant_scan_resolved_pct_session`
- `attention_to_outside_agents_resolved_pct_session`
- `scratch_resolved_pct_session`
- `self_groom_resolved_pct_session`
- `hiccups_resolved_pct_session`
- `pace_resolved_pct_session`
- `forage_search_resolved_pct_session`
- `object_manipulate_resolved_pct_session`
- `inferred_leave_per_hour`

Rationale:

- These are not the main hypothesis tests, but they help distinguish socially selective effects from broader changes in arousal, maintenance behavior, locomotion, distractibility, or atypical state.

## Audio Sensitivity Logic

Audio is used only for sensitivity analysis, not for defining the core behavior states.

- Use the trimmed pairing window.
- Use the longest synchronized 720p video as the default audio source.
- If the longest video has a silent or unusable audio track during the pairing window, fall back to the second-longest.
- Never use the shortest video.

### Main sensitivity comparison

- `full_trimmed`: all trimmed behavioral data
- `quiet_masked_p90`: same trimmed session after removing smoothed loud epochs defined from a centered 5 s rolling-average loudness trace, thresholded at the session-specific 90th percentile, with short-gap bridging and isolated-blip removal

Rationale:

- This gives a simple test of whether the main behavioral conclusions change after removing the noisiest moments.
- It avoids overcomplicating the analysis with many noise classes.

## Session Exceptions

These sessions should remain in the dataset but be flagged in interpretation.

- `596273`: vets entered the room to evaluate Leakey; the pair was distracted for part of the session.
- `626219`: front camera died approximately 40 min into recording.

## Blinded Outputs To Use Before Unblinding

- `results/blinded/tables/blinded_decision_table.csv`
- `results/blinded/tables/blinded_exploratory_nonsocial_table.csv`
- `docs/audio_mask_sensitivity.md`

## Unblinding Rule

Do not merge the session-condition key until the endpoint set above is accepted as the locked analysis plan.

# Audio Mask Sensitivity

## Logic

- Comparison is paired within session: `quiet_masked_p90 - full_trimmed`.
- The quiet mask is built from a centered 5 s rolling-average loudness trace within each session.
- Bins above the session-specific smoothed 90th-percentile threshold are marked as loud, quiet gaps `<= 2 s` within loud stretches are filled, and isolated loud blips `< 3 s` are dropped from the mask.
- Metrics are recomputed on the retained 1 s bins after removing those smoothed loud epochs.
- The main question is not whether the two versions are mathematically identical, but whether masking changes the primary endpoints by a practically meaningful amount.
- Practical equivalence bounds were set a priori at `+/- 5 percentage points` for duration-based percent-of-session metrics and `+/- 0.05` for grooming reciprocity.
- Evidence for robustness is defined as the bootstrap 95% CI of the mean delta lying fully within the prespecified equivalence bound.

## Primary endpoints

- Net grooming duration: mean delta `0.240 pct_session`, 95% bootstrap CI `[-0.503, 1.029]`, equivalence supported = `True`.
- Groom reciprocity: mean delta `0.005 index`, 95% bootstrap CI `[-0.005, 0.014]`, equivalence supported = `True`.

## Supporting endpoints

- Total grooming: mean delta `1.632 pct_session`, 95% bootstrap CI `[0.843, 2.471]`, equivalence supported = `True`.
- Social engagement: mean delta `1.104 pct_session`, 95% bootstrap CI `[0.365, 1.951]`, equivalence supported = `True`.

## Mask-validation endpoint

- Attention to outside agents: mean delta `-0.708 pct_session`, 95% bootstrap CI `[-1.187, -0.367]`.

## Interpretation

- The normalized net grooming endpoint changed little on average and had `1` sign flip(s) across 16 sessions after masking.
- Groom reciprocity is the most robust primary endpoint because it is already session-length independent and shows very small mask-related shifts.
- Attention to outside agents decreases after masking, which supports that the mask is preferentially removing distraction-related loud moments rather than strongly altering the main grooming balance measures.

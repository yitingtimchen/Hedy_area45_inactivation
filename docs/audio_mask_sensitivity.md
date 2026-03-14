# Audio Mask Sensitivity

## Logic

- Comparison is paired within session: `quiet_masked_p90 - full_trimmed`.
- The quiet mask removes the loudest 10% of 1 s bins from each trimmed session.
- The main question is not whether the two versions are mathematically identical, but whether masking changes the primary endpoints by a practically meaningful amount.
- Practical equivalence bounds were set a priori at `+/- 5 percentage points` for duration-based percent-of-session metrics and `+/- 0.05` for grooming reciprocity.
- Evidence for robustness is defined as the bootstrap 95% CI of the mean delta lying fully within the prespecified equivalence bound.

## Primary endpoints

- Net grooming duration: mean delta `0.273 pct_session`, 95% bootstrap CI `[-0.236, 0.769]`, equivalence supported = `True`.
- Groom reciprocity: mean delta `0.006 index`, 95% bootstrap CI `[-0.000, 0.013]`, equivalence supported = `True`.

## Supporting endpoints

- Total grooming: mean delta `1.285 pct_session`, 95% bootstrap CI `[0.661, 1.974]`, equivalence supported = `True`.
- Social engagement: mean delta `0.831 pct_session`, 95% bootstrap CI `[0.248, 1.554]`, equivalence supported = `True`.

## Mask-validation endpoint

- Attention to outside agents: mean delta `-0.516 pct_session`, 95% bootstrap CI `[-0.930, -0.229]`.

## Interpretation

- The normalized net grooming endpoint changed little on average and had `1` sign flip(s) across 16 sessions after masking.
- Groom reciprocity is the most robust primary endpoint because it is already session-length independent and shows very small mask-related shifts.
- Attention to outside agents decreases after masking, which supports that the mask is preferentially removing distraction-related loud moments rather than strongly altering the main grooming balance measures.

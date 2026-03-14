# Unblinded Condition Comparison

Cohort: full session set.
Condition labels were merged only after the blinded preprocessing, endpoint locking, and audio sensitivity analysis were finalized.

## Statistical approach

- Session-level comparisons use the locked outputs.
- `DCZ` and `vehicle` groups contain `8` and `8` sessions, respectively.
- For each metric, the group contrast is `DCZ - vehicle`.
- P values come from an exact two-sided label permutation test over all label assignments consistent with the cohort size.
- Bootstrap 95% confidence intervals are provided for the mean difference as descriptive uncertainty intervals.

## Primary endpoints

- `groom_duration_net_receive_minus_give_pct_session`: vehicle mean `-27.401`, DCZ mean `-8.593`, mean difference `18.808`, 95% CI `[10.182, 27.482]`, exact permutation `p = 0.0017`.
- `groom_duration_reciprocity_0to1`: vehicle mean `0.655`, DCZ mean `0.845`, mean difference `0.190`, 95% CI `[0.090, 0.287]`, exact permutation `p = 0.0047`.

## Secondary endpoints

- `groom_total_pct_session`: vehicle mean `79.647`, DCZ mean `70.490`, mean difference `-9.157`, 95% CI `[-20.539, 3.128]`, exact permutation `p = 0.1751`.
- `groom_bout_net_receive_minus_give`: vehicle mean `-8.625`, DCZ mean `-3.375`, mean difference `5.250`, 95% CI `[-0.625, 11.250]`, exact permutation `p = 0.1420`.
- `groom_bout_reciprocity_0to1`: vehicle mean `0.654`, DCZ mean `0.728`, mean difference `0.073`, 95% CI `[-0.066, 0.199]`, exact permutation `p = 0.3215`.
- `social_engaged_pct_session`: vehicle mean `85.300`, DCZ mean `77.572`, mean difference `-7.728`, 95% CI `[-17.438, 2.481]`, exact permutation `p = 0.1720`.

## Quiet-mask sensitivity for primary endpoints

- `groom_duration_net_receive_minus_give_pct_quiet_masked_p90`: vehicle mean `-27.370`, DCZ mean `-8.077`, mean difference `19.293`, 95% CI `[10.827, 27.855]`, exact permutation `p = 0.0014`.
- `groom_duration_reciprocity_0to1_quiet_masked_p90`: vehicle mean `0.663`, DCZ mean `0.850`, mean difference `0.186`, 95% CI `[0.095, 0.278]`, exact permutation `p = 0.0030`.

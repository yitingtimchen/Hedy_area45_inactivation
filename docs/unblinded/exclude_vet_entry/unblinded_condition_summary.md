# Unblinded Condition Comparison

Cohort: excluding known vet-entry session 596273.
Condition labels were merged only after the blinded preprocessing, endpoint locking, and audio sensitivity analysis were finalized.

## Statistical approach

- Session-level comparisons use the locked outputs.
- `DCZ` and `vehicle` groups contain `7` and `8` sessions, respectively.
- For each metric, the group contrast is `DCZ - vehicle`.
- P values come from an exact two-sided label permutation test over all label assignments consistent with the cohort size.
- Bootstrap 95% confidence intervals are provided for the mean difference as descriptive uncertainty intervals.

## Primary endpoints

- `groom_duration_net_receive_minus_give_pct_session`: vehicle mean `-27.401`, DCZ mean `-7.220`, mean difference `20.181`, 95% CI `[11.177, 29.007]`, exact permutation `p = 0.0017`.
- `groom_duration_reciprocity_0to1`: vehicle mean `0.655`, DCZ mean `0.869`, mean difference `0.213`, 95% CI `[0.118, 0.306]`, exact permutation `p = 0.0020`.

## Secondary endpoints

- `groom_total_pct_session`: vehicle mean `79.647`, DCZ mean `72.473`, mean difference `-7.174`, 95% CI `[-19.030, 5.213]`, exact permutation `p = 0.2897`.
- `groom_bout_net_receive_minus_give`: vehicle mean `-8.625`, DCZ mean `-2.286`, mean difference `6.339`, 95% CI `[0.018, 12.518]`, exact permutation `p = 0.0844`.
- `groom_bout_reciprocity_0to1`: vehicle mean `0.654`, DCZ mean `0.739`, mean difference `0.085`, 95% CI `[-0.063, 0.214]`, exact permutation `p = 0.2788`.
- `social_engaged_pct_session`: vehicle mean `85.300`, DCZ mean `78.754`, mean difference `-6.546`, 95% CI `[-17.239, 3.991]`, exact permutation `p = 0.2549`.

## Quiet-mask sensitivity for primary endpoints

- `groom_duration_net_receive_minus_give_pct_quiet_masked_p90`: vehicle mean `-27.370`, DCZ mean `-6.675`, mean difference `20.695`, 95% CI `[11.857, 29.353]`, exact permutation `p = 0.0014`.
- `groom_duration_reciprocity_0to1_quiet_masked_p90`: vehicle mean `0.663`, DCZ mean `0.872`, mean difference `0.208`, 95% CI `[0.119, 0.295]`, exact permutation `p = 0.0017`.

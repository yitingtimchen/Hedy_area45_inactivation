# Grooming Ledger Analysis

This follow-up extends the same-episode grooming analysis to medium timescales by asking how often the opposite grooming direction appears within fixed lag windows after a grooming bout ends.

## Definitions

- Trigger bouts come from the cleaned merged social-behavior intervals.
- `Groom give -> Groom receive` means Hedy grooms first and Hooke later returns grooming.
- `Groom receive -> Groom give` is the symmetric reverse direction.
- Window-based probabilities use only triggers with the full future window still observed inside the session.
- The shuffled baseline circularly shifts the opposite-direction grooming starts within session to estimate a within-session chance expectation while preserving each session's event count.

## Condition comparisons

- Return-groom probability within 120 s after Hedy grooms Hooke: vehicle mean `0.526`, DCZ mean `0.611`, mean difference `0.085`, 95% CI `[-0.038, 0.210]`, exact permutation `p = 0.2263`.
- Return-groom probability within 120 s after Hooke grooms Hedy: vehicle mean `0.900`, DCZ mean `0.694`, mean difference `-0.206`, 95% CI `[-0.334, -0.064]`, exact permutation `p = 0.0202`.
- Return-groom probability within 600 s after Hedy grooms Hooke: vehicle mean `0.931`, DCZ mean `0.986`, mean difference `0.056`, 95% CI `[-0.014, 0.132]`, exact permutation `p = 0.3231`.
- Return-groom probability within 600 s after Hooke grooms Hedy: vehicle mean `1.000`, DCZ mean `0.933`, mean difference `-0.067`, 95% CI `[-0.116, -0.018]`, exact permutation `p = 0.0769`.
- Observed minus shuffled 120 s return probability after Hedy grooms Hooke: vehicle mean `0.317`, DCZ mean `0.344`, mean difference `0.026`, 95% CI `[-0.067, 0.122]`, exact permutation `p = 0.6176`.
- Observed minus shuffled 120 s return probability after Hooke grooms Hedy: vehicle mean `0.552`, DCZ mean `0.400`, mean difference `-0.152`, 95% CI `[-0.273, -0.024]`, exact permutation `p = 0.0455`.
- Median latency until Hooke returns grooming after Hedy grooms: vehicle mean `86.181`, DCZ mean `57.542`, mean difference `-28.639`, 95% CI `[-92.092, 29.648]`, exact permutation `p = 0.3970`.
- Median latency until Hedy returns grooming after Hooke grooms: vehicle mean `2.498`, DCZ mean `36.315`, mean difference `33.817`, 95% CI `[15.444, 52.304]`, exact permutation `p = 0.0034`.

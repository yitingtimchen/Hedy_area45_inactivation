# Macro-State Transition Analysis

Cohort: quiet-mask sensitivity session set.
This version removes `unscored` macro-bouts of duration `<= 3 s` from the transition stream before recollapsing adjacent macro-states.

## Condition comparisons

- Macro-state switches per hour: vehicle mean `70.691`, DCZ mean `71.026`, mean difference `0.335`, 95% CI `[-39.217, 31.080]`, exact permutation `p = 0.9924`.
- Social to nonsocial-activity probability: vehicle mean `0.365`, DCZ mean `0.500`, mean difference `0.135`, 95% CI `[-0.039, 0.309]`, exact permutation `p = 0.1764`.
- Social to attention-only probability: vehicle mean `0.213`, DCZ mean `0.225`, mean difference `0.012`, 95% CI `[-0.155, 0.181]`, exact permutation `p = 0.9063`.
- Nonsocial-activity to social probability: vehicle mean `0.180`, DCZ mean `0.303`, mean difference `0.123`, 95% CI `[-0.016, 0.274]`, exact permutation `p = 0.1389`.
- Attention-only to social probability: vehicle mean `0.160`, DCZ mean `0.252`, mean difference `0.093`, 95% CI `[-0.039, 0.227]`, exact permutation `p = 0.2295`.

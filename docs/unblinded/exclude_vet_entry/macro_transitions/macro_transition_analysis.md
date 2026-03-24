# Macro-State Transition Analysis

Cohort: excluding known vet-entry session 596273.
This version removes `unscored` macro-bouts of duration `<= 3 s` from the transition stream before recollapsing adjacent macro-states.

## Condition comparisons

- Macro-state switches per hour: vehicle mean `70.691`, DCZ mean `65.134`, mean difference `-5.557`, 95% CI `[-43.506, 22.431]`, exact permutation `p = 0.9158`.
- Social to nonsocial-activity probability: vehicle mean `0.365`, DCZ mean `0.550`, mean difference `0.185`, 95% CI `[0.022, 0.347]`, exact permutation `p = 0.0553`.
- Social to attention-only probability: vehicle mean `0.213`, DCZ mean `0.173`, mean difference `-0.040`, 95% CI `[-0.187, 0.088]`, exact permutation `p = 0.6305`.
- Nonsocial-activity to social probability: vehicle mean `0.180`, DCZ mean `0.341`, mean difference `0.161`, 95% CI `[0.028, 0.311]`, exact permutation `p = 0.0364`.
- Attention-only to social probability: vehicle mean `0.160`, DCZ mean `0.217`, mean difference `0.057`, 95% CI `[-0.068, 0.193]`, exact permutation `p = 0.4301`.

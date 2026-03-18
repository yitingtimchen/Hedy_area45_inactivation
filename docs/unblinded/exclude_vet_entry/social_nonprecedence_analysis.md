# Raw Social Non-Precedence Exploration

Cohort: excluding known vet-entry session 596273.
This exploratory pass ignores precedence within the social layer and summarizes raw trimmed-window behavior events directly from the BORIS state-event stream.

## Scope and assumptions

- Durations can overlap across behaviors because precedence is intentionally ignored.
- These metrics should be read as independent event-family summaries, not as an additive partition of the session.
- This analysis is exploratory and intended to surface potentially interesting non-groom social signals for follow-up.

## Strongest apparent condition differences

- Sexual behavior duration (% session): vehicle mean `0.419`, DCZ mean `0.186`, mean difference `-0.233`, 95% CI `[-0.359, -0.095]`, exact permutation `p = 0.0087`.
- Mount-give duration (% session): vehicle mean `0.411`, DCZ mean `0.169`, mean difference `-0.242`, 95% CI `[-0.378, -0.095]`, exact permutation `p = 0.0095`.
- Sexual behavior bouts per session: vehicle mean `2.875`, DCZ mean `1.857`, mean difference `-1.018`, 95% CI `[-2.107, 0.107]`, exact permutation `p = 0.1473`.
- Mount-give bouts per session: vehicle mean `2.750`, DCZ mean `1.714`, mean difference `-1.036`, 95% CI `[-2.250, 0.196]`, exact permutation `p = 0.1792`.
- Approach bouts per session: vehicle mean `3.625`, DCZ mean `1.857`, mean difference `-1.768`, 95% CI `[-4.661, 0.625]`, exact permutation `p = 0.3291`.
- Approach duration (% session): vehicle mean `0.353`, DCZ mean `0.198`, mean difference `-0.155`, 95% CI `[-0.462, 0.088]`, exact permutation `p = 0.4325`.
- Mount-receive duration (% session): vehicle mean `0.000`, DCZ mean `0.017`, mean difference `0.017`, 95% CI `[0.000, 0.050]`, exact permutation `p = 0.4667`.
- Open-mouth-threat duration (% session): vehicle mean `0.000`, DCZ mean `0.003`, mean difference `0.003`, 95% CI `[0.000, 0.010]`, exact permutation `p = 0.4667`.
- Mount-receive bouts per session: vehicle mean `0.000`, DCZ mean `0.143`, mean difference `0.143`, 95% CI `[0.000, 0.429]`, exact permutation `p = 0.4667`.
- Open-mouth-threat bouts per session: vehicle mean `0.000`, DCZ mean `0.143`, mean difference `0.143`, 95% CI `[0.000, 0.429]`, exact permutation `p = 0.4667`.
- Affiliative non-groom duration (% session): vehicle mean `1.006`, DCZ mean `0.632`, mean difference `-0.374`, 95% CI `[-1.311, 0.464]`, exact permutation `p = 0.5142`.
- Cage-shake-display bouts per session: vehicle mean `0.125`, DCZ mean `0.286`, mean difference `0.161`, 95% CI `[-0.250, 0.571]`, exact permutation `p = 0.5692`.

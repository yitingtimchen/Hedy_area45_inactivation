# Raw Social Non-Precedence Exploration

Cohort: full session set.
This exploratory pass ignores precedence within the social layer and summarizes raw trimmed-window behavior events directly from the BORIS state-event stream.

## Scope and assumptions

- Durations can overlap across behaviors because precedence is intentionally ignored.
- These metrics should be read as independent event-family summaries, not as an additive partition of the session.
- This analysis is exploratory and intended to surface potentially interesting non-groom social signals for follow-up.

## Strongest apparent condition differences

- Mount-give duration (% session): vehicle mean `0.411`, DCZ mean `0.186`, mean difference `-0.225`, 95% CI `[-0.356, -0.088]`, exact permutation `p = 0.0095`.
- Sexual behavior duration (% session): vehicle mean `0.419`, DCZ mean `0.226`, mean difference `-0.193`, 95% CI `[-0.331, -0.047]`, exact permutation `p = 0.0291`.
- Mount-give bouts per session: vehicle mean `2.750`, DCZ mean `1.750`, mean difference `-1.000`, 95% CI `[-2.125, 0.125]`, exact permutation `p = 0.1792`.
- Sexual behavior bouts per session: vehicle mean `2.875`, DCZ mean `2.000`, mean difference `-0.875`, 95% CI `[-1.875, 0.250]`, exact permutation `p = 0.2210`.
- Mount-receive duration (% session): vehicle mean `0.000`, DCZ mean `0.040`, mean difference `0.040`, 95% CI `[0.000, 0.094]`, exact permutation `p = 0.4667`.
- Mount-receive bouts per session: vehicle mean `0.000`, DCZ mean `0.250`, mean difference `0.250`, 95% CI `[0.000, 0.625]`, exact permutation `p = 0.4667`.
- Approach bouts per session: vehicle mean `3.625`, DCZ mean `2.250`, mean difference `-1.375`, 95% CI `[-4.375, 1.125]`, exact permutation `p = 0.4838`.
- Affiliative non-groom duration (% session): vehicle mean `1.006`, DCZ mean `0.654`, mean difference `-0.353`, 95% CI `[-1.247, 0.436]`, exact permutation `p = 0.5097`.
- Approach duration (% session): vehicle mean `0.353`, DCZ mean `0.236`, mean difference `-0.117`, 95% CI `[-0.429, 0.141]`, exact permutation `p = 0.5613`.
- Enlist/recruit duration (% session): vehicle mean `0.064`, DCZ mean `0.007`, mean difference `-0.057`, 95% CI `[-0.177, 0.009]`, exact permutation `p = 0.5897`.
- Groom-solicit duration (% session): vehicle mean `0.653`, DCZ mean `0.417`, mean difference `-0.236`, 95% CI `[-1.081, 0.495]`, exact permutation `p = 0.6047`.
- Groom-solicit bouts per session: vehicle mean `2.500`, DCZ mean `3.000`, mean difference `0.500`, 95% CI `[-1.375, 2.125]`, exact permutation `p = 0.7046`.

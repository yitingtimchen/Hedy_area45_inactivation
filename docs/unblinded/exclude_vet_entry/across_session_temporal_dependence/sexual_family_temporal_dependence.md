# Sexual-Family Temporal Dependence

Cohort: excluding known vet-entry session 596273.
This exploratory check asks whether sexual-family metrics show simple within-condition drift over session order that could help explain the session-level condition differences.

## Methods

- Raw condition effect is the exact two-sided label permutation result on the session-level metric.
- Vehicle and DCZ slopes are fit separately over session order within condition.
- Slope significance is assessed with the same permutation-on-slope logic used in the grooming temporal check.

## Results

### Mount-give duration (% session)
- Raw condition effect: `-0.242`, exact permutation `p = 0.0095`.
- Vehicle slope: `0.006` per session, slope permutation `p = 0.5365`.
- DCZ slope: `-0.035` per session, slope permutation `p = 0.0056`.

### Mount-receive duration (% session)
- Raw condition effect: `0.017`, exact permutation `p = 0.4667`.
- Vehicle slope: `0.000` per session, slope permutation `p = 1.0000`.
- DCZ slope: `0.004` per session, slope permutation `p = 0.4286`.

### Mount-give bouts per session
- Raw condition effect: `-1.036`, exact permutation `p = 0.1792`.
- Vehicle slope: `0.060` per session, slope permutation `p = 0.4821`.
- DCZ slope: `-0.298` per session, slope permutation `p = 0.0143`.

### Mount-receive bouts per session
- Raw condition effect: `0.143`, exact permutation `p = 0.4667`.
- Vehicle slope: `0.000` per session, slope permutation `p = 1.0000`.
- DCZ slope: `0.032` per session, slope permutation `p = 0.4286`.

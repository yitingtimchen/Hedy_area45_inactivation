# Temporal Dependence Analysis

Cohort: quiet-mask sensitivity session set.
This exploratory analysis checks whether the primary grooming results could plausibly be explained by simple drift across session order.

## Methods

- Metrics analyzed: net grooming and grooming reciprocity.
- `Raw condition effect` is the original exact two-sided label permutation result on the session-level metric.
- `Vehicle slope` and `DCZ slope` are estimated separately by fitting a linear trend over session order within each condition.
- Slope significance is assessed with a two-sided permutation test within each condition, using the fitted slope rather than `R^2` as the test statistic.

## Results

### Net grooming (% session; receive - give)
- Raw condition effect: `19.383`, exact permutation `p = 0.0014`.
- Vehicle slope: `0.973` per session, slope permutation `p = 0.1031`.
- DCZ slope: `0.702` per session, slope permutation `p = 0.4538`.

### Grooming reciprocity (0 to 1)
- Raw condition effect: `0.184`, exact permutation `p = 0.0028`.
- Vehicle slope: `0.010` per session, slope permutation `p = 0.1133`.
- DCZ slope: `0.006` per session, slope permutation `p = 0.5339`.

### Net grooming bouts (receive - give)
- Raw condition effect: `3.875`, exact permutation `p = 0.0807`.
- Vehicle slope: `-0.037` per session, slope permutation `p = 0.8888`.
- DCZ slope: `0.710` per session, slope permutation `p = 0.0685`.

### Grooming bout reciprocity (0 to 1)
- Raw condition effect: `0.080`, exact permutation `p = 0.2671`.
- Vehicle slope: `-0.004` per session, slope permutation `p = 0.8065`.
- DCZ slope: `0.003` per session, slope permutation `p = 0.6646`.

# Temporal Dependence Analysis

Cohort: full session set.
This exploratory analysis checks whether the primary grooming results could plausibly be explained by simple drift across session order.

## Methods

- Metrics analyzed: net grooming and grooming reciprocity.
- `Raw condition effect` is the original exact two-sided label permutation result on the session-level metric.
- `Vehicle slope` and `DCZ slope` are estimated separately by fitting a linear trend over session order within each condition.
- Slope significance is assessed with a two-sided permutation test within each condition, using the fitted slope rather than `R^2` as the test statistic.

## Results

### Net grooming (% session; receive - give)
- Raw condition effect: `18.808`, exact permutation `p = 0.0017`.
- Vehicle slope: `1.011` per session, slope permutation `p = 0.1100`.
- DCZ slope: `0.716` per session, slope permutation `p = 0.4454`.

### Grooming reciprocity (0 to 1)
- Raw condition effect: `0.190`, exact permutation `p = 0.0047`.
- Vehicle slope: `0.010` per session, slope permutation `p = 0.1287`.
- DCZ slope: `0.008` per session, slope permutation `p = 0.4818`.

### Net grooming bouts (receive - give)
- Raw condition effect: `5.250`, exact permutation `p = 0.1420`.
- Vehicle slope: `-0.101` per session, slope permutation `p = 0.7616`.
- DCZ slope: `1.336` per session, slope permutation `p = 0.0520`.

### Grooming bout reciprocity (0 to 1)
- Raw condition effect: `0.073`, exact permutation `p = 0.3215`.
- Vehicle slope: `-0.009` per session, slope permutation `p = 0.4113`.
- DCZ slope: `0.012` per session, slope permutation `p = 0.3938`.

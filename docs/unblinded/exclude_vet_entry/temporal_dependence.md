# Temporal Dependence Analysis

Cohort: excluding known vet-entry session 596273.
This exploratory analysis checks whether the primary grooming results could plausibly be explained by simple drift across session order.

## Methods

- Metrics analyzed: net grooming and grooming reciprocity.
- `Raw condition effect` is the original exact two-sided label permutation result on the session-level metric.
- `Vehicle slope` and `DCZ slope` are estimated separately by fitting a linear trend over session order within each condition.
- Slope significance is assessed with a two-sided permutation test within each condition, using the fitted slope rather than `R^2` as the test statistic.

## Results

### Net grooming (% session; receive - give)
- Raw condition effect: `20.181`, exact permutation `p = 0.0017`.
- Vehicle slope: `1.011` per session, slope permutation `p = 0.1100`.
- DCZ slope: `0.427` per session, slope permutation `p = 0.7000`.

### Grooming reciprocity (0 to 1)
- Raw condition effect: `0.213`, exact permutation `p = 0.0020`.
- Vehicle slope: `0.010` per session, slope permutation `p = 0.1287`.
- DCZ slope: `0.002` per session, slope permutation `p = 0.8808`.

### Net grooming bouts (receive - give)
- Raw condition effect: `6.339`, exact permutation `p = 0.0844`.
- Vehicle slope: `-0.101` per session, slope permutation `p = 0.7616`.
- DCZ slope: `1.270` per session, slope permutation `p = 0.1038`.

### Grooming bout reciprocity (0 to 1)
- Raw condition effect: `0.085`, exact permutation `p = 0.2788`.
- Vehicle slope: `-0.009` per session, slope permutation `p = 0.4113`.
- DCZ slope: `0.011` per session, slope permutation `p = 0.4948`.

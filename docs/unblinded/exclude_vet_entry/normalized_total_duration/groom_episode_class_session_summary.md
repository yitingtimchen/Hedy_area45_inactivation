# Groom Feedback Dynamics Analysis

Cohort: excluding known vet-entry session 596273.
This follow-up asks whether the directional structure of grooming episodes changes over the course of a session in a way that is compatible with a feedback loop.

## Definitions

- The unit of analysis is the grooming-containing social episode defined in the locked preprocessing pipeline.
- Each grooming episode is assigned to exactly one cell in the `who grooms first x whether the partner reciprocates` decomposition.
- The main share denominator is always `all grooming episodes in that session`, so the four share metrics sum to `1.0` for sessions with at least one grooming episode.
- `Reciprocated` means the opposite grooming role appears later in the same social episode; `unreciprocated` means it does not.
- The slope metrics fit a simple linear trend over grooming-episode order within each session. Positive values mean that cell becomes more common later in the session.

## Interpretation boundaries

- These are mechanistic follow-ups aimed at within-session dynamics, not new primary endpoints.
- Because the slope is computed within each session over grooming-episode order, it uses all grooming episodes rather than an arbitrary early/late split.
- As with the directional episode analysis, brief `Groom receive` events may mix genuine received grooming with partner solicitation; interpret receive-side metrics accordingly.

## Condition comparisons

### Cell counts per session
- Hedy grooms first, Hooke reciprocates episodes per session: vehicle mean `1.000`, DCZ mean `0.857`, mean difference `-0.143`, 95% CI `[-0.696, 0.429]`, exact permutation `p = 0.6904`.
- Hedy grooms first, Hooke does not reciprocate episodes per session: vehicle mean `3.875`, DCZ mean `3.000`, mean difference `-0.875`, 95% CI `[-3.321, 1.429]`, exact permutation `p = 0.5709`.
- Hooke grooms first, Hedy reciprocates episodes per session: vehicle mean `2.875`, DCZ mean `2.714`, mean difference `-0.161`, 95% CI `[-1.214, 1.000]`, exact permutation `p = 0.8334`.
- Hooke grooms first, Hedy does not reciprocate episodes per session: vehicle mean `1.125`, DCZ mean `2.714`, mean difference `1.589`, 95% CI `[-0.143, 3.214]`, exact permutation `p = 0.1256`.

### Cell shares of all grooming episodes
- Share of all grooming episodes where Hedy grooms first and Hooke reciprocates: vehicle mean `0.118`, DCZ mean `0.096`, mean difference `-0.021`, 95% CI `[-0.093, 0.051]`, exact permutation `p = 0.5862`.
- Share of all grooming episodes where Hedy grooms first and Hooke does not reciprocate: vehicle mean `0.401`, DCZ mean `0.306`, mean difference `-0.095`, 95% CI `[-0.247, 0.058]`, exact permutation `p = 0.2779`.
- Share of all grooming episodes where Hooke grooms first and Hedy reciprocates: vehicle mean `0.375`, DCZ mean `0.320`, mean difference `-0.055`, 95% CI `[-0.223, 0.133]`, exact permutation `p = 0.5838`.
- Share of all grooming episodes where Hooke grooms first and Hedy does not reciprocate: vehicle mean `0.106`, DCZ mean `0.278`, mean difference `0.172`, 95% CI `[0.021, 0.320]`, exact permutation `p = 0.0446`.

### Cell slopes over grooming-episode order
- Slope of episodes where Hedy grooms first and Hooke reciprocates over grooming-episode order: vehicle mean `-0.012`, DCZ mean `-0.017`, mean difference `-0.005`, 95% CI `[-0.048, 0.037]`, exact permutation `p = 0.8274`.
- Slope of episodes where Hedy grooms first and Hooke does not reciprocate over grooming-episode order: vehicle mean `0.072`, DCZ mean `-0.015`, mean difference `-0.088`, 95% CI `[-0.165, -0.014]`, exact permutation `p = 0.0559`.
- Slope of episodes where Hooke grooms first and Hedy reciprocates over grooming-episode order: vehicle mean `-0.073`, DCZ mean `0.011`, mean difference `0.084`, 95% CI `[-0.012, 0.179]`, exact permutation `p = 0.1347`.
- Slope of episodes where Hooke grooms first and Hedy does not reciprocate over grooming-episode order: vehicle mean `0.013`, DCZ mean `0.021`, mean difference `0.009`, 95% CI `[-0.042, 0.053]`, exact permutation `p = 0.7702`.


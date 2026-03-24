# Groom Feedback Dynamics Analysis

Cohort: quiet-mask sensitivity session set.
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
- Hedy grooms first, Hooke reciprocates episodes per session: vehicle mean `1.000`, DCZ mean `0.875`, mean difference `-0.125`, 95% CI `[-0.625, 0.375]`, exact permutation `p = 1.0000`.
- Hedy grooms first, Hooke does not reciprocate episodes per session: vehicle mean `3.875`, DCZ mean `3.375`, mean difference `-0.500`, 95% CI `[-2.875, 1.750]`, exact permutation `p = 0.7831`.
- Hooke grooms first, Hedy reciprocates episodes per session: vehicle mean `2.875`, DCZ mean `2.750`, mean difference `-0.125`, 95% CI `[-1.125, 1.000]`, exact permutation `p = 1.0000`.
- Hooke grooms first, Hedy does not reciprocate episodes per session: vehicle mean `1.125`, DCZ mean `2.750`, mean difference `1.625`, 95% CI `[0.125, 3.125]`, exact permutation `p = 0.0970`.

### Cell shares of all grooming episodes
- Share of all grooming episodes where Hedy grooms first and Hooke reciprocates: vehicle mean `0.118`, DCZ mean `0.094`, mean difference `-0.024`, 95% CI `[-0.091, 0.042]`, exact permutation `p = 0.5268`.
- Share of all grooming episodes where Hedy grooms first and Hooke does not reciprocate: vehicle mean `0.401`, DCZ mean `0.325`, mean difference `-0.076`, 95% CI `[-0.223, 0.068]`, exact permutation `p = 0.3694`.
- Share of all grooming episodes where Hooke grooms first and Hedy reciprocates: vehicle mean `0.375`, DCZ mean `0.308`, mean difference `-0.067`, 95% CI `[-0.227, 0.107]`, exact permutation `p = 0.4880`.
- Share of all grooming episodes where Hooke grooms first and Hedy does not reciprocate: vehicle mean `0.106`, DCZ mean `0.272`, mean difference `0.166`, 95% CI `[0.033, 0.302]`, exact permutation `p = 0.0426`.

### Cell slopes over grooming-episode order
- Slope of episodes where Hedy grooms first and Hooke reciprocates over grooming-episode order: vehicle mean `-0.012`, DCZ mean `-0.018`, mean difference `-0.006`, 95% CI `[-0.046, 0.032]`, exact permutation `p = 0.7700`.
- Slope of episodes where Hedy grooms first and Hooke does not reciprocate over grooming-episode order: vehicle mean `0.072`, DCZ mean `-0.011`, mean difference `-0.083`, 95% CI `[-0.158, -0.014]`, exact permutation `p = 0.0514`.
- Slope of episodes where Hooke grooms first and Hedy reciprocates over grooming-episode order: vehicle mean `-0.073`, DCZ mean `0.005`, mean difference `0.079`, 95% CI `[-0.012, 0.170]`, exact permutation `p = 0.1343`.
- Slope of episodes where Hooke grooms first and Hedy does not reciprocate over grooming-episode order: vehicle mean `0.013`, DCZ mean `0.024`, mean difference `0.011`, 95% CI `[-0.038, 0.053]`, exact permutation `p = 0.6788`.


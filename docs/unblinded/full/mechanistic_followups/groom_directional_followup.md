# Groom Directional Follow-Up Analysis

Cohort: full session set.
These follow-ups decompose grooming episodes by which grooming direction appeared first, so the session-level shift can be interpreted as a possible within-session interaction pattern rather than only a static session average.

## Definitions

- Grooming episodes use the existing social-episode definition from the locked preprocessing pipeline: `social_engaged` segments are merged across gaps `<= 2 s` into one social bout.
- `social_engaged` includes `Proximity (<arm's reach)`, `Contact/Sit-with`, `Groom give`, `Groom receive`, `Groom solicit`, `Mount give`, `Mount receive`, `Mount attempt`, `Affiliative touch`, and `Muzzle-muzzle contact`.
- `give_initiated_episode_count` and `receive_initiated_episode_count` count grooming-containing social episodes by whether Hedy or Hooke grooms first in the episode.
- `give_to_receive_prob_same_episode` is the proportion of Hedy-start episodes in which Hooke grooms later in that same episode.
- `receive_to_give_prob_same_episode` is the proportion of Hooke-start episodes in which Hedy grooms later in that same episode.
- The directional latency metrics summarize the median time from the end of the first grooming role to the start of the partner's reciprocating grooming within the same episode.

## Assumptions and interpretation boundaries

- An episode is a social-engagement bout, not a single grooming bout. Non-groom social states such as proximity or contact may occur between the first grooming role and the later opposite grooming role and still count as the same episode.
- The directional probabilities are episode-level follow-through measures. They do not require the opposite grooming role to be the immediate next state, and they do not count every back-and-forth alternation within an episode.
- A Hedy-start episode counts as a `give_to_receive` success if any later `Groom receive` occurs after the end of the first `Groom give` segment in that same episode; the Hooke-start definition is symmetric.
- These measures are intended as mechanistic follow-ups to the session-level grooming result, not as replacements for the primary condition comparison.

## Condition comparisons

- Hedy start episodes per session: vehicle mean `4.875`, DCZ mean `4.250`, mean difference `-0.625`, 95% CI `[-3.125, 1.625]`, exact permutation `p = 0.7198`.
- Hooke start episodes per session: vehicle mean `4.000`, DCZ mean `5.500`, mean difference `1.500`, 95% CI `[0.125, 2.750]`, exact permutation `p = 0.0775`.
- Probability that Hooke reciprocates within the same episode after Hedy starts: vehicle mean `0.238`, DCZ mean `0.230`, mean difference `-0.008`, 95% CI `[-0.173, 0.150]`, exact permutation `p = 0.9313`.
- Probability that Hedy reciprocates within the same episode after Hooke starts: vehicle mean `0.729`, DCZ mean `0.555`, mean difference `-0.175`, 95% CI `[-0.428, 0.107]`, exact permutation `p = 0.2625`.
- Time until Hooke reciprocates within the same episode (s): vehicle mean `31.643`, DCZ mean `3.350`, mean difference `-28.293`, 95% CI `[-80.831, 1.153]`, exact permutation `p = 0.4441`.
- Time until Hedy reciprocates within the same episode (s): vehicle mean `2.812`, DCZ mean `1.294`, mean difference `-1.518`, 95% CI `[-5.401, 0.693]`, exact permutation `p = 0.7524`.

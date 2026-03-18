# Groom Directional Follow-Up Analysis

Cohort: excluding known vet-entry session 596273.
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

- Hedy start episodes per session: vehicle mean `4.875`, DCZ mean `3.857`, mean difference `-1.018`, 95% CI `[-3.500, 1.268]`, exact permutation `p = 0.5200`.
- Hooke start episodes per session: vehicle mean `4.000`, DCZ mean `5.429`, mean difference `1.429`, 95% CI `[-0.018, 2.821]`, exact permutation `p = 0.1047`.
- Probability that Hooke reciprocates within the same episode after Hedy starts: vehicle mean `0.238`, DCZ mean `0.243`, mean difference `0.004`, 95% CI `[-0.171, 0.171]`, exact permutation `p = 0.9840`.
- Probability that Hedy reciprocates within the same episode after Hooke starts: vehicle mean `0.729`, DCZ mean `0.562`, mean difference `-0.167`, 95% CI `[-0.434, 0.141]`, exact permutation `p = 0.3114`.
- Time until Hooke reciprocates within the same episode (s): vehicle mean `31.643`, DCZ mean `3.273`, mean difference `-28.370`, 95% CI `[-80.866, 1.303]`, exact permutation `p = 0.5821`.
- Time until Hedy reciprocates within the same episode (s): vehicle mean `2.812`, DCZ mean `1.412`, mean difference `-1.400`, 95% CI `[-5.259, 0.788]`, exact permutation `p = 0.9499`.

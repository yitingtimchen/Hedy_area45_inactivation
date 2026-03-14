# Groom Follow-Up Analysis

Cohort: excluding known vet-entry session 596273.
These exploratory follow-ups were designed to stay close to the main grooming result rather than mining the full transition matrix.

## Definitions

- Social episodes use the locked preprocessing definition in which `social_engaged` periods are merged across gaps `<= 2 s`.
- The transition stream for non-social entry and exit metrics collapses the cleaned layered timeline into `groom_give`, `groom_receive`, `other_social`, `nonsocial_activity`, `attention_only`, `atypical_only`, and `unscored`.
- Short `unscored` gaps of duration `<= 3 s` are removed before recollapsing adjacent identical states for the non-social entry and exit metrics.
- `episode_turn_taking_prob`: among social episodes that contain grooming, the proportion in which the opposite grooming role appears later in the same social episode.
- `episode_turn_taking_latency_median_s`: the median latency from the end of the first grooming role to the start of the opposite grooming role within that same social episode.
- `groom_to_nonsocial_prob`: among grooming bouts with a known next state, the proportion whose next state is `nonsocial_activity`.
- `nonsocial_to_groom_prob`: among `nonsocial_activity` bouts with a known next state, the proportion whose next state is grooming (`give` or `receive`).

## Condition comparisons

- Episode-level grooming turn-taking probability: vehicle mean `0.493`, DCZ mean `0.416`, mean difference `-0.077`, 95% CI `[-0.244, 0.105]`, exact permutation `p = 0.4427`.
- Median episode-level turn-taking latency (s): vehicle mean `25.406`, DCZ mean `1.514`, mean difference `-23.892`, 95% CI `[-70.086, 0.337]`, exact permutation `p = 0.6329`.
- Groom to nonsocial-activity probability: vehicle mean `0.099`, DCZ mean `0.155`, mean difference `0.056`, 95% CI `[-0.051, 0.155]`, exact permutation `p = 0.3333`.
- Nonsocial-activity to groom probability: vehicle mean `0.092`, DCZ mean `0.117`, mean difference `0.025`, 95% CI `[-0.056, 0.117]`, exact permutation `p = 0.6390`.

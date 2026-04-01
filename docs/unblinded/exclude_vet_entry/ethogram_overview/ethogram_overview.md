# Ethogram Overview

Cohort: excluding known vet-entry session 596273.

This section adds a Figure 1c/1d-style behavioral overview using the repo's locked preprocessing choices:

- Behavior composition uses the precedence-resolved layered timeline, so each second contributes to exactly one primary behavior state.
- The Figure 1c-style pies are coarse summaries: `Rest/Vigilant` pools `Rest/Stationary` with `Vigilant/Scan`, `Behaving` is everything else except `Unscored`, and the final social pie folds sexual behavior into the non-aggressive side.
- Transition analyses remove `Unscored` gaps of duration `<= 3 s` before re-collapsing adjacent identical states.
- Transition probabilities are computed from the resulting primary-state stream as `count(source -> target) / total outgoing transitions from source`.
- To keep the transition maps readable, each source behavior shows up to `2` outgoing edges with count `>= 3`.

## Coverage

- Observed resolved behaviors: `28`.
- Top resolved behavior by pooled mean session time: `Groom give` (`47.14%`).

## Category-level composition

- Affiliative: vehicle `18.94%`, DCZ `15.75%` mean session time.
- Sexual: vehicle `0.37%`, DCZ `0.22%` mean session time.
- Aggression: vehicle `0.13%`, DCZ `0.02%` mean session time.
- Maintenance: vehicle `1.16%`, DCZ `3.51%` mean session time.
- Feeding: vehicle `3.75%`, DCZ `2.99%` mean session time.
- Locomotion: vehicle `1.26%`, DCZ `0.74%` mean session time.
- Attention: vehicle `1.72%`, DCZ `2.17%` mean session time.
- Other: vehicle `0.51%`, DCZ `0.50%` mean session time.
- Atypical: vehicle `0.90%`, DCZ `0.34%` mean session time.
- Unscored: vehicle `0.69%`, DCZ `0.93%` mean session time.

## Top resolved behaviors

- Groom give (Affiliative): pooled mean `47.14%` of session, present in `15` sessions.
- Groom receive (Affiliative): pooled mean `29.16%` of session, present in `15` sessions.
- Proximity (<arm’s reach) (Affiliative): pooled mean `5.09%` of session, present in `15` sessions.
- Rest/Stationary (Maintenance): pooled mean `5.02%` of session, present in `15` sessions.
- Forage/Search (Feeding): pooled mean `4.72%` of session, present in `15` sessions.
- Vigilant/Scan (Attention): pooled mean `3.26%` of session, present in `15` sessions.
- Pace (Atypical): pooled mean `1.09%` of session, present in `3` sessions.
- Drink (Feeding): pooled mean `1.08%` of session, present in `6` sessions.

## Strongest pooled transitions

- Mount give -> Groom give: probability `0.618` from `21` pooled transitions.
- Chew non-food -> Enlist/Recruit: probability `0.583` from `7` pooled transitions.
- Groom solicit -> Groom receive: probability `0.548` from `23` pooled transitions.
- Enlist/Recruit -> Vigilant/Scan: probability `0.421` from `8` pooled transitions.
- Groom receive -> Groom give: probability `0.380` from `46` pooled transitions.
- Drink -> Proximity (<arm’s reach): probability `0.357` from `5` pooled transitions.
- Scratch -> Hiccups: probability `0.343` from `24` pooled transitions.
- Groom receive -> Proximity (<arm’s reach): probability `0.331` from `40` pooled transitions.

# Ethogram Overview

Cohort: full session set.

This section adds a Figure 1c/1d-style behavioral overview using the repo's locked preprocessing choices:

- Behavior composition uses the precedence-resolved layered timeline, so each second contributes to exactly one primary behavior state.
- The Figure 1c-style pies are coarse summaries: `Rest/Vigilant` pools `Rest/Stationary` with `Vigilant/Scan`, `Behaving` is everything else except `Unscored`, and the final social pie folds sexual behavior into the non-aggressive side.
- Transition analyses remove `Unscored` gaps of duration `<= 3 s` before re-collapsing adjacent identical states.
- Transition probabilities are computed from the resulting primary-state stream as `count(source -> target) / total outgoing transitions from source`.
- To keep the transition maps readable, each source behavior shows up to `2` outgoing edges with count `>= 3`.

## Coverage

- Observed resolved behaviors: `29`.
- Top resolved behavior by pooled mean session time: `Groom give` (`46.53%`).

## Category-level composition

- Affiliative: vehicle `18.94%`, DCZ `15.52%` mean session time.
- Sexual: vehicle `0.37%`, DCZ `0.23%` mean session time.
- Aggression: vehicle `0.13%`, DCZ `0.02%` mean session time.
- Maintenance: vehicle `1.16%`, DCZ `3.43%` mean session time.
- Feeding: vehicle `3.75%`, DCZ `2.75%` mean session time.
- Locomotion: vehicle `1.26%`, DCZ `0.78%` mean session time.
- Attention: vehicle `1.72%`, DCZ `2.87%` mean session time.
- Other: vehicle `0.51%`, DCZ `0.46%` mean session time.
- Atypical: vehicle `0.90%`, DCZ `0.45%` mean session time.
- Unscored: vehicle `0.69%`, DCZ `0.93%` mean session time.

## Top resolved behaviors

- Groom give (Affiliative): pooled mean `46.53%` of session, present in `16` sessions.
- Groom receive (Affiliative): pooled mean `28.54%` of session, present in `16` sessions.
- Proximity (<arm’s reach) (Affiliative): pooled mean `5.51%` of session, present in `16` sessions.
- Rest/Stationary (Maintenance): pooled mean `5.25%` of session, present in `16` sessions.
- Forage/Search (Feeding): pooled mean `4.47%` of session, present in `16` sessions.
- Vigilant/Scan (Attention): pooled mean `3.34%` of session, present in `16` sessions.
- Drink (Feeding): pooled mean `1.11%` of session, present in `7` sessions.
- Attention to outside agents (Attention): pooled mean `1.11%` of session, present in `14` sessions.

## Strongest pooled transitions

- Mount give -> Groom give: probability `0.639` from `23` pooled transitions.
- Groom solicit -> Groom receive: probability `0.533` from `24` pooled transitions.
- Chew non-food -> Enlist/Recruit: probability `0.467` from `7` pooled transitions.
- Enlist/Recruit -> Vigilant/Scan: probability `0.421` from `8` pooled transitions.
- Groom receive -> Groom give: probability `0.377` from `49` pooled transitions.
- Scratch -> Hiccups: probability `0.361` from `26` pooled transitions.
- Groom give -> Proximity (<arm’s reach): probability `0.335` from `61` pooled transitions.
- Approach (non-agonistic) -> Hiccups: probability `0.326` from `15` pooled transitions.

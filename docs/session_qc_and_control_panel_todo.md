# Session QC And Control Panel TODO

## Goal

Add a blinded session-visualization and QC layer, expand the broader nonsocial control panels, and keep grooming as the primary result while making the supporting analyses easier to defend and present.

## Blinded Session QC

- Add a new module under `analysis/01_blinded/session_qc/`.
- Generate a detailed ethogram trace for each session using the full resolved behavior labels over time.
- Generate a family-level ethogram trace for each session collapsing labels into:
  - `affiliative`
  - `aggressive`
  - `sexual`
  - `feeding`
  - `locomotion`
  - `attention`
  - `maintenance`
  - `atypical`
  - `unscored`
- Generate an all-session small-multiples QC sheet for quick visual review before unblinding.
- Generate session composition summaries at both the detailed-label level and the family level.

## Blinded QC Table

- Build a blinded QC table with one row per session.
- Include objective review metrics such as:
  - total `unscored` percent of session
  - total `attention` percent of session
  - total `maintenance` percent of session
  - total `feeding` percent of session
  - total `locomotion` percent of session
  - total `atypical` percent of session
  - total number of resolved state transitions
  - total number of family-level transitions
  - existing session exception metadata
- Add outlier-style review flags using blinded rules only.
- Treat flagged sessions as review targets, not automatic exclusions.

## Unblinded Supportive Control Panels

- Expand `analysis/02_unblinded/arousal_controls/` so the broader nonsocial control panel includes all requested families.
- Keep this panel clearly supportive rather than primary.
- Add family-level summaries for:
  - `feeding`
  - `locomotion`
  - `attention`
  - `maintenance`
- Add component-label summaries within those families where useful.
- Keep the usual repo pattern:
  - metrics-by-session table
  - condition summary table
  - figures
  - markdown interpretation doc

## Terminology

- Use `percent of session` in figures, slide text, and presentation-facing docs.
- Avoid using `normalization` as the main public-facing term for duration divided by session length.
- Use `session-length-adjusted duration` only if a more formal phrase is needed in methods prose.

## Repo Organization

- Keep blinded QC outputs under blinded results/docs.
- Keep supportive control outputs under unblinded results/docs.
- Do not mix blinded QC artifacts into the primary grooming result folders.
- Keep grooming as the main result story.

## Sensitivity And Review

- After blinded QC review, decide whether any flagged sessions need sensitivity analyses.
- Keep the main dataset unchanged unless there is a predefined reason for exclusion.
- If exclusions are used, present them as sensitivity analyses rather than redefining the primary dataset.

# Hedy Area 45 Inactivation

Analysis workspace for a blinded behavioral study of DREADD inactivation of Area 45 in a freely interacting macaque dyad.

## Project Layout

- `analysis/00_preprocess/`: preprocessing scripts that turn raw BORIS and video metadata into derived behavior and audio data.
- `analysis/01_blinded/`: blinded summary, sensitivity, and plotting scripts.
- `analysis/02_unblinded/`: unblinding, condition-comparison, transition, and plotting scripts.
- `analysis/utils/`: supporting metadata such as exception notes.
- `data/raw/`: source BORIS tables, videos, ethogram files, and the session key.
- `data/derived/`: regenerated intermediate products such as cleaned timelines and per-second audio features.
- `results/blinded/`: blinded tables and figures used to lock the analysis plan.
- `results/unblinded/full/`: canonical unblinded tables and figures using all sessions.
- `results/unblinded/exclude_vet_entry/`: parallel unblinded tables and figures excluding the known vet-entry session `596273`.
- `results/unblinded/session_unblinding_key.csv`: shared session-to-condition mapping used by both unblinded cohorts.
- `docs/unblinded/full/` and `docs/unblinded/exclude_vet_entry/`: matching narrative summaries for the two unblinded cohorts.
- `docs/`: analysis decisions, sensitivity writeups, and result summaries.

## Current Workflow

1. Run `analysis/00_preprocess/` scripts to build trimmed layered behavior timelines and aligned audio features.
2. Run `analysis/01_blinded/` scripts to generate blinded summaries, figures, and masking sensitivity outputs.
3. Lock endpoints using the blinded tables and docs in `results/blinded/` and `docs/`.
4. Run `analysis/02_unblinded/` scripts to merge condition labels and generate condition-level summaries and figures.

## Notes

- Session-condition mapping remains separate in `data/raw/session_key/Sessions name encoding.xlsx`.
- Generated outputs in `data/derived/` and `results/` can be regenerated from the scripts in `analysis/`.
- The current blinded endpoint logic is documented in `docs/blinded_analysis_plan.md`.
- The current masking sensitivity summary is documented in `docs/audio_mask_sensitivity.md`.

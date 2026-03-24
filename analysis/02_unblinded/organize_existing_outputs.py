from __future__ import annotations

import shutil
from pathlib import Path

from reorg_common import OUTPUT_SELECTION_DIRS


ROOT = Path(__file__).resolve().parents[2]
OLD_RESULTS = ROOT / "results" / "unblinded"
OLD_DOCS = ROOT / "docs" / "unblinded"
NEW_RESULTS = ROOT / "results" / "unblinded"
NEW_DOCS = ROOT / "docs" / "unblinded"

SELECTION_MAP = {
    "full": "full",
    "exclude_vet_entry": "exclude_vet_entry",
    "exclude_smoothed_loud_epochs": "quiet_mask",
}

NORMALIZED_FIGURES = [
    "contextual_behavior_session_summary.png",
    "groom_bout_composite_session_summary.png",
    "groom_bout_duration_session_summary.png",
    "groom_bout_session_summary.png",
    "groom_composite_session_summary.png",
    "groom_directional_followup.png",
    "groom_duration_session_summary.png",
    "groom_episode_class_mean_composition.png",
    "groom_episode_class_session_summary.png",
    "groom_transition_followup_panel.png",
    "sexual_family_bout_exploratory.png",
    "sexual_family_duration_exploratory.png",
]

WITHIN_SESSION_FIGURES = [
    "groom_composite_cumulative_dynamics.png",
    "groom_duration_cumulative_dynamics.png",
    "groom_feedback_dynamics_panel.png",
]

TEMPORAL_FIGURES = [
    "temporal_dependence.png",
    "sexual_family_temporal_dependence.png",
]

NORMALIZED_DOCS = [
    "groom_bout_composite_session_summary.md",
    "groom_bout_duration_session_summary.md",
    "groom_bout_session_summary.md",
    "groom_composite_session_summary.md",
    "groom_directional_followup.md",
    "groom_duration_session_summary.md",
    "groom_episode_class_session_summary.md",
    "sexual_family_exploratory.md",
]

TEMPORAL_DOCS = [
    "temporal_dependence.md",
    "sexual_family_temporal_dependence.md",
]


def copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def main() -> None:
    for new_selection, old_selection in SELECTION_MAP.items():
        output_selection = OUTPUT_SELECTION_DIRS[new_selection]
        for name in NORMALIZED_FIGURES:
            copy_if_exists(
                OLD_RESULTS / old_selection / "figures" / name,
                NEW_RESULTS / output_selection / "normalized_total_duration" / "figures" / name,
            )
        for name in WITHIN_SESSION_FIGURES:
            copy_if_exists(
                OLD_RESULTS / old_selection / "figures" / name,
                NEW_RESULTS / output_selection / "within_session_dynamics_minutes" / "figures" / name,
            )
        for name in TEMPORAL_FIGURES:
            copy_if_exists(
                OLD_RESULTS / old_selection / "figures" / name,
                NEW_RESULTS / output_selection / "across_session_temporal_dependence" / "figures" / name,
            )

        for name in NORMALIZED_DOCS:
            copy_if_exists(
                OLD_DOCS / old_selection / name,
                NEW_DOCS / output_selection / "normalized_total_duration" / name,
            )
        for name in TEMPORAL_DOCS:
            copy_if_exists(
                OLD_DOCS / old_selection / name,
                NEW_DOCS / output_selection / "across_session_temporal_dependence" / name,
            )


if __name__ == "__main__":
    main()

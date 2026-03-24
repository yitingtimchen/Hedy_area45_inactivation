from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from reorg_common import OUTPUT_SELECTION_DIRS


ROOT = Path(__file__).resolve().parent
RESULTS_ROOT = ROOT.parents[1] / "results" / "unblinded"
DOCS_ROOT = ROOT.parents[1] / "docs" / "unblinded"
SCRIPTS = [
    ROOT / "raw_total_duration" / "plot_raw_total_duration.py",
    ROOT / "arousal_controls" / "plot_arousal_controls.py",
    ROOT / "loud_only_stress_plots.py",
    ROOT / "organize_existing_outputs.py",
]
AGGREGATION_MODES = [
    "raw_total_duration",
    "normalized_total_duration",
    "across_session_temporal_dependence",
    "within_session_dynamics_minutes",
]
LEGACY_SELECTION_ALIASES = [
    "exclude_smoothed_loud_epochs",
]


def main() -> None:
    for selection_dir in OUTPUT_SELECTION_DIRS.values():
        for aggregation_mode in AGGREGATION_MODES:
            shutil.rmtree(RESULTS_ROOT / selection_dir / aggregation_mode, ignore_errors=True)
            shutil.rmtree(DOCS_ROOT / selection_dir / aggregation_mode, ignore_errors=True)
    for selection_dir in LEGACY_SELECTION_ALIASES:
        shutil.rmtree(RESULTS_ROOT / selection_dir, ignore_errors=True)
        shutil.rmtree(DOCS_ROOT / selection_dir, ignore_errors=True)
    for script in SCRIPTS:
        subprocess.run([sys.executable, str(script)], check=True)


if __name__ == "__main__":
    main()

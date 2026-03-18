from __future__ import annotations

import sys
from pathlib import Path

PARENT = Path(__file__).resolve().parents[1]
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from plot_session_summaries import main as plot_main  # noqa: E402
from unblind_and_compare import main as analyze_main  # noqa: E402


def main() -> None:
    analyze_main()
    plot_main()


if __name__ == "__main__":
    main()

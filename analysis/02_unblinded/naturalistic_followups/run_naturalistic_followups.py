from __future__ import annotations

from analyze_followups import main as analyze_main
from plot_followups import main as plot_main


def main() -> None:
    analyze_main()
    plot_main()


if __name__ == "__main__":
    main()

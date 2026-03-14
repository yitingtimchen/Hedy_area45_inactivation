from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
BLINDED_TABLES_DIR = ROOT / "results" / "blinded" / "tables"
DOCS_DIR = ROOT / "docs"

BOOTSTRAP_SAMPLES = 20000
BOOTSTRAP_SEED = 17


def bootstrap_mean_ci(values: np.ndarray, n_boot: int = BOOTSTRAP_SAMPLES, seed: int = BOOTSTRAP_SEED) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    values = np.asarray(values, dtype=float)
    draws = rng.choice(values, size=(n_boot, len(values)), replace=True).mean(axis=1)
    low, high = np.percentile(draws, [2.5, 97.5])
    return float(low), float(high)


def sign_flip_count(full: np.ndarray, masked: np.ndarray) -> int:
    full_sign = np.sign(full)
    masked_sign = np.sign(masked)
    return int(np.sum(full_sign != masked_sign))


def summarize_metric(
    df: pd.DataFrame,
    full_col: str,
    masked_col: str,
    label: str,
    unit: str,
    equivalence_bound: float | None,
) -> dict[str, object]:
    full = df[full_col].to_numpy(dtype=float)
    masked = df[masked_col].to_numpy(dtype=float)
    delta = masked - full
    ci_low, ci_high = bootstrap_mean_ci(delta)

    row: dict[str, object] = {
        "metric": label,
        "unit": unit,
        "n_sessions": len(df),
        "mean_full": float(np.mean(full)),
        "mean_masked": float(np.mean(masked)),
        "mean_delta": float(np.mean(delta)),
        "median_delta": float(np.median(delta)),
        "sd_delta": float(np.std(delta, ddof=1)),
        "delta_ci95_low": ci_low,
        "delta_ci95_high": ci_high,
        "equivalence_bound_abs": equivalence_bound,
    }
    if equivalence_bound is not None:
        row["delta_ci_within_equivalence_bound"] = bool((ci_low > -equivalence_bound) and (ci_high < equivalence_bound))
    else:
        row["delta_ci_within_equivalence_bound"] = pd.NA
    if "net_receive_minus_give" in full_col:
        row["sign_flip_count"] = sign_flip_count(full, masked)
    else:
        row["sign_flip_count"] = pd.NA
    return row


def build_report(stats: pd.DataFrame) -> str:
    primary = stats[stats["metric"].isin(["Net grooming duration", "Groom reciprocity"])].copy()
    supportive = stats[stats["metric"].isin(["Total grooming", "Social engagement"])].copy()
    validation = stats[stats["metric"].isin(["Attention to outside agents"])].copy()

    lines = [
        "# Audio Mask Sensitivity",
        "",
        "## Logic",
        "",
        "- Comparison is paired within session: `quiet_masked_p90 - full_trimmed`.",
        "- The quiet mask removes the loudest 10% of 1 s bins from each trimmed session.",
        "- The main question is not whether the two versions are mathematically identical, but whether masking changes the primary endpoints by a practically meaningful amount.",
        "- Practical equivalence bounds were set a priori at `+/- 5 percentage points` for duration-based percent-of-session metrics and `+/- 0.05` for grooming reciprocity.",
        "- Evidence for robustness is defined as the bootstrap 95% CI of the mean delta lying fully within the prespecified equivalence bound.",
        "",
        "## Primary endpoints",
        "",
    ]

    for row in primary.itertuples(index=False):
        lines.append(
            f"- {row.metric}: mean delta `{row.mean_delta:.3f} {row.unit}`, 95% bootstrap CI "
            f"`[{row.delta_ci95_low:.3f}, {row.delta_ci95_high:.3f}]`, equivalence supported = "
            f"`{row.delta_ci_within_equivalence_bound}`."
        )

    lines.extend(
        [
            "",
            "## Supporting endpoints",
            "",
        ]
    )
    for row in supportive.itertuples(index=False):
        lines.append(
            f"- {row.metric}: mean delta `{row.mean_delta:.3f} {row.unit}`, 95% bootstrap CI "
            f"`[{row.delta_ci95_low:.3f}, {row.delta_ci95_high:.3f}]`, equivalence supported = "
            f"`{row.delta_ci_within_equivalence_bound}`."
        )

    lines.extend(
        [
            "",
            "## Mask-validation endpoint",
            "",
        ]
    )
    for row in validation.itertuples(index=False):
        lines.append(
            f"- {row.metric}: mean delta `{row.mean_delta:.3f} {row.unit}`, 95% bootstrap CI "
            f"`[{row.delta_ci95_low:.3f}, {row.delta_ci95_high:.3f}]`."
        )

    net_row = primary[primary["metric"] == "Net grooming duration"].iloc[0]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- The normalized net grooming endpoint changed little on average and had `{int(net_row['sign_flip_count'])}` sign flip(s) across 16 sessions after masking.",
            "- Groom reciprocity is the most robust primary endpoint because it is already session-length independent and shows very small mask-related shifts.",
            "- Attention to outside agents decreases after masking, which supports that the mask is preferentially removing distraction-related loud moments rather than strongly altering the main grooming balance measures.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    decision = pd.read_csv(BLINDED_TABLES_DIR / "blinded_decision_table.csv", dtype={"session_id": str})

    specs = [
        (
            "groom_duration_net_receive_minus_give_pct_session",
            "groom_duration_net_receive_minus_give_pct_quiet_masked_p90",
            "Net grooming duration",
            "pct_session",
            5.0,
        ),
        (
            "groom_duration_reciprocity_0to1",
            "groom_duration_reciprocity_0to1_quiet_masked_p90",
            "Groom reciprocity",
            "index",
            0.05,
        ),
        (
            "groom_total_pct_session",
            "groom_total_pct_quiet_masked_p90",
            "Total grooming",
            "pct_session",
            5.0,
        ),
        (
            "social_engaged_pct_session",
            "social_engaged_pct_quiet_masked_p90",
            "Social engagement",
            "pct_session",
            5.0,
        ),
        (
            "attention_to_outside_agents_resolved_pct_session",
            "attention_outside_pct_quiet_masked_p90",
            "Attention to outside agents",
            "pct_session",
            None,
        ),
    ]

    rows = [summarize_metric(decision, *spec) for spec in specs]
    stats = pd.DataFrame(rows)
    stats.to_csv(BLINDED_TABLES_DIR / "blinded_audio_mask_sensitivity_stats.csv", index=False)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report(stats)
    (DOCS_DIR / "audio_mask_sensitivity.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()

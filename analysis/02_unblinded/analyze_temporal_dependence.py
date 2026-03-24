from __future__ import annotations

from itertools import combinations, permutations
from pathlib import Path

import numpy as np
import pandas as pd

from output_layout import docs_section_dir, results_tables_dir


ROOT = Path(__file__).resolve().parents[2]
UNBLINDED_ROOT = ROOT / "results" / "unblinded"
DOCS_ROOT = ROOT / "docs" / "unblinded"

COHORTS = [
    ("full", "full session set"),
    ("quiet_mask", "quiet-mask sensitivity session set"),
    ("exclude_vet_entry", "excluding known vet-entry session 596273"),
]

PRIMARY_METRICS = [
    "groom_duration_net_receive_minus_give_pct_session",
    "groom_duration_reciprocity_0to1",
    "groom_bout_net_receive_minus_give",
    "groom_bout_reciprocity_0to1",
]

PRETTY = {
    "groom_duration_net_receive_minus_give_pct_session": "Net grooming (% session; receive - give)",
    "groom_duration_reciprocity_0to1": "Grooming reciprocity (0 to 1)",
    "groom_bout_net_receive_minus_give": "Net grooming bouts (receive - give)",
    "groom_bout_reciprocity_0to1": "Grooming bout reciprocity (0 to 1)",
}


def exact_label_permutation_p(values: np.ndarray, labels: np.ndarray) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    labels = np.asarray(labels)
    n = len(values)
    dcz_n = int(np.sum(labels == "DCZ"))
    observed = values[labels == "DCZ"].mean() - values[labels == "vehicle"].mean()
    diffs = []
    for idx in combinations(range(n), dcz_n):
        mask = np.zeros(n, dtype=bool)
        mask[list(idx)] = True
        diffs.append(values[mask].mean() - values[~mask].mean())
    diffs = np.asarray(diffs)
    return float(observed), float(np.mean(np.abs(diffs) >= abs(observed)))


def fit_line(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    xc = x - x.mean()
    X = np.column_stack([np.ones(len(x)), xc])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    fitted = X @ beta
    resid = y - fitted
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    ss_res = float(np.sum(resid**2))
    r2 = np.nan if ss_tot == 0 else 1.0 - ss_res / ss_tot
    return {
        "intercept_at_mean_session": float(beta[0]),
        "slope_per_session": float(beta[1]),
        "r2": float(r2),
    }


def exact_slope_permutation_p(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    observed = abs(fit_line(x, y)["slope_per_session"])
    n = len(y)
    if n <= 8:
        perm_slopes = [abs(fit_line(x, y[list(order)])["slope_per_session"]) for order in permutations(range(n))]
        return float(np.mean(np.asarray(perm_slopes, dtype=float) >= observed))

    rng = np.random.default_rng(101)
    perm_slopes = []
    for _ in range(20000):
        perm_slopes.append(abs(fit_line(x, rng.permutation(y))["slope_per_session"]))
    return float(np.mean(np.asarray(perm_slopes, dtype=float) >= observed))


def analyze_metric(df: pd.DataFrame, metric: str) -> dict[str, object]:
    ordered = df.sort_values("session_index").reset_index(drop=True)
    y = ordered[metric].to_numpy(dtype=float)
    x = ordered["session_index"].to_numpy(dtype=float)
    condition = ordered["condition"].to_numpy()

    raw_effect, raw_p = exact_label_permutation_p(y, condition)
    vehicle = ordered.loc[ordered["condition"] == "vehicle", ["session_index", metric]]
    dcz = ordered.loc[ordered["condition"] == "DCZ", ["session_index", metric]]
    vehicle_fit = fit_line(vehicle["session_index"].to_numpy(dtype=float), vehicle[metric].to_numpy(dtype=float))
    dcz_fit = fit_line(dcz["session_index"].to_numpy(dtype=float), dcz[metric].to_numpy(dtype=float))

    return {
        "metric": metric,
        "pretty_metric": PRETTY[metric],
        "n_sessions": int(len(ordered)),
        "raw_condition_effect": float(raw_effect),
        "raw_condition_permutation_p_two_sided": float(raw_p),
        "vehicle_slope_per_session": float(vehicle_fit["slope_per_session"]),
        "vehicle_slope_permutation_p_two_sided": float(
            exact_slope_permutation_p(
                vehicle["session_index"].to_numpy(dtype=float),
                vehicle[metric].to_numpy(dtype=float),
            )
        ),
        "vehicle_r2": float(vehicle_fit["r2"]),
        "dcz_slope_per_session": float(dcz_fit["slope_per_session"]),
        "dcz_slope_permutation_p_two_sided": float(
            exact_slope_permutation_p(
                dcz["session_index"].to_numpy(dtype=float),
                dcz[metric].to_numpy(dtype=float),
            )
        ),
        "dcz_r2": float(dcz_fit["r2"]),
    }


def build_markdown(summary: pd.DataFrame, cohort_label: str) -> str:
    lines = [
        "# Temporal Dependence Analysis",
        "",
        f"Cohort: {cohort_label}.",
        "This exploratory analysis checks whether the primary grooming results could plausibly be explained by simple drift across session order.",
        "",
        "## Methods",
        "",
        "- Metrics analyzed: net grooming and grooming reciprocity.",
        "- `Raw condition effect` is the original exact two-sided label permutation result on the session-level metric.",
        "- `Vehicle slope` and `DCZ slope` are estimated separately by fitting a linear trend over session order within each condition.",
        "- Slope significance is assessed with a two-sided permutation test within each condition, using the fitted slope rather than `R^2` as the test statistic.",
        "",
        "## Results",
        "",
    ]
    for row in summary.itertuples(index=False):
        lines.extend(
            [
                f"### {row.pretty_metric}",
                f"- Raw condition effect: `{row.raw_condition_effect:.3f}`, exact permutation `p = {row.raw_condition_permutation_p_two_sided:.4f}`.",
                f"- Vehicle slope: `{row.vehicle_slope_per_session:.3f}` per session, slope permutation `p = {row.vehicle_slope_permutation_p_two_sided:.4f}`.",
                f"- DCZ slope: `{row.dcz_slope_per_session:.3f}` per session, slope permutation `p = {row.dcz_slope_permutation_p_two_sided:.4f}`.",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    for cohort_name, cohort_label in COHORTS:
        tables_dir = results_tables_dir(cohort_name, "across_session_temporal_dependence")
        docs_dir = docs_section_dir(cohort_name, "across_session_temporal_dependence")

        decision = pd.read_csv(results_tables_dir(cohort_name, "single_value_core") / "unblinded_decision_table.csv", dtype={"session_id": str})
        summary = pd.DataFrame([analyze_metric(decision, metric) for metric in PRIMARY_METRICS])
        summary.to_csv(tables_dir / "temporal_dependence_summary.csv", index=False)
        markdown = build_markdown(summary, cohort_label)
        (docs_dir / "temporal_dependence.md").write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    main()

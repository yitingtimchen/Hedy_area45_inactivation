from __future__ import annotations

from itertools import combinations, permutations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SESSION_FRACTION_GRID = np.linspace(0.0, 1.0, 101)

VEHICLE_COLOR = "#A9B7C9"
DCZ_COLOR = "#1F4AA8"
LINE_COLOR = "#7A7A7A"
TEXT_COLOR = "#111111"
SIG_COLOR = "#A61C1C"
FONT_SIZE = 10.5
TITLE_SIZE = 12


def round_up_abs_limit(value: float, step: float) -> float:
    if not np.isfinite(value) or value <= 0:
        return step
    return float(step * np.ceil(value / step))


def fit_line(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    xc = x - x.mean()
    X = np.column_stack([np.ones(len(x)), xc])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return float(beta[0]), float(beta[1])


def exact_label_permutation_p(values: np.ndarray, labels: np.ndarray) -> float:
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
    diffs = np.asarray(diffs, dtype=float)
    return float(np.mean(np.abs(diffs) >= abs(observed)))


def exact_slope_permutation_p(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    _, observed_slope = fit_line(x, y)
    observed = abs(observed_slope)
    n = len(y)
    if n <= 8:
        perm_slopes = [abs(fit_line(x, y[list(order)])[1]) for order in permutations(range(n))]
        return float(np.mean(np.asarray(perm_slopes, dtype=float) >= observed))

    rng = np.random.default_rng(101)
    perm_slopes = []
    for _ in range(20000):
        perm_slopes.append(abs(fit_line(x, rng.permutation(y))[1]))
    return float(np.mean(np.asarray(perm_slopes, dtype=float) >= observed))


def p_style(p_value: float | None) -> dict[str, object]:
    if p_value is None or not np.isfinite(p_value):
        return {"text": "p = NA", "color": TEXT_COLOR, "fontweight": "normal"}
    is_sig = p_value < 0.05
    return {
        "text": f"p = {p_value:.4f}",
        "color": SIG_COLOR if is_sig else TEXT_COLOR,
        "fontweight": "bold" if is_sig else "normal",
    }


def style_axis(ax: plt.Axes, tick_size: float = 10.0) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.tick_params(length=3.5, width=0.8, labelsize=tick_size)


def paired_strip(
    ax: plt.Axes,
    df: pd.DataFrame,
    metric: str,
    ylabel: str,
    title: str,
    p_value: float | None = None,
    y_limits: tuple[float, float] | None = None,
    log_scale: bool = False,
    p_loc: tuple[float, float] = (0.02, 0.97),
) -> None:
    sub = df[["condition", metric]].copy()
    sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
    sub = sub.dropna(subset=[metric]).reset_index(drop=True)

    vehicle = sub.loc[sub["condition"] == "vehicle", metric].to_numpy(dtype=float)
    dcz = sub.loc[sub["condition"] == "DCZ", metric].to_numpy(dtype=float)

    rng = np.random.default_rng(4)
    veh_jitter = rng.uniform(-0.06, 0.06, size=len(vehicle))
    dcz_jitter = rng.uniform(-0.06, 0.06, size=len(dcz))

    ax.scatter(np.full(len(vehicle), 0) + veh_jitter, vehicle, color=VEHICLE_COLOR, s=40, zorder=3)
    ax.scatter(np.full(len(dcz), 1) + dcz_jitter, dcz, color=DCZ_COLOR, s=40, zorder=3)

    for x, values, color in [(0, vehicle, VEHICLE_COLOR), (1, dcz, DCZ_COLOR)]:
        if len(values) == 0:
            continue
        mean_value = float(np.mean(values))
        ax.plot([x - 0.18, x + 0.18], [mean_value, mean_value], color=color, linewidth=3.0, zorder=4)

    ax.set_xticks([0, 1], ["Vehicle", "DCZ"])
    ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
    ax.set_title(title, fontsize=TITLE_SIZE, loc="left")
    if p_value is not None:
        label = p_style(p_value)
        ax.text(
            p_loc[0],
            p_loc[1],
            label["text"],
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9.6,
            color=label["color"],
            fontweight=label["fontweight"],
        )
    if log_scale:
        ax.set_yscale("log")
    if y_limits is not None:
        ax.set_ylim(*y_limits)
    style_axis(ax)


def interpolate_session_curve(
    session_df: pd.DataFrame,
    metric: str,
    duration_s: float,
    is_signed: bool,
) -> np.ndarray:
    ordered = (
        session_df[["elapsed_frac_session", metric]]
        .dropna(subset=["elapsed_frac_session", metric])
        .drop_duplicates(subset=["elapsed_frac_session"], keep="last")
        .sort_values("elapsed_frac_session")
        .reset_index(drop=True)
    )
    x = ordered["elapsed_frac_session"].to_numpy(dtype=float)
    y = 100.0 * ordered[metric].to_numpy(dtype=float) / duration_s
    if len(x) == 0:
        return np.full_like(SESSION_FRACTION_GRID, np.nan, dtype=float)
    if x[0] > 0:
        x = np.insert(x, 0, 0.0)
        y = np.insert(y, 0, 0.0)
    if x[-1] < 1.0:
        x = np.append(x, 1.0)
        y = np.append(y, y[-1])
    curve = np.interp(SESSION_FRACTION_GRID, x, y)
    if not is_signed:
        curve = np.maximum.accumulate(curve)
    return curve

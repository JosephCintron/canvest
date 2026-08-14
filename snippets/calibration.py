"""Prediction calibration — an illustrative excerpt.

The accuracy question a research-minded operator actually cares about: do the
resale *predictions* track what pieces *realized*, and does that tracking improve
as data accumulates?

Given (predicted, realized) pairs, this computes signed and absolute error, a
"success rate" (share of predictions within a tolerance band), and a per-category
bias-correction factor that is only trusted once a category has enough realized
samples. Simplified, standalone, dependency-free.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median


@dataclass(frozen=True)
class Outcome:
    category: str
    predicted_usd: float   # the model's resale-mid estimate, made before the sale
    realized_usd: float    # what the piece actually sold for


@dataclass
class ErrorRow:
    category: str
    predicted_usd: float
    realized_usd: float
    error_pct: float       # signed: (realized - predicted) / predicted; + = under-estimate
    abs_error_pct: float


def error_rows(outcomes: list[Outcome]) -> list[ErrorRow]:
    rows: list[ErrorRow] = []
    for o in outcomes:
        if o.predicted_usd <= 0:
            continue  # can't score a non-positive prediction
        err = (o.realized_usd - o.predicted_usd) / o.predicted_usd
        rows.append(ErrorRow(o.category, o.predicted_usd, o.realized_usd,
                             round(err, 4), round(abs(err), 4)))
    return rows


def success_rate(rows: list[ErrorRow], tolerance: float = 0.20) -> float:
    """Share of predictions landing within +/- `tolerance` of the realized price."""
    if not rows:
        return 0.0
    hits = sum(1 for r in rows if r.abs_error_pct <= tolerance)
    return hits / len(rows)


def summarize(rows: list[ErrorRow]) -> dict:
    if not rows:
        return {"n": 0}
    return {
        "n": len(rows),
        "mean_abs_error_pct": round(mean(r.abs_error_pct for r in rows), 4),
        "median_error_pct": round(median(r.error_pct for r in rows), 4),
        "mean_error_pct": round(mean(r.error_pct for r in rows), 4),  # signed = overall bias
        "success_rate_20pct": round(success_rate(rows, 0.20), 3),
    }


def bias_factors(rows: list[ErrorRow], min_samples: int = 5) -> dict[str, dict]:
    """Per-category multiplier that corrects a systematic bias.

    factor = 1 / (1 + mean_signed_error). A category we consistently UNDER-estimate
    (mean error > 0) gets factor > 1, nudging future estimates up; and vice-versa.
    Advisory only, and only applied once a category has `min_samples` realizations —
    the whole point is to not "learn" from noise.
    """
    by_cat: dict[str, list[ErrorRow]] = {}
    for r in rows:
        by_cat.setdefault(r.category or "uncategorized", []).append(r)

    out: dict[str, dict] = {}
    for cat, rs in by_cat.items():
        if len(rs) < min_samples:
            continue
        mean_err = mean(r.error_pct for r in rs)
        denom = 1.0 + mean_err
        if denom <= 0:  # degenerate; skip rather than flip the sign
            continue
        out[cat] = {"factor": round(1.0 / denom, 4), "n": len(rs),
                    "mean_error_pct": round(mean_err, 4)}
    return out


if __name__ == "__main__":
    demo = [
        Outcome("Screenprint", 470, 455), Outcome("Serigraph", 350, 380),
        Outcome("Serigraph", 520, 610), Outcome("Etching", 260, 220),
        Outcome("Lithograph", 300, 315), Outcome("Screenprint", 410, 300),
        Outcome("Serigraph", 300, 330), Outcome("Serigraph", 480, 505),
        Outcome("Serigraph", 410, 395), Outcome("Serigraph", 360, 350),
    ]
    rows = error_rows(demo)
    print("summary:", summarize(rows))
    print("bias factors (categories with >= 5 samples):")
    for cat, f in bias_factors(rows).items():
        print(f"  {cat:12s} factor {f['factor']}  (n={f['n']}, mean err {f['mean_error_pct']:+.1%})")

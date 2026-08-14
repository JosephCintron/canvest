"""
Canvest — the evidence gate: a self-contained, runnable illustration.

This is a STANDALONE teaching example, not the Canvest product source. It
demonstrates the discipline at the heart of Canvest and, more generally, the
pattern the project uses to make a language model's output *safe to act on with
money*:

    valuation (a model proposes)  ->  deterministic ROI economics
                                  ->  the EVIDENCE GATE (code disposes)
                                  ->  a bid / no-bid / watch / skip verdict

The interesting engineering is the *gate* and the *honest calibration of the
predictions* — the parts that let you trust the output — not the model itself. So
the resale estimates here are hard-coded (as if a model already returned them),
and the example runs with the Python standard library only: no network, no model,
no dependencies.

    python gate_demo.py              # run synthetic lots through the gate
    python gate_demo.py --calibrate  # score past predictions against realized prices

The whole point of the gate: a lot with a *great* ROI on paper is returned as
NO-BID when no verified, realized comparable supports the resale number. That
refusal — not the optimistic estimate — is the product.

For review only; not licensed for reuse. See ../../LICENSE.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from statistics import mean, median

# =========================================================================== #
# PART 1 — Deterministic cost / ROI economics
#
# The economics of a bid are cheap and change every time the bid moves; the
# resale *estimate* is expensive (a model call) and rare. So a valuation is made
# once, and this pure math recomputes ROI on every read for free. (A simplified
# version of snippets/roi.py; rates are illustrative, not Canvest's tuned values.)
# =========================================================================== #

BUYER_PREMIUM_RATE = 0.22   # auction-house premium on the hammer bid
SALES_TAX_RATE = 0.07       # applied to bid + premium
RESALE_FEE_RATE = 0.15      # marketplace / consignment fees on resale
SHIPPING = {"small": 55.0, "medium": 110.0, "large": 180.0}

MAX_BID_USD = 200.0         # hard ceiling for this price band
ROI_BID_TARGET = 0.40       # ROI a lot must clear to be *biddable* economics
COMP_SUPPORT_FRAC = 0.60    # a realized comp must be >= this * resale estimate


def all_in_cost(bid: float, size_class: str) -> float:
    """Landed cost of winning at `bid`: hammer + premium + tax + shipping."""
    premium = bid * BUYER_PREMIUM_RATE
    tax = (bid + premium) * SALES_TAX_RATE
    return bid + premium + tax + SHIPPING.get(size_class, SHIPPING["medium"])


def roi_of(bid: float, resale_mid: float, size_class: str) -> float:
    """Projected ROI = net profit / landed cost. Negative means a projected loss."""
    cost = all_in_cost(bid, size_class)
    net_resale = resale_mid * (1.0 - RESALE_FEE_RATE)
    return (net_resale - cost) / cost if cost > 0 else 0.0


# =========================================================================== #
# PART 2 — The lot and its evidence
#
# `best_comp` is the strongest comparable sale the valuation could find. The gate
# cares about ONE thing above all: is the resale number backed by a real, sold
# (realized) price — not merely an *asking* price, and not nothing?
# =========================================================================== #

@dataclass(frozen=True)
class Comp:
    price: float
    kind: str      # "realized" (actually sold) or "asking" (just listed)
    source: str    # where it came from; a comp with no source does not qualify


@dataclass(frozen=True)
class Lot:
    title: str
    category: str
    size_class: str
    bid: float             # current bid
    resale_mid: float      # the model's resale estimate (0 == not yet valued)
    best_comp: Comp | None


def comp_qualifies(lot: Lot) -> bool:
    """The evidence test. A comp backs the resale number only if it is realized,
    sourced, and not wildly below the estimate we are being asked to trust."""
    c = lot.best_comp
    return bool(
        c
        and c.kind == "realized"
        and c.source
        and c.price >= COMP_SUPPORT_FRAC * lot.resale_mid
    )


# =========================================================================== #
# PART 3 — The gate. Economics propose a tier; the evidence gate disposes.
# =========================================================================== #

def verdict_for(lot: Lot) -> tuple[str, float, str]:
    """Return (verdict, roi, note). Verdict is one of BID / NO-BID / WATCH / SKIP."""
    roi = roi_of(lot.bid, lot.resale_mid, lot.size_class) if lot.resale_mid > 0 else 0.0

    if lot.bid > MAX_BID_USD:
        return "SKIP", roi, "over budget"
    if lot.resale_mid <= 0:
        return "WATCH", roi, "not yet valued"
    if roi <= 0:
        return "SKIP", roi, "projected loss"
    if roi < ROI_BID_TARGET:
        return "WATCH", roi, "positive but below the bid target"

    # Economics are biddable. NOW the gate decides — and this is the whole point.
    if comp_qualifies(lot):
        return "BID", roi, f"backed by a realized comp (${lot.best_comp.price:.0f})"
    if lot.best_comp is None:
        return "NO-BID", roi, "great economics, but no comparable at all"
    if lot.best_comp.kind != "realized":
        return "NO-BID", roi, "only an *asking* comp — no realized sale to trust"
    return "NO-BID", roi, "best realized comp sits below the evidence floor"


# Synthetic lots — no real listings, artists, or prices.
LOTS = [
    Lot("Signed serigraph, framed", "Serigraph", "small", bid=130, resale_mid=620,
        best_comp=Comp(560, "realized", "auction-archive")),
    Lot("Attractive lithograph, no track record", "Lithograph", "small", bid=90,
        resale_mid=520, best_comp=Comp(150, "realized", "auction-archive")),
    Lot("Estate screenprint, unbacked", "Screenprint", "medium", bid=110,
        resale_mid=480, best_comp=None),
    Lot("Gallery etching, asking-price only", "Etching", "small", bid=95,
        resale_mid=430, best_comp=Comp(700, "asking", "gallery-listing")),
    Lot("Mid-tier etching", "Etching", "small", bid=95, resale_mid=250,
        best_comp=Comp(240, "realized", "auction-archive")),
    Lot("Blue-chip lot, out of band", "Serigraph", "medium", bid=260, resale_mid=1500,
        best_comp=Comp(1450, "realized", "auction-archive")),
    Lot("Overbid decorative piece", "Decor", "medium", bid=120, resale_mid=90,
        best_comp=None),
]


def run_gate() -> None:
    print("verdict   ROI    best comp            lot")
    print("-" * 72)
    for lot in LOTS:
        v, roi, note = verdict_for(lot)
        if lot.best_comp is None:
            comp = "none"
        else:
            comp = f"${lot.best_comp.price:.0f} {lot.best_comp.kind}"
        flag = "   <- the point" if lot.title.startswith("Attractive lithograph") else ""
        print(f"{v:8s}  {roi * 100:4.0f}%  {comp:18s}  {lot.title}{flag}")
    print("-" * 72)
    print("A biddable ROI with no verified realized comp is NO-BID, not a buy.\n"
          "The refusal is the product: it is what stops an optimistic estimate\n"
          "from turning into a losing purchase.")


# =========================================================================== #
# PART 4 — Calibration: are the predictions honest?
#
# The output we trust least is the resale prediction, so it is measured, not
# assumed. Given (predicted, realized) pairs, report the success rate, the mean
# errors, and a per-category bias correction that is only trusted once a category
# has enough realized samples. (A simplified version of snippets/calibration.py.)
# =========================================================================== #

@dataclass(frozen=True)
class Outcome:
    category: str
    predicted_usd: float
    realized_usd: float


# Synthetic realized outcomes — illustrate the *method*, not a track record.
OUTCOMES = [
    Outcome("Serigraph", 350, 380), Outcome("Serigraph", 520, 610),
    Outcome("Serigraph", 300, 330), Outcome("Serigraph", 480, 505),
    Outcome("Serigraph", 410, 395), Outcome("Serigraph", 360, 350),
    Outcome("Screenprint", 470, 455), Outcome("Screenprint", 410, 300),
    Outcome("Etching", 260, 220), Outcome("Lithograph", 300, 315),
]


def run_calibration(tolerance: float = 0.20, min_samples: int = 5) -> None:
    errs = [(o.category, (o.realized_usd - o.predicted_usd) / o.predicted_usd)
            for o in OUTCOMES if o.predicted_usd > 0]
    signed = [e for _, e in errs]
    hits = sum(1 for e in signed if abs(e) <= tolerance)

    print(f"n = {len(errs)} realized predictions\n")
    print(f"prediction success rate (within +/-{tolerance:.0%}): "
          f"{hits / len(errs):.0%}  ({hits}/{len(errs)})")
    print(f"mean absolute error : {mean(abs(e) for e in signed):.1%}")
    print(f"mean signed error   : {mean(signed):+.1%}   (overall bias)")
    print(f"median signed error : {median(signed):+.1%}\n")

    # Per-category advisory bias correction — only where we have enough samples.
    by_cat: dict[str, list[float]] = {}
    for cat, e in errs:
        by_cat.setdefault(cat, []).append(e)
    print(f"per-category bias correction (>= {min_samples} realized samples):")
    shown = False
    for cat, es in sorted(by_cat.items()):
        if len(es) < min_samples:
            continue
        m = mean(es)
        if 1.0 + m <= 0:
            continue
        factor = 1.0 / (1.0 + m)
        print(f"  {cat:12s} factor {factor:.3f}  (n={len(es)}, mean err {m:+.1%})")
        shown = True
    if not shown:
        print("  (no category has enough samples yet — correction withheld on purpose)")
    print("\nThe bid/no-bid gate still uses the raw, conservative estimate; the\n"
          "bias factor is advisory only, and never trusted on thin data.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--calibrate", action="store_true",
                    help="score past predictions against realized prices instead")
    args = ap.parse_args()
    if args.calibrate:
        run_calibration()
    else:
        run_gate()


if __name__ == "__main__":
    main()

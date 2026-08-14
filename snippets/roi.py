"""Deterministic cost / ROI / tier math — an illustrative excerpt.

The economics of a bid are cheap to compute and change every time the bid moves,
while the resale *estimate* is expensive (a model call) and rare. Canvest keeps
them separate: a valuation is produced once, then this pure function recomputes
ROI and the tier on every read, so verdicts stay live as an auction moves without
spending anything.

This is a simplified, standalone version for review. The real system stores these
rates as configurable settings and layers an evidence gate on top (see
`docs/methodology.md`); the numbers below are illustrative example defaults, not
Canvest's tuned values.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostModel:
    """All-in cost + resale-fee assumptions. Illustrative defaults."""
    buyer_premium_rate: float = 0.22      # auction house premium on the hammer bid
    sales_tax_rate: float = 0.07          # applied to bid + premium
    resale_fee_rate: float = 0.15         # marketplace / consignment fees on resale
    shipping_by_size: dict[str, float] = None  # flat cost per size class

    def shipping(self, size_class: str) -> float:
        table = self.shipping_by_size or {"small": 55.0, "medium": 110.0, "large": 180.0}
        return table.get(size_class, table["medium"])


@dataclass(frozen=True)
class Thresholds:
    """ROI/confidence bands that map economics to a tier. Illustrative."""
    roi_strong_min: float = 0.40
    roi_medium_min: float = 0.20
    confidence_strong_min: float = 0.60
    max_bid_usd: float = 200.0


@dataclass
class RoiBreakdown:
    bid_usd: float
    total_cost_usd: float
    net_resale_usd: float
    profit_usd: float
    roi: float
    max_recommended_bid_usd: float
    tier: str
    reason: str


def all_in_cost(bid: float, cm: CostModel, size_class: str = "medium") -> float:
    """Landed cost of winning at `bid`: hammer + premium + tax + shipping."""
    premium = bid * cm.buyer_premium_rate
    tax = (bid + premium) * cm.sales_tax_rate
    return bid + premium + tax + cm.shipping(size_class)


def max_bid_for_roi(resale_mid: float, target_roi: float, cm: CostModel,
                    size_class: str = "medium") -> float:
    """Largest bid at which projected ROI still meets `target_roi`.

    Solved in closed form. We need net_resale - cost >= target_roi * cost, i.e.
    cost <= net_resale / (1 + target_roi). Cost is affine in the bid:
    cost = bid * (1 + premium) * (1 + tax) + shipping, so invert for the bid.
    """
    net_resale = resale_mid * (1.0 - cm.resale_fee_rate)
    per_bid = (1.0 + cm.buyer_premium_rate) * (1.0 + cm.sales_tax_rate)
    max_cost = net_resale / (1.0 + target_roi)
    bid = (max_cost - cm.shipping(size_class)) / per_bid
    return max(0.0, bid)


def compute_roi(bid: float, resale_mid: float, confidence: float,
                cm: CostModel, th: Thresholds, size_class: str = "medium") -> RoiBreakdown:
    """Pure economics → an ROI breakdown and a tier with a plain-English reason.

    NOTE: `tier` is intentionally *only* economics. The production system overlays
    a separate evidence gate (no 'bid' without a verified realized comp) to turn a
    tier into an actual recommendation — deliberately omitted here.
    """
    total_cost = all_in_cost(bid, cm, size_class)
    net_resale = resale_mid * (1.0 - cm.resale_fee_rate)
    profit = net_resale - total_cost
    roi = profit / total_cost if total_cost > 0 else 0.0
    pct = lambda x: f"{x * 100:.0f}%"

    if bid > th.max_bid_usd:
        tier, reason = "over_budget", f"bid ${bid:.0f} exceeds the ${th.max_bid_usd:.0f} ceiling"
    elif resale_mid <= 0:
        tier, reason = "watch", "no resale estimate yet"
    elif roi >= th.roi_strong_min and confidence >= th.confidence_strong_min:
        tier, reason = "strong", f"ROI {pct(roi)} and confidence {pct(confidence)} both clear the strong bar"
    elif roi >= th.roi_medium_min:
        tier = "medium"
        reason = (f"ROI {pct(roi)} clears medium; "
                  + ("confidence below the strong bar" if roi >= th.roi_strong_min
                     else "below the strong ROI bar"))
    elif roi > 0:
        tier, reason = "watch", f"ROI {pct(roi)} positive but below the medium bar"
    else:
        tier, reason = "skip", f"projected loss (ROI {pct(roi)})"

    return RoiBreakdown(
        bid_usd=round(bid, 2),
        total_cost_usd=round(total_cost, 2),
        net_resale_usd=round(net_resale, 2),
        profit_usd=round(profit, 2),
        roi=round(roi, 4),
        max_recommended_bid_usd=round(min(max_bid_for_roi(resale_mid, th.roi_medium_min, cm, size_class),
                                          th.max_bid_usd), 2),
        tier=tier,
        reason=reason,
    )


if __name__ == "__main__":
    cm, th = CostModel(), Thresholds()
    b = compute_roi(bid=130, resale_mid=560, confidence=0.78, cm=cm, th=th, size_class="small")
    print(f"bid ${b.bid_usd} -> all-in ${b.total_cost_usd}, net resale ${b.net_resale_usd}")
    print(f"profit ${b.profit_usd}  ROI {b.roi:.0%}  tier={b.tier}  ({b.reason})")
    print(f"max recommended bid: ${b.max_recommended_bid_usd}")

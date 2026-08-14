# Methodology

How Canvest turns "flip art for profit" into a disciplined, repeatable loop. This
page explains the *approach*; it deliberately keeps the tuned internals — the exact
rubric, prompts, and thresholds — private. The numbers below are **illustrative
example defaults** to make the mechanics concrete, not the platform's real operating
values (every one is configurable).

---

## The one question

For every lot, Canvest answers a single question, honestly and cheaply:

> **What are you buying, what will it cost you all-in, what will it resell for, and is
> it therefore worth bidding?**

Everything else is in service of answering that with *evidence* instead of taste.

---

## The loop, stage by stage

### 1 · Research
Establish where the market is and what actually resells in your band: which
categories, styles, and tiers are appreciating, and what moves fast on the secondary
market. The output is a written, versioned **thesis** with named target categories and
price bands, cited to real results.

### 2 · Rubric
Translate the thesis into a **versioned acquisition rubric** — a small set of scored
dimensions plus a few hard veto gates for things you never want. Because it's
versioned, the rubric evolves as research does; every scored item records which
version judged it.

### 3 · Source
A repeatable capture flow pulls promising listings into the platform. This is
**human-in-the-loop by design** — supervised capture, not bulk automated scraping —
which keeps the operation polite and low-risk.

### 4 · Triage — free, on everything
Every captured lot is scored by a **local vision model** running on your own hardware.
It costs nothing per item, so you can capture generously and let weak lots sink. Only
what clears the bar becomes a candidate for paid analysis.

### 5 · Deep valuation — metered, on the shortlist
For lots worth a closer look, a **cloud model with web search** produces a
schema-strict valuation: a predicted resale range, recommended listing prices,
confidence, key positives and risks, and a set of **comparable sales** — each tagged
as a *realized* sale or a mere asking price, and each citing a source. This is the only
routine paid step, so it runs on the shortlist, never the firehose.

### 6 · The evidence gate — the heart of the method
A strong ROI *on paper* means nothing if the resale figure rests on no real sold
comparable. So Canvest separates two things:

- **Tier** is pure economics — the ROI math alone (see the cost model below).
- **The verdict** overlays a hard gate: a **BID** is only recommended when the
  valuation cites at least one *verified, realized* sold comp at or above a floor.
  Otherwise the verdict is **NO-BID**, no matter how good the paper ROI.

| Verdict | Meaning |
|---|---|
| **BID** | Biddable economics **and** a verified realized comp clears the floor. |
| **NO-BID** | Good ROI on paper, but no qualifying realized comp — pass. |
| **WATCH** | Positive but sub-target, or not yet valued. |
| **SKIP** | Projected loss, or over budget. |

A **ship-risk** flag is raised separately for oversized freight or fragile
framed-under-glass pieces, so fragile or expensive-to-move lots get a human second look.

### 7 · Track
ROI never costs anything to refresh: it's recomputed deterministically on every read
from the stored valuation and the current bid, so verdicts stay live as auctions move.
A per-lot chart shows the bid over time against the resale estimate and the max bid.

### 8 · Outcome
Record what happened — won, lost, or resold, with the price. Resale prices are the
gold-standard signal that makes the loop *learn*.

### 9 · Calibrate
Compare each prediction to what the item actually realized, grouped by category and
confidence. A **prediction success rate** (how often estimates land within a tolerance
of the real price) is the single number that should trend up. Where estimates are
consistently off, an advisory per-category correction can nudge future numbers — but
the bid/no-bid gate always uses the raw, conservative estimate.

---

## The cost model (illustrative)

The deterministic ROI uses an all-in cost model. Example defaults — **not** the real
tuned values:

```
all-in cost = bid
            + buyer premium   (e.g. ~22% of bid)
            + sales tax        (e.g. ~7%)
            + shipping         (a flat amount by size class)

net resale  = predicted resale − marketplace/resale fees (e.g. ~15%)

profit      = net resale − all-in cost
ROI         = profit ÷ all-in cost
```

From ROI, a lot is tiered (e.g. *strong / medium / watch / skip*) and a **max
recommended bid** is derived — the highest bid at which the ROI still clears the target.

An illustrative **evidence floor** (e.g. "a verified realized comp of at least a few
hundred dollars") reflects a simple truth: at a low bid ceiling, a lot only pencils out
where comparable pieces have genuinely resold well. Below that, the honest answer is
*don't bid* — and Canvest says so.

> The specific dimensions, veto gates, floors, rates, and prompt design are the tuned,
> proprietary part of Canvest and are not published here.

---

## Why this compounds

- The **comp library** grows from your own closed auctions, your resales, and periodic
  harvests — the larger the pool, the better-grounded every future valuation.
- **Calibration** measures where estimates run high or low and closes the gap over time.
- **Research → rubric** is revisited each cycle, so what you buy tracks where the money
  actually is.

Any single flip can go either way. The *loop* is the edge.

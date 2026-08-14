# Runnable example — the evidence gate

A **self-contained, runnable** illustration of the discipline at the heart of
Canvest: turning an expensive, model-produced resale *estimate* into a
trustworthy **bid / no-bid** decision — and being honest about how good those
estimates actually are.

It is **not** the product source. It is a single standard-library Python file
with no dependencies, no network, and no model required.

## Run it

```bash
python gate_demo.py              # run synthetic lots through the evidence gate
python gate_demo.py --calibrate  # score past predictions against realized prices
```

(On Windows, use the `py -3` launcher.)

## What it demonstrates

The same path the real system uses:

```
valuation (a model proposes)  ->  deterministic ROI economics
                              ->  the EVIDENCE GATE (code disposes)
                              ->  BID / NO-BID / WATCH / SKIP
```

- **Economics are only economics.** ROI is a pure, deterministic function of the
  live bid and the resale estimate — cheap to recompute on every read, so verdicts
  stay live as an auction moves without spending anything.
- **The model proposes, the gate disposes.** A biddable ROI is *necessary but not
  sufficient*. A bid is allowed only when a **verified, realized** comparable sale
  backs the resale number. A great number resting on an *asking* price, a comp far
  below the estimate, or no comp at all becomes **NO-BID** — not a buy.
- **The refusal is the product.** In the sample run, a lot with ~156% paper ROI is
  returned as NO-BID because its best comp sits below the evidence floor. That
  refusal is exactly what stops an optimistic estimate from becoming a losing
  purchase.

Sample verdicts:

```
verdict   ROI    best comp            lot
------------------------------------------------------------------------
BID        135%  $560 realized       Signed serigraph, framed
NO-BID     156%  $150 realized       Attractive lithograph, no track record   <- the point
NO-BID      61%  none                Estate screenprint, unbacked
NO-BID     104%  $700 asking         Gallery etching, asking-price only
WATCH       19%  $240 realized       Mid-tier etching
SKIP       184%  $1450 realized      Blue-chip lot, out of band
SKIP       -71%  none                Overbid decorative piece
```

## The calibration pass

`--calibrate` answers the question a research-minded operator actually cares
about: **do the resale predictions track what pieces realized, and does that
tracking improve as data accumulates?** It reports a success rate (share of
predictions within a tolerance of the real price), mean signed and absolute error,
and a **per-category bias correction that is only trusted once a category has
enough realized samples** — the whole point being to *not* learn from noise.

```
prediction success rate (within +/-20%): 90%  (9/10)
mean absolute error : 9.8%
mean signed error   : -0.6%   (overall bias)

per-category bias correction (>= 5 realized samples):
  Serigraph    factor 0.945  (n=6, mean err +5.8%)
```

The numbers are on **synthetic** data — they illustrate the *method*, not a track
record. And the biggest lever on quality is the coverage of the realized-comp
library and the rubric behind it: a thin or overstated rubric will *flatter* these
figures, so that input is the first thing to interrogate, not the last.

*For review only; not licensed for reuse. See the repository [LICENSE](../../LICENSE).*

# Illustrative excerpts

These are **short, simplified excerpts** written for review — not the production Canvest
engine. Each is a `simplified excerpt, for review only`, and each demonstrates coding
style and the quantitative reasoning behind one part of the system:

- **[`roi.py`](roi.py)** — the deterministic, unit-testable cost / ROI / tier math that
  runs on every read (no model calls). Standard arithmetic; the *interesting* part is
  that valuations are expensive and rare while ROI is cheap and live, so the two are
  cleanly separated, and the max-recommended-bid is solved for in closed form.
- **[`rubric.py`](rubric.py)** — the **shape** of the Stage-A acquisition rubric: six
  scored dimensions plus three hard veto gates, with the aggregation kept pure and
  deterministic (a veto is absolute — it zeroes the score). The rubric is *data, not
  code*: a versioned record research can amend without a deploy.
- **[`deep_pass.py`](deep_pass.py)** — the Stage-B **schema-strict valuation contract**:
  the closed JSON shape the cloud model must fill (`record_valuation`) and the
  parse-then-validate seam that runs before a valuation may influence anything. Comps
  are tagged *realized* vs *asking*; only realized, sourced sales survive validation.
- **[`calibration.py`](calibration.py)** — the validation layer: predicted-vs-realized
  error, a success rate within tolerance, and a per-category bias correction derived only
  once a category has enough realized samples.

## What is *not* here

The tuned, proprietary parts of Canvest are deliberately withheld:

- the **real rubric** dimension criteria and veto triggers (here they are generic
  placeholders — `<redacted>`);
- the **valuation system prompt** and sourcing guidance (redacted in `deep_pass.py`);
- the **evidence-gate floors**, and the **real cost-model rates** (the numbers shown are
  illustrative example defaults, not Canvest's tuned values).

Each file runs standalone and prints a tiny worked example:

```bash
python roi.py
python rubric.py
python deep_pass.py
python calibration.py
```

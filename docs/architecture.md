# Architecture

A high-level tour of how Canvest is built. This describes the *shape* of the system,
not its internals — the scoring engine, prompts, and tuned parameters are private.

<div align="center"><img src="../assets/architecture.svg" alt="Architecture" width="820"></div>

---

## Two processes, one database

Canvest runs as a compact, **self-hosted** stack:

- **API + web app** — serves a REST API and a fast, no-build single-page web app. It
  handles capture, records decisions, and recomputes ROI on every read. When something
  needs paid or slow work, it enqueues a background job rather than blocking.
- **Worker** — a single polling loop that claims queued jobs and runs them: local
  triage, deep valuation, price refreshes, end-of-auction capture, research, comp
  harvests, and calibration/backtests.
- **Database** — holds items, price snapshots, triage and valuation results, decisions,
  the versioned rubric and theses, the comp library, and an attributed audit log.

There's no heavyweight scheduler or message broker; the worker's own timer is the only
clock. The whole thing is designed to run quietly on a single machine and be reached
privately by a small team.

## Hybrid analysis — the key design choice

The most important architectural decision is splitting analysis into two tiers:

| | Local triage | Cloud deep valuation |
|---|---|---|
| **Runs on** | every captured lot | the shortlist only |
| **Where** | a vision model on your own GPU | a metered cloud model + web search |
| **Cost** | free | pay-per-lot |
| **Job** | fast aesthetic/category score against the rubric | resale range, listing prices, confidence, cited realized comps |

This keeps spend **proportional to signal**: you can capture generously because triage
is free, and you only pay for depth on lots that already look worth it.

## Deterministic ROI on read

ROI, tier, and max-recommended-bid are **pure functions** of the stored valuation and
the current bid. They're recomputed every time a page loads, so:

- verdicts always reflect the *current* bid without re-running any model, and
- refreshing costs nothing — the expensive step (the valuation) happened once.

The cost-model rates and thresholds are configurable settings, not hard-coded.

## The learning components

- **Comp library** — a growing table of *realized* sold prices, fed by auctions you
  watched that closed, your own resales, and periodic harvests. Relevant comps are
  retrieved and injected into each valuation so the model reasons from your accumulated
  evidence, not just a fresh web search.
- **Calibration** — derived on read: for every lot that was both valued and later
  realized a price, it compares predicted vs. actual, grouped by category and
  confidence, and reports a success rate.
- **Backtest** — replays the bid/no-bid recommendation over realized outcomes to
  measure whether the engine actually makes money.

## Data model posture

The schema is **additive** — new capabilities add tables rather than rewriting history,
so past valuations and outcomes are never mutated after the fact. Every mutating action
is attributed to a user in an audit log.

## Tech stack

- **Backend:** Python, FastAPI
- **Database:** PostgreSQL (with a vector extension for future similarity search);
  SQLite in local/dev mode
- **Frontend:** a dependency-free, no-build vanilla-JS single-page app
- **Local model:** a self-hosted vision model for free triage
- **Cloud model:** a hosted LLM with web search for deep valuation
- **Packaging:** containerized for single-host self-hosting

## Security & operating posture

- **Human-in-the-loop capture**, no high-frequency scraping.
- **Private by default** — self-hosted and reached over a private network, not exposed
  publicly.
- **Token auth** with a full audit trail of who did what.

> What's intentionally *not* here: the rubric dimensions and veto gates, the valuation
> prompts and schemas, the evidence-gate floors and cost-model rates, and the sourcing
> specifics. Those are the tuned core of the product.

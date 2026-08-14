"""Stage-B deep valuation — the schema-strict contract, as an illustrative excerpt.

The one metered step in Canvest asks a cloud model (with web search) to value a
lot. The engineering that makes that output *safe to act on with money* is not the
prompt — it's the **closed schema** the model must fill and the **validation** that
runs before the result is allowed to influence anything.

The model fills exactly one tool call, `record_valuation`, whose input schema is a
single fixed JSON shape:

    predicted_resale        low / mid / high USD
    recommended_listing     price per sales channel + a short rationale
    confidence              0-1 (low when no realized comps were found)
    key_positives / risks   short strings
    comparable_sales[]      each: description, price, source_url, and a
                            REALIZED-vs-ASKING flag — only realized sales may
                            ever back a bid
    reasoning_summary       free text, for the human, not for the math

`additionalProperties: false` everywhere means the model cannot smuggle in extra
keys; `required` means it cannot omit the ones the downstream math depends on. The
model *proposes*; deterministic code and the evidence gate *dispose*.

REDACTION: the system prompt (the tuned analyst instructions and the sourcing
guidance) and the live model/tool wiring are the proprietary core and are omitted.
What remains is the contract and the validation — the part worth reviewing.

For review only; not the production engine. See ../LICENSE.
"""
from __future__ import annotations

import json

# --------------------------------------------------------------------------- #
# The closed output schema the model must fill (a strict tool-use contract).
# --------------------------------------------------------------------------- #

VALUATION_TOOL = {
    "name": "record_valuation",
    "description": "Record the structured valuation for the artwork. Call exactly once.",
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "predicted_resale": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "low_usd":  {"type": "number"},
                    "mid_usd":  {"type": "number"},
                    "high_usd": {"type": "number"},
                },
                "required": ["low_usd", "mid_usd", "high_usd"],
            },
            "recommended_listing_price": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "primary_market_usd":   {"type": "number"},
                    "secondary_market_usd": {"type": "number"},
                    "auction_reserve_usd":  {"type": "number"},
                    "rationale_short":      {"type": "string"},
                },
                "required": ["primary_market_usd", "secondary_market_usd",
                             "auction_reserve_usd", "rationale_short"],
            },
            "confidence": {"type": "number",
                           "description": "0-1; below 0.3 if no realized comps found"},
            "artist_identified": {"type": "string"},
            "key_positives": {"type": "array", "items": {"type": "string"}},
            "key_risks":     {"type": "array", "items": {"type": "string"}},
            "comparable_sales": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "description": {"type": "string"},
                        "sold_usd":    {"type": "number"},
                        "sold_date":   {"type": "string"},
                        "source_url":  {"type": "string"},
                        "is_realized_sale": {
                            "type": "boolean",
                            "description": (
                                "true = an actual completed hammer/sold/final price; "
                                "false = an asking / active-listing price. Only "
                                "realized sales count toward the bid decision."),
                        },
                    },
                    # A comp with no price, no source, or no realized/asking flag
                    # is not evidence — so those fields are required.
                    "required": ["description", "sold_usd", "source_url",
                                 "is_realized_sale"],
                },
            },
            "reasoning_summary": {"type": "string"},
        },
        "required": [
            "predicted_resale", "recommended_listing_price", "confidence",
            "key_positives", "key_risks", "comparable_sales", "reasoning_summary",
        ],
    },
}

# The system prompt — the tuned analyst instructions, the conservative-valuation
# rules, and the realized-comp sourcing guidance — is the proprietary core and is
# intentionally NOT included in this public excerpt.
SYSTEM = "<tuned valuation system prompt — redacted>"


class ValuationError(ValueError):
    """Raised when a model response fails the contract. Carries the payload so a
    bad response is diagnosable (and the pass can be safely re-run)."""


def extract_valuation(response_blocks: list) -> dict:
    """Pull the single `record_valuation` tool call out of a model response.

    Even with a strict schema, a model can decline to call the tool, or call the
    wrong one. Fail loudly with what it *did* return rather than limping on with a
    missing valuation.
    """
    for block in response_blocks:
        if getattr(block, "type", None) == "tool_use" and block.name == "record_valuation":
            return block.input
    kinds = [getattr(b, "type", "?") for b in response_blocks]
    raise ValuationError(f"model did not call record_valuation (got: {kinds})")


def validate(valuation: dict) -> dict:
    """Defensive validation *before* the valuation is allowed to influence anything.

    The tool schema should guarantee these shapes, but a model can still emit a
    malformed input (e.g. `predicted_resale` as a JSON *string*). This is the
    parse-then-validate seam the whole system leans on: a valuation that fails
    here never reaches the ROI math or the evidence gate.
    """
    pr = valuation.get("predicted_resale")
    if not isinstance(pr, dict) or "mid_usd" not in pr:
        raise ValuationError("predicted_resale malformed: " + json.dumps(valuation)[:400])
    for k in ("low_usd", "mid_usd", "high_usd"):
        v = pr.get(k)
        if not isinstance(v, (int, float)) or v < 0:
            raise ValuationError(f"predicted_resale.{k} not a non-negative number: {v!r}")
    if not (pr["low_usd"] <= pr["mid_usd"] <= pr["high_usd"]):
        raise ValuationError(f"resale range not ordered low<=mid<=high: {pr}")

    conf = valuation.get("confidence")
    if not isinstance(conf, (int, float)) or not 0.0 <= conf <= 1.0:
        raise ValuationError(f"confidence out of [0,1]: {conf!r}")

    # Every comp must actually be evidence: priced, sourced, and flagged. Anything
    # else is dropped rather than trusted — an asking price is not a sold price.
    clean_comps = []
    for c in valuation.get("comparable_sales", []):
        if (isinstance(c.get("sold_usd"), (int, float)) and c["sold_usd"] > 0
                and str(c.get("source_url") or "").strip()
                and isinstance(c.get("is_realized_sale"), bool)):
            clean_comps.append(c)
    valuation["comparable_sales"] = clean_comps
    return valuation


def parse_response(response_blocks: list) -> dict:
    """The full seam: extract the tool call, then validate it. Only a value that
    survives both is handed on to the deterministic ROI + evidence-gate layer."""
    return validate(extract_valuation(response_blocks))


if __name__ == "__main__":
    # A stand-in for a model tool-call block, to show the validation seam.
    class _Block:
        type = "tool_use"
        name = "record_valuation"
        input = {
            "predicted_resale": {"low_usd": 400, "mid_usd": 560, "high_usd": 720},
            "recommended_listing_price": {"primary_market_usd": 700,
                                          "secondary_market_usd": 560,
                                          "auction_reserve_usd": 300,
                                          "rationale_short": "framed, décor buyer"},
            "confidence": 0.72,
            "key_positives": ["signed", "period frame"],
            "key_risks": ["glass — ship risk"],
            "comparable_sales": [
                {"description": "similar serigraph", "sold_usd": 560,
                 "source_url": "https://example-archive/lot/123", "is_realized_sale": True},
                {"description": "asking only", "sold_usd": 900,
                 "source_url": "", "is_realized_sale": False},  # dropped: no source
            ],
            "reasoning_summary": "one realized comp supports ~$560 framed resale",
        }
    v = parse_response([_Block()])
    print("valid. resale mid $%(mid_usd)s, confidence" % v["predicted_resale"],
          v["confidence"])
    print("comps kept (evidence-grade only):", len(v["comparable_sales"]))

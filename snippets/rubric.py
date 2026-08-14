"""The acquisition rubric — its *shape*, as an illustrative excerpt.

Stage-A triage scores every captured lot against a small, versioned rubric: a
handful of numeric dimensions plus a few hard veto gates. The scoring itself is
pure and deterministic — a language/vision model supplies the raw per-dimension
scores, but the aggregate score and the veto logic are ordinary code, so they are
testable and never "argue back."

What makes this worth showing is the *structure*, not the wording:

  * the rubric is **data, not code** — in the real system it lives in the database
    as a versioned record, so research can amend it without a deploy, and every
    scored item stores which rubric version judged it;
  * a **veto** is absolute: any tripped gate zeroes the score regardless of how
    high the dimensions are, because some traits are disqualifying, not just
    negative;
  * the functions take *whatever* spec is passed in, so a new rubric version is a
    new row, not a new build.

REDACTION: the dimension descriptions and veto definitions below are deliberately
**generic placeholders**. The real, tuned rubric — the specific aesthetic thesis
that decides what actually resells — is the proprietary core and is not published
here. This file demonstrates the mechanism the tuned values plug into.
"""
from __future__ import annotations

# --- The seed spec (version 1). In production this is a row in the DB, amended by
# --- research over time; the constants here are only an illustrative default. ---

DEFAULT_RUBRIC_VERSION = 1

# Six scored dimensions, integer 1-5. The *keys* are the real shape; the
# descriptions are placeholders standing in for the tuned aesthetic thesis.
DEFAULT_DIMENSIONS: dict[str, str] = {
    "dimension_1": "<tuned criterion — redacted>  (5 = strong fit … 1 = poor fit)",
    "dimension_2": "<tuned criterion — redacted>  (5 = strong fit … 1 = poor fit)",
    "dimension_3": "<tuned criterion — redacted>  (5 = strong fit … 1 = poor fit)",
    "dimension_4": "<tuned criterion — redacted>  (5 = strong fit … 1 = poor fit)",
    "dimension_5": "<tuned criterion — redacted>  (5 = strong fit … 1 = poor fit)",
    "medium_fit":  "how well the work's medium matches the target inventory",
}

# Three hard veto gates (booleans). Any one true → the item is rejected outright,
# no matter how the dimensions scored. Names are structural; the exact triggers
# are part of the tuned core and are redacted.
DEFAULT_VETO_GATES: dict[str, str] = {
    "veto_gate_1": "<disqualifying trait — redacted>",
    "veto_gate_2": "<disqualifying trait — redacted>",
    "veto_gate_3": "<disqualifying trait — redacted>",
}


def triage_prompt(dimensions: dict, veto_gates: dict, item_title: str,
                  item_description: str, artist: str) -> str:
    """Render the rubric spec into a scoring prompt.

    The prompt is built *from the spec* so a new rubric version needs no code
    change. It asks the model for one JSON object — integer scores for every
    dimension, a boolean for every veto gate, plus a short category and an artist
    guess — and nothing else. (The exact tuned wording is not shown here.)
    """
    dims = "\n".join(f'- "{k}": {v}' for k, v in dimensions.items())
    gates = "\n".join(f'- "{k}": true if {v}' for k, v in veto_gates.items())
    return (
        "Score this auction lot against a fixed acquisition rubric.\n"
        f"Title: {item_title}\nArtist: {artist or 'unknown'}\n"
        f"Description: {item_description[:2000]}\n\n"
        f"Score each dimension 1-5:\n{dims}\n\n"
        f"Veto gates (booleans):\n{gates}\n\n"
        "Respond with ONLY a JSON object: "
        '{"scores": {...}, "vetoes": {...}, "category": "...", "artist_guess": "..."}'
    )


def aesthetic_score(dimensions: dict, veto_gates: dict,
                    scores: dict, vetoes: dict) -> float:
    """Aggregate a rubric result into a single 0-5 score.

    Deterministic and pure:
      * average the scored dimensions, then
      * if ANY veto gate is tripped, the score is 0.0 — a veto is absolute, it
        does not merely subtract.

    Keeping this out of the model means the disqualifying logic is auditable and
    identical for every item, instead of re-decided in prose each time.
    """
    if not dimensions:
        return 0.0
    if any(bool(vetoes.get(k)) for k in veto_gates):
        return 0.0
    vals = [float(scores.get(k, 0) or 0) for k in dimensions]
    return round(sum(vals) / len(dimensions), 2)


# A deterministic guard also runs after scoring to *clear* known model
# false-positives (e.g. a class of item the vision model reliably mislabels).
# It only ever CLEARS a veto, never adds one, so it can loosen a rejection but
# never invent one. The specifics are part of the tuned core and omitted here.


if __name__ == "__main__":
    dims, gates = DEFAULT_DIMENSIONS, DEFAULT_VETO_GATES
    # A model would return these; here they are hand-set to show the mechanics.
    good = {"scores": {k: 4 for k in dims}, "vetoes": {k: False for k in gates}}
    vetoed = {"scores": {k: 5 for k in dims}, "vetoes": {**{k: False for k in gates},
                                                         "veto_gate_1": True}}
    print("clean item  score:", aesthetic_score(dims, gates, good["scores"], good["vetoes"]))
    print("vetoed item score:", aesthetic_score(dims, gates, vetoed["scores"], vetoed["vetoes"]),
          "(a single veto zeroes an otherwise-perfect item)")

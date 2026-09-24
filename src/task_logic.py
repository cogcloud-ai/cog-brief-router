"""Brief Router task logic — the only file in src/ this Cog owns.

A System One model answers five narrow questions about one missing-Cog brief
(context/questions.json). This code turns those answers into a recommendation
— code, context or decision Cog — and states, as flags and reasons, every
place where a person should look before the builder acts on it.

Policy lives here, not in the questions:
- the recommendation is the `implementation` choice, unless its confidence is
  below MIN_CONFIDENCE, in which case it is `needs-review`;
- the three Noul signals must not contradict the chosen kind;
- an underspecified brief is flagged whatever the recommendation;
- a designer who proposed `context` for work that is a bounded typed decision
  is told about the decision class (a decision Cog is a context Cog).
"""

MIN_CONFIDENCE = 0.5
STRONG = 0.7          # a Noul at or above this is a clear yes
WEAK = 0.3            # at or below this, a clear no
CLEAR_SPEC = 1.0      # specification_clarity score below this is underspecified


def check_input(bundle):
    import cog_core
    problems = []
    brief = bundle.get("brief") or {}
    if not str(brief.get("brief", "")).strip():
        problems.append(cog_core.problem("input", "brief.brief must contain text"))
    return problems


def state(bundle):
    """Only what the questions need: the name, the brief and its prohibitions.
    Step ids and the designer's kind are withheld so they cannot anchor the
    model; the designer's kind is compared afterwards, in code."""
    brief = bundle["brief"]
    return {"name": brief["name"], "brief": brief["brief"], "prohibits": brief.get("prohibits", [])}


def questions(bundle, declared):
    return declared


def _contradictions(kind, answers):
    open_ended = answers["open_ended_output"]["noul"]
    bounded = answers["bounded_answer_space"]["noul"]
    rules = answers["rules_suffice"]["noul"]
    found = []
    if kind == "code" and rules <= WEAK:
        found.append(f"code recommended but rules_suffice is {rules:.2f}")
    if kind == "decision" and open_ended >= STRONG:
        found.append(f"decision recommended but open_ended_output is {open_ended:.2f}")
    if kind == "decision" and bounded <= WEAK:
        found.append(f"decision recommended but bounded_answer_space is {bounded:.2f}")
    if kind == "context" and bounded >= STRONG and open_ended <= WEAK:
        found.append(f"context recommended but the answer space looks bounded "
                     f"({bounded:.2f}) and not open-ended ({open_ended:.2f})")
    return found


def decide(bundle, answers):
    brief = bundle["brief"]
    implementation = answers["implementation"]
    kind, confidence = implementation["choice"], implementation["confidence"]
    flags, reasons = [], [f"implementation: {kind} (confidence {confidence:.2f})"]

    recommendation = kind
    if confidence < MIN_CONFIDENCE:
        recommendation = "needs-review"
        flags.append("low-confidence")
        reasons.append(f"confidence is below {MIN_CONFIDENCE}")
    contradictions = _contradictions(kind, answers)
    if contradictions:
        recommendation = "needs-review"
        flags.append("signals-disagree")
        reasons.extend(contradictions)
    clarity = answers["specification_clarity"]["score"]
    if clarity < CLEAR_SPEC:
        flags.append("underspecified-brief")
        reasons.append(f"specification_clarity is {clarity:.2f}; name inputs, outputs and success criteria")

    designer = brief.get("cog_kind")
    agrees = None
    if designer is not None and recommendation != "needs-review":
        # The designer's vocabulary is kind: context or code. A decision Cog
        # is a context Cog, so `context` agrees with a decision recommendation.
        agrees = designer == recommendation or (designer == "context" and recommendation == "decision")
        if designer == "context" and recommendation == "decision":
            flags.append("consider-decision-class")
            reasons.append("designer proposed context; a decision Cog is a context Cog in the decision class")
        elif not agrees:
            reasons.append(f"designer proposed {designer}")
    return {"brief_id": brief["id"], "name": brief["name"], "recommendation": recommendation,
            "confidence": confidence, "designer_kind": designer, "agrees_with_designer": agrees,
            "flags": flags, "reasons": reasons}


def check_output(payload, bundle):
    import cog_core
    problems = []
    decision = payload["decision"]
    if decision["brief_id"] != bundle["brief"]["id"]:
        problems.append(cog_core.problem("consistency", "decision names a different brief"))
    if decision["recommendation"] == "needs-review" and not decision["flags"]:
        problems.append(cog_core.problem("consistency", "needs-review requires a flag saying why"))
    return problems

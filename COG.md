---
type: cog [0.1]
name: cog-brief-router
description: "Decision Cog. Recommends whether a missing-Cog brief should be built as a code, context or decision Cog, with calibrated confidence and review flags. A System One model answers its typed questions; its code makes the decision."
version: "0.1.0"
license: Apache-2.0
publisher: OpenTeams
manifest: cog.yaml
manifest_schema: openteams/cog-manifest [0.1]
---

# Brief Router

## Purpose

When cog-op-designer proposes an Op, it describes each missing Cog in a brief.
Before a Cog is authored, someone must decide what kind of Cog it is: a
**code** Cog (explicit rules), a **context** Cog (a model composes open-ended
output) or a **decision** Cog (a System One model answers bounded, typed
questions and code decides). This Cog makes that recommendation for one brief,
with a calibrated confidence, and says plainly when a person should look.

It is the suite's example decision Cog, created with
`smith new --class decision` from a request file.

## Supported work

A System One model answers five questions about the brief:

| Question | Type | Asks |
|---|---|---|
| `implementation` | choice: code / context / decision | which kind fits |
| `open_ended_output` | noul | must it compose free text or new content? |
| `bounded_answer_space` | noul | is every output a known label, yes/no or rating? |
| `rules_suffice` | noul | could explicit rules produce the right output? |
| `specification_clarity` | score: vague / partial / clear | how complete is the brief? |

`decide` recommends the `implementation` choice, unless:

- its confidence is below 0.5 → `needs-review` (`low-confidence`);
- a Noul contradicts the chosen kind (code without rules, a decision with
  open-ended output or no bounded answer space, context for a clearly bounded
  answer space) → `needs-review` (`signals-disagree`).

An underspecified brief (clarity score below 1.0) is flagged but keeps its
recommendation. The designer's proposed `cog_kind` is withheld from the model
and compared afterwards; since a decision Cog is a context Cog, a designer's
`context` agrees with a `decision` recommendation and is flagged
`consider-decision-class`.

## Unsupported work

It does not author, build or accept a Cog, rewrite the brief, or judge whether
the Cog is worth building. The recommendation is advice to the builder
workflow; its Gates and a person decide. It sends only the brief's name, text
and prohibitions to the admitted provider — never step ids or the designer's
kind.

## Who answers

`system-one/decisions`, admitted by a host: cog-typesafe (Jev,
`answer_source: system-one-model`, cloud) or cog-system-one-adapter (an
admitted LLM such as local Qwen, `answer_source: llm-adapter`). The thresholds
above were chosen for Jev's calibrated confidence; treat adapter answers as
weaker evidence.

## Using it

```bash
pixi install
pixi run check
pixi run prepare -- --bundle examples/sample-bundle.json
pixi run replay -- --bundle examples/sample-bundle.json --result examples/sample-result.json
pixi run test
```

Live: admit a System One binding in Workbench, then from cog-workbench run
`pixi run suite -- activate-composition --context cog-brief-router --binding-id ID --revision N`,
and here `pixi run ask-composed -- --request bundle.json`.

`examples/sample-result.json` is an illustrative fixture (model
`illustrative-fixture`), not a recorded model response; the tests use it to
exercise the decision policy.

## Where the machinery came from

`src/cog_core.py`, `src/cog_cli.py` and `src/system_one_contract.py` are
cog-smith decision-cog machinery 0.1.1, verified by `smith check`;
`scripts/composed_usage.py` is Workbench's canonical adapter. This Cog's
identity is `cog.yaml`, `context/` and `src/task_logic.py`.

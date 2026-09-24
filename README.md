# cog-brief-router

The builder suite's example **decision Cog**: it recommends whether a
missing-Cog brief should be built as a code, context or decision Cog. A System
One model (TypeSafe's Jev, or an LLM through the System One adapter) answers
five typed questions about the brief; `src/task_logic.py` turns the answers
into a recommendation with explicit review flags.

See [COG.md](COG.md) for the contract and policy.

```sh
pixi install
pixi run test      # model-free
pixi run check
```

Created with `smith new --class decision --from-request`; see cog-smith's
BUILDING_COGS.md §7c for the decision class.

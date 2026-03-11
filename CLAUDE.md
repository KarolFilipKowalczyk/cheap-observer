# CLAUDE.md

You are working on **cheap-observer**, a research project that asks:
in the space of simple computational rules, do observer-like structures
emerge at lower complexity thresholds than physics-like regularities?

## The claim

**Sparks produce observers before they produce ruliads.**

Three concepts:

- **Spark** — a rule and its minimal seed
- **Observer** — a bounded self-referential structure with an inside
- **Ruliad** — globally coherent dynamics; what we call physics

We measure T_obs (when an observer appears) and T_rul (when ruliad-like
coherence appears) across rule classes, and claim T_obs < T_rul for the
vast majority of rules.

## Project anchor

Every decision — which code to write, which experiment to run, which
tangent to pursue — must pass one test:

**Does this help us compare T_obs against T_rul?**

If yes, do it. If no, note it in `theory/open_problems.md` and move on.

## Architecture

```
THE ARGUMENT:  claim.md → falsification.md → definitions.md → theory/
THE EVIDENCE:  experiments/{rule_class}/ → experiments/counterexamples/
THE MACHINERY: src/spark/ src/observer/ src/ruliad/
THE CONTEXT:   paper/ docs/ notebooks/
```

The argument comes first. The code serves the argument, not the other
way around.

`src/` contains three general modules that work on any rule class:
- `src/spark/` — rule enumeration, seed search
- `src/observer/` — observer detection using four criteria
- `src/ruliad/` — physics-likeness benchmarks

The Game of Intelligence engine lives in
`experiments/directed_graph/engine/`. It is a specific rule class
instance, not part of the general framework.

## Observer definition

An observer is a connected subgraph of the evolution graph satisfying
four criteria in conjunction:

1. **Boundary stability** — the interface with the exterior changes
   slowly relative to internal rewrites
2. **Internal entropy** — the interior undergoes non-trivial state
   transitions
3. **Causal decoupling** — mutual information between interior and
   exterior is bounded relative to internal mutual information
4. **Self-reference** — at least one internal cycle exists (a rewrite
   path from a node back to itself through internal edges)

The logical structure, partial ordering, and any dependency between
these criteria is specified in `src/observer/definition.py`. That file
is the formal contract. All detection code must conform to it.

## Falsification

The hypothesis is refuted if:
- A natural rule class exists where T_rul < T_obs for the majority
  of rules
- The observer criteria are so loose that random noise satisfies them
- Tightening criteria to exclude trivial cases collapses the
  prevalence gap

Counterexamples are first-class citizens. They live in
`experiments/counterexamples/` with a taxonomy and notes on what
they teach us about the definitions.

## Relation to Wolfram

We use: the ruliad concept, Observer Theory's characterization of
observers as bounded subsystems exploiting pockets of computational
reducibility, the enumeration methodology from NKS, and the criteria
for causal invariance from the Physics Project.

We fork: by reversing the generative arrow (observers before physics),
by foregrounding self-reference as constitutive (not incidental), and
by measuring the generic product of simple rules rather than searching
for our specific physics.

## What this project is not

- Not a consciousness project. We never define or measure consciousness.
- Not a simulation hypothesis paper. We never argue we live in a
  simulation.
- Not a critique of Wolfram. We extend his framework with a question
  he hasn't prioritized.

## Style

- Definitions before code. Always.
- One concept, one name. Spark. Observer. Ruliad. Don't introduce
  synonyms.
- Plain language in documentation. Formalism in `definitions.md` and
  `theory/`. Don't mix.
- Counterexamples are as valuable as positive results. Never hide them.
- If you're unsure whether a change serves T_obs vs T_rul comparison,
  ask before implementing.

## Key files to read first

1. `motivation.md` — why this project exists
2. `claim.md` — the hypothesis in plain language
3. `falsification.md` — what would refute us
4. `definitions.md` — the mathematics
5. `src/observer/definition.py` — the formal contract for detection

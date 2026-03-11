# cheap-observer

**Sparks produce observers before they produce ruliads.**

In the space of simple computational rules, bounded self-referential
structures — things with an inside — emerge at lower complexity
thresholds than globally coherent dynamics — things that look like
physics. Observers are cheaper than universes.

This repository contains:

- **The claim** — [`claim.md`](claim.md)
- **The falsification criteria** — [`falsification.md`](falsification.md) — what would refute us
- **The definitions** — [`definitions.md`](definitions.md)
- **The theory** — [`theory/`](theory/) — structural arguments and proofs
- **The evidence** — [`experiments/`](experiments/) — prevalence data across rule classes
- **The weaknesses** — [`experiments/counterexamples/`](experiments/counterexamples/)
- **The code** — [`src/`](src/)

```bash
# See an observer emerge from a spark
python src/spark/enumerate.py --class string --count 1 --evolve 500 | \
python src/observer/detect.py --visualize

# Run the prevalence experiment for string rewriting rules
python experiments/string_rewriting/sweep.py --config experiments/string_rewriting/config.yaml

# Compare observer vs ruliad thresholds across all rule classes
python experiments/comparison/aggregate.py --plot
```

## Three concepts

**Spark.** A rule and its minimal seed. The cheapest possible starting
condition. Almost nothing — but enough.

**Observer.** A bounded region of the evolution whose interior rewrites
refer back to themselves. It has an inside. It persists. It is partially
decoupled from the outside. Formal criteria: boundary stability, internal
entropy, causal decoupling, self-reference. See
[`definitions.md`](definitions.md) for the logical structure.

**Ruliad.** The regime where the rule's evolution exhibits global
coherence — causal invariance, effective dimensionality, agreement
between observers. What Wolfram's Physics Project searches for.
What we call physics.

## One claim

For a given class of rules with bounded description length, let
**T_obs(r)** be the first step at which rule r produces an observer,
and **T_rul(r)** the first step at which it produces ruliad-like
coherence.

The fraction of rules where T_obs is finite vastly exceeds the fraction
where T_rul is finite. Among rules where both are finite, T_obs < T_rul.

Observers are cheap. Physics is expensive. Interiority precedes
objectivity.

## Read the argument

Start with [`claim.md`](claim.md) for the hypothesis in plain language.
Then [`falsification.md`](falsification.md) for what would refute us.
Then [`definitions.md`](definitions.md) for the mathematics.
Then [`theory/`](theory/) for the structural arguments.
Then [`experiments/`](experiments/) for the data.
Then [`experiments/counterexamples/`](experiments/counterexamples/) for
the honest accounting of what doesn't work.

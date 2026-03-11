# cheap-observer

**Sparks produce observers before they produce ruliads.**

---

## Repository Structure

```
cheap-observer/
│
├── README.md
├── LICENSE
├── CITATION.cff
│
│
│   ══════════════════════════════════════
│   THE ARGUMENT
│   ══════════════════════════════════════
│
├── claim.md                         # The hypothesis in one page. No jargon.
├── falsification.md                 # What would refute us. The second thing
│                                    # a skeptic reads.
│
├── definitions.md                   # Single document, reads top to bottom:
│                                    #   1. Spark (rule + seed)
│                                    #   2. Observer (four criteria, their logical
│                                    #      structure, partial order, conjunction rules)
│                                    #   3. Ruliad-like coherence (causal invariance,
│                                    #      dimensionality, global agreement)
│                                    #   4. Thresholds T_obs and T_rul
│                                    #   5. The formal claim as inequality over
│                                    #      prevalence and ordering
│
├── theory/
│   ├── local_vs_global.md           # Structural argument: why local coherence
│   │                                # is generically easier than global confluence.
│   │                                # Constraint-counting, asymptotic bounds.
│   ├── bootstrapping.md             # Impossibility theorem: which observer
│   │                                # configurations cannot self-generate,
│   │                                # which can given minimal sparks.
│   ├── observer_logic.md            # What fragment of SO/fixpoint logic captures
│   │                                # observer-hood? Descriptive complexity of
│   │                                # the observer property vs the coherence property.
│   └── open_problems.md             # What we don't know. What would break the claim.
│
│
│   ══════════════════════════════════════
│   THE EVIDENCE
│   ══════════════════════════════════════
│
├── experiments/
│   ├── design.md                    # Experimental methodology. What we measure,
│   │                                # how we measure it, what counts as evidence.
│   │
│   ├── string_rewriting/
│   │   ├── sweep.py
│   │   ├── config.yaml              # Rule class params, detection thresholds, seeds
│   │   ├── results/
│   │   └── analysis.ipynb
│   │
│   ├── hypergraph/
│   │   ├── sweep.py
│   │   ├── config.yaml
│   │   ├── results/
│   │   └── analysis.ipynb
│   │
│   ├── directed_graph/              # Game of Intelligence rule class
│   │   ├── sweep.py
│   │   ├── config.yaml
│   │   ├── results/
│   │   ├── analysis.ipynb
│   │   └── engine/                  # The Game of Intelligence simulation.
│   │       │                        # A specific rule class, not the framework.
│   │       ├── core.py              # Activity creates structure, disuse destroys it
│   │       ├── rules.py             # v2 ruleset
│   │       ├── topology.py          # Scale-free analysis, stratified memory
│   │       └── visualize.py
│   │
│   ├── comparison/                  # Cross-class threshold analysis
│   │   ├── aggregate.py             # Combine results across rule classes
│   │   ├── threshold_distributions.ipynb
│   │   └── figures/
│   │
│   └── counterexamples/
│       ├── README.md                # Taxonomy of failures. What breaks and why.
│       ├── obs_without_rul.py       # Rules that produce observers but never coherence
│       ├── rul_without_obs.py       # Rules that produce coherence but no observers (!)
│       ├── false_positives.py       # Structures that pass 3 of 4 criteria
│       ├── borderline/              # Cases that stress the definitions
│       └── notes.md                 # What counterexamples teach us about the definitions
│
│
│   ══════════════════════════════════════
│   THE MACHINERY
│   ══════════════════════════════════════
│
├── src/
│   ├── README.md                    # These three modules are the general
│   │                                # framework. They work on any rule class.
│   ├── spark/
│   │   ├── enumerate.py             # Systematic rule enumeration
│   │   ├── seed_search.py           # Minimal seed finder
│   │   └── rule_classes/
│   │       ├── string_rewriting.py
│   │       ├── hypergraph.py
│   │       └── directed_graph.py
│   │
│   ├── observer/
│   │   ├── definition.py            # The logical structure of observer-hood.
│   │   │                            # Conjunction? Partial order? Weighted?
│   │   │                            # This file is the formal contract.
│   │   ├── detect.py                # Detection algorithm using definition.py
│   │   ├── boundary_stability.py
│   │   ├── internal_entropy.py
│   │   ├── causal_decoupling.py
│   │   ├── self_reference.py
│   │   └── spectrum.py              # Proto-observer → observer classification
│   │
│   └── ruliad/
│       ├── causal_invariance.py
│       ├── dimensionality.py
│       └── coherence.py
│
│
│   ══════════════════════════════════════
│   CONTEXT
│   ══════════════════════════════════════
│
├── paper/
│   ├── cheap-observer.tex
│   ├── figures/
│   └── references.bib
│
├── docs/
│   ├── wolfram_relation.md          # What we take, where we fork
│   ├── prior_art.md                 # Garrett 2011, Arsiwalla et al. 2025,
│   │                                # Zhao/Harlow/Usatyuk 2025, etc.
│   └── faq.md                       # "Isn't a glider just a pattern?"
│
└── notebooks/
    ├── 01_see_an_observer.ipynb     # Run a rule. Watch a spark become an observer.
    ├── 02_the_claim.ipynb           # Threshold comparison, visualized.
    └── 03_game_of_intelligence.ipynb
```

---

## README.md

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

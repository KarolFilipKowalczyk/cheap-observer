# Motivation

## The question

Which is simpler: a perspective, or a universe?

A perspective is something that has an inside. It maintains itself,
it refers to itself, it is partially cut off from everything else.
It doesn't need to be conscious. It doesn't need to understand anything.
It just needs to be a bounded region whose internal workings are partly
its own business.

A universe is something where multiple perspectives agree. There are
stable laws. There is shared structure. Different insides, looking out,
see something compatible. The agreement doesn't need to be perfect. But
it needs to hold well enough that the perspectives can, in principle,
compare notes.

We are asking: in the space of all simple computational rules — the
kind Wolfram has been enumerating since the 1980s — which of these
two things appears first?

## Why this matters

There are two default stories about where minds come from.

The first says: the universe came first. Physics produced chemistry,
chemistry produced biology, biology produced brains, and brains
produced minds. The perspective is the last thing to arrive, the most
complex, the most expensive. This is the standard scientific picture.

The second says: something was dreaming before there was a universe
to dream about. The computational process that generates a bounded
perspective — an inside — is simpler than the computational process
that generates a shared, law-governed, observer-independent world.
The dreamer is cheaper than the dream.

We are not arguing for either story philosophically. We are asking
whether the second story is *mathematically simpler* than the first.
Specifically: when you enumerate simple rules and run them, do
observer-like structures appear at lower complexity thresholds than
physics-like regularities?

If yes, this inverts the standard picture. Not because physics is
wrong, but because physics is expensive. The default product of
simple computation is not a universe — it is a perspective. Shared
reality is a rare, hard-won coordination between perspectives, not
the background they emerge from.

If no — if physics-like coherence appears just as easily or more
easily than observer-like structures — then the standard picture
holds, and the cheapness of observers was an illusion born of
loose definitions.

## What counts as an answer

We define three things:

**Spark.** A rule and its minimal seed. The simplest possible
starting point for a computation.

**Observer.** A bounded region of the computation's evolution graph
that maintains itself, has non-trivial internal dynamics, is partly
decoupled from its exterior, and refers back to itself. Defined by
four measurable graph-theoretic criteria with an explicit logical
structure.

**Ruliad.** The regime where a rule's evolution exhibits global
coherence — causal invariance, effective dimensionality, agreement
between observers. What Wolfram's Physics Project searches for.
What we experience as physics.

We then measure two thresholds for each rule in a given class:

- **T_obs**: the first step at which an observer appears.
- **T_rul**: the first step at which ruliad-like coherence appears.

The hypothesis is confirmed if, across multiple rule classes:

1. The fraction of rules where T_obs is finite vastly exceeds the
   fraction where T_rul is finite.
2. Among rules where both are finite, T_obs < T_rul with high
   probability.
3. These results are robust to reasonable tightening of the observer
   definition.

The hypothesis is refuted if:

1. A natural rule class is found where T_rul < T_obs for the
   majority of rules.
2. The observer criteria are shown to be so loose that random
   noise satisfies them.
3. Tightening the criteria to exclude trivial cases collapses the
   prevalence gap.

## What this project is not

This is not a consciousness project. We never define or measure
consciousness. We define and measure bounded self-referential
structure. Whether such structure has "experience" is not our
question.

This is not a simulation hypothesis paper. We never argue that
we live in a simulation. We argue that the computational cost
of generating a perspective is lower than the cost of generating
a shared physics. The philosophical implications are for the
reader to draw.

This is not a critique of Wolfram. We use his framework, his
rule space, his definitions of causal invariance and observer
theory. We add one question he hasn't prioritized: what is the
generic product of simple rules? His project searches for our
physics. Ours maps what comes before physics.

This is not a theory of everything. It is a measurement of
relative complexity in rule space. If the measurement comes out
the way we predict, the implications are large. But the project
itself is small, precise, and falsifiable.

## The anchor

Every decision in this project — which rule class to study, which
metric to implement, which experiment to run, which tangent to
pursue or abandon — should be tested against one question:

**Does this help us compare T_obs against T_rul?**

If yes, do it. If no, write it down in `theory/open_problems.md`
and come back later. The project is the comparison. Everything
else is context.

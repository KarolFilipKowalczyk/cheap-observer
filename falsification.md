# Falsification

The Cheap Observer Hypothesis is falsified if any of the following
holds.


## 1. The ordering is wrong

A natural rule class exists where T_rul < T_obs for the majority of
rules. That is, most rules in the class produce ruliad-like coherence
before they produce an observer, or produce coherence without ever
producing an observer at all.

This would mean physics is not expensive. It would mean that global
coordination between update orders is at least as easy to achieve as
bounded self-referential structure — that confluence comes cheap and
observers come late. The central claim of the hypothesis would be
directly contradicted. A single such rule class is sufficient, provided
it is natural (not constructed specifically to defeat the hypothesis).

Our initial test case is string rewriting with description length
at most 4. If the ordering already fails there, the hypothesis is
dead before it begins.


## 2. The definitions are trivial

The observer criteria are so loose that random graphs satisfy them at
comparable rates to actual evolution graphs. Specifically, when we
generate configuration model random DAGs — matched to each evolution
graph in node count, edge count, and degree sequence — and run the
observer detection algorithm on them, the fraction of random graphs
containing a structure satisfying all four criteria (P_null) is
comparable to the fraction of evolution graphs containing observers
(P_obs).

This would mean the four criteria do not detect anything specific to
rewriting dynamics. They would be graph-theoretic accidents —
properties that any sufficiently connected DAG satisfies by chance.
The claim that observers are produced by the computation would be
vacuous, because the computation is doing no real work. We chose the
configuration model as our null precisely because it is the harder
test: it preserves local connectivity structure, giving random graphs
every advantage. If the criteria cannot beat this null, they capture
nothing.


## 3. The claim is fragile

Tightening the observer criteria to exclude borderline cases collapses
the prevalence gap between P_obs and P_rul. For instance, raising the
persistence window, lowering the boundary stability threshold, raising
the decoupling requirement, or requiring multiple self-referential
returns instead of one — any reasonable tightening that eliminates
marginal cases also eliminates the gap between observer prevalence and
ruliad prevalence.

This would mean the hypothesis survives only in a narrow parameter
regime. The observers we count would be the definitional equivalent
of noise — structures that barely qualify and whose existence depends
on where exactly we draw the line. A robust empirical claim cannot
rest on a knife-edge. If the gap between P_obs and P_rul vanishes
under modest tightening, the gap was never real.


## What does not falsify us

Finding individual rules where T_rul < T_obs is expected and
unremarkable. The claim is statistical, not universal. We predict a
strong majority, not unanimity. Counterexamples are collected in
`experiments/counterexamples/` and studied for what they reveal about
the definitions. A handful of rules where physics comes before
observers would be interesting data points. A rule class dominated
by such rules would be a refutation.

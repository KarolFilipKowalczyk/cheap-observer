# Definitions

This document reads top to bottom. Each definition depends on those
before it. The final section states the hypothesis as a formal claim
over the preceding definitions.


## 1. Rule class

A **rule class** is a parametric family of rewriting systems. We begin
with the simplest interesting class: two-symbol, single-rule string
rewriting.

A **string rewriting rule** r is a pair (L, R) where L and R are
non-empty strings over the alphabet {0, 1}. At each step, the rule
replaces one occurrence of L in the current string with R.

A **rule class** C(l) is the set of all string rewriting rules where
|L| + |R| <= l. The parameter l controls the description length of
the rule — its Kolmogorov cost.

For l = 4 (e.g., L and R are each at most 2 symbols), C(4) contains
a finite, enumerable set of rules. Its exact cardinality is computed
as follows: for each pair of lengths (|L|, |R|) with |L| >= 1,
|R| >= 1, and |L| + |R| <= 4, we count all binary strings of those
lengths, excluding cases where L is empty (the rule must match
something). The cardinality |C(4)| = 56. This is our initial
experimental domain. Later work may extend to hypergraph rewriting and directed
graph rewriting (the Game of Intelligence rule class), but all
definitions below are stated for string rewriting first and must be
verified on this class before generalization.


## 2. Spark

A **spark** is a pair (r, s_0) where r is a rule and s_0 is a seed
string.

The **minimal spark** for a rule r is the pair (r, s_0*) where s_0*
is the shortest seed string such that applying r to s_0* produces a
non-trivial evolution — meaning the string neither vanishes nor
reaches a fixed point within the first 100 steps.

Note: this criterion is deliberately simple and does not depend on
the characteristic time tau (defined in Section 4), which requires
an already-selected spark to compute. The threshold of 100 steps is
a bootstrap parameter, not a deep constant. Sensitivity to this
choice is reported in experiments.

In practice, we search for s_0* by enumerating seeds of increasing
length. A spark that produces no non-trivial evolution for any seed
up to length l_max is classified as **sterile**. Default: l_max = 2l
(twice the rule description length).


## 3. Evolution graph

Given a spark (r, s_0), the **evolution** is the sequence of strings
s_0, s_1, s_2, ... produced by repeatedly applying r. When multiple
occurrences of L exist at some step, we apply the **canonical update
order**: the leftmost match is rewritten first.

The evolution graph G(r, s_0) is therefore deterministic — it is
uniquely determined by the rule and the seed under leftmost-match
ordering. Section 7 explicitly varies this ordering to test causal
invariance; all other sections use the canonical order.

The **evolution graph** G(r, s_0) encodes the causal structure of
this evolution. It is a directed acyclic graph defined as follows:

- **Nodes.** Each node (i, t) represents position i in the string at
  time t. The node's label is the symbol s_t[i].

- **Edges.** A directed edge connects (i, t) to (j, t+1) if position
  i at time t causally influenced position j at time t+1. Specifically:
  - If position i was part of the matched occurrence of L at time t,
    it has edges to all positions in the inserted R at time t+1.
  - If position i was not part of the match, it has an edge to its
    shifted position at time t+1 (identity propagation).

This graph encodes both temporal and spatial structure. A contiguous
region of the graph corresponds to a spatiotemporal region of the
string's evolution. Locality, influence, and boundedness are all
readable from the graph.


## 4. Characteristic time

The **characteristic time** tau(r, s_0) of a spark measures the
natural timescale of the evolution's dynamics.

**Definition.** Compute the Hamming distance d(t) between consecutive
strings s_t and s_{t+1} for each step, normalized by string length.
The characteristic time tau is the smallest lag k such that the
autocorrelation of the sequence d(0), d(1), d(2), ... drops below
1/e:

    autocorr(k) = corr(d(t), d(t+k)) < 1/e

If the autocorrelation never drops below 1/e within the evolution
(indicating periodic or highly regular dynamics), tau is set to the
period length.

This definition is standard in time series analysis. It does not
depend on absolute string length and is well-defined for both
fixed-length and growing strings. The characteristic time normalizes
all duration-dependent quantities below. This prevents fast rules
from appearing observer-rich and slow rules from appearing
observer-poor for trivial reasons.


## 5. Observer

An **observer** in an evolution graph G is a connected subgraph S of
G satisfying four criteria simultaneously (strict conjunction) over
a persistence window of at least 10 * tau.


### 5.1 Boundary stability

The **boundary** of S at time t is the set of edges crossing between
nodes inside S and nodes outside S at time t.

**Criterion.** The symmetric difference between the boundary at time
t and the boundary at time t+1, averaged over the persistence window,
is small relative to the total boundary size:

    (1 / W) * sum_{t in window} |B(t) △ B(t+1)| / |B(t)| < epsilon_B

where W is the window length and epsilon_B is the boundary stability
threshold. Default: epsilon_B = 0.3.

Interpretation: the boundary changes by less than 30% per step on
average. The structure maintains its shape.


### 5.2 Internal entropy

The **internal state** of S at time t is the string of labels of all
nodes in S at time t, read left to right.

**Criterion.** The Shannon entropy of the internal state distribution,
computed over a sliding window of tau steps, exceeds a minimum:

    H(internal states over tau window) > epsilon_H

where epsilon_H is the internal entropy threshold.
Default: epsilon_H = 1.0 bit.

Interpretation: the interior is not frozen. It undergoes non-trivial
state transitions. A structure with constant internal state is not an
observer — it is a crystal.


### 5.3 Causal decoupling

For a window of tau steps, compute:
- I_int: the mutual information between the internal state of S at
  time t and the internal state at time t + tau.
- I_ext: the mutual information between the internal state of S at
  time t and the external state (the complement of S) at time t + tau.

**Criterion.**

    I_int / (I_int + I_ext) > epsilon_D

where epsilon_D is the decoupling threshold. Default: epsilon_D = 0.6.

**Estimator.** Mutual information between discrete string-valued
variables is estimated using the plug-in estimator with Miller-Madow
bias correction when the internal state length is at most 20 symbols.
For longer internal states, where sample counts are insufficient for
reliable MI estimation, we use normalized compression distance (NCD)
as a proxy: NCD(x, y) = (C(xy) - min(C(x), C(y))) / max(C(x), C(y))
where C denotes the compressed length. The decoupling ratio is then
computed as (1 - NCD_int) / ((1 - NCD_int) + (1 - NCD_ext)), which
preserves the same semantics: higher values indicate greater internal
predictability relative to external influence.

Interpretation: at least 60% of the predictive information about the
structure's future comes from its own past, not from the environment.
The interior is partly its own business.


### 5.4 Self-reference

The evolution graph is a DAG — it has no topological cycles. The
"cycle" in self-reference is spatial, not temporal: the structure's
output causally returns to its own spatial region.

A **self-referential return** in S is a pair of directed paths in the
evolution graph such that:

1. A node (i, t) inside S has a forward causal path, passing only
   through nodes inside S, to a node (j, t') inside S at a later
   time t' > t.

2. The rewrite at time t' that produces content at position j is
   causally downstream of position i at time t.

3. Position j at time t' in turn has a forward causal path, again
   through nodes inside S, to a node (i', t'') where i' occupies
   the same spatial region as the original position i (meaning
   |i' - i| < the width of S at time t).

The graph path is acyclic — it moves forward in time at every edge.
But the spatial trajectory returns to where it started. The
structure's dynamics feed back into their own spatial region.

**Criterion.** At least one self-referential return exists within
the persistence window.

Interpretation: this criterion distinguishes an observer from a mere
persistent pattern. A glider that propagates without internal feedback
is not an observer — its causal paths exit the spatial region and
never return. A structure whose rewrites produce content that causally
re-enters its own region is.


### 5.5 Conjunction

A connected subgraph S is an **observer** if and only if all four
criteria (5.1 through 5.4) are satisfied simultaneously over a
contiguous window of at least 10 * tau steps.

There is no partial credit. No weighting. No scoring function. A
structure either is or is not an observer under this definition.
This strictness is deliberate — see `falsification.md` for what
would motivate relaxing it.


## 6. T_obs

**T_obs(r)** is the earliest time step t such that the evolution
graph G(r, s_0*) contains an observer (as defined in Section 5)
whose persistence window begins at or before t.

If no observer appears within the maximum evolution length N_max,
then T_obs(r) = infinity. Default: N_max = 10000 steps.

For the prevalence study, we report:
- P_obs(C): the fraction of rules in class C where T_obs is finite.
- The distribution of T_obs values over rules where it is finite.


## 7. Ruliad-like coherence

A rule r exhibits **ruliad-like coherence** at evolution length n if
its evolution graph is invariant under change of update order.

**Operational test.** Given a spark (r, s_0*) and evolution length n:

1. Sample k distinct update orders uniformly at random. At each step
   where multiple occurrences of L exist, randomly choose which to
   rewrite. Default: k = 50.

2. For each update order, construct the evolution graph G_j up to
   step n.

3. For all pairs (G_j, G_k), test whether the causal graphs are
   isomorphic as labeled DAGs. Since full DAG isomorphism is
   GI-complete, we use a canonical hash: sort nodes by (time,
   position), serialize the labeled edge list, and compute a
   cryptographic hash. For string rewriting evolution graphs, the
   node labeling by (position, time, symbol) is rich enough that
   this hash is effectively a complete invariant — non-isomorphic
   graphs produce distinct hashes with overwhelming probability.
   Two graphs are deemed isomorphic if and only if their canonical
   hashes match.

4. The rule exhibits ruliad-like coherence at length n if all
   sampled pairs are isomorphic.

This is a statistical test, not a proof. It can produce false
positives (a rule that appears invariant under 50 samples but fails
under the 51st). It cannot produce false negatives. We report the
sample size k alongside all results.

**Note.** Causal invariance is Wolfram's primary criterion for
physics-like behavior. It corresponds to confluence in rewriting
theory — the property that the result is independent of the order
in which rewrites are applied. Most rewriting systems are not
confluent. This is the expensive property.


## 8. T_rul

**T_rul(r)** is the earliest evolution length n such that r exhibits
ruliad-like coherence (as defined in Section 7) at length n.

If no coherence is detected within N_max steps under k sampled
orderings, then T_rul(r) = infinity.

For the prevalence study, we report:
- P_rul(C): the fraction of rules in class C where T_rul is finite.
- The distribution of T_rul values over rules where it is finite.


## 9. Null model

To verify that the observer criteria are not trivially satisfied by
arbitrary graph structure, we define a **null model**:

For each evolution graph G(r, s_0*) that produces an observer,
generate a random DAG using the **configuration model**: matched
node count, edge count, and degree sequence. This is the stronger
null — it preserves local connectivity structure, making it more
likely to accidentally satisfy observer criteria than an Erdos-Renyi
graph would. If the observer criteria still separate rewriting
graphs from configuration model nulls, the criteria detect rewriting
dynamics specifically, not just degree-regular subgraph structure.

Apply the observer detection algorithm to each random graph.

Report **P_null**: the fraction of random graphs that contain a
structure satisfying all four observer criteria.

If P_null is comparable to P_obs, the observer definition is too
loose and must be tightened. If P_null is negligible compared to
P_obs, the definition captures genuine structure produced by the
rewriting dynamics, not graph-theoretic accidents.

The null model comparison is reported alongside every prevalence
result. It is not optional.


## 10. The formal claim

**Cheap Observer Hypothesis.** For string rewriting rule class C(l)
with l >= 4:

1. **Prevalence.** P_obs(C) >> P_rul(C). The fraction of rules
   producing observers vastly exceeds the fraction producing
   ruliad-like coherence.

2. **Ordering.** Among rules where both T_obs and T_rul are finite,
   P(T_obs < T_rul) > 1 - delta for small delta. Observers appear
   first in almost all cases.

3. **Non-triviality.** P_obs(C) >> P_null. The observer prevalence
   is not an artifact of loose definitions.

4. **Robustness.** Claims (1) and (2) hold under reasonable
   variation of the thresholds epsilon_B, epsilon_H, epsilon_D, and
   the persistence window multiplier.

If all four conditions hold for string rewriting, we then test
whether they generalize to other rule classes (hypergraph rewriting,
directed graph rewriting). Generalization is expected but not
assumed.

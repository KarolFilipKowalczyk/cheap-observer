# String Rewriting: Conclusion

Summary of all results from C(4), C(6), and C(8) binary string
rewriting experiments. This closes the string rewriting chapter and
motivates the move to a second rule class.


## 1. What we found

### Observer threshold at C(8)

| Class | Rules | Active | Observers | Near-miss (3/4) | P_obs  |
|-------|-------|--------|-----------|-----------------|--------|
| C(4)  | 68    | 20     | 0         | 0               | 0%     |
| C(6)  | 516   | 174    | 0         | 0               | 0%     |
| C(8)  | 3076  | 1026   | 2         | 8               | 0.195% |

The observer threshold for binary string rewriting is C(8): rules
with |L| + |R| <= 8. Below this, no rule produces a structure passing
all four observer criteria.

The two observers are 01->10001 and 10->01110 — a single distinct
structure and its 0<->1 bit-flip mirror. Properties:

- |L| = 2, |R| = 5 (growth +3 per step)
- T_obs = 310 (observer appears after 310 evolution steps)
- tau = 4 (characteristic time)
- Sawtooth match dynamics: period-3 oscillation, net drift +1/3

Corrected prevalence: P_obs = 1/1026 = 0.097% (unique structures)
or 2/1026 = 0.195% (counting mirrors). The 8 near-misses are 4
unique structures, all failing only on causal decoupling.

### Progressive failure across classes

The failure mode evolves as rule complexity increases:

- **C(4):** Criteria reject trivially. Interiors are frozen (H = 0).
  Boundaries are stable only because nothing happens near them.
  Self-reference is free because the match site never moves.

- **C(6):** First non-frozen interiors. Six rules produce H > 0.
  But the match site drifts monotonically — no spatial localization.
  Boundary stability and decoupling fail for structural reasons.

- **C(8):** The sawtooth oscillation creates a semi-localized active
  zone. The match site oscillates within a width-3 band before
  drifting. This is enough for boundary stability over the
  persistence window. Two rules push decoupling above threshold.

### Sensitivity analysis

The C(8) observer is moderately robust under threshold variation:

| Parameter       | Default | Observer range | Assessment       |
|-----------------|---------|----------------|------------------|
| epsilon_D       | 0.60    | 0.52 – >0.70   | Most robust      |
| epsilon_B       | 0.30    | 0.25 – 0.30+   | 17% margin       |
| epsilon_H       | 1.00    | <0.50 – 1.25   | 50% margin       |
| persistence     | 10      | 5 – 10         | Tightest axis    |

The initial "knife-edge at D=0.605" characterization was misleading.
Different candidate subgraphs for the same rule achieve D > 0.70.
The true bottleneck is persistence: the sawtooth drift outpaces the
subgraph after ~40 steps. At persistence_multiplier=8, six observers
exist (three unique structures).

### Causal invariance: absent or vacuous

| Metric                        | Count | Fraction |
|-------------------------------|-------|----------|
| Vacuous T_rul = 0             | 314   | 30.6%    |
| Genuine finite T_rul          | 0     | 0%       |
| T_rul = infinity              | 712   | 69.4%    |

No rule in C(8) exhibits genuine causal invariance. The 314 rules
with T_rul = 0 are vacuously invariant (always a unique match per
step — no choice of update order exists). This is the absence of
ambiguity, not the presence of confluence.

### The sets are disjoint

**No rule in C(8) has both finite T_obs and finite T_rul.**

- The 2 observer rules have T_obs = 310, T_rul = infinity.
- The 314 vacuously invariant rules have T_rul = 0, T_obs = infinity.
- 710 rules have both T_obs = infinity and T_rul = infinity.

The T_obs vs T_rul scatter plot is degenerate: all points lie on the
axes. There are no data points in the interior where T_obs and T_rul
could be compared on the same rule.


## 2. What this means

### The structural limitation

Single-rule binary string rewriting cannot test the full Cheap
Observer Hypothesis. The rule class has a structural gap:

- **Rules complex enough for observers** (|L| >= 2, with the right
  R-string to create semi-localized dynamics) inevitably produce
  multiple matches per step, making causal invariance non-trivial to
  satisfy. In fact, none satisfy it.

- **Rules simple enough for confluence** (those with always-unique
  matches) are too simple for observers — their interiors are frozen
  or their match sites are trivially localized.

The two properties require opposite structural features:
- Observers need spatial heterogeneity, which requires multiple
  interacting rewrites within a region.
- Causal invariance requires that the choice of rewrite order doesn't
  matter, which is hardest precisely when multiple rewrites interact.

In 1D string rewriting with a single rule, these demands are
irreconcilable. The rule class lacks the middle ground where both
properties could coexist.

### What C(8) does establish

1. **P_obs > 0.** Observers exist in simple computational rules.
   The four criteria are satisfiable by actual rewriting dynamics,
   not just in principle.

2. **P_rul(genuine) = 0.** Physics-like coherence does not appear
   at this complexity level. If the hypothesis is correct, genuine
   causal invariance requires higher complexity than observers do.
   This is consistent with the claim but does not confirm it.

3. **The criteria work.** They correctly reject trivial dynamics
   (C(4)), catch structural near-misses (C(6)), and identify genuine
   observers (C(8)). The sensitivity analysis confirms the results
   are not artifacts of threshold tuning.


## 3. What we take forward

### Validated pipeline

The observer detection pipeline is production-ready:

- **Enumeration and seed search** work for any single-rule binary
  string rewriting class.
- **Evolution graph construction** correctly encodes causal structure.
- **Four-criteria scoring** with early pruning handles 1000+ rules
  efficiently (~5 minutes for C(8) at 1000 steps).
- **Causal invariance testing** with canonical hashing and random
  orderings correctly identifies vacuous and non-invariant rules.
- **GUI runners** provide real-time progress for long sweeps.

The `src/observer/` and `src/ruliad/` modules are rule-class-agnostic
by design. They operate on evolution graphs, not on strings. A new
rule class needs only to implement the evolution graph protocol.

### Counterexample catalog

Four documented patterns inform future work:

1. **Trivial boundary stability** in uniform-growth rules (C(4)):
   stability through spatial isolation, not structural persistence.
2. **Trivial self-reference** in fixed-match-site rules (C(4)):
   spatial return through anchoring, not feedback.
3. **Drift-limited persistence** (C(8)): the sawtooth dynamics impose
   a hard ceiling on how long the observer structure survives.
4. **Mirror double-counting**: bit-flip symmetry in binary rules
   inflates prevalence by 2x. Report unique and total separately.

### Key quantitative benchmarks

| Benchmark                          | Value        |
|------------------------------------|--------------|
| Smallest class with observers      | C(8)         |
| Observer threshold (description)   | |L|+|R| = 7  |
| T_obs for first observer           | 310 steps    |
| P_obs at C(8)                      | 0.097% unique|
| Sensitivity range (persistence)    | P=5 to P=10  |
| P_rul(genuine) at C(8)             | 0%           |


## 4. What's next

### Why hypergraph rewriting

String rewriting is inherently 1D: the match site is a contiguous
interval in a linear string. This constrains dynamics to ballistic
drift or bounded oscillation. The structural limitation described in
Section 2 is a consequence of this dimensionality.

Hypergraph rewriting breaks this constraint:

- **Spatial structure is 2D/3D.** Match sites are subgraphs, not
  intervals. Multiple non-overlapping matches can coexist in
  spatially separated regions.

- **Match sites are non-linear.** A hypergraph rewrite can affect
  a node's neighborhood without displacing distant nodes. This
  enables localized dynamics without ballistic drift.

- **Multiple simultaneous rewrites interact in richer ways.** Two
  nearby rewrites can create or destroy each other's match conditions,
  enabling genuine competition and cooperation between active sites.

- **Causal invariance is non-trivial.** The Wolfram Physics Project
  demonstrates that specific hypergraph rules DO exhibit causal
  invariance. The rule class has the structural capacity for both
  observers and physics-like coherence.

This is the middle ground that string rewriting lacks. Hypergraph
rewriting is the natural next rule class for the Cheap Observer
Hypothesis.

### What needs to happen

1. **Adapt definitions.md** for hypergraph evolution graphs. The four
   observer criteria are stated in terms of evolution graphs, not
   strings. The main work is defining spatial regions (subgraphs of
   a hypergraph) and their boundaries.

2. **Implement hypergraph evolution.** The Wolfram model provides
   the framework: nodes, hyperedges, pattern matching, rewriting.
   The evolution graph is a causal graph over rewrite events.

3. **Enumerate and sweep.** Start with small hypergraph rules
   (2-3 elements per hyperedge, small rule tables) and run the same
   sweep methodology: T_obs and T_rul for every rule.

4. **The scatter plot.** For the first time, we may have rules where
   both T_obs and T_rul are finite. The scatter plot becomes the
   central artifact of the project.

### Waves 4-6 for string rewriting: deprioritized

The null model (Wave 4), counterexample taxonomy (Wave 5), and
robustness sweep (Wave 6) for string rewriting are deferred until
hypergraph results provide context. If hypergraph rewriting produces
the expected non-degenerate scatter plot, the string rewriting null
model becomes a secondary validation. If hypergraph rewriting fails,
revisiting string rewriting thresholds becomes necessary.

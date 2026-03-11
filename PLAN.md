# Plan

Last updated: 2026-03-11

## Status: STRING REWRITING CHAPTER COMPLETE

C(8) string rewriting: 1026 active rules, 2 observers (1 unique),
P_obs = 0.097%. Observer is moderately robust (sensitivity-tested).
0 rules have genuine causal invariance. T_obs and T_rul sets are
completely disjoint — no rule has both finite. The scatter plot is
degenerate.

String rewriting cannot test the full hypothesis: the rule class
structurally separates observer-producing and confluent rules.
Moving to hypergraph rewriting as the second rule class, where
confluence and observers can coexist.

See experiments/string_rewriting/results/conclusion.md for the full
summary.

## Performance profile (measured on CPU)

All 20 active C(4) rules are growing rules (L shorter than R). String
length grows linearly with steps. Detection cost scales ~O(n^2) in
step count due to candidate generation × scoring.

| Steps | Per rule (detect) | 20 rules  | Max strlen |
|-------|-------------------|-----------|------------|
| 200   | 0.11s             | ~8s       | 201        |
| 500   | 0.78s             | ~25s      | 501–1001   |
| 1000  | 3.1s              | ~1 min    | 1001       |
| 2000  | ~12s (est.)       | ~4 min    |            |
| 5000  | ~78s (est.)       | ~26 min   |            |
| 10000 | ~310s (est.)      | ~1.7 hrs  |            |

Bottleneck is `detect.py` — Python-level loops over candidate
subgraphs, set operations for boundaries, BFS for self-reference.
Graph construction is fast (<0.1s at 1000 steps).

**Optimization path (before CUDA):**
1. Algorithmic pruning — better candidate selection, tighter early exit
2. Multiprocessing — 20 rules are fully independent
3. Cython/Numba for boundary set ops and BFS
4. CUDA only at C(6)+ scale (thousands of rules)

## Waves

### Wave 1 — Detection pipeline [COMPLETE]
Build the full observer detection for a single rule.

- [x] Repository structure
- [x] CLAUDE.md, motivation.md, definitions.md
- [x] claim.md, falsification.md
- [x] src/observer/definition.py
- [x] src/spark/rule_classes/string_rewriting.py
- [x] src/spark/enumerate.py
- [x] src/spark/seed_search.py
- [x] src/spark/evolution_graph.py
- [x] src/spark/characteristic_time.py
- [x] src/observer/boundary_stability.py
- [x] src/observer/internal_entropy.py
- [x] src/observer/causal_decoupling.py
- [x] src/observer/self_reference.py
- [x] src/observer/detect.py
- [x] src/observer/spectrum.py
- [x] experiments/string_rewriting/test_single_rule.py

**Gate:** Does the pipeline run end-to-end on one rule? Does T_obs
come back finite for at least one rule in C(4)?

**Gate result:** Pipeline runs end-to-end. T_obs = infinity for all of
C(4). The class is below the observer complexity threshold. This is a
valid negative result, not a pipeline failure.


### Wave 2 — The sweep [C(4) and C(6) COMPLETE]
Run every rule in a class. First histogram of T_obs.

- [x] C(4) sweep: 0/20 active rules produce observers (see results/c4_summary.md)
- [x] Entropy pre-filter in detect.py (skip frozen interiors immediately)
- [x] src/engine/runner.py (multiprocessing runner with optional GUI)
- [x] experiments/string_rewriting/config.yaml
- [x] experiments/string_rewriting/sweep.py (T_obs only)
- [x] C(6) sweep: 0/174 observers, 6 rules past entropy filter,
      best 2/4 (see results/c6_summary.md)
- [x] C(6) match site diagnostic (see results/c6_match_dynamics.md)
- [x] C(8) sweep: 2/1026 observers, 8 near-misses at 3/4
      (see results/c8_summary.md)
- [x] first_observer.json saved
- [ ] experiments/string_rewriting/analysis.ipynb (T_obs histogram)

**Gate:** What fraction produces observers?

**C(4) gate result:** P_obs = 0. Rules too simple for any internal dynamics.

**C(6) gate result:** P_obs = 0. First non-frozen interiors (6 rules).
Match site drifts monotonically in all cases.

**C(8) gate result:** P_obs = 0.2% (2/1026). **GATE PASSED.** First
finite T_obs = 310. Observers are 01->10001 and 10->01110. Decoupling
passes by 0.005 (knife-edge). All 8 near-misses fail only on D.


### Wave 2.5 — Threshold sensitivity [COMPLETE]
Pre-Wave-3 robustness check on C(8) observers.

- [x] experiments/string_rewriting/sensitivity.py (GUI runner)
- [x] Vary epsilon_D: 0.50–0.70 (13 values)
- [x] Vary epsilon_B: 0.15–0.40 (10 values)
- [x] Vary epsilon_H: 0.50–2.00 (7 values)
- [x] Vary persistence_multiplier: 5–20 (6 values)
- [x] experiments/string_rewriting/results/c8_sensitivity.md
- [x] experiments/string_rewriting/results/c8_sensitivity.json
- [x] Mirror symmetry correction: 2 observers = 1 distinct structure

**Result:** Observer is moderately robust, not a knife-edge artifact.
- epsilon_D: flat 2 obs from 0.52 to >0.70 (most robust axis)
- epsilon_B: 2 obs from 0.25–0.30, 6 obs at 0.35+ (critical at 0.25)
- epsilon_H: 2 obs from 0.50–1.25 (lost at 1.50)
- persistence: 2 obs at P=10, 6 at P=8, 0 at P=12 (tightest axis)

The "knife-edge at D=0.605" characterization was misleading — that was
one candidate's score. Other candidates for the same rule achieve
D > 0.70. Persistence multiplier is the true bottleneck: the sawtooth
drift limits how long the structure can sustain itself.


### Wave 3 — The other side [COMPLETE]
Measure T_rul. Produce the central scatter plot.

- [x] src/ruliad/causal_invariance.py (canonical hash test, k=50)
- [x] experiments/string_rewriting/trul_sweep.py (GUI runner)
- [x] experiments/string_rewriting/results/c8_trul.json
- [x] experiments/string_rewriting/results/c8_trul.md
- [x] experiments/string_rewriting/results/c8_scatter.json
- [ ] src/ruliad/dimensionality.py
- [ ] First T_obs vs T_rul scatter plot (degenerate in C(8) — see below)

**Gate:** Is T_obs < T_rul for the majority of rules where both are
finite? If yes, the hypothesis has first contact with evidence. If
no, we have a problem — either the hypothesis is wrong or the rule
class is too small. Try C(6) before giving up.

**C(8) gate result:** 0 rules have BOTH finite T_obs and T_rul. The
sets are completely disjoint. 314 rules have vacuous T_rul=0 (unique
match, no choice of order). 0 rules have genuine finite T_rul. Both
observer rules have T_rul=infinity.

P_obs=0.2% vs P_rul(genuine)=0%. Observers exist; genuine physics
does not. The ordering claim (T_obs < T_rul) is vacuously true
(zero data points). C(8) establishes that observers are cheap but
cannot test whether physics is expensive *relative to* observers,
because physics doesn't appear at all.

The scatter plot is degenerate: all points lie on the axes. A
meaningful scatter requires a rule class where both properties can
coexist. **GATE: HALF-PASSED.** String rewriting chapter closed.
Hypergraph rewriting promoted to immediate next step.

See experiments/string_rewriting/results/conclusion.md.


### Wave 4 — Hypergraph rewriting [IMMEDIATE NEXT STEP]
Second rule class. Promoted from Wave 9 because string rewriting
cannot produce the non-degenerate scatter plot the hypothesis needs.

Hypergraph rewriting breaks the structural limitation: confluence and
observers can coexist because spatial structure is 2D/3D, match sites
are non-linear, and multiple simultaneous rewrites interact richly.

- [x] Restructure definitions.md: rule-class-agnostic §1–§9, string rewriting to Appendix A, directed graph Appendix B placeholder
- [ ] src/spark/rule_classes/hypergraph_rewriting.py
- [ ] src/spark/hypergraph_evolution_graph.py
- [ ] experiments/hypergraph/sweep.py
- [ ] experiments/hypergraph/config.yaml
- [ ] experiments/hypergraph/results/
- [ ] First non-degenerate T_obs vs T_rul scatter plot

**Gate:** Does any hypergraph rule have both finite T_obs and finite
T_rul? If yes, the scatter plot becomes the central artifact. If no,
the hypothesis may need a different rule class or revised definitions.


### Wave 5 — Null model [BLOCKED on Wave 4]
Verify definitions aren't trivially satisfied.

- [ ] Null model generator (configuration model, matched degree sequence)
- [ ] Run observer detection on null graphs for both string and hypergraph
- [ ] Compute P_null, compare to P_obs

**Gate:** Is P_null << P_obs? If not, definitions are too loose.


### Wave 6 — Robustness [BLOCKED on Wave 4]
Threshold sensitivity for hypergraph rewriting (string rewriting
sensitivity already done in Wave 2.5).

- [ ] Parameter sweep for hypergraph observers
- [ ] Cross-class comparison in experiments/comparison/
- [ ] Robustness figures

**Gate:** Does the prevalence gap survive reasonable parameter
variation across rule classes?


### Wave 7 — String rewriting deferred work [DEPRIORITIZED]
Null model and additional counterexamples for string rewriting.
Revisit after hypergraph results provide context.

- [ ] src/ruliad/coherence.py (string rewriting null model)
- [ ] experiments/counterexamples/ taxonomy completion
- [ ] experiments/string_rewriting/analysis.ipynb (T_obs histogram)
- [ ] notebooks/01_see_an_observer.ipynb (one rule, visualized)


### Wave 8 — Theory [PARTIALLY UNBLOCKED]
Structural arguments. The disjoint-sets result from string rewriting
motivates theoretical analysis of why observer-producing rules and
confluent rules separate.

- [ ] theory/local_vs_global.md
- [ ] theory/bootstrapping.md (migrate from Game of Intelligence work)
- [ ] theory/observer_logic.md (descriptive complexity question)
- [ ] theory/open_problems.md (accumulates throughout)
- [ ] theory/dimensionality_gap.md (why 1D rewriting separates the sets)


### Wave 9 — Directed graph rewriting [PARTIALLY UNBLOCKED]
Third rule class (Game of Intelligence engine).

- [x] src/spark/rule_classes/directed_graph.py (DirectedGraphRule: match, apply, evolve, enumerate)
- [x] src/spark/directed_graph_evolution.py (evolution graph with three causal edge types)
- [x] src/spark/seed_search.py extended for graph rules (find_minimal_seed_graph)
- [x] Cardinality verified: |D(2,3,2)| = 3,240,532, |D(2,2,2)| = 29,268
- [ ] experiments/directed_graph/engine/ (Game of Intelligence)
- [ ] experiments/directed_graph/sweep.py
- [ ] experiments/directed_graph/config.yaml
- [ ] experiments/directed_graph/analysis.ipynb


### Wave 10 — Paper and docs [BLOCKED on Wave 6]
Written last. Summarizes results that exist.

- [ ] paper/cheap-observer.tex
- [ ] paper/references.bib
- [ ] docs/wolfram_relation.md
- [ ] docs/prior_art.md
- [ ] docs/faq.md
- [ ] CITATION.cff


## Revision log

| Date       | Change                                    |
|------------|-------------------------------------------|
| 2026-03-11 | Initial plan created. Wave 1 in progress. |
| 2026-03-11 | All Wave 1 code complete. Pipeline runs end-to-end. Gate pending: need longer runs to check for finite T_obs. |
| 2026-03-11 | Added performance profile. Detection is O(n^2), ~1.7hrs for 10K steps. CPU optimization before CUDA. |
| 2026-03-11 | Wave 2 gate reached: T_obs = inf for all C(4). Uniform 2/4 failure (entropy=0, decoupling=0.5). Pivoting to C(6). Entropy pre-filter added to detect.py. |
| 2026-03-11 | C(6) swept: 0/174 observers. 6 rules past entropy filter, best 2/4 (01->1001). All LP/shrinking rules sterile. Bottleneck: boundary stability and decoupling. |
| 2026-03-11 | C(6) match site diagnostic: all 6 rules drift monotonically, no spatial localization possible. |
| 2026-03-11 | C(8) swept: **2 observers found** (01->10001, 10->01110). T_obs=310. 8 near-misses at 3/4. P_obs=0.2%. Wave 2 gate passed. |
| 2026-03-11 | Sensitivity check: observer is moderately robust. D not knife-edge (survives 0.52–>0.70). Persistence is tightest axis (0 at P=12). Mirror symmetry: 1 distinct structure. |
| 2026-03-11 | Wave 3: T_rul measured for all 1026 active C(8) rules. 314 vacuous (T_rul=0), 0 genuine finite, 712 infinite. Observer rules have T_rul=inf. Sets disjoint. Gate half-passed. |
| 2026-03-11 | String rewriting chapter closed. Disjoint sets: observer-producing and confluent rules don't overlap. Rule class structurally cannot test full hypothesis. Hypergraph rewriting promoted to Wave 4. |
| 2026-03-11 | definitions.md restructured: §1–§9 now rule-class-agnostic (abstract evolution graphs). All string-specific content moved to Appendix A (complete, final). Zero mathematical content deleted. |
| 2026-03-11 | Appendix B written: directed graph rewriting fully specified. Rule class D(n,m,k) defined with cardinality tables. D(2,3,2) = 3.2M rules; D(2,2,2) = 29K feasible for sweep. Evolution graph protocol, canonical order, distance function, spatial proximity all defined. Game of Intelligence noted as parametric instance. |
| 2026-03-11 | Directed graph rewriting implemented: DirectedGraphRule (match via subgraph isomorphism, apply with reconnection, enumerate D(n,m,k)), DirectedGraphEvolution (causal DAG with three edge types), seed_search extended for graph rules. Cardinalities verified against definitions.md. Pipeline runs end-to-end. |

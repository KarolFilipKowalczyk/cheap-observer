# Plan

Last updated: 2026-03-11

## Status: Wave 2 gate reached — C(4) below threshold, pivoting to C(6)

T_obs = infinity for all 20 active C(4) rules. Every rule produces
uniform or perfectly periodic strings. Internal entropy = 0 and
causal decoupling = 0.5 universally. Boundary stability and
self-reference pass trivially (uniform growth, fixed match site).

C(4) lacks multi-symbol matches and length-preserving rules. C(6)
is the smallest class with these features (516 rules, 174 active,
84 length-preserving). Estimated sweep time: ~6 min at 1000 steps.

See `experiments/string_rewriting/results/c4_summary.md` for full
results and `experiments/counterexamples/notes.md` for trivial-pass
concerns.

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


### Wave 2 — The sweep [C(4) COMPLETE, PIVOTING TO C(6)]
Run every rule in a class. First histogram of T_obs.

- [x] C(4) sweep: 0/20 active rules produce observers (see results/c4_summary.md)
- [x] Entropy pre-filter in detect.py (skip frozen interiors immediately)
- [ ] C(6) sweep at 1000 steps (~6 min estimated)
- [ ] experiments/string_rewriting/config.yaml
- [ ] experiments/string_rewriting/sweep.py (T_obs only)
- [ ] experiments/string_rewriting/analysis.ipynb (T_obs histogram)

**Gate:** What fraction of C(6) produces observers? If zero, definitions
may be too tight or the rule class too small — try C(8) or revise
definitions.md. If all, definitions are too loose. Either outcome loops
back to definitions.md, not forward.

**C(4) gate result:** P_obs(C(4)) = 0. This is the "too tight" path,
but the cause is structural (rules too simple for heterogeneous
dynamics), not definitional. Pivoting to C(6) before revising
definitions.


### Wave 3 — The other side [BLOCKED on Wave 2]
Measure T_rul. Produce the central scatter plot.

- [ ] src/ruliad/causal_invariance.py (canonical hash test, k=50)
- [ ] src/ruliad/dimensionality.py
- [ ] Extend sweep.py to compute T_rul alongside T_obs
- [ ] First T_obs vs T_rul scatter plot

**Gate:** Is T_obs < T_rul for the majority of rules where both are
finite? If yes, the hypothesis has first contact with evidence. If
no, we have a problem — either the hypothesis is wrong or the rule
class is too small. Try C(6) before giving up.


### Wave 4 — Null model [BLOCKED on Wave 3]
Verify definitions aren't trivially satisfied.

- [ ] src/ruliad/coherence.py
- [ ] Null model generator (configuration model, matched degree sequence)
- [ ] Run observer detection on null graphs
- [ ] Compute P_null, compare to P_obs

**Gate:** Is P_null << P_obs? If not, definitions are too loose.
Tighten and rerun from Wave 2. This is the second most likely
revision point.


### Wave 5 — Counterexamples [BLOCKED on Wave 3]
Populate the failure taxonomy.

- [ ] experiments/counterexamples/obs_without_rul.py
- [ ] experiments/counterexamples/rul_without_obs.py
- [ ] experiments/counterexamples/false_positives.py
- [ ] experiments/counterexamples/borderline/ (specific cases)
- [ ] experiments/counterexamples/notes.md

**Gate:** Do counterexamples reveal a systematic flaw in the
definitions, or are they informative edge cases? If systematic,
revise definitions.md.


### Wave 6 — Robustness [BLOCKED on Wave 4]
Vary thresholds. Does the prevalence gap survive?

- [ ] Parameter sweep: epsilon_B, epsilon_H, epsilon_D, persistence multiplier
- [ ] experiments/comparison/aggregate.py
- [ ] experiments/comparison/threshold_distributions.ipynb
- [ ] Robustness figures

**Gate:** Does the gap survive reasonable parameter variation? If it
collapses under small changes, the claim is fragile — report honestly.


### Wave 7 — Notebooks [BLOCKED on Wave 3]
Public-facing walkthroughs.

- [ ] notebooks/01_see_an_observer.ipynb (one rule, visualized)
- [ ] notebooks/02_the_claim.ipynb (scatter plot, histograms)
- [ ] notebooks/03_game_of_intelligence.ipynb (placeholder until Wave 9)


### Wave 8 — Theory [BLOCKED on Wave 3, partially independent]
Structural arguments. Can begin after first scatter plot exists.

- [ ] theory/local_vs_global.md
- [ ] theory/bootstrapping.md (migrate from Game of Intelligence work)
- [ ] theory/observer_logic.md (descriptive complexity question)
- [ ] theory/open_problems.md (accumulates throughout)


### Wave 9 — Second rule class [BLOCKED on Wave 6]
Generalization test.

- [ ] experiments/directed_graph/engine/ (Game of Intelligence)
- [ ] experiments/directed_graph/sweep.py
- [ ] experiments/directed_graph/config.yaml
- [ ] experiments/directed_graph/analysis.ipynb
- [ ] experiments/hypergraph/sweep.py
- [ ] experiments/hypergraph/config.yaml
- [ ] experiments/hypergraph/analysis.ipynb
- [ ] Cross-class comparison in experiments/comparison/

**Gate:** Does the prevalence gap generalize beyond string rewriting?
Confirmation, not discovery. Report either way.


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

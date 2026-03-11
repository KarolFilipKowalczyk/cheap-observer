# Scaling Estimate: C(6) and C(8)

## Cardinalities

| Class | Total rules | Active | Sterile | Growing | Length-preserving | Shrinking |
|-------|-------------|--------|---------|---------|-------------------|-----------|
| C(4)  | 68          | 20     | 48      | 20      | 4                 | 4         |
| C(6)  | 516         | 174    | 342     | 216     | 84                | 216       |
| C(8)  | 3076        | ~1000* | ~2000*  | 1368    | 340               | 1368      |

*C(8) active count estimated. The ratio active/total is ~34% for C(6);
applying the same ratio to C(8) gives ~1000 active rules.


## Why C(6) is qualitatively different from C(4)

C(4) has only single-symbol LHS rules (|L| = 1). Every occurrence of
the target symbol matches, the match site is always at position 0, and
the string grows uniformly.

C(6) introduces:
- **Multi-symbol matches** (|L| = 2, 3, 4, 5): the LHS may not match
  at every position, so match sites can move across the string.
- **Length-preserving rules** (|L| = |R|): the string stays fixed-length,
  so dynamics must be spatial rather than growth-driven.
- **Shrinking rules with longer LHS** (|L| = 3, |R| = 1): the string
  shrinks, creating competition between match sites.
- **Multi-character rewrites** where L and R share no structure: these
  can produce spatially heterogeneous regions.

The 84 length-preserving rules in C(6) are especially promising: they
cannot produce observers through growth artifacts and must rely on
genuine internal dynamics.


## Time estimates

Based on C(4) profiling: detection cost scales ~O(n^2) in step count
for growing rules. Length-preserving rules have fixed string length, so
detection cost is O(n) in steps.

### C(6) at 1000 steps (conservative first pass)

Growing rules (|L| < |R|): ~3s/rule × ~100 active growing rules = ~5 min
Length-preserving rules: ~0.5s/rule × ~40 active = ~20s
Shrinking rules: <0.5s/rule × ~30 active = ~15s

**Estimated total: ~6 min for C(6) at 1000 steps.**

### C(6) at 5000 steps

Growing rules: ~78s/rule × ~100 = ~2.2 hrs
Length-preserving: ~2.5s/rule × ~40 = ~2 min
Shrinking: ~1s/rule × ~30 = ~30s

**Estimated total: ~2.3 hrs for C(6) at 5000 steps.**

### C(8) at 1000 steps

~3s/rule × ~1000 active = ~50 min

**Estimated total: ~50 min for C(8) at 1000 steps.**


## Recommendation

**Run C(6) first at 1000 steps.** Estimated wall-clock: ~6 minutes.

Rationale:
1. C(6) is the smallest class with multi-symbol matches and
   length-preserving rules — the structural features missing from C(4).
2. 6 minutes is fast enough to iterate: run, inspect, adjust, rerun.
3. If no observers appear at 1000 steps, run length-preserving rules
   at 5000 steps (~2 min) before trying growing rules at 5000 steps.
4. C(8) is a fallback if C(6) also produces no observers.

**Do not run C(8) until C(6) results are understood.** C(8) is 6x
larger and the scaling estimate assumes C(6) detection code is already
optimized (entropy pre-filter, multiprocessing).

# C(8) Threshold Sensitivity Analysis

Pre-Wave-3 robustness check on the two C(8) observers and eight
near-misses. Varies one parameter at a time, holding the others at
defaults (epsilon_B=0.3, epsilon_H=1.0, epsilon_D=0.6,
persistence_multiplier=10).

Tested on 32 rules that passed the entropy filter in the default sweep.
The remaining 994 active rules have frozen entropy (H < 0.01) and
cannot become observers at any reasonable threshold.


## Mirror symmetry correction

The two observers (01->10001, 10->01110) are 0<->1 bit-flip mirrors.
Under bit flip, every symbol swaps, L and R swap correspondingly, and
the evolution is isomorphic. The two rules produce identical scores
(B=0.2446, H=1.5000, D=0.6054, S=1.0), identical T_obs=310, and
identical tau=4.

These are **1 distinct observer structure**, not 2 independent
discoveries. The bit-flip symmetry of binary string rewriting
guarantees that every observer has a mirror partner.

Corrected prevalence:
- P_obs = 2/1026 = 0.195% (counting symmetry partners)
- P_obs = 1/1026 = 0.097% (unique structures)

Both are reported. The 8 near-misses also form 4 mirror pairs.


## 1. Causal decoupling (epsilon_D)

Default: 0.60. The c8_summary.md noted D=0.605, passing by 0.005,
and called this a "knife-edge." The sensitivity data corrects this.

| epsilon_D | 4/4 obs | 3/4 near | Notes                    |
|-----------|---------|----------|--------------------------|
| 0.50      | 4       | 6        | 2 near-misses promoted   |
| 0.52      | 2       | 8        |                          |
| 0.54      | 2       | 8        |                          |
| 0.56      | 2       | 8        |                          |
| 0.58      | 2       | 8        |                          |
| 0.59      | 2       | 8        |                          |
| **0.60**  | **2**   | **8**    | **default**              |
| 0.61      | 2       | 8        |                          |
| 0.62      | 2       | 8        |                          |
| 0.64      | 2       | 8        |                          |
| 0.66      | 2       | 8        |                          |
| 0.68      | 2       | 8        |                          |
| 0.70      | 2       | 8        |                          |

**Critical threshold: above 0.70** (not reached in this scan).

The observers survive across the entire tested range 0.52-0.70. This
is because `scan_all_candidates` evaluates multiple candidate subgraphs
per rule at different spatial widths and time windows. The D=0.605 score
reported in c8_summary.md was for one particular candidate. Other
candidates for the same rule (01->10001) achieve D > 0.70 while still
passing boundary, entropy, and self-reference.

**The "knife-edge" characterization was incorrect.** Causal decoupling
is the MOST robust parameter — the observer count is stable from
D=0.52 to at least D=0.70.

At D=0.50, two near-miss rules are promoted to observers. These are
the near-misses with D=0.500 (01->100011 / 10->011100) which have
candidates that barely clear a 0.50 threshold.


## 2. Boundary stability (epsilon_B)

Default: 0.30. Lower means stricter (boundary must change less).

| epsilon_B | 4/4 obs | 3/4 near | Notes                     |
|-----------|---------|----------|---------------------------|
| 0.15      | 0       | 6        | All fail boundary         |
| 0.20      | 0       | 8        |                           |
| 0.22      | 0       | 8        |                           |
| 0.24      | 0       | 8        |                           |
| **0.25**  | **2**   | **6**    | **observers first appear** |
| 0.26      | 2       | 8        |                           |
| 0.28      | 2       | 8        |                           |
| **0.30**  | **2**   | **8**    | **default**               |
| 0.35      | 6       | 6        | 4 near-misses promoted    |
| 0.40      | 6       | 9        |                           |

**Critical threshold: epsilon_B = 0.25** (observers first appear).

The observer's best boundary score is B=0.2446. It passes at
epsilon_B >= 0.25 (since 0.2446 < 0.25). Below that, no observer
exists in C(8).

Boundary stability is the **tightest epsilon parameter**. The observer
needs epsilon_B at least 0.25 — a 17% margin below the 0.30 default.

At epsilon_B >= 0.35, four additional rules cross the boundary
threshold and become observers. These have B scores between 0.25 and
0.35.


## 3. Internal entropy (epsilon_H)

Default: 1.0 bit. Higher means stricter (more internal activity
required).

| epsilon_H | 4/4 obs | 3/4 near | Notes                    |
|-----------|---------|----------|--------------------------|
| 0.50      | 2       | 9        |                          |
| 0.75      | 2       | 9        |                          |
| **1.00**  | **2**   | **8**    | **default**              |
| 1.25      | 2       | 8        |                          |
| **1.50**  | **0**   | **10**   | **observers lost**       |
| 1.75      | 0       | 6        |                          |
| 2.00      | 0       | 4        |                          |

**Critical threshold: epsilon_H = 1.50** (observers lost).

The observers have H=1.5000 bits. The pass condition is strict
inequality (H > epsilon_H), so H=1.5000 does not pass at
epsilon_H=1.50. Observers survive across 0.50-1.25 (a 3x range).

Internal entropy is **moderately sensitive**. The observer has a 50%
margin above the default threshold (1.5 vs 1.0).


## 4. Persistence multiplier

Default: 10 (window = 10 * tau = 40 steps at tau=4).

| Multiplier | 4/4 obs | 3/4 near | Window (tau=4) | Notes         |
|------------|---------|----------|----------------|---------------|
| 5          | 4       | 24       | 20 steps       |               |
| 8          | 6       | 6        | 32 steps       | **peak obs**  |
| **10**     | **2**   | **8**    | **40 steps**   | **default**   |
| 12         | 0       | 8        | 48 steps       | observers lost|
| 15         | 0       | 4        | 60 steps       |               |
| 20         | 0       | 0        | 80 steps       | all lost      |

**Critical threshold: persistence_multiplier = 12** (observers lost).

Persistence is the **most sensitive parameter overall**. The observers
exist only in the narrow band P=5 to P=10. At P=8, the observer count
peaks at 6 (three mirror pairs). At P=12, zero observers survive.

At P=5 (window=20 steps), 4 observers but 24 near-misses — the short
window is easier to satisfy, producing many more marginal candidates.

At P=20 (window=80 steps), zero observers AND zero near-misses. No
structure in C(8) can sustain all four criteria for 80 steps.


## Summary: robustness assessment

| Parameter       | Default | Observer range    | Margin           |
|-----------------|---------|-------------------|------------------|
| epsilon_D       | 0.60    | 0.52 – >0.70      | wide (robust)    |
| epsilon_B       | 0.30    | 0.25 – 0.30+      | 17% below default|
| epsilon_H       | 1.00    | <0.50 – 1.25      | 50% above default|
| persistence     | 10      | 5 – 10            | at boundary      |

**Assessment: the C(8) observer is MODERATELY ROBUST.**

It is NOT a knife-edge artifact of a single threshold setting. The
observer survives across meaningful ranges of all four parameters:

- **Causal decoupling** is the most robust axis: flat from 0.52 to
  at least 0.70. The initial characterization as "knife-edge at
  D=0.605" was misleading — that was one candidate's score, not the
  structure's limit.

- **Boundary stability** and **internal entropy** provide moderate
  margins. The observer needs epsilon_B >= 0.25 and epsilon_H <= 1.25.

- **Persistence multiplier** is the tightest constraint. The observer
  exists at P=5-10 but not P=12+. This means the observer structure
  persists for 40 steps but not 48 — it is a transient coherent
  structure, not a permanent one. This is consistent with the
  sawtooth dynamics: the match site drifts by ~13 positions per
  persistence window, eventually outrunning the subgraph.

The fact that P=8 yields 6 observers (vs 2 at default P=10) suggests
the default persistence requirement may be slightly too strict for
C(8). The structures have genuine self-referential dynamics but
limited persistence due to their drift rate.


## Implications for Wave 3

1. **Proceed with default thresholds.** The observer is real and
   survives reasonable perturbation.

2. **Report P_obs with symmetry correction.** P_obs = 1/1026 (unique)
   or 2/1026 (counting mirrors). The 8 near-misses are 4 unique
   structures.

3. **Persistence is the bottleneck for C(8).** If C(10)+ produces
   observers with slower drift (lower net velocity), they may sustain
   longer persistence windows and be more robust.

4. **Decoupling is not the bottleneck.** Despite the initial D=0.605
   scare, the observer structure achieves high decoupling across
   multiple candidate subgraphs. The bottleneck is spatial persistence,
   not causal autonomy.

5. **Falsification check (definitions.md Claim 10.4):** the observer
   survives "reasonable variation of the thresholds." The weakest axis
   (persistence) reflects a genuine physical property (drift-limited
   persistence) rather than a tuning artifact.

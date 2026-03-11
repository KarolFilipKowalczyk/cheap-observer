"""
Causal decoupling criterion (definitions.md Section 5.3).

Measures how much of the subgraph's future is predicted by its own past
vs the external environment. The decoupling ratio must exceed epsilon_D
(default 0.6) to pass.

    I_int / (I_int + I_ext) > epsilon_D

Uses plug-in MI with Miller-Madow correction for short states (<=20
symbols), and normalized compression distance (NCD) for longer states.
"""

from __future__ import annotations

import math
import zlib
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.spark.evolution_graph import SubgraphView


# ---------------------------------------------------------------------------
# Mutual information estimators
# ---------------------------------------------------------------------------

def _plugin_mi_miller_madow(xs: list[str], ys: list[str]) -> float:
    """Plug-in mutual information estimator with Miller-Madow bias correction.

    MI(X; Y) = H(X) + H(Y) - H(X, Y) with bias correction term
    (k - 1) / (2n) where k is the number of bins with non-zero count
    and n is the sample size.

    Args:
        xs: List of X observations (strings).
        ys: List of Y observations (strings).

    Returns:
        Estimated mutual information in bits, floored at 0.
    """
    n = len(xs)
    if n == 0:
        return 0.0

    # Joint and marginal counts
    joint = Counter(zip(xs, ys))
    cx = Counter(xs)
    cy = Counter(ys)

    def _entropy_with_correction(counts: Counter, n: int) -> float:
        k = len(counts)
        h = 0.0
        for c in counts.values():
            p = c / n
            if p > 0:
                h -= p * math.log2(p)
        # Miller-Madow correction
        h += (k - 1) / (2 * n * math.log(2))
        return h

    h_x = _entropy_with_correction(cx, n)
    h_y = _entropy_with_correction(cy, n)
    h_xy = _entropy_with_correction(joint, n)

    mi = h_x + h_y - h_xy
    return max(mi, 0.0)


def _ncd(x: str, y: str) -> float:
    """Normalized compression distance between two strings.

    NCD(x, y) = (C(xy) - min(C(x), C(y))) / max(C(x), C(y))

    See definitions.md Section 5.3.
    """
    bx = x.encode("utf-8")
    by = y.encode("utf-8")
    cx = len(zlib.compress(bx, 9))
    cy = len(zlib.compress(by, 9))
    cxy = len(zlib.compress(bx + by, 9))

    denom = max(cx, cy)
    if denom == 0:
        return 0.0
    return (cxy - min(cx, cy)) / denom


# ---------------------------------------------------------------------------
# Decoupling score
# ---------------------------------------------------------------------------

def _external_state(subgraph: SubgraphView, t: int) -> str:
    """The complement of the subgraph's internal state at time t."""
    inside = subgraph.position_set_at_time(t)
    full = subgraph.parent_graph.strings[t]
    return "".join(full[i] for i in range(len(full)) if i not in inside)


def causal_decoupling_score(
    subgraph: SubgraphView, t_start: int, t_end: int, tau: int
) -> float:
    """Compute causal decoupling per definitions.md Section 5.3.

    For each valid time offset t in [t_start, t_end - tau], collects
    (internal(t), internal(t+tau)) and (internal(t), external(t+tau)).
    Computes the decoupling ratio I_int / (I_int + I_ext).

    Uses plug-in MI with Miller-Madow correction when internal states
    are at most 20 symbols. Uses NCD for longer states.

    Args:
        subgraph: The candidate observer subgraph.
        t_start: First time step (inclusive).
        t_end: Last time step (inclusive).
        tau: Characteristic time, used as temporal offset.

    Returns:
        Decoupling ratio in [0, 1]. Higher means more self-determined.
    """
    if tau <= 0 or t_end - t_start < tau:
        return 0.0

    # Collect state pairs
    int_now: list[str] = []
    int_future: list[str] = []
    ext_future: list[str] = []

    for t in range(t_start, t_end - tau + 1):
        int_now.append(subgraph.internal_state_at_time(t))
        int_future.append(subgraph.internal_state_at_time(t + tau))
        ext_future.append(_external_state(subgraph, t + tau))

    if not int_now:
        return 0.0

    # Choose estimator based on internal state length
    max_state_len = max(len(s) for s in int_now)

    if max_state_len <= 20:
        # Plug-in MI with Miller-Madow
        i_int = _plugin_mi_miller_madow(int_now, int_future)
        i_ext = _plugin_mi_miller_madow(int_now, ext_future)
    else:
        # NCD-based proxy
        # Average over all time pairs
        sim_int_total = 0.0
        sim_ext_total = 0.0
        n = len(int_now)
        for idx in range(n):
            sim_int_total += 1.0 - _ncd(int_now[idx], int_future[idx])
            sim_ext_total += 1.0 - _ncd(int_now[idx], ext_future[idx])
        i_int = sim_int_total / n
        i_ext = sim_ext_total / n

    denom = i_int + i_ext
    if denom < 1e-15:
        return 0.5  # No information either way

    return i_int / denom


# ---------------------------------------------------------------------------
# __main__
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from src.spark.rule_classes.string_rewriting import StringRewritingRule
    from src.spark.seed_search import find_minimal_seed
    from src.spark.evolution_graph import StringEvolutionGraph
    from src.spark.characteristic_time import characteristic_time

    rule = StringRewritingRule("1", "010")
    seed = find_minimal_seed(rule)
    print(f"Rule: {rule}  |  Seed: {seed!r}")

    graph = StringEvolutionGraph(rule, seed)
    graph.evolve(500)
    tau = characteristic_time(graph)
    print(f"Steps: {graph.n_steps_evolved}  |  tau: {tau}")

    configs = [
        ("fixed [2,8) t=[50,150)", 2, 8, 50, 150),
        ("narrow [3,5) t=[50,150)", 3, 5, 50, 150),
        ("wide [0,15) t=[50,150)", 0, 15, 50, 150),
        ("left edge [0,3) t=[10,60)", 0, 3, 10, 60),
    ]

    for label, ps, pe, ts, te in configs:
        sg = graph.get_subgraph(pos_start=ps, pos_end=pe, time_start=ts, time_end=te)

        # Check which estimator will be used
        sample_state = sg.internal_state_at_time(ts)
        estimator = "MI+MM" if len(sample_state) <= 20 else "NCD"

        score = causal_decoupling_score(sg, ts, te, tau)
        print(f"  {label}: decoupling = {score:.4f} ({estimator})"
              f"  {'PASS' if score > 0.6 else 'FAIL'} (> 0.6)")

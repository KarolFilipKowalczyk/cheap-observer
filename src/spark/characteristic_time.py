"""
Characteristic time (tau) computation.

The characteristic time tau measures the natural timescale of a spark's
evolution. It is the smallest lag k where the autocorrelation of the
normalized Hamming distance series drops below 1/e. If the series is
periodic, tau is set to the period length.

See definitions.md Section 4.
"""

from __future__ import annotations

import math

import numpy as np

from src.spark.evolution_graph import StringEvolutionGraph


def normalized_hamming_distances(graph: StringEvolutionGraph) -> np.ndarray:
    """Compute d(t) = normalized Hamming distance between s_t and s_{t+1}.

    For strings of equal length, this is the fraction of positions that
    differ. For strings of different length (when |L| != |R|), positions
    beyond the shorter string are counted as all differing, and the
    result is normalized by the maximum of the two lengths.

    See definitions.md Section 4: "Compute the Hamming distance d(t)
    between consecutive strings s_t and s_{t+1} for each step, normalized
    by string length."

    Args:
        graph: An evolved StringEvolutionGraph.

    Returns:
        1D float64 array of length n_steps_evolved, where d[t] is the
        normalized distance between strings at time t and t+1.
    """
    n = graph.n_steps_evolved
    if n == 0:
        return np.array([], dtype=np.float64)

    d = np.empty(n, dtype=np.float64)
    for t in range(n):
        s_t = graph.strings[t]
        s_t1 = graph.strings[t + 1]
        len_t = len(s_t)
        len_t1 = len(s_t1)
        max_len = max(len_t, len_t1)

        if max_len == 0:
            d[t] = 0.0
            continue

        min_len = min(len_t, len_t1)
        mismatches = sum(
            1 for i in range(min_len) if s_t[i] != s_t1[i]
        )
        mismatches += abs(len_t1 - len_t)
        d[t] = mismatches / max_len

    return d


def autocorrelation(series: np.ndarray, max_lag: int | None = None) -> np.ndarray:
    """Compute the autocorrelation function of a 1D time series.

    Uses the standard definition: autocorr(k) = corr(x(t), x(t+k)),
    which is the Pearson correlation between the series and its
    k-shifted copy.

    Args:
        series: 1D float array.
        max_lag: Maximum lag to compute. Defaults to len(series) // 2.

    Returns:
        1D array where result[k] is the autocorrelation at lag k.
        result[0] = 1.0 by definition.
    """
    n = len(series)
    if n < 2:
        return np.array([1.0])

    if max_lag is None:
        max_lag = n // 2
    max_lag = min(max_lag, n - 1)

    mean = np.mean(series)
    var = np.var(series)

    if var < 1e-15:
        # Constant series: autocorrelation is 1.0 at all lags
        return np.ones(max_lag + 1, dtype=np.float64)

    centered = series - mean
    ac = np.empty(max_lag + 1, dtype=np.float64)
    ac[0] = 1.0

    for k in range(1, max_lag + 1):
        ac[k] = np.dot(centered[:n - k], centered[k:]) / (n * var)

    return ac


def detect_period(series: np.ndarray, ac: np.ndarray) -> int | None:
    """Detect the period of a quasi-periodic series from its autocorrelation.

    Finds the first lag > 0 where the autocorrelation has a local maximum
    above 1/e. This indicates a dominant period in the signal.

    Args:
        series: The original time series.
        ac: Its autocorrelation function.

    Returns:
        The detected period length, or None if no periodicity found.
    """
    threshold = 1.0 / math.e
    n = len(ac)

    # Look for first local maximum above threshold after lag 0
    for k in range(2, n - 1):
        if ac[k] > threshold and ac[k] >= ac[k - 1] and ac[k] >= ac[k + 1]:
            return k

    return None


def characteristic_time(graph: StringEvolutionGraph) -> int:
    """Compute tau, the characteristic time of a spark's evolution.

    The characteristic time is the smallest lag k such that the
    autocorrelation of the normalized Hamming distance series drops
    below 1/e.

    If the autocorrelation never drops below 1/e (periodic or highly
    regular dynamics), tau is set to the detected period length. If no
    period is detected either, tau defaults to 1 (the minimum
    meaningful timescale).

    See definitions.md Section 4.

    Args:
        graph: An evolved StringEvolutionGraph with at least a few steps.

    Returns:
        tau as a positive integer (at least 1).
    """
    d = normalized_hamming_distances(graph)

    if len(d) < 2:
        return 1

    ac = autocorrelation(d)
    threshold = 1.0 / math.e

    # Find first lag where autocorrelation drops below 1/e
    for k in range(1, len(ac)):
        if ac[k] < threshold:
            return max(k, 1)

    # Autocorrelation never drops: periodic dynamics.
    # Set tau to the period length.
    period = detect_period(d, ac)
    if period is not None:
        return period

    # Fallback: constant or near-constant dynamics
    return 1


# ---------------------------------------------------------------------------
# __main__: compute tau for active C(4) rules
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from src.spark.rule_classes.string_rewriting import StringRewritingRule
    from src.spark.seed_search import find_minimal_seed
    from src.spark.evolution_graph import StringEvolutionGraph

    N_STEPS = 1000

    # Collect all active rules from C(4)
    active_rules = []
    for rule in StringRewritingRule.enumerate(4):
        seed = find_minimal_seed(rule)
        if seed is not None:
            active_rules.append((rule, seed))

    print(f"Active rules in C(4): {len(active_rules)}")
    print(f"Evolving each for {N_STEPS} steps...\n")

    print(f"  {'rule':>12}  {'seed':>4}  {'steps':>5}  "
          f"{'|s_final|':>9}  {'tau':>4}  {'mean d(t)':>9}  {'std d(t)':>9}")
    print(f"  {'-' * 65}")

    for rule, seed in active_rules:
        graph = StringEvolutionGraph(rule, seed)
        graph.evolve(N_STEPS)

        tau = characteristic_time(graph)
        d = normalized_hamming_distances(graph)

        steps = graph.n_steps_evolved
        final_len = graph.string_length_at_time(steps)
        mean_d = float(np.mean(d)) if len(d) > 0 else 0.0
        std_d = float(np.std(d)) if len(d) > 0 else 0.0

        print(f"  {str(rule):>12}  {seed:>4}  {steps:>5}  "
              f"{final_len:>9}  {tau:>4}  {mean_d:>9.4f}  {std_d:>9.4f}")

    # Detailed view of one rule
    print("\n" + "=" * 60)
    print("Detailed view: 0 -> 011")
    print("=" * 60)

    rule = StringRewritingRule("0", "011")
    seed = find_minimal_seed(rule)
    graph = StringEvolutionGraph(rule, seed)
    graph.evolve(N_STEPS)

    tau = characteristic_time(graph)
    d = normalized_hamming_distances(graph)
    ac = autocorrelation(d, max_lag=min(50, len(d) // 2))

    print(f"  Rule: {rule}  |  Seed: {seed!r}")
    print(f"  Steps evolved: {graph.n_steps_evolved}")
    print(f"  Final string length: {graph.string_length_at_time(graph.n_steps_evolved)}")
    print(f"  tau = {tau}")
    print(f"\n  String length at selected steps:")
    for t in [0, 10, 50, 100, 200, 500, min(999, graph.n_steps_evolved)]:
        if t <= graph.n_steps_evolved:
            print(f"    t={t:>4}: |s| = {graph.string_length_at_time(t)}")

    print(f"\n  Autocorrelation (first 20 lags):")
    for k in range(min(20, len(ac))):
        bar = "#" * int(max(0, ac[k]) * 40)
        marker = " <-- tau" if k == tau else ""
        print(f"    k={k:>2}: {ac[k]:>7.3f}  {bar}{marker}")

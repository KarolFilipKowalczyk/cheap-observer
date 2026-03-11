"""
End-to-end test: enumerate C(4) -> find minimal sparks -> build evolution
graphs -> compute tau -> run observer detection -> report T_obs.

This is our first real contact with the data. If T_obs comes back
finite for even one rule in C(4), we have contact.

Usage:
    py -m experiments.string_rewriting.test_single_rule
    py -m experiments.string_rewriting.test_single_rule --steps 5000
    py -m experiments.string_rewriting.test_single_rule --rule "0 -> 011"
"""

from __future__ import annotations

import argparse
import sys
import time

from src.spark.rule_classes.string_rewriting import StringRewritingRule
from src.spark.seed_search import find_minimal_seed
from src.spark.evolution_graph import StringEvolutionGraph
from src.spark.characteristic_time import characteristic_time
from src.observer.definition import ObserverCriteria, DEFAULT_CRITERIA
from src.observer.detect import detect_observers, scan_all_candidates
from src.observer.spectrum import classify_subgraph, spectrum_summary, SpectrumResult


def run_single_rule(
    rule: StringRewritingRule,
    seed: str,
    n_steps: int = 10000,
    criteria: ObserverCriteria = DEFAULT_CRITERIA,
    verbose: bool = True,
) -> tuple[int | None, list[SpectrumResult]]:
    """Full pipeline for one rule.

    Returns:
        (T_obs or None, list of spectrum results for all candidates)
    """
    if verbose:
        print(f"\n{'=' * 64}")
        print(f"  Rule: {rule}  |  Seed: {seed!r}")
        print(f"{'=' * 64}")

    # 1. Build evolution graph
    t0 = time.time()
    graph = StringEvolutionGraph(rule, seed)
    graph.evolve(n_steps)
    evolve_time = time.time() - t0

    actual_steps = graph.n_steps_evolved
    final_len = graph.string_length_at_time(actual_steps)

    if verbose:
        print(f"  Evolved {actual_steps} steps in {evolve_time:.2f}s")
        print(f"  String length: {len(seed)} -> {final_len}")

    # 2. Compute tau
    tau = characteristic_time(graph)
    min_window = criteria.persistence_multiplier * tau

    if verbose:
        print(f"  tau = {tau}  |  min persistence window = {min_window} steps")

    if actual_steps < min_window:
        if verbose:
            print(f"  SKIP: evolution too short ({actual_steps} < {min_window})")
        return None, []

    # 3. Detect observers
    if verbose:
        print(f"\n  --- Observer detection ---")

    t0 = time.time()
    observers = detect_observers(graph, tau, criteria, verbose=verbose)
    detect_time = time.time() - t0

    t_obs: int | None = None
    if observers:
        t_obs = observers[0].t_window_start
        if verbose:
            print(f"\n  T_obs = {t_obs}  ({len(observers)} observer(s) found)")
            print(f"  Detection time: {detect_time:.2f}s")
            for i, obs in enumerate(observers[:3]):
                print(f"\n  Observer {i+1}:")
                report = obs.criteria_report(criteria)
                for name, (score, passed) in report.items():
                    tag = "PASS" if passed else "FAIL"
                    print(f"    {name}: {score:.4f}  {tag}")
    else:
        if verbose:
            print(f"\n  No observer found. T_obs = infinity")
            print(f"  Detection time: {detect_time:.2f}s")

    # 4. Spectrum analysis: score all candidates for near-misses
    if verbose:
        print(f"\n  --- Spectrum analysis ---")

    t0 = time.time()
    all_scored = scan_all_candidates(graph, tau, criteria, verbose=verbose)
    spec_time = time.time() - t0

    spectra = []
    for scored in all_scored:
        sr = SpectrumResult(
            boundary_score=scored.boundary,
            entropy_score=scored.entropy,
            decoupling_score=scored.decoupling,
            self_ref_score=scored.self_ref,
            boundary_pass=scored.boundary < criteria.epsilon_B,
            entropy_pass=scored.entropy > criteria.epsilon_H,
            decoupling_pass=scored.decoupling > criteria.epsilon_D,
            self_ref_pass=scored.self_ref >= 1.0,
        )
        spectra.append(sr)

    if verbose:
        print(spectrum_summary(spectra))
        print(f"  Spectrum time: {spec_time:.2f}s")

    return t_obs, spectra


def run_all_c4(n_steps: int = 10000, verbose: bool = True) -> None:
    """Run the full pipeline on all active rules in C(4)."""
    print(f"{'#' * 64}")
    print(f"  cheap-observer: C(4) sweep")
    print(f"  {n_steps} evolution steps per rule")
    print(f"{'#' * 64}")

    # Find all active rules
    active: list[tuple[StringRewritingRule, str]] = []
    for rule in StringRewritingRule.enumerate(4):
        seed = find_minimal_seed(rule)
        if seed is not None:
            active.append((rule, seed))

    print(f"\n  Active rules in C(4): {len(active)}")

    # Results tracking
    results: dict[str, int | None] = {}
    best_near_miss: tuple[str, int, SpectrumResult | None] = ("", 0, None)

    total_t0 = time.time()

    for rule, seed in active:
        t_obs, spectra = run_single_rule(
            rule, seed, n_steps=n_steps, verbose=verbose,
        )
        results[str(rule)] = t_obs

        # Track best near-miss
        for sr in spectra:
            if not sr.is_observer and sr.n_passed > best_near_miss[1]:
                best_near_miss = (str(rule), sr.n_passed, sr)

    total_time = time.time() - total_t0

    # Final summary
    print(f"\n{'#' * 64}")
    print(f"  SUMMARY")
    print(f"{'#' * 64}")

    finite = {r: t for r, t in results.items() if t is not None}
    infinite = {r: t for r, t in results.items() if t is None}

    print(f"\n  Rules with T_obs finite:   {len(finite)} / {len(results)}")
    print(f"  Rules with T_obs infinite: {len(infinite)} / {len(results)}")

    if finite:
        print(f"\n  Observers found:")
        for rule_str, t_obs in sorted(finite.items(), key=lambda x: x[1]):
            print(f"    {rule_str}: T_obs = {t_obs}")
    else:
        print(f"\n  No observers found in C(4) at {n_steps} steps.")

    if best_near_miss[2] is not None:
        print(f"\n  Best near-miss across all rules:")
        print(f"    Rule: {best_near_miss[0]}")
        print(best_near_miss[2].summary())

    print(f"\n  Total time: {total_time:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="End-to-end observer detection for string rewriting rules"
    )
    parser.add_argument(
        "--steps", type=int, default=10000,
        help="Evolution steps per rule (default: 10000)"
    )
    parser.add_argument(
        "--rule", type=str, default=None,
        help="Test a single rule, e.g. '0 -> 011'"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-candidate output"
    )
    args = parser.parse_args()

    if args.rule:
        # Parse "L -> R" format
        parts = args.rule.split("->")
        if len(parts) != 2:
            print(f"Invalid rule format: {args.rule!r}. Use 'L -> R'.")
            sys.exit(1)
        L = parts[0].strip()
        R = parts[1].strip()
        rule = StringRewritingRule(L, R)
        seed = find_minimal_seed(rule)
        if seed is None:
            print(f"Rule {rule} is sterile (no non-trivial evolution found).")
            sys.exit(1)
        run_single_rule(rule, seed, n_steps=args.steps, verbose=not args.quiet)
    else:
        run_all_c4(n_steps=args.steps, verbose=not args.quiet)


if __name__ == "__main__":
    main()

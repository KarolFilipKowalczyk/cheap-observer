"""
C(8) threshold sensitivity check with live GUI.

Varies one parameter at a time (epsilon_D, epsilon_B, epsilon_H,
persistence_multiplier) while holding others at defaults. Reports
observer count and 3/4 near-miss count at each value.

For epsilon parameters: scores are threshold-independent, so we collect
all candidate scores once and re-threshold instantly.
For persistence_multiplier: window size affects candidate generation,
so we re-run detection for each value.

Usage:
    python -m experiments.string_rewriting.sensitivity
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from multiprocessing import freeze_support
from pathlib import Path
from threading import Thread

from src.spark.rule_classes.string_rewriting import StringRewritingRule
from src.spark.seed_search import find_minimal_seed
from src.spark.evolution_graph import StringEvolutionGraph
from src.spark.characteristic_time import characteristic_time
from src.observer.definition import ObserverCriteria
from src.observer.detect import (
    detect_observers,
    scan_all_candidates,
    ScoredCandidate,
)


# ---------------------------------------------------------------------------
# Parameter grids
# ---------------------------------------------------------------------------

EPSILON_D_VALUES = [0.50, 0.52, 0.54, 0.56, 0.58, 0.59, 0.60, 0.61, 0.62,
                    0.64, 0.66, 0.68, 0.70]
EPSILON_B_VALUES = [0.15, 0.20, 0.22, 0.24, 0.25, 0.26, 0.28, 0.30, 0.35,
                    0.40]
EPSILON_H_VALUES = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
PERSISTENCE_VALUES = [5, 8, 10, 12, 15, 20]

DEFAULTS = ObserverCriteria(
    epsilon_B=0.3, epsilon_H=1.0, epsilon_D=0.6, persistence_multiplier=10
)

STEPS = 1000
TOTAL_JOBS = (len(EPSILON_D_VALUES) + len(EPSILON_B_VALUES)
              + len(EPSILON_H_VALUES) + len(PERSISTENCE_VALUES))


# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

@dataclass
class SensitivityRow:
    parameter: str
    value: float
    observers: int
    near_misses: int


@dataclass
class SensitivityState:
    phase: str = "init"           # init, evolving, scoring, epsilon_D, ...
    total_jobs: int = TOTAL_JOBS
    completed_jobs: int = 0
    n_rules: int = 0
    current_detail: str = ""
    elapsed: float = 0.0
    rows: list[SensitivityRow] = field(default_factory=list)
    log_lines: list[str] = field(default_factory=list)
    done: bool = False


# ---------------------------------------------------------------------------
# Data loading and evolution
# ---------------------------------------------------------------------------

def _load_interesting_rules() -> list[tuple[str, str]]:
    """Rules that scored >= 1/4 in the default C(8) sweep."""
    raw_path = Path(__file__).parent / "results" / "c8_raw.json"
    with open(raw_path) as f:
        data = json.load(f)
    rules = []
    for r in data["rules"]:
        if r["sterile"]:
            continue
        if r["best_n_passed"] >= 1 or r.get("t_obs") is not None:
            rules.append((r["L"], r["R"]))
    return rules


def _evolve_rules(
    rules: list[tuple[str, str]], state: SensitivityState,
) -> list[tuple[str, str, StringEvolutionGraph, int]]:
    results = []
    for i, (L, R) in enumerate(rules):
        state.current_detail = f"Evolving {L}->{R} ({i+1}/{len(rules)})"
        rule = StringRewritingRule(L, R)
        seed = find_minimal_seed(rule)
        if seed is None:
            continue
        graph = StringEvolutionGraph(rule, seed)
        graph.evolve(STEPS)
        tau = characteristic_time(graph)
        results.append((L, R, graph, tau))
    return results


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _count_from_cached(
    candidates_by_rule: dict[str, list[ScoredCandidate]],
    criteria: ObserverCriteria,
) -> tuple[int, int]:
    n_obs = 0
    n_near = 0
    for candidates in candidates_by_rule.values():
        best_n = 0
        is_obs = False
        for sc in candidates:
            n = sc.n_criteria_passed(criteria)
            if n == 4:
                is_obs = True
                break
            if n > best_n:
                best_n = n
        if is_obs:
            n_obs += 1
        elif best_n >= 3:
            n_near += 1
    return n_obs, n_near


def _count_with_persistence(
    evolved: list[tuple[str, str, StringEvolutionGraph, int]],
    pm: int,
) -> tuple[int, int]:
    criteria = ObserverCriteria(
        epsilon_B=DEFAULTS.epsilon_B, epsilon_H=DEFAULTS.epsilon_H,
        epsilon_D=DEFAULTS.epsilon_D, persistence_multiplier=pm,
    )
    n_obs = 0
    n_near = 0
    for L, R, graph, tau in evolved:
        observers = detect_observers(graph, tau, criteria)
        if observers:
            n_obs += 1
        else:
            all_scored = scan_all_candidates(graph, tau, criteria)
            best_n = max(
                (sc.n_criteria_passed(criteria) for sc in all_scored),
                default=0,
            )
            if best_n >= 3:
                n_near += 1
    return n_obs, n_near


# ---------------------------------------------------------------------------
# Work thread
# ---------------------------------------------------------------------------

def _work_thread(state: SensitivityState) -> None:
    t0 = time.time()

    # 1. Load and evolve
    state.phase = "evolving"
    rules = _load_interesting_rules()
    state.n_rules = len(rules)
    state.log_lines.append(f"Loaded {len(rules)} interesting rules from C(8)")

    evolved = _evolve_rules(rules, state)
    state.elapsed = time.time() - t0
    state.log_lines.append(f"Evolved {len(evolved)} rules in {state.elapsed:.1f}s")

    # 2. Collect all candidate scores at default persistence
    state.phase = "scoring"
    state.current_detail = "Scoring all candidates at default settings..."
    candidates_by_rule: dict[str, list[ScoredCandidate]] = {}
    for L, R, graph, tau in evolved:
        key = f"{L}->{R}"
        candidates_by_rule[key] = scan_all_candidates(graph, tau, DEFAULTS)
    total_cands = sum(len(v) for v in candidates_by_rule.values())
    state.elapsed = time.time() - t0
    state.log_lines.append(
        f"Scored {total_cands} candidates across {len(candidates_by_rule)} rules"
    )

    # 3. epsilon_D sweep (re-threshold cached scores)
    state.phase = "epsilon_D"
    for ed in EPSILON_D_VALUES:
        state.current_detail = f"epsilon_D = {ed:.2f}"
        criteria = ObserverCriteria(
            epsilon_B=DEFAULTS.epsilon_B, epsilon_H=DEFAULTS.epsilon_H,
            epsilon_D=ed, persistence_multiplier=DEFAULTS.persistence_multiplier,
        )
        n_obs, n_near = _count_from_cached(candidates_by_rule, criteria)
        row = SensitivityRow("epsilon_D", ed, n_obs, n_near)
        state.rows.append(row)
        state.completed_jobs += 1
        state.elapsed = time.time() - t0
        tag = " <-- default" if ed == 0.60 else ""
        state.log_lines.append(
            f"  D={ed:.2f}: {n_obs} obs, {n_near} near-miss{tag}"
        )

    # 4. epsilon_B sweep
    state.phase = "epsilon_B"
    for eb in EPSILON_B_VALUES:
        state.current_detail = f"epsilon_B = {eb:.2f}"
        criteria = ObserverCriteria(
            epsilon_B=eb, epsilon_H=DEFAULTS.epsilon_H,
            epsilon_D=DEFAULTS.epsilon_D,
            persistence_multiplier=DEFAULTS.persistence_multiplier,
        )
        n_obs, n_near = _count_from_cached(candidates_by_rule, criteria)
        row = SensitivityRow("epsilon_B", eb, n_obs, n_near)
        state.rows.append(row)
        state.completed_jobs += 1
        state.elapsed = time.time() - t0
        tag = " <-- default" if eb == 0.30 else ""
        state.log_lines.append(
            f"  B={eb:.2f}: {n_obs} obs, {n_near} near-miss{tag}"
        )

    # 5. epsilon_H sweep
    state.phase = "epsilon_H"
    for eh in EPSILON_H_VALUES:
        state.current_detail = f"epsilon_H = {eh:.2f}"
        criteria = ObserverCriteria(
            epsilon_B=DEFAULTS.epsilon_B, epsilon_H=eh,
            epsilon_D=DEFAULTS.epsilon_D,
            persistence_multiplier=DEFAULTS.persistence_multiplier,
        )
        n_obs, n_near = _count_from_cached(candidates_by_rule, criteria)
        row = SensitivityRow("epsilon_H", eh, n_obs, n_near)
        state.rows.append(row)
        state.completed_jobs += 1
        state.elapsed = time.time() - t0
        tag = " <-- default" if eh == 1.00 else ""
        state.log_lines.append(
            f"  H={eh:.2f}: {n_obs} obs, {n_near} near-miss{tag}"
        )

    # 6. persistence_multiplier sweep (re-runs detection)
    state.phase = "persistence"
    for pm in PERSISTENCE_VALUES:
        state.current_detail = f"persistence = {pm}"
        n_obs, n_near = _count_with_persistence(evolved, pm)
        row = SensitivityRow("persistence", float(pm), n_obs, n_near)
        state.rows.append(row)
        state.completed_jobs += 1
        state.elapsed = time.time() - t0
        tag = " <-- default" if pm == 10 else ""
        state.log_lines.append(
            f"  P={pm:2d}: {n_obs} obs, {n_near} near-miss{tag}"
        )

    # 7. Save results
    output_path = Path(__file__).parent / "results" / "c8_sensitivity.json"
    data = {}
    for row in state.rows:
        data.setdefault(row.parameter, []).append({
            "value": row.value,
            "observers": row.observers,
            "near_misses": row.near_misses,
        })
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    state.log_lines.append(f"\nResults saved to {output_path}")
    state.log_lines.append(f"Total time: {state.elapsed:.1f}s")
    state.done = True


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

def _fmt_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{int(m)}m {int(s)}s"
    else:
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{int(h)}h {int(m)}m"


def _try_gui(state: SensitivityState) -> None:
    try:
        import tkinter as tk
        from tkinter import scrolledtext
    except Exception:
        return

    try:
        root = tk.Tk()
        root.title("cheap-observer: C(8) sensitivity check")
        root.geometry("900x550")
        root.resizable(True, True)
    except Exception:
        return

    try:
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Progress bar
        bar_canvas = tk.Canvas(frame, height=24, bg="#e0e0e0",
                               highlightthickness=0)
        bar_canvas.pack(fill=tk.X, pady=(0, 6))
        bar_fill = bar_canvas.create_rectangle(0, 0, 0, 24, fill="#4a90d9",
                                               outline="")
        bar_text = bar_canvas.create_text(450, 12, text="0 / 0",
                                          font=("Consolas", 10))

        # Info labels
        info_frame = tk.Frame(frame)
        info_frame.pack(fill=tk.X, pady=(0, 6))

        lbl_time = tk.Label(info_frame, text="Elapsed: 0s  |  Remaining: --",
                            font=("Consolas", 10), anchor="w")
        lbl_time.pack(side=tk.LEFT)

        lbl_phase = tk.Label(info_frame, text="Phase: init",
                             font=("Consolas", 10), anchor="e")
        lbl_phase.pack(side=tk.RIGHT)

        # Tally
        lbl_tally = tk.Label(
            frame, text="Parameter: --  |  Current: --",
            font=("Consolas", 10), anchor="w",
        )
        lbl_tally.pack(fill=tk.X, pady=(0, 6))

        # Summary (turns green when done)
        lbl_summary = tk.Label(frame, text="", font=("Consolas", 11, "bold"),
                               anchor="w")
        lbl_summary.pack(fill=tk.X, pady=(0, 4))

        # Log
        log = scrolledtext.ScrolledText(frame, font=("Consolas", 9),
                                        height=18, state=tk.DISABLED)
        log.pack(fill=tk.BOTH, expand=True)
    except Exception:
        try:
            root.destroy()
        except Exception:
            pass
        return

    last_logged = 0

    def _update():
        nonlocal last_logged
        try:
            # Progress bar
            total = max(state.total_jobs, 1)
            frac = state.completed_jobs / total
            w = bar_canvas.winfo_width()
            bar_canvas.coords(bar_fill, 0, 0, int(w * frac), 24)
            bar_canvas.itemconfig(
                bar_text,
                text=f"{state.completed_jobs} / {state.total_jobs} threshold checks",
            )

            # Time
            elapsed = state.elapsed
            if state.completed_jobs > 0 and not state.done:
                rate = elapsed / state.completed_jobs
                remaining = rate * (state.total_jobs - state.completed_jobs)
                remaining_str = _fmt_time(remaining)
            else:
                remaining_str = "--"
            lbl_time.config(
                text=f"Elapsed: {_fmt_time(elapsed)}  |  Remaining: {remaining_str}"
            )

            # Phase and detail
            lbl_phase.config(text=f"Phase: {state.phase}")
            lbl_tally.config(
                text=f"Parameter: {state.phase}  |  {state.current_detail}"
            )

            # Log
            n_lines = len(state.log_lines)
            if n_lines > last_logged:
                log.config(state=tk.NORMAL)
                for line in state.log_lines[last_logged:n_lines]:
                    log.insert(tk.END, line + "\n")
                log.see(tk.END)
                log.config(state=tk.DISABLED)
                last_logged = n_lines

            if state.done:
                total_obs = sum(1 for r in state.rows
                                if r.parameter == "epsilon_D"
                                and r.value == 0.60 and r.observers > 0)
                lbl_summary.config(
                    text=f"DONE  |  {state.completed_jobs} checks  |  "
                         f"{_fmt_time(state.elapsed)}",
                    fg="#006600",
                )
                root.after(3000, root.destroy)
            else:
                root.after(200, _update)
        except Exception:
            pass

    try:
        root.after(200, _update)
        root.mainloop()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("C(8) Threshold Sensitivity Check")
    print("=" * 60)

    state = SensitivityState()

    worker = Thread(target=_work_thread, args=(state,), daemon=True)
    worker.start()

    _try_gui(state)

    worker.join()

    # Console summary
    print(f"\n{'=' * 60}")
    for line in state.log_lines:
        print(line)
    print(f"{'=' * 60}")


if __name__ == "__main__":
    freeze_support()
    main()

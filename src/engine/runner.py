"""
Experiment runner with optional live GUI.

Runs the full pipeline (enumerate -> seed search -> evolution graph ->
tau -> observer detection) for every rule in a class. Tries to show a
tkinter progress window but never fails if it can't — the sweep runs
regardless.

Usage:
    from src.engine.runner import run_sweep
    results = run_sweep(max_description_length=6, steps=1000, workers=4,
                        output="results/c6_raw.json")
"""

from __future__ import annotations

import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from multiprocessing import freeze_support
from pathlib import Path
from threading import Thread
from typing import Any

from src.spark.rule_classes.string_rewriting import StringRewritingRule
from src.spark.seed_search import find_minimal_seed
from src.spark.evolution_graph import StringEvolutionGraph
from src.spark.characteristic_time import characteristic_time
from src.observer.definition import DEFAULT_CRITERIA, ObserverCriteria
from src.observer.detect import detect_observers, scan_all_candidates


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class RuleResult:
    """Result of running the pipeline on one rule."""

    L: str
    R: str
    seed: str | None
    sterile: bool
    steps_evolved: int = 0
    tau: int = 0
    t_obs: int | None = None
    n_observers: int = 0
    best_n_passed: int = 0
    best_scores: dict[str, float] = field(default_factory=dict)
    elapsed: float = 0.0
    max_strlen: int = 0

    @property
    def rule_str(self) -> str:
        return f"{self.L} -> {self.R}"


@dataclass
class SweepState:
    """Mutable state shared between the sweep thread and the GUI."""

    total: int = 0
    completed: int = 0
    sterile: int = 0
    active: int = 0
    observers_found: int = 0
    near_misses: int = 0
    current_rule: str = ""
    elapsed: float = 0.0
    results: list[RuleResult] = field(default_factory=list)
    done: bool = False


# ---------------------------------------------------------------------------
# Single-rule pipeline (runs in worker process)
# ---------------------------------------------------------------------------

def _run_one_rule(
    L: str,
    R: str,
    steps: int,
    criteria_dict: dict[str, Any],
) -> dict[str, Any]:
    """Run the full pipeline for one rule. Returns a plain dict for pickling."""
    criteria = ObserverCriteria(**criteria_dict)
    rule = StringRewritingRule(L, R)
    seed = find_minimal_seed(rule)

    if seed is None:
        return asdict(RuleResult(L=L, R=R, seed=None, sterile=True))

    t0 = time.time()

    graph = StringEvolutionGraph(rule, seed)
    graph.evolve(steps)
    actual_steps = graph.n_steps_evolved
    max_strlen = max(len(s) for s in graph.strings)

    tau = characteristic_time(graph)

    observers = detect_observers(graph, tau, criteria)
    t_obs = observers[0].t_window_start if observers else None

    # Find best near-miss from all scored candidates
    best_n = 0
    best_scores: dict[str, float] = {}
    if observers:
        best_n = 4
        obs = observers[0]
        best_scores = {
            "boundary": obs.boundary,
            "entropy": obs.entropy,
            "decoupling": obs.decoupling,
            "self_ref": obs.self_ref,
        }
    else:
        all_scored = scan_all_candidates(graph, tau, criteria)
        for sc in all_scored:
            n = sc.n_criteria_passed(criteria)
            if n > best_n:
                best_n = n
                best_scores = {
                    "boundary": sc.boundary,
                    "entropy": sc.entropy,
                    "decoupling": sc.decoupling,
                    "self_ref": sc.self_ref,
                }

    elapsed = time.time() - t0

    return asdict(RuleResult(
        L=L, R=R, seed=seed, sterile=False,
        steps_evolved=actual_steps, tau=tau, t_obs=t_obs,
        n_observers=len(observers), best_n_passed=best_n,
        best_scores=best_scores, elapsed=elapsed, max_strlen=max_strlen,
    ))


# ---------------------------------------------------------------------------
# Sweep logic (runs in background thread when GUI is active)
# ---------------------------------------------------------------------------

def _run_sweep_thread(
    rules: list[tuple[str, str]],
    steps: int,
    workers: int,
    criteria: ObserverCriteria,
    state: SweepState,
    output: str | None,
    progress_path: str,
) -> None:
    """Execute the sweep, updating state as results arrive."""
    state.total = len(rules)
    criteria_dict = {
        "epsilon_B": criteria.epsilon_B,
        "epsilon_H": criteria.epsilon_H,
        "epsilon_D": criteria.epsilon_D,
        "persistence_multiplier": criteria.persistence_multiplier,
    }
    t0 = time.time()

    if workers <= 1:
        # Sequential — simpler, better for debugging
        for L, R in rules:
            state.current_rule = f"{L} -> {R}"
            raw = _run_one_rule(L, R, steps, criteria_dict)
            _ingest_result(raw, state)
            state.elapsed = time.time() - t0
            _write_progress(state, progress_path)
    else:
        # Parallel
        futures = {}
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for L, R in rules:
                fut = pool.submit(_run_one_rule, L, R, steps, criteria_dict)
                futures[fut] = (L, R)

            for fut in as_completed(futures):
                L, R = futures[fut]
                state.current_rule = f"{L} -> {R}"
                try:
                    raw = fut.result()
                except Exception as exc:
                    # Record failure but don't crash the sweep
                    raw = asdict(RuleResult(
                        L=L, R=R, seed=None, sterile=True,
                    ))
                    raw["error"] = str(exc)
                _ingest_result(raw, state)
                state.elapsed = time.time() - t0
                _write_progress(state, progress_path)

    state.done = True
    state.elapsed = time.time() - t0

    # Write final output
    if output:
        _write_output(state, output, steps, criteria)
    _write_progress(state, progress_path)


def _ingest_result(raw: dict[str, Any], state: SweepState) -> None:
    """Update sweep state with one rule's result."""
    result = RuleResult(**{k: v for k, v in raw.items() if k != "error"})
    state.results.append(result)
    state.completed += 1

    if result.sterile:
        state.sterile += 1
    else:
        state.active += 1
        if result.t_obs is not None:
            state.observers_found += 1
        elif result.best_n_passed >= 3:
            state.near_misses += 1


def _write_progress(state: SweepState, path: str) -> None:
    """Write .progress.json atomically."""
    try:
        data = {
            "total": state.total,
            "completed": state.completed,
            "sterile": state.sterile,
            "active": state.active,
            "observers_found": state.observers_found,
            "near_misses": state.near_misses,
            "elapsed": round(state.elapsed, 1),
            "done": state.done,
        }
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
    except OSError:
        pass


def _write_output(
    state: SweepState,
    path: str,
    steps: int,
    criteria: ObserverCriteria,
) -> None:
    """Write full results JSON."""
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        data = {
            "config": {
                "steps": steps,
                "epsilon_B": criteria.epsilon_B,
                "epsilon_H": criteria.epsilon_H,
                "epsilon_D": criteria.epsilon_D,
                "persistence_multiplier": criteria.persistence_multiplier,
            },
            "summary": {
                "total": state.total,
                "sterile": state.sterile,
                "active": state.active,
                "observers_found": state.observers_found,
                "near_misses": state.near_misses,
                "elapsed": round(state.elapsed, 1),
            },
            "rules": [asdict(r) for r in state.results],
        }
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
    except OSError as exc:
        print(f"Warning: could not write output to {path}: {exc}")


# ---------------------------------------------------------------------------
# GUI (best-effort tkinter)
# ---------------------------------------------------------------------------

def _try_gui(state: SweepState) -> None:
    """Try to open a tkinter progress window. If anything fails, return."""
    try:
        import tkinter as tk
        from tkinter import scrolledtext
    except Exception:
        return

    try:
        root = tk.Tk()
        root.title("cheap-observer sweep")
        root.geometry("800x500")
        root.resizable(True, True)
    except Exception:
        return

    # -- widgets --
    try:
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Progress bar (canvas-based, no ttk dependency)
        bar_canvas = tk.Canvas(frame, height=24, bg="#e0e0e0",
                               highlightthickness=0)
        bar_canvas.pack(fill=tk.X, pady=(0, 6))
        bar_fill = bar_canvas.create_rectangle(0, 0, 0, 24, fill="#4a90d9",
                                               outline="")
        bar_text = bar_canvas.create_text(400, 12, text="0 / 0",
                                          font=("Consolas", 10))

        # Info labels
        info_frame = tk.Frame(frame)
        info_frame.pack(fill=tk.X, pady=(0, 6))

        lbl_time = tk.Label(info_frame, text="Elapsed: 0s  |  Remaining: --",
                            font=("Consolas", 10), anchor="w")
        lbl_time.pack(side=tk.LEFT)

        lbl_rule = tk.Label(info_frame, text="Current: --",
                            font=("Consolas", 10), anchor="e")
        lbl_rule.pack(side=tk.RIGHT)

        # Tallies
        tally_frame = tk.Frame(frame)
        tally_frame.pack(fill=tk.X, pady=(0, 6))

        lbl_tally = tk.Label(
            tally_frame,
            text="Sterile: 0  |  Active: 0  |  Observers: 0  |  Near-miss (3/4): 0",
            font=("Consolas", 10), anchor="w",
        )
        lbl_tally.pack(side=tk.LEFT)

        # Summary line (turns green when done)
        lbl_summary = tk.Label(frame, text="", font=("Consolas", 11, "bold"),
                               anchor="w")
        lbl_summary.pack(fill=tk.X, pady=(0, 4))

        # Scrollable log
        log = scrolledtext.ScrolledText(frame, font=("Consolas", 9),
                                        height=16, state=tk.DISABLED)
        log.pack(fill=tk.BOTH, expand=True)
    except Exception:
        try:
            root.destroy()
        except Exception:
            pass
        return

    # -- update loop --
    last_logged = 0

    def _update():
        nonlocal last_logged
        try:
            # Progress bar
            total = max(state.total, 1)
            frac = state.completed / total
            w = bar_canvas.winfo_width()
            bar_canvas.coords(bar_fill, 0, 0, int(w * frac), 24)
            bar_canvas.itemconfig(bar_text,
                                  text=f"{state.completed} / {state.total}")

            # Time
            elapsed = state.elapsed
            if state.completed > 0 and not state.done:
                rate = elapsed / state.completed
                remaining = rate * (state.total - state.completed)
                remaining_str = _fmt_time(remaining)
            else:
                remaining_str = "--"
            lbl_time.config(
                text=f"Elapsed: {_fmt_time(elapsed)}  |  Remaining: {remaining_str}"
            )

            # Current rule
            lbl_rule.config(text=f"Current: {state.current_rule}")

            # Tallies
            lbl_tally.config(
                text=(f"Sterile: {state.sterile}  |  "
                      f"Active: {state.active}  |  "
                      f"Observers: {state.observers_found}  |  "
                      f"Near-miss (3/4): {state.near_misses}")
            )

            # Log new results
            if state.completed > last_logged:
                log.config(state=tk.NORMAL)
                for r in state.results[last_logged:state.completed]:
                    if r.sterile:
                        line = f"{r.rule_str:>12s}  sterile\n"
                    else:
                        scores = r.best_scores
                        b = scores.get("boundary", -1)
                        h = scores.get("entropy", -1)
                        d = scores.get("decoupling", -1)
                        s = scores.get("self_ref", -1)
                        obs_tag = "OBS" if r.t_obs is not None else f"{r.best_n_passed}/4"
                        line = (f"{r.rule_str:>12s}  "
                                f"B={b:.3f} H={h:.3f} D={d:.3f} S={s:.0f}  "
                                f"{obs_tag}  ({r.elapsed:.1f}s)\n")
                    log.insert(tk.END, line)
                log.see(tk.END)
                log.config(state=tk.DISABLED)
                last_logged = state.completed

            # Summary when done
            if state.done:
                summary = (
                    f"DONE  |  {state.active} active, "
                    f"{state.observers_found} observers, "
                    f"{state.near_misses} near-misses  |  "
                    f"{_fmt_time(state.elapsed)}"
                )
                lbl_summary.config(text=summary, fg="#006600")
            else:
                root.after(200, _update)
        except Exception:
            # GUI died — that's fine, sweep continues
            pass

    try:
        root.after(200, _update)
        root.mainloop()
    except Exception:
        pass


def _fmt_time(seconds: float) -> str:
    """Format seconds as human-readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{int(m)}m {int(s)}s"
    else:
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{int(h)}h {int(m)}m"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_sweep(
    max_description_length: int = 6,
    steps: int = 1000,
    workers: int = 1,
    output: str | None = None,
    criteria: ObserverCriteria = DEFAULT_CRITERIA,
    gui: bool = True,
    progress_path: str = ".progress.json",
) -> list[RuleResult]:
    """Run the full sweep over a rule class.

    Args:
        max_description_length: Rule class parameter l for C(l).
        steps: Evolution steps per rule.
        workers: Number of parallel workers (1 = sequential).
        output: Path for the output JSON file. None to skip.
        criteria: Observer criteria thresholds.
        gui: Whether to attempt opening a tkinter window.
        progress_path: Path for the .progress.json checkpoint file.

    Returns:
        List of RuleResult for every rule in C(l).
    """
    # Enumerate all rules
    rules = [(r.L, r.R) for r in StringRewritingRule.enumerate(max_description_length)]

    print(f"cheap-observer sweep: C({max_description_length})")
    print(f"  {len(rules)} rules, {steps} steps, {workers} worker(s)")
    if output:
        print(f"  Output: {output}")

    state = SweepState()

    # Start sweep in a background thread
    sweep_thread = Thread(
        target=_run_sweep_thread,
        args=(rules, steps, workers, criteria, state, output, progress_path),
        daemon=True,
    )
    sweep_thread.start()

    # Try GUI on the main thread (tkinter requires it)
    if gui:
        _try_gui(state)

    # If GUI didn't run or closed early, wait for sweep to finish
    sweep_thread.join()

    # Print final summary to console
    print(f"\n{'=' * 60}")
    print(f"  Completed: {state.completed}/{state.total}")
    print(f"  Sterile: {state.sterile}  |  Active: {state.active}")
    print(f"  Observers: {state.observers_found}  |  Near-miss (3/4): {state.near_misses}")
    print(f"  Elapsed: {_fmt_time(state.elapsed)}")
    if output:
        print(f"  Results written to: {output}")
    print(f"{'=' * 60}")

    return state.results


if __name__ == "__main__":
    freeze_support()
    run_sweep()

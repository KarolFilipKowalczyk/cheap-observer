"""
T_rul sweep for C(8) active rules with live GUI.

Measures causal invariance (T_rul) for all active C(8) rules. Loads
the c8_raw.json to identify active rules and their seeds, then runs
the causal invariance test on each.

Usage:
    python -m experiments.string_rewriting.trul_sweep
    python -m experiments.string_rewriting.trul_sweep --class-size 8 --steps 1000 --workers 4
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from multiprocessing import freeze_support
from pathlib import Path
from threading import Thread
from typing import Any

from src.spark.rule_classes.string_rewriting import StringRewritingRule
from src.spark.seed_search import find_minimal_seed
from src.ruliad.causal_invariance import find_t_rul


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class TrulResult:
    L: str
    R: str
    seed: str
    len_L: int
    t_rul: int | None     # None = infinity
    vacuous: bool          # True if always unique match
    elapsed: float = 0.0

    @property
    def rule_str(self) -> str:
        return f"{self.L} -> {self.R}"


@dataclass
class TrulSweepState:
    total: int = 0
    completed: int = 0
    vacuous_count: int = 0
    genuine_finite: int = 0
    infinite_count: int = 0
    current_rule: str = ""
    elapsed: float = 0.0
    results: list[TrulResult] = field(default_factory=list)
    log_lines: list[str] = field(default_factory=list)
    done: bool = False


# ---------------------------------------------------------------------------
# Single-rule worker (picklable for multiprocessing)
# ---------------------------------------------------------------------------

def _run_one_trul(L: str, R: str, seed: str, max_steps: int, k: int) -> dict:
    """Run T_rul measurement for one rule. Returns plain dict."""
    t0 = time.time()
    rule = StringRewritingRule(L, R)
    t_rul, vacuous = find_t_rul(rule, seed, max_steps=max_steps, k=k)
    elapsed = time.time() - t0
    return {
        "L": L, "R": R, "seed": seed, "len_L": len(L),
        "t_rul": t_rul, "vacuous": vacuous, "elapsed": elapsed,
    }


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_active_rules(class_size: int) -> list[tuple[str, str, str]]:
    """Load active rules from c8_raw.json or enumerate + seed search.

    Returns list of (L, R, seed) tuples.
    """
    raw_path = Path(__file__).parent / "results" / f"c{class_size}_raw.json"
    if raw_path.exists():
        with open(raw_path) as f:
            data = json.load(f)
        rules = []
        for r in data["rules"]:
            if not r["sterile"] and r["seed"]:
                rules.append((r["L"], r["R"], r["seed"]))
        return rules

    # Fallback: enumerate and find seeds
    rules = []
    for rule in StringRewritingRule.enumerate(class_size):
        seed = find_minimal_seed(rule)
        if seed is not None:
            rules.append((rule.L, rule.R, seed))
    return rules


# ---------------------------------------------------------------------------
# Work thread
# ---------------------------------------------------------------------------

def _work_thread(
    state: TrulSweepState,
    class_size: int,
    max_steps: int,
    k: int,
    workers: int,
    output_path: str | None,
) -> None:
    t0 = time.time()

    rules = _load_active_rules(class_size)
    state.total = len(rules)
    state.log_lines.append(f"C({class_size}) T_rul sweep: {len(rules)} active rules, "
                           f"k={k}, max_steps={max_steps}")

    if workers <= 1:
        for L, R, seed in rules:
            state.current_rule = f"{L} -> {R}"
            raw = _run_one_trul(L, R, seed, max_steps, k)
            _ingest(raw, state)
            state.elapsed = time.time() - t0
    else:
        futures = {}
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for L, R, seed in rules:
                fut = pool.submit(_run_one_trul, L, R, seed, max_steps, k)
                futures[fut] = (L, R)
            for fut in as_completed(futures):
                L, R = futures[fut]
                state.current_rule = f"{L} -> {R}"
                try:
                    raw = fut.result()
                except Exception as exc:
                    raw = {
                        "L": L, "R": R, "seed": "", "len_L": len(L),
                        "t_rul": None, "vacuous": False,
                        "elapsed": 0.0, "error": str(exc),
                    }
                _ingest(raw, state)
                state.elapsed = time.time() - t0

    state.done = True
    state.elapsed = time.time() - t0

    # Save results
    if output_path:
        _save_results(state, output_path, class_size, max_steps, k)

    state.log_lines.append(f"\nDone in {state.elapsed:.1f}s")
    state.log_lines.append(f"Vacuous (unique match): {state.vacuous_count}")
    state.log_lines.append(f"Genuine finite T_rul: {state.genuine_finite}")
    state.log_lines.append(f"T_rul = infinity: {state.infinite_count}")


def _ingest(raw: dict, state: TrulSweepState) -> None:
    result = TrulResult(
        L=raw["L"], R=raw["R"], seed=raw["seed"], len_L=raw["len_L"],
        t_rul=raw["t_rul"], vacuous=raw["vacuous"], elapsed=raw["elapsed"],
    )
    state.results.append(result)
    state.completed += 1

    if result.vacuous:
        state.vacuous_count += 1
        tag = f"T_rul=0 (vacuous)"
    elif result.t_rul is not None:
        state.genuine_finite += 1
        tag = f"T_rul={result.t_rul} (genuine)"
    else:
        state.infinite_count += 1
        tag = "T_rul=inf"

    state.log_lines.append(
        f"  {result.rule_str:>14s}  |L|={result.len_L}  {tag}  ({result.elapsed:.2f}s)"
    )


def _save_results(
    state: TrulSweepState,
    path: str,
    class_size: int,
    max_steps: int,
    k: int,
) -> None:
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        data = {
            "config": {
                "class_size": class_size,
                "max_steps": max_steps,
                "k_samples": k,
            },
            "summary": {
                "total": state.total,
                "vacuous": state.vacuous_count,
                "genuine_finite": state.genuine_finite,
                "infinite": state.infinite_count,
                "elapsed": round(state.elapsed, 1),
            },
            "rules": [
                {
                    "L": r.L, "R": r.R, "seed": r.seed,
                    "len_L": r.len_L, "t_rul": r.t_rul,
                    "vacuous": r.vacuous, "elapsed": round(r.elapsed, 3),
                }
                for r in state.results
            ],
        }
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        import os
        os.replace(tmp, path)
    except OSError as exc:
        state.log_lines.append(f"Warning: could not save to {path}: {exc}")


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


def _try_gui(state: TrulSweepState) -> None:
    try:
        import tkinter as tk
        from tkinter import scrolledtext
    except Exception:
        return

    try:
        root = tk.Tk()
        root.title("cheap-observer: C(8) T_rul sweep")
        root.geometry("900x550")
        root.resizable(True, True)
    except Exception:
        return

    try:
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        bar_canvas = tk.Canvas(frame, height=24, bg="#e0e0e0",
                               highlightthickness=0)
        bar_canvas.pack(fill=tk.X, pady=(0, 6))
        bar_fill = bar_canvas.create_rectangle(0, 0, 0, 24, fill="#4a90d9",
                                               outline="")
        bar_text = bar_canvas.create_text(450, 12, text="0 / 0",
                                          font=("Consolas", 10))

        info_frame = tk.Frame(frame)
        info_frame.pack(fill=tk.X, pady=(0, 6))
        lbl_time = tk.Label(info_frame, text="Elapsed: 0s  |  Remaining: --",
                            font=("Consolas", 10), anchor="w")
        lbl_time.pack(side=tk.LEFT)
        lbl_rule = tk.Label(info_frame, text="Current: --",
                            font=("Consolas", 10), anchor="e")
        lbl_rule.pack(side=tk.RIGHT)

        lbl_tally = tk.Label(
            frame,
            text="Vacuous: 0  |  Genuine finite: 0  |  Infinite: 0",
            font=("Consolas", 10), anchor="w",
        )
        lbl_tally.pack(fill=tk.X, pady=(0, 6))

        lbl_summary = tk.Label(frame, text="", font=("Consolas", 11, "bold"),
                               anchor="w")
        lbl_summary.pack(fill=tk.X, pady=(0, 4))

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
            total = max(state.total, 1)
            frac = state.completed / total
            w = bar_canvas.winfo_width()
            bar_canvas.coords(bar_fill, 0, 0, int(w * frac), 24)
            bar_canvas.itemconfig(bar_text,
                                  text=f"{state.completed} / {state.total}")

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
            lbl_rule.config(text=f"Current: {state.current_rule}")
            lbl_tally.config(
                text=(f"Vacuous: {state.vacuous_count}  |  "
                      f"Genuine finite: {state.genuine_finite}  |  "
                      f"Infinite: {state.infinite_count}")
            )

            n_lines = len(state.log_lines)
            if n_lines > last_logged:
                log.config(state=tk.NORMAL)
                for line in state.log_lines[last_logged:n_lines]:
                    log.insert(tk.END, line + "\n")
                log.see(tk.END)
                log.config(state=tk.DISABLED)
                last_logged = n_lines

            if state.done:
                lbl_summary.config(
                    text=(f"DONE  |  {state.vacuous_count} vacuous, "
                          f"{state.genuine_finite} genuine, "
                          f"{state.infinite_count} infinite  |  "
                          f"{_fmt_time(state.elapsed)}"),
                    fg="#006600",
                )
                root.after(2000, root.destroy)
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
    parser = argparse.ArgumentParser(
        description="Measure T_rul for string rewriting rules"
    )
    parser.add_argument("--class-size", type=int, default=8)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--k", type=int, default=50)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    if args.output is None:
        args.output = str(
            Path(__file__).parent / "results" / f"c{args.class_size}_trul.json"
        )

    print(f"T_rul sweep: C({args.class_size}), k={args.k}, "
          f"max_steps={args.steps}, workers={args.workers}")

    state = TrulSweepState()
    worker = Thread(
        target=_work_thread,
        args=(state, args.class_size, args.steps, args.k,
              args.workers, args.output),
        daemon=True,
    )
    worker.start()

    _try_gui(state)
    worker.join()

    print(f"\n{'=' * 60}")
    print(f"  Completed: {state.completed}/{state.total}")
    print(f"  Vacuous (unique match): {state.vacuous_count}")
    print(f"  Genuine finite T_rul: {state.genuine_finite}")
    print(f"  T_rul = infinity: {state.infinite_count}")
    print(f"  Elapsed: {_fmt_time(state.elapsed)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    freeze_support()
    main()

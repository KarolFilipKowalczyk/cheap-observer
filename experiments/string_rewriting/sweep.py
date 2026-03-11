"""
Sweep over string rewriting rules, measuring T_obs for each.

Reads config from config.yaml (or command-line overrides) and delegates
to src.engine.runner.run_sweep.

Usage:
    py -m experiments.string_rewriting.sweep
    py -m experiments.string_rewriting.sweep --steps 2000 --workers 8
"""

from __future__ import annotations

import argparse
import os
import sys
from multiprocessing import freeze_support
from pathlib import Path

import yaml

from src.engine.runner import run_sweep
from src.observer.definition import ObserverCriteria


def _load_config(config_path: str) -> dict:
    """Load YAML config, returning empty dict on failure."""
    try:
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sweep string rewriting rules for observer detection"
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to config.yaml (default: auto-detect in script directory)"
    )
    parser.add_argument("--class-size", type=int, default=None,
                        help="Rule class C(l) parameter")
    parser.add_argument("--steps", type=int, default=None,
                        help="Evolution steps per rule")
    parser.add_argument("--workers", type=int, default=None,
                        help="Parallel workers")
    parser.add_argument("--output", type=str, default=None,
                        help="Output JSON path")
    args = parser.parse_args()

    # Find config.yaml
    if args.config:
        config_path = args.config
    else:
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    cfg = _load_config(config_path)

    # Merge: CLI args override config, config overrides defaults
    class_size = args.class_size or cfg.get("max_description_length", 6)
    steps = args.steps or cfg.get("steps", 1000)
    workers = args.workers or cfg.get("workers", 1)
    if args.output:
        # CLI path: relative to cwd
        output = args.output
    else:
        # Config path: relative to config file directory
        output = cfg.get("output", None)
        if output and not os.path.isabs(output):
            output = os.path.join(os.path.dirname(config_path), output)

    # Build criteria from config
    criteria_cfg = cfg.get("criteria", {})
    criteria = ObserverCriteria(
        epsilon_B=criteria_cfg.get("epsilon_B", 0.3),
        epsilon_H=criteria_cfg.get("epsilon_H", 1.0),
        epsilon_D=criteria_cfg.get("epsilon_D", 0.6),
        persistence_multiplier=criteria_cfg.get("persistence_multiplier", 10),
    )

    run_sweep(
        max_description_length=class_size,
        steps=steps,
        workers=workers,
        output=output,
        criteria=criteria,
    )


if __name__ == "__main__":
    freeze_support()
    main()

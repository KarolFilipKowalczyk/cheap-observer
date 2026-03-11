"""
String rewriting rule class.

A string rewriting rule r is a pair (L, R) where L and R are non-empty
binary strings. At each step, the rule replaces one occurrence of L in
the current string with R.

The rule class C(l) is the set of all such rules where |L| + |R| <= l.

See definitions.md Sections 1 and 3.
"""

from __future__ import annotations

import random
import warnings
from dataclasses import dataclass
from typing import Iterator, Literal

STATED_CARDINALITY_C4 = 56


@dataclass(frozen=True)
class StringRewritingRule:
    """A string rewriting rule (L, R) over the alphabet {0, 1}.

    See definitions.md Section 1: "A string rewriting rule r is a pair
    (L, R) where L and R are non-empty strings over the alphabet {0, 1}.
    At each step, the rule replaces one occurrence of L in the current
    string with R."
    """

    L: str
    R: str

    def __post_init__(self) -> None:
        if not self.L or not self.R:
            raise ValueError("L and R must be non-empty")
        if not all(c in "01" for c in self.L):
            raise ValueError(f"L must be a binary string, got {self.L!r}")
        if not all(c in "01" for c in self.R):
            raise ValueError(f"R must be a binary string, got {self.R!r}")

    @property
    def description_length(self) -> int:
        """The Kolmogorov cost |L| + |R|."""
        return len(self.L) + len(self.R)

    def find_occurrences(self, string: str) -> list[int]:
        """Find all start indices where L occurs in the string."""
        indices = []
        start = 0
        while True:
            pos = string.find(self.L, start)
            if pos == -1:
                break
            indices.append(pos)
            start = pos + 1
        return indices

    def apply(
        self,
        string: str,
        order: Literal["leftmost", "rightmost", "random"] = "leftmost",
    ) -> str:
        """Apply the rule once to the string.

        Finds occurrences of L and rewrites one according to the specified
        order. Returns the new string, or the original string unchanged if
        L is not found.

        The default order is 'leftmost' — the canonical update order from
        definitions.md Section 3: "the leftmost match is rewritten first."

        Args:
            string: The current binary string.
            order: Which occurrence to rewrite.
                'leftmost' — canonical order (Section 3).
                'rightmost' — last occurrence.
                'random' — uniformly random (for Section 7 causal
                    invariance testing).

        Returns:
            The string after one rewrite step.
        """
        occurrences = self.find_occurrences(string)
        if not occurrences:
            return string

        if order == "leftmost":
            pos = occurrences[0]
        elif order == "rightmost":
            pos = occurrences[-1]
        elif order == "random":
            pos = random.choice(occurrences)
        else:
            raise ValueError(f"Unknown order: {order!r}")

        return string[:pos] + self.R + string[pos + len(self.L):]

    def evolve(
        self,
        seed: str,
        steps: int,
        order: Literal["leftmost", "rightmost", "random"] = "leftmost",
    ) -> list[str]:
        """Evolve the seed string for the given number of steps.

        Returns the full sequence [s_0, s_1, ..., s_steps] where s_0 is
        the seed. Stops early if the string becomes empty or reaches a
        fixed point (L not found, so string unchanged).

        Args:
            seed: The initial string s_0.
            steps: Maximum number of rewrite steps.
            order: Update order (see apply).

        Returns:
            List of strings from s_0 through the final state.
        """
        history = [seed]
        current = seed
        for _ in range(steps):
            next_str = self.apply(current, order=order)
            history.append(next_str)
            if not next_str or next_str == current:
                break
            current = next_str
        return history

    @classmethod
    def enumerate(cls, max_description_length: int) -> Iterator[StringRewritingRule]:
        """Yield all rules in C(l) for a given description length bound l.

        Enumerates all pairs (L, R) of non-empty binary strings where
        |L| + |R| <= max_description_length.

        See definitions.md Section 1: "A rule class C(l) is the set of
        all string rewriting rules where |L| + |R| <= l."

        Args:
            max_description_length: The bound l on |L| + |R|.

        Yields:
            StringRewritingRule instances, ordered by (|L|, |R|, L, R).
        """
        count = 0
        for len_L in range(1, max_description_length):
            for len_R in range(1, max_description_length - len_L + 1):
                for L_int in range(2**len_L):
                    L = format(L_int, f"0{len_L}b")
                    for R_int in range(2**len_R):
                        R = format(R_int, f"0{len_R}b")
                        yield cls(L=L, R=R)
                        count += 1

        if max_description_length == 4 and count != STATED_CARDINALITY_C4:
            warnings.warn(
                f"|C(4)| = {count}, but definitions.md states {STATED_CARDINALITY_C4}. "
                f"The enumeration produces {count} rules for all (L, R) pairs with "
                f"|L| >= 1, |R| >= 1, |L| + |R| <= 4 over alphabet {{0, 1}}. "
                f"The stated cardinality may need correction.",
                stacklevel=2,
            )

    def __str__(self) -> str:
        return f"{self.L} -> {self.R}"

    def __repr__(self) -> str:
        return f"StringRewritingRule(L={self.L!r}, R={self.R!r})"

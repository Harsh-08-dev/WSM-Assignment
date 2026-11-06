"""
wildcard_processor.py

Wildcard Processing Module
----------------------------
Responsible for resolving wildcard query terms (containing `*`)
against the index vocabulary, e.g.:

    comput*   -> computer, computation, computing, ...
    *tion     -> information, retrieval... (any term ending in "tion")
    comp*ter  -> computer, compiler-like terms with "comp" ... "ter"

This module only deals with *term expansion*: given a wildcard
pattern and a vocabulary, it returns the matching real terms. It does
not know about documents or postings -- that lookup happens in the
Query Processing module, which combines this module's output with
the InvertedIndex.
"""

from __future__ import annotations

import re
from typing import List, Pattern


class WildcardProcessor:
    """
    Resolves `*`-based wildcard patterns into matching vocabulary
    terms.

    Usage:
        processor = WildcardProcessor()
        matches = processor.expand("comput*", vocabulary)
        # -> ["computation", "computer", "computing"]
    """

    @staticmethod
    def is_wildcard(term: str) -> bool:
        """
        Check whether a query term contains a wildcard character.

        Args:
            term: The query term to inspect.

        Returns:
            True if the term contains at least one `*`, False
            otherwise.
        """
        return "*" in term

    def _compile_pattern(self, wildcard_term: str) -> Pattern[str]:
        """
        Convert a wildcard term (using `*`) into a compiled regular
        expression that matches whole vocabulary terms.

        Every literal character in the wildcard term is escaped so
        that only `*` is treated specially (translated to `.*`).

        Args:
            wildcard_term: The raw wildcard pattern, e.g. "comp*ter".

        Returns:
            A compiled regex object suitable for use with
            `fullmatch` against candidate vocabulary terms.
        """
        parts = wildcard_term.split("*")
        escaped_parts = [re.escape(part) for part in parts]
        regex_str = ".*".join(escaped_parts)
        return re.compile(f"^{regex_str}$")

    def expand(self, wildcard_term: str, vocabulary: List[str]) -> List[str]:
        """
        Expand a wildcard pattern into all matching vocabulary terms.

        Args:
            wildcard_term: The wildcard pattern, e.g. "comput*",
                "*tion", or "comp*ter". Matching is case-sensitive
                relative to the vocabulary passed in -- callers
                should pass an already-normalized (e.g. lowercase)
                wildcard term and vocabulary for consistent results.
            vocabulary: The list of candidate terms to match against
                (typically InvertedIndex.get_vocabulary()).

        Returns:
            A sorted list of vocabulary terms that match the
            wildcard pattern. Empty list if no terms match or if the
            pattern contains no `*` and no exact match exists.
        """
        if not self.is_wildcard(wildcard_term):
            # No wildcard character present: treat as an exact lookup.
            return [wildcard_term] if wildcard_term in vocabulary else []

        pattern = self._compile_pattern(wildcard_term)
        matches = [term for term in vocabulary if pattern.fullmatch(term)]
        return sorted(matches)

"""
normalizer.py

Text Normalization Module
--------------------------
Responsible for normalizing tokens produced by the Tokenizer:
case folding, whitespace cleanup, and optional hooks for stop-word
removal and stemming so those features can be added later without
changing the module's public interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Set


# Type alias for a stemming function: takes a token, returns its stem.
StemmerFunc = Callable[[str], str]


@dataclass
class NormalizerConfig:
    """
    Configuration options controlling how tokens are normalized.

    Attributes:
        lowercase: Whether to case-fold tokens to lowercase.
        stop_words: An optional set of stop words to remove. Empty by
            default (no stop-word removal), but can be populated to
            enable the feature without changing any code.
        stemmer: An optional callable implementing a stemming
            algorithm (e.g. Porter stemmer). Left as None by default;
            this is a hook for future extension.
    """

    lowercase: bool = True
    stop_words: Set[str] = field(default_factory=set)
    stemmer: Optional[StemmerFunc] = None


class Normalizer:
    """
    Normalizes tokens: case folding, whitespace trimming, and
    optional stop-word removal / stemming.

    Usage:
        normalizer = Normalizer()
        clean_tokens = normalizer.normalize(["Search", "  Engines "])
        # -> ["search", "engines"]
    """

    def __init__(self, config: NormalizerConfig | None = None) -> None:
        """
        Initialize the normalizer with an optional configuration.

        Args:
            config: A NormalizerConfig instance controlling
                normalization behavior. If omitted, sensible
                defaults are used (lowercase only, no stop-word
                removal, no stemming).
        """
        self.config: NormalizerConfig = config or NormalizerConfig()

    def normalize_token(self, token: str) -> Optional[str]:
        """
        Normalize a single token.

        Args:
            token: The raw token to normalize.

        Returns:
            The normalized token, or None if the token should be
            dropped entirely (e.g. it is a stop word or becomes
            empty after trimming).
        """
        normalized = token.strip()
        if not normalized:
            return None

        if self.config.lowercase:
            normalized = normalized.lower()

        if normalized in self.config.stop_words:
            return None

        if self.config.stemmer is not None:
            normalized = self.config.stemmer(normalized)

        return normalized

    def normalize(self, tokens: List[str]) -> List[str]:
        """
        Normalize a list of tokens.

        Args:
            tokens: The list of raw tokens to normalize (typically
                the output of Tokenizer.tokenize).

        Returns:
            A list of normalized tokens with stop words removed and
            empty results filtered out. Order is preserved.
        """
        normalized_tokens: List[str] = []
        for token in tokens:
            normalized = self.normalize_token(token)
            if normalized is not None:
                normalized_tokens.append(normalized)
        return normalized_tokens

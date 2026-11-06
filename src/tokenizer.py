"""
tokenizer.py

Tokenization Module
--------------------
Responsible for converting raw text into a list of tokens (words),
stripping punctuation and special characters along the way.

Tokenization rules are configurable through the TokenizerConfig
dataclass, so callers can adjust behavior (e.g. minimum token length,
whether digits are kept) without modifying this module's code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Pattern


@dataclass
class TokenizerConfig:
    """
    Configuration options controlling how text is tokenized.

    Attributes:
        min_token_length: Tokens shorter than this length are dropped.
            Defaults to 1 (keep everything non-empty).
        keep_digits: Whether tokens made purely of digits are kept.
        pattern: The regular expression used to find token candidates.
            Defaults to a pattern that matches sequences of letters
            and digits, effectively stripping punctuation and
            special characters.
    """

    min_token_length: int = 1
    keep_digits: bool = True
    pattern: str = r"[A-Za-z0-9]+"


class Tokenizer:
    """
    Splits raw text into a list of cleaned tokens.

    Usage:
        tokenizer = Tokenizer()
        tokens = tokenizer.tokenize("Hello, world! Search-engines rock.")
        # -> ["Hello", "world", "Search", "engines", "rock"]
    """

    def __init__(self, config: TokenizerConfig | None = None) -> None:
        """
        Initialize the tokenizer with an optional configuration.

        Args:
            config: A TokenizerConfig instance controlling tokenization
                behavior. If omitted, sensible defaults are used.
        """
        self.config: TokenizerConfig = config or TokenizerConfig()
        self._compiled_pattern: Pattern[str] = re.compile(self.config.pattern)

    def tokenize(self, text: str) -> List[str]:
        """
        Convert a string of text into a list of tokens.

        Punctuation and special characters are removed as a side
        effect of the regex-based extraction (only characters that
        match the configured pattern are kept as part of a token).

        Args:
            text: The raw input text to tokenize.

        Returns:
            A list of token strings, in the order they appear in the
            text, filtered according to the tokenizer configuration.
        """
        if not text:
            return []

        raw_tokens = self._compiled_pattern.findall(text)

        tokens: List[str] = []
        for token in raw_tokens:
            if len(token) < self.config.min_token_length:
                continue
            if not self.config.keep_digits and token.isdigit():
                continue
            tokens.append(token)

        return tokens

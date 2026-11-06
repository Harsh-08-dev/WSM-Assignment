"""
inverted_index.py

Inverted Index Module
-----------------------
Responsible for building and storing an inverted index (term -> set
of document IDs) from already-tokenized and normalized documents.

The index is the core data structure the query layer relies on. It
deliberately knows nothing about how tokens were produced (that is
the Tokenizer/Normalizer's job) -- it only deals with clean term
lists mapped to document IDs.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Set


class InvertedIndex:
    """
    Maintains a term -> set of document IDs mapping (the classic
    inverted index used by search engines for fast lookups).

    Usage:
        index = InvertedIndex()
        index.build({
            "doc1": ["information", "retrieval", "system"],
            "doc2": ["search", "engine", "index"],
        })
        index.get_postings("information")  # -> {"doc1"}
    """

    def __init__(self) -> None:
        """Initialize an empty inverted index."""
        # term -> set of document IDs containing that term
        self._index: Dict[str, Set[str]] = defaultdict(set)
        # doc_id -> list of normalized tokens (kept for snippet generation
        # and term-frequency style features used by the query layer)
        self._doc_tokens: Dict[str, List[str]] = {}

    def add_document(self, doc_id: str, tokens: Iterable[str]) -> None:
        """
        Add a single document's normalized tokens to the index.

        Args:
            doc_id: Unique identifier of the document.
            tokens: An iterable of normalized tokens belonging to
                this document (typically the output of the
                Normalizer).
        """
        token_list = list(tokens)
        self._doc_tokens[doc_id] = token_list

        for term in token_list:
            self._index[term].add(doc_id)

    def build(self, tokenized_documents: Dict[str, List[str]]) -> None:
        """
        Build the index from a full collection of tokenized documents.

        Args:
            tokenized_documents: A mapping of doc_id -> list of
                normalized tokens for that document. Any existing
                index contents are cleared first.
        """
        self._index.clear()
        self._doc_tokens.clear()

        for doc_id, tokens in tokenized_documents.items():
            self.add_document(doc_id, tokens)

    def get_postings(self, term: str) -> Set[str]:
        """
        Retrieve the set of document IDs containing an exact term.

        Args:
            term: The (already normalized) term to look up.

        Returns:
            A set of document IDs containing the term. Empty set if
            the term does not exist in the index.
        """
        return set(self._index.get(term, set()))

    def get_tokens_for_document(self, doc_id: str) -> List[str]:
        """
        Retrieve the stored normalized tokens for a given document.

        Args:
            doc_id: The document ID to look up.

        Returns:
            The list of normalized tokens for that document, or an
            empty list if the document is not present in the index.
        """
        return list(self._doc_tokens.get(doc_id, []))

    def get_vocabulary(self) -> List[str]:
        """
        Retrieve the full vocabulary (all distinct indexed terms).

        Returns:
            A sorted list of every unique term currently in the
            index. Sorted output makes wildcard scanning and display
            deterministic.
        """
        return sorted(self._index.keys())

    def get_document_ids(self) -> List[str]:
        """
        Retrieve all document IDs currently represented in the index.

        Returns:
            A sorted list of document IDs.
        """
        return sorted(self._doc_tokens.keys())

    def __contains__(self, term: str) -> bool:
        """Allow `term in index` checks against the vocabulary."""
        return term in self._index

    def __len__(self) -> int:
        """Return the number of distinct terms in the index."""
        return len(self._index)

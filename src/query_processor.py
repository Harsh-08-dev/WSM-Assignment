"""
query_processor.py

Query Processing Module
-------------------------
Responsible for taking a raw user query string, running it through
preprocessing consistent with how documents were indexed, and
returning ranked, matching documents -- including support for
wildcard terms (delegated to WildcardProcessor) and human-readable
snippets pulled from the original document text.

This module ties together:
    - Tokenizer / Normalizer  (consistent preprocessing)
    - InvertedIndex           (term -> document lookups)
    - WildcardProcessor       (`*` pattern expansion)
    - Document                (raw content, for snippet generation)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set

from src.document_loader import Document
from src.inverted_index import InvertedIndex
from src.normalizer import Normalizer
from src.tokenizer import Tokenizer
from src.wildcard_processor import WildcardProcessor


# Regex used to split a raw query into candidate terms while
# preserving `*` so wildcard patterns survive query tokenization
# (the main Tokenizer's pattern intentionally strips `*`, since it
# is not a valid character within an indexed document term).
_QUERY_TERM_PATTERN = re.compile(r"[A-Za-z0-9*]+")


@dataclass
class SearchResult:
    """
    Represents a single ranked search result.

    Attributes:
        doc_id: Identifier of the matching document.
        file_name: Original file name of the matching document.
        score: Number of distinct query terms this document matched
            (higher is more relevant).
        matched_terms: The actual vocabulary terms that contributed
            to this document's match (wildcard terms are expanded).
        snippet: A short excerpt from the document showing the
            matched content in context.
    """

    doc_id: str
    file_name: str
    score: int
    matched_terms: List[str] = field(default_factory=list)
    snippet: str = ""


class QueryProcessor:
    """
    Processes user queries against an InvertedIndex and returns
    ranked SearchResult objects.

    Usage:
        processor = QueryProcessor(tokenizer, normalizer, index,
                                    wildcard_processor, documents)
        results = processor.process_query("comput* retrieval")
    """

    def __init__(
        self,
        tokenizer: Tokenizer,
        normalizer: Normalizer,
        index: InvertedIndex,
        wildcard_processor: WildcardProcessor,
        documents: List[Document],
        snippet_window: int = 8,
    ) -> None:
        """
        Initialize the query processor.

        Args:
            tokenizer: Tokenizer instance (kept for API symmetry and
                potential future use on query text).
            normalizer: Normalizer instance used to case-fold and
                filter stop words from query terms.
            index: The built InvertedIndex to search against.
            wildcard_processor: WildcardProcessor used to expand `*`
                patterns into real vocabulary terms.
            documents: The original loaded Document objects, used to
                generate readable snippets around matched terms.
            snippet_window: Number of words to show on each side of
                a matched term when building a snippet.
        """
        self.tokenizer = tokenizer
        self.normalizer = normalizer
        self.index = index
        self.wildcard_processor = wildcard_processor
        self.snippet_window = snippet_window
        self._documents_by_id: Dict[str, Document] = {doc.doc_id: doc for doc in documents}

    def _extract_query_terms(self, query: str) -> List[str]:
        """
        Split and normalize a raw query string into query terms,
        preserving `*` wildcard characters.

        Args:
            query: The raw query string typed by the user.

        Returns:
            A list of normalized query terms (lowercase, stop words
            removed for non-wildcard terms), in the order they
            appeared in the query.
        """
        raw_terms = _QUERY_TERM_PATTERN.findall(query)
        processed_terms: List[str] = []

        for raw_term in raw_terms:
            term = raw_term.lower() if self.normalizer.config.lowercase else raw_term

            is_wildcard = WildcardProcessor.is_wildcard(term)
            if not is_wildcard and term in self.normalizer.config.stop_words:
                continue

            processed_terms.append(term)

        return processed_terms

    def _resolve_term(self, term: str) -> "tuple[Set[str], Dict[str, Set[str]]]":
        """
        Resolve a single (already normalized) query term to the set of
        matching document IDs, expanding wildcards as needed.

        Unlike a naive lookup, this also tracks *which real vocabulary
        terms* matched within each document -- for an exact term that is
        just the term itself, but for a wildcard pattern (e.g.
        "comput*") it is the actual expanded words (e.g. "computer",
        "computation") found in that document. Downstream code uses this
        so result display and snippet generation reflect real words
        rather than the literal wildcard pattern.

        Args:
            term: A normalized query term, possibly containing `*`.

        Returns:
            A tuple of:
                - The set of document IDs that contain this term (or,
                  for wildcards, any term matching the pattern).
                - A mapping of doc_id -> set of the actual vocabulary
                  terms (within this query term's expansion) that were
                  found in that document.
        """
        if WildcardProcessor.is_wildcard(term):
            vocabulary = self.index.get_vocabulary()
            expanded_terms = self.wildcard_processor.expand(term, vocabulary)

            doc_ids: Set[str] = set()
            doc_to_vocab_terms: Dict[str, Set[str]] = {}
            for expanded_term in expanded_terms:
                postings = self.index.get_postings(expanded_term)
                doc_ids |= postings
                for doc_id in postings:
                    doc_to_vocab_terms.setdefault(doc_id, set()).add(expanded_term)

            return doc_ids, doc_to_vocab_terms

        postings = self.index.get_postings(term)
        doc_to_vocab_terms = {doc_id: {term} for doc_id in postings}
        return postings, doc_to_vocab_terms

    def _generate_snippet(self, content: str, terms: List[str]) -> str:
        """
        Build a short, readable snippet from a document's raw content
        centered on the first occurrence of any of the given terms.

        Args:
            content: The document's raw (unprocessed) text.
            terms: The literal terms to search for within the text
                (case-insensitive whole-word match).

        Returns:
            A snippet string. Falls back to the first words of the
            document if none of the terms can be located verbatim
            (this can happen if stemming/normalization changed the
            term compared to the raw text).
        """
        words = content.split()
        lower_words = [w.lower().strip(".,!?;:\"'()") for w in words]

        match_index = -1
        for i, word in enumerate(lower_words):
            if word in terms:
                match_index = i
                break

        if match_index == -1:
            snippet_words = words[: self.snippet_window * 2]
            suffix = "..." if len(words) > len(snippet_words) else ""
            return " ".join(snippet_words) + suffix

        start = max(0, match_index - self.snippet_window)
        end = min(len(words), match_index + self.snippet_window + 1)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(words) else ""

        return f"{prefix}{' '.join(words[start:end])}{suffix}"

    def process_query(self, query: str, match_mode: str = "OR") -> List[SearchResult]:
        """
        Process a raw user query and return ranked search results.

        Args:
            query: The raw query string, e.g. "information retrieval"
                or "comput* system".
            match_mode: Either "OR" (documents matching *any* query
                term are returned, ranked by how many terms they
                matched) or "AND" (only documents matching *every*
                query term are returned). Defaults to "OR".

        Returns:
            A list of SearchResult objects sorted by descending
            score (most relevant first), then by doc_id for stable
            ordering among ties. Returns an empty list if the query
            is empty or matches nothing.
        """
        terms = self._extract_query_terms(query)
        if not terms:
            return []

        term_doc_sets: Dict[str, Set[str]] = {}
        term_vocab_maps: Dict[str, Dict[str, Set[str]]] = {}
        for term in terms:
            doc_ids, vocab_map = self._resolve_term(term)
            term_doc_sets[term] = doc_ids
            term_vocab_maps[term] = vocab_map

        # Determine the candidate set of documents based on match mode.
        non_empty_sets = [doc_ids for doc_ids in term_doc_sets.values() if doc_ids]
        if not non_empty_sets:
            return []

        if match_mode.upper() == "AND":
            candidate_docs: Set[str] = set.intersection(*non_empty_sets) if len(
                non_empty_sets
            ) == len(terms) else set()
        else:
            candidate_docs = set.union(*non_empty_sets)

        results: List[SearchResult] = []
        for doc_id in candidate_docs:
            # Distinct *query terms* satisfied by this document -- this
            # drives the score, so a wildcard that expands to five words
            # all found in one document still only counts as one matched
            # query term (consistent with how many terms the user typed).
            matched_query_terms = [
                term for term, doc_ids in term_doc_sets.items() if doc_id in doc_ids
            ]
            score = len(matched_query_terms)

            # Actual vocabulary words (wildcard-expanded where relevant)
            # found in this document -- used for display and snippets so
            # the user sees real words, not the raw wildcard pattern.
            matched_vocab_terms: Set[str] = set()
            for term in matched_query_terms:
                matched_vocab_terms |= term_vocab_maps[term].get(doc_id, set())

            document = self._documents_by_id.get(doc_id)
            file_name = document.file_name if document else doc_id
            snippet = (
                self._generate_snippet(document.content, sorted(matched_vocab_terms))
                if document
                else ""
            )

            results.append(
                SearchResult(
                    doc_id=doc_id,
                    file_name=file_name,
                    score=score,
                    matched_terms=sorted(matched_vocab_terms),
                    snippet=snippet,
                )
            )

        results.sort(key=lambda result: (-result.score, result.doc_id))
        return results
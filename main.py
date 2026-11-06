"""
main.py

Application Entry Point
------------------------
Wires together the document loading, tokenization, normalization,
indexing, and query-processing modules, then launches the Tkinter GUI.

This is the only place in the project where every module is imported
and connected -- individual modules remain independent and reusable
on their own (e.g. in unit tests) without needing this file.

Run with:
    python main.py
"""

from __future__ import annotations

import os
import sys
import tkinter as tk
from typing import Dict, List

from src.document_loader import Document, DocumentLoader
from src.gui import SearchApp
from src.inverted_index import InvertedIndex
from src.normalizer import Normalizer, NormalizerConfig
from src.query_processor import QueryProcessor
from src.tokenizer import Tokenizer
from src.wildcard_processor import WildcardProcessor

# Directory containing the sample/user corpus, resolved relative to this
# file so the app runs correctly regardless of the current working
# directory it was launched from.
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIRECTORY = os.path.join(_PROJECT_ROOT, "data")

# A small default stop-word list. Left minimal on purpose -- callers can
# extend or replace this set without touching the Normalizer itself.
DEFAULT_STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "of", "in", "on", "at", "to", "for", "and", "or", "but", "with",
    "by", "as", "it", "this", "that", "these", "those",
}


def build_query_processor(data_directory: str) -> QueryProcessor:
    """
    Construct the full IR pipeline and return a ready-to-use
    QueryProcessor.

    This function performs, in order:
        1. Document loading   (DocumentLoader)
        2. Tokenization       (Tokenizer)
        3. Normalization      (Normalizer)
        4. Index construction (InvertedIndex)
    and wires the result together with a WildcardProcessor into a
    QueryProcessor.

    Args:
        data_directory: Path to the directory containing `.txt`
            documents to index.

    Returns:
        A fully constructed QueryProcessor ready to handle queries.

    Raises:
        FileNotFoundError: If the data directory does not exist.
        NotADirectoryError: If the data directory path is not a
            directory.
    """
    loader = DocumentLoader(data_directory)
    documents: List[Document] = loader.load_documents()

    tokenizer = Tokenizer()
    normalizer = Normalizer(NormalizerConfig(stop_words=set(DEFAULT_STOP_WORDS)))

    tokenized_documents: Dict[str, List[str]] = {}
    for document in documents:
        raw_tokens = tokenizer.tokenize(document.content)
        tokenized_documents[document.doc_id] = normalizer.normalize(raw_tokens)

    index = InvertedIndex()
    index.build(tokenized_documents)

    wildcard_processor = WildcardProcessor()

    return QueryProcessor(
        tokenizer=tokenizer,
        normalizer=normalizer,
        index=index,
        wildcard_processor=wildcard_processor,
        documents=documents,
    )


def main() -> None:
    """
    Build the IR pipeline, launch the Tkinter GUI, and start the
    event loop.

    Exits with a non-zero status code and a printed error message if
    the data directory cannot be found, rather than letting an
    unhandled exception crash with a raw traceback.
    """
    try:
        query_processor = build_query_processor(DATA_DIRECTORY)
    except (FileNotFoundError, NotADirectoryError) as error:
        print(f"Error: {error}")
        print(f"Expected a documents folder at: {DATA_DIRECTORY}")
        sys.exit(1)

    root = tk.Tk()
    SearchApp(root, query_processor)
    root.mainloop()


if __name__ == "__main__":
    main()

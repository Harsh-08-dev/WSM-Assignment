"""
document_loader.py

Document Loading Module
------------------------
Responsible for reading raw text documents from a directory on disk
and exposing them as simple, structured in-memory objects.

This module intentionally knows nothing about tokenization,
normalization, or indexing -- its only job is I/O: find `.txt` files
and return their IDs and raw contents.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Document:
    """
    Represents a single loaded document.

    Attributes:
        doc_id: A unique identifier for the document (its filename,
            without extension, by default).
        file_name: The original file name on disk (e.g. "doc1.txt").
        content: The raw, unprocessed text content of the document.
    """

    doc_id: str
    file_name: str
    content: str


class DocumentLoader:
    """
    Loads `.txt` documents from a specified directory.

    Usage:
        loader = DocumentLoader("data")
        documents = loader.load_documents()
    """

    def __init__(self, directory: str) -> None:
        """
        Initialize the loader with the directory to read from.

        Args:
            directory: Path to the folder containing `.txt` files.

        Raises:
            FileNotFoundError: If the directory does not exist.
            NotADirectoryError: If the path is not a directory.
        """
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
        if not os.path.isdir(directory):
            raise NotADirectoryError(f"Not a directory: {directory}")

        self.directory: str = directory

    def load_documents(self) -> List[Document]:
        """
        Load all `.txt` files from the configured directory.

        Returns:
            A list of Document objects, one per `.txt` file found.
            Files are read using UTF-8 encoding. Files that cannot be
            decoded as UTF-8 are skipped with a printed warning rather
            than crashing the whole load process.
        """
        documents: List[Document] = []

        for file_name in sorted(os.listdir(self.directory)):
            if not file_name.lower().endswith(".txt"):
                continue

            file_path = os.path.join(self.directory, file_name)
            if not os.path.isfile(file_path):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as file_handle:
                    content = file_handle.read()
            except UnicodeDecodeError:
                print(f"Warning: could not decode '{file_name}' as UTF-8. Skipping.")
                continue

            doc_id = os.path.splitext(file_name)[0]
            documents.append(Document(doc_id=doc_id, file_name=file_name, content=content))

        return documents

    def load_documents_as_dict(self) -> Dict[str, str]:
        """
        Convenience method returning documents as a simple mapping.

        Returns:
            A dictionary mapping doc_id -> raw content, useful for
            callers that don't need the full Document object.
        """
        return {doc.doc_id: doc.content for doc in self.load_documents()}

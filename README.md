# IR_Project — Python Information Retrieval System

A production-quality, modular **Information Retrieval (IR) System** written in pure Python, featuring an inverted index, wildcard query support, and a minimalistic Tkinter GUI.

---

## Overview

IR_Project lets you index a collection of plain-text documents and search them through a clean desktop interface. It demonstrates a classic IR pipeline — document loading, tokenization, normalization, indexing, and querying — implemented with clean object-oriented design and full separation between business logic and UI.

Core capabilities:

- Load and index any folder of `.txt` documents
- Tokenize and normalize text (case folding, whitespace cleanup, optional stop-word removal / stemming hooks)
- Build and query an in-memory inverted index (term → document mapping)
- Run single-term and multi-term queries with ranked/matching results
- Run wildcard queries using `*` (e.g. `comput*`, `*tion`, `comp*ter`)
- Search and view results through a minimal, modern Tkinter GUI

---

## Project Structure

```text
IR_Project/
│
├── data/                       # Sample corpus of .txt documents
│   ├── doc1.txt
│   ├── doc2.txt
│   └── doc3.txt
│
├── src/                        # Application source code (business logic + UI)
│   ├── __init__.py
│   ├── document_loader.py      # Loads documents from a directory
│   ├── tokenizer.py            # Splits text into tokens, strips punctuation
│   ├── normalizer.py           # Case folding, whitespace cleanup, stop-word/stemming hooks
│   ├── inverted_index.py       # Builds and stores the term → document index
│   ├── query_processor.py      # Preprocesses and executes user queries
│   ├── wildcard_processor.py   # Resolves `*` wildcard queries against the vocabulary
│   └── gui.py                  # Tkinter front end
│
├── main.py                     # Application entry point
├── requirements.txt            # Dependencies (standard library only)
└── README.md                   # This file
```

> **Note:** This README describes the intended architecture and usage of the full system. The remaining project files (modules under `src/`, `main.py`, sample data, etc.) are created separately.

---

## Architecture

The system follows a layered, modular design:

| Layer | Module | Responsibility |
|---|---|---|
| Data Access | `document_loader.py` | Reads raw `.txt` files from disk, returns document IDs and content |
| Text Processing | `tokenizer.py` | Converts raw text into a list of tokens |
| Text Processing | `normalizer.py` | Lowercases, trims whitespace, applies optional stop-word removal/stemming |
| Indexing | `inverted_index.py` | Maintains the term → document-set mapping used for retrieval |
| Query Layer | `query_processor.py` | Runs the same preprocessing pipeline on user queries, matches against the index |
| Query Layer | `wildcard_processor.py` | Expands `*` patterns into matching vocabulary terms before lookup |
| Presentation | `gui.py` | Tkinter UI that calls into the query layer; contains no business logic |
| Orchestration | `main.py` | Wires modules together and launches the GUI |

Design principles applied throughout:

- **Object-oriented design** — each module exposes one or more classes with a single responsibility.
- **Separation of concerns** — UI code never touches tokenization/indexing internals directly; it only calls the query layer's public API.
- **Type hints** — all public functions and methods are annotated.
- **Docstrings & comments** — every class and function is documented.
- **Extensibility** — normalization includes hooks for future stemming/stop-word customization; the index and query layers are decoupled so alternate ranking strategies can be added later.
- **Standard library only** — no external dependencies required to run the core system.

---

## Requirements

- Python 3.9+
- Tkinter (bundled with most standard Python installations; on some Linux distributions install via `sudo apt-get install python3-tk`)

No third-party packages are required — see `requirements.txt`.

---

## Installation

1. Clone or copy the `IR_Project/` directory to your machine.
2. (Optional) Create a virtual environment:
   ```bash
   python -m venv wsm
   source wsm/bin/activate      # Windows: wsm\Scripts\activate
   ```
3. Install dependencies (standard library only, so this is typically a no-op, but included for completeness):
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application

From the project root:

```bash
python main.py
```

This will:

1. Load all `.txt` documents from the `data/` directory.
2. Tokenize and normalize their contents.
3. Build the inverted index.
4. Launch the Tkinter GUI.

---

## Using the GUI

1. Type a query into the search box. Examples:
   - Single term: `information`
   - Multi-term: `information retrieval system`
   - Wildcard: `comput*`, `*tion`, `comp*ter`
2. Click **Search** (or press Enter).
3. Matching document names and relevant snippets appear in the read-only results area.
4. Click **Clear** to reset the search box and results.

---

## Adding Your Own Documents

Place any number of `.txt` files into the `data/` directory (or point the loader at a different directory) and restart the application. The index is rebuilt automatically on startup.

---

## Extending the System

The architecture is designed to be extended without breaking existing modules:

- **Stemming / Lemmatization** — implement inside the hook provided in `normalizer.py`.
- **Stop-word lists** — plug a custom list into the normalizer's stop-word hook.
- **Ranking algorithms** — extend `query_processor.py` with TF-IDF or BM25 scoring without changing the index structure.
- **Alternate file formats** — extend `document_loader.py` to support additional formats (e.g. `.md`, `.pdf`) while keeping the rest of the pipeline unchanged.
- **Persistence** — serialize the inverted index (e.g. with `pickle` or `json`) to avoid rebuilding on every startup.

---

## License

This project is provided as-is for educational and demonstration purposes.

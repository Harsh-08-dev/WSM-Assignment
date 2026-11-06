"""
gui.py

Frontend GUI Module
--------------------
A minimalistic, modern Tkinter front end for the IR system.

This module contains ONLY presentation logic: it builds and lays out
widgets, reads user input, calls into the QueryProcessor's public API,
and renders SearchResult objects. It does not tokenize, normalize,
index, or otherwise implement any retrieval logic itself -- all of
that lives in the `src` business-logic modules and is reached solely
through `QueryProcessor.process_query`.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import List

from src.query_processor import QueryProcessor, SearchResult

# ---------------------------------------------------------------------------
# Minimalistic, modern color / font palette (kept in one place so the look
# of the app can be tweaked without hunting through widget code).
# ---------------------------------------------------------------------------
_BG_COLOR = "#f5f5f7"
_PANEL_COLOR = "#ffffff"
_ACCENT_COLOR = "#2f6fed"
_ACCENT_COLOR_ACTIVE = "#1f52c0"
_TEXT_COLOR = "#1c1c1e"
_MUTED_TEXT_COLOR = "#6e6e73"
_BORDER_COLOR = "#d9d9de"

_FONT_FAMILY = "Segoe UI"
_FONT_NORMAL = (_FONT_FAMILY, 11)
_FONT_TITLE = (_FONT_FAMILY, 16, "bold")
_FONT_BOLD = (_FONT_FAMILY, 11, "bold")
_FONT_MUTED = (_FONT_FAMILY, 9)


class SearchApp:
    """
    Top-level Tkinter application window for the IR system.

    Usage:
        root = tk.Tk()
        app = SearchApp(root, query_processor)
        root.mainloop()
    """

    def __init__(self, root: tk.Tk, query_processor: QueryProcessor) -> None:
        """
        Build and lay out the GUI.

        Args:
            root: The Tkinter root window.
            query_processor: A fully constructed QueryProcessor used to
                execute searches. The GUI never talks to the tokenizer,
                normalizer, index, or wildcard processor directly.
        """
        self.root = root
        self.query_processor = query_processor

        # "OR" (any term matches, ranked) or "AND" (every term must match).
        self.match_mode = tk.StringVar(value="OR")

        self._configure_window()
        self._configure_styles()
        self._build_layout()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def _configure_window(self) -> None:
        """Set window title, size, and background color."""
        self.root.title("IR System — Document Search")
        self.root.geometry("760x560")
        self.root.minsize(560, 420)
        self.root.configure(bg=_BG_COLOR)

    def _configure_styles(self) -> None:
        """Configure ttk styles for a flat, minimalistic appearance."""
        style = ttk.Style(self.root)
        # "clam" is the most reliably themeable built-in ttk theme across
        # platforms, which lets the flat/minimal styling below take effect.
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=_BG_COLOR)
        style.configure("Panel.TFrame", background=_PANEL_COLOR)

        style.configure(
            "TRadiobutton",
            background=_PANEL_COLOR,
            foreground=_TEXT_COLOR,
            font=_FONT_NORMAL,
        )
        style.map("TRadiobutton", background=[("active", _PANEL_COLOR)])

        style.configure(
            "Search.TEntry",
            fieldbackground=_PANEL_COLOR,
            foreground=_TEXT_COLOR,
            bordercolor=_BORDER_COLOR,
            lightcolor=_BORDER_COLOR,
            darkcolor=_BORDER_COLOR,
            padding=8,
        )

        style.configure(
            "Accent.TButton",
            background=_ACCENT_COLOR,
            foreground="#ffffff",
            font=_FONT_BOLD,
            padding=(16, 8),
            borderwidth=0,
        )
        style.map(
            "Accent.TButton",
            background=[("active", _ACCENT_COLOR_ACTIVE), ("pressed", _ACCENT_COLOR_ACTIVE)],
        )

        style.configure(
            "Ghost.TButton",
            background=_PANEL_COLOR,
            foreground=_MUTED_TEXT_COLOR,
            font=_FONT_NORMAL,
            padding=(16, 8),
            borderwidth=1,
        )
        style.map("Ghost.TButton", background=[("active", _BG_COLOR)])

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        """Construct and place all widgets in the window."""
        container = ttk.Frame(self.root, padding=24, style="TFrame")
        container.pack(fill=tk.BOTH, expand=True)

        self._build_header(container)
        self._build_search_bar(container)
        self._build_options_bar(container)
        self._build_results_area(container)
        self._build_status_bar(container)

    def _build_header(self, parent: tk.Widget) -> None:
        """Build the title header at the top of the window."""
        title = tk.Label(
            parent,
            text="Document Search",
            font=_FONT_TITLE,
            bg=_BG_COLOR,
            fg=_TEXT_COLOR,
        )
        title.pack(anchor="w", pady=(0, 4))

        subtitle = tk.Label(
            parent,
            text="Search the indexed collection — supports multi-term and wildcard (*) queries.",
            font=_FONT_MUTED,
            bg=_BG_COLOR,
            fg=_MUTED_TEXT_COLOR,
        )
        subtitle.pack(anchor="w", pady=(0, 16))

    def _build_search_bar(self, parent: tk.Widget) -> None:
        """Build the search input box and Search/Clear buttons."""
        bar = ttk.Frame(parent, style="TFrame")
        bar.pack(fill=tk.X)

        self.search_entry = ttk.Entry(bar, font=_FONT_NORMAL, style="Search.TEntry")
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.search_entry.focus_set()
        self.search_entry.bind("<Return>", lambda _event: self.on_search())

        search_button = ttk.Button(
            bar, text="Search", style="Accent.TButton", command=self.on_search
        )
        search_button.pack(side=tk.LEFT, padx=(8, 0))

        clear_button = ttk.Button(
            bar, text="Clear", style="Ghost.TButton", command=self.on_clear
        )
        clear_button.pack(side=tk.LEFT, padx=(8, 0))

    def _build_options_bar(self, parent: tk.Widget) -> None:
        """Build the AND/OR match-mode toggle."""
        options = ttk.Frame(parent, style="TFrame")
        options.pack(fill=tk.X, pady=(10, 16))

        label = tk.Label(
            options,
            text="Match mode:",
            font=_FONT_NORMAL,
            bg=_BG_COLOR,
            fg=_MUTED_TEXT_COLOR,
        )
        label.pack(side=tk.LEFT, padx=(0, 8))

        or_radio = tk.Radiobutton(
            options,
            text="OR (any term)",
            variable=self.match_mode,
            value="OR",
            font=_FONT_NORMAL,
            bg=_BG_COLOR,
            fg=_TEXT_COLOR,
            activebackground=_BG_COLOR,
            selectcolor=_PANEL_COLOR,
            command=self.on_search_if_query_present,
        )
        or_radio.pack(side=tk.LEFT, padx=(0, 12))

        and_radio = tk.Radiobutton(
            options,
            text="AND (all terms)",
            variable=self.match_mode,
            value="AND",
            font=_FONT_NORMAL,
            bg=_BG_COLOR,
            fg=_TEXT_COLOR,
            activebackground=_BG_COLOR,
            selectcolor=_PANEL_COLOR,
            command=self.on_search_if_query_present,
        )
        and_radio.pack(side=tk.LEFT)

    def _build_results_area(self, parent: tk.Widget) -> None:
        """Build the scrollable, read-only results text area."""
        panel = ttk.Frame(parent, style="Panel.TFrame")
        panel.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(panel)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_text = tk.Text(
            panel,
            wrap=tk.WORD,
            font=_FONT_NORMAL,
            bg=_PANEL_COLOR,
            fg=_TEXT_COLOR,
            relief=tk.FLAT,
            padx=16,
            pady=16,
            yscrollcommand=scrollbar.set,
            state=tk.DISABLED,  # read-only
            cursor="arrow",
        )
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_text.yview)

        # Text tags used to style different parts of a result entry.
        self.results_text.tag_configure("doc_title", font=_FONT_BOLD, foreground=_TEXT_COLOR)
        self.results_text.tag_configure(
            "meta", font=_FONT_MUTED, foreground=_MUTED_TEXT_COLOR
        )
        self.results_text.tag_configure(
            "snippet", font=_FONT_NORMAL, foreground=_TEXT_COLOR
        )
        self.results_text.tag_configure(
            "empty", font=_FONT_NORMAL, foreground=_MUTED_TEXT_COLOR
        )

        self._show_placeholder("Results will appear here once you search.")

    def _build_status_bar(self, parent: tk.Widget) -> None:
        """Build a small status label beneath the results area."""
        self.status_label = tk.Label(
            parent,
            text="Ready.",
            font=_FONT_MUTED,
            bg=_BG_COLOR,
            fg=_MUTED_TEXT_COLOR,
            anchor="w",
        )
        self.status_label.pack(fill=tk.X, pady=(8, 0))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def on_search(self) -> None:
        """Handle a Search button click or Enter key press."""
        query = self.search_entry.get().strip()
        if not query:
            self._show_placeholder("Type a query and press Search.")
            self.status_label.config(text="Ready.")
            return

        results = self.query_processor.process_query(query, match_mode=self.match_mode.get())
        self._render_results(results, query)

    def on_search_if_query_present(self) -> None:
        """Re-run the search when the match-mode toggle changes, but only
        if there is already a query typed in (avoids surprising the user
        with a search firing while the box is empty)."""
        if self.search_entry.get().strip():
            self.on_search()

    def on_clear(self) -> None:
        """Handle a Clear button click: reset input and results."""
        self.search_entry.delete(0, tk.END)
        self.search_entry.focus_set()
        self._show_placeholder("Results will appear here once you search.")
        self.status_label.config(text="Ready.")

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def _show_placeholder(self, message: str) -> None:
        """Display a single muted placeholder line in the results area."""
        self._set_results_text_editable(True)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, message, "empty")
        self._set_results_text_editable(False)

    def _render_results(self, results: List[SearchResult], query: str) -> None:
        """
        Render a list of SearchResult objects into the results area.

        Each result is shown as:
            <file_name>   (score: N, matched: term1, term2)
            <snippet>

        Args:
            results: Ranked search results returned by the QueryProcessor.
            query: The original query string, used for the status message.
        """
        self._set_results_text_editable(True)
        self.results_text.delete("1.0", tk.END)

        if not results:
            self.results_text.insert(
                tk.END, f'No documents matched "{query}".', "empty"
            )
            self._set_results_text_editable(False)
            self.status_label.config(text=f'0 results for "{query}".')
            return

        for i, result in enumerate(results):
            if i > 0:
                self.results_text.insert(tk.END, "\n\n")

            self.results_text.insert(tk.END, result.file_name, "doc_title")

            matched = ", ".join(result.matched_terms) if result.matched_terms else "—"
            meta = f"   (score: {result.score}, matched: {matched})"
            self.results_text.insert(tk.END, meta, "meta")

            if result.snippet:
                self.results_text.insert(tk.END, "\n")
                self.results_text.insert(tk.END, result.snippet, "snippet")

        self._set_results_text_editable(False)
        plural = "result" if len(results) == 1 else "results"
        self.status_label.config(text=f'{len(results)} {plural} for "{query}".')

    def _set_results_text_editable(self, editable: bool) -> None:
        """Toggle the results Text widget between editable and read-only."""
        self.results_text.config(state=tk.NORMAL if editable else tk.DISABLED)

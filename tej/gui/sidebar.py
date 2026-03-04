"""
TejStrike AI - Sidebar Panel
Left sidebar with tool categories, tool list, search, and session info.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from tej.gui.theme import Theme
from tej.tools.registry import (
    get_all_categories, get_tools_by_category, search_tools,
    get_tool_count, TOOL_REGISTRY, ToolInfo
)


class Sidebar(tk.Frame):
    """
    Left sidebar with:
    - Logo / brand area
    - Search bar
    - Tool categories (collapsible)
    - Quick actions
    - Session info
    """

    def __init__(self, parent, on_tool_click=None, on_category_click=None,
                 on_search=None, **kwargs):
        super().__init__(parent, bg=Theme.BG_MEDIUM,
                         width=Theme.SIDEBAR_WIDTH, **kwargs)
        self.pack_propagate(False)

        self.on_tool_click = on_tool_click
        self.on_category_click = on_category_click
        self.on_search = on_search

        self._expanded_categories = set()
        self._tool_buttons = {}

        self._build_ui()

    def _build_ui(self):
        """Build the sidebar UI."""

        # ── Brand Header ─────────────────────────────────────────────
        header = tk.Frame(self, bg=Theme.BG_MEDIUM, padx=16, pady=16)
        header.pack(fill=tk.X)

        # Logo line
        logo_frame = tk.Frame(header, bg=Theme.BG_MEDIUM)
        logo_frame.pack(fill=tk.X)

        # TEJ text logo
        tk.Label(
            logo_frame, text="TEJSTRIKE",
            bg=Theme.BG_MEDIUM, fg=Theme.ACCENT,
            font=Theme.get_font("title", bold=True),
        ).pack(side=tk.LEFT)

        tk.Label(
            logo_frame, text=" AI",
            bg=Theme.BG_MEDIUM, fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("title"),
        ).pack(side=tk.LEFT)

        # Version badge
        ver_frame = tk.Frame(logo_frame, bg=Theme.ACCENT_DIM, padx=6, pady=1)
        ver_frame.pack(side=tk.RIGHT)
        tk.Label(
            ver_frame, text="v2.0",
            bg=Theme.ACCENT_DIM, fg="#ffffff",
            font=Theme.get_font("small"),
        ).pack()

        # Subtitle
        tk.Label(
            header, text="Security Tool Orchestrator",
            bg=Theme.BG_MEDIUM, fg=Theme.TEXT_SECONDARY,
            font=Theme.get_font("small"), anchor="w",
        ).pack(fill=tk.X, pady=(4, 0))

        # ── Search Bar ───────────────────────────────────────────────
        search_frame = tk.Frame(self, bg=Theme.BG_MEDIUM, padx=12)
        search_frame.pack(fill=tk.X, pady=(4, 12))

        search_container = tk.Frame(
            search_frame, bg=Theme.BG_INPUT,
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.ACCENT,
            highlightthickness=1,
        )
        search_container.pack(fill=tk.X)

        # Search icon label
        tk.Label(
            search_container, text=" 🔍 ",
            bg=Theme.BG_INPUT, fg=Theme.TEXT_TERTIARY,
            font=Theme.get_font("small"),
        ).pack(side=tk.LEFT)

        self.search_entry = tk.Entry(
            search_container,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("small"),
            insertbackground=Theme.TEXT_PRIMARY,
            highlightthickness=0,
            borderwidth=0,
            relief="flat",
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=6)
        self.search_entry.insert(0, "Search tools...")
        self.search_entry.config(fg=Theme.TEXT_TERTIARY)

        self.search_entry.bind("<FocusIn>", self._search_focus_in)
        self.search_entry.bind("<FocusOut>", self._search_focus_out)
        self.search_entry.bind("<Return>", self._search_submit)
        self.search_entry.bind("<KeyRelease>", self._search_live)

        # ── Separator ────────────────────────────────────────────────
        tk.Frame(self, height=1, bg=Theme.BORDER).pack(fill=tk.X)

        # ── Tool count ───────────────────────────────────────────────
        count_frame = tk.Frame(self, bg=Theme.BG_MEDIUM, padx=16, pady=8)
        count_frame.pack(fill=tk.X)

        tk.Label(
            count_frame,
            text=f"TOOLS ({get_tool_count()})",
            bg=Theme.BG_MEDIUM, fg=Theme.TEXT_TERTIARY,
            font=Theme.get_font("small", bold=True),
            anchor="w",
        ).pack(fill=tk.X)

        # ── Scrollable category list ─────────────────────────────────
        scroll_frame = tk.Frame(self, bg=Theme.BG_MEDIUM)
        scroll_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(
            scroll_frame, bg=Theme.BG_MEDIUM,
            highlightthickness=0, borderwidth=0,
        )
        scrollbar = tk.Scrollbar(
            scroll_frame, orient="vertical",
            command=canvas.yview,
            bg=Theme.SCROLLBAR_BG,
            troughcolor=Theme.SCROLLBAR_BG,
            activebackground=Theme.SCROLLBAR_HOVER,
            width=8, bd=0,
        )

        self.categories_frame = tk.Frame(canvas, bg=Theme.BG_MEDIUM)
        self.categories_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.categories_frame,
                             anchor="nw", width=Theme.SIDEBAR_WIDTH - 10)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")

        # Populate categories
        self._populate_categories()

        # ── Quick Actions ────────────────────────────────────────────
        tk.Frame(self, height=1, bg=Theme.BORDER).pack(fill=tk.X)

        actions_frame = tk.Frame(self, bg=Theme.BG_MEDIUM, padx=12, pady=8)
        actions_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Quick action buttons
        for text, icon, cmd_text in [
            ("Scan Tools", "⚡", "scan-tools"),
            ("Platform Info", "🖥️", "platform"),
        ]:
            btn = tk.Button(
                actions_frame,
                text=f" {icon}  {text}",
                bg=Theme.BG_HOVER, fg=Theme.TEXT_SECONDARY,
                font=Theme.get_font("small"),
                activebackground=Theme.BORDER,
                activeforeground=Theme.TEXT_PRIMARY,
                relief="flat", cursor="hand2",
                anchor="w", padx=8, pady=4, bd=0,
            )
            btn.pack(fill=tk.X, pady=1)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=Theme.BORDER, fg=Theme.TEXT_PRIMARY))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=Theme.BG_HOVER, fg=Theme.TEXT_SECONDARY))

    def _populate_categories(self):
        """Populate the category tree with tools."""
        cat_names = get_all_categories()

        for cat_name in sorted(cat_names):
            count = len(get_tools_by_category(cat_name))
            color = Theme.get_cat_color(cat_name)

            # Category header
            cat_frame = tk.Frame(self.categories_frame, bg=Theme.BG_MEDIUM)
            cat_frame.pack(fill=tk.X)

            display_name = cat_name.replace("_", " ").title()

            cat_btn = tk.Button(
                cat_frame,
                text=f"  ▸  {display_name}  ({count})",
                bg=Theme.BG_MEDIUM, fg=color,
                font=Theme.get_font("small", bold=True),
                activebackground=Theme.BG_HOVER,
                activeforeground=color,
                relief="flat", cursor="hand2",
                anchor="w", padx=8, pady=6, bd=0,
            )
            cat_btn.pack(fill=tk.X)

            # Tools container (hidden by default)
            tools_frame = tk.Frame(self.categories_frame, bg=Theme.BG_MEDIUM)

            # Populate tools for this category
            tools = get_tools_by_category(cat_name)
            for tool in sorted(tools, key=lambda t: t.name):
                tool_btn = tk.Button(
                    tools_frame,
                    text=f"    •  {tool.name}",
                    bg=Theme.BG_MEDIUM, fg=Theme.TEXT_SECONDARY,
                    font=Theme.get_font("small"),
                    activebackground=Theme.BG_HOVER,
                    activeforeground=Theme.TEXT_PRIMARY,
                    relief="flat", cursor="hand2",
                    anchor="w", padx=16, pady=2, bd=0,
                )
                tool_btn.pack(fill=tk.X)

                # Hover effects
                tool_btn.bind("<Enter>",
                    lambda e, b=tool_btn: b.config(bg=Theme.BG_HOVER, fg=Theme.TEXT_PRIMARY))
                tool_btn.bind("<Leave>",
                    lambda e, b=tool_btn: b.config(bg=Theme.BG_MEDIUM, fg=Theme.TEXT_SECONDARY))

                # Click handler
                name = tool.name
                tool_btn.config(command=lambda n=name: self._tool_clicked(n))
                self._tool_buttons[tool.name] = tool_btn

            # Toggle handler for category
            def make_toggle(cf, tf, cb, cn):
                def toggle():
                    if cn in self._expanded_categories:
                        tf.pack_forget()
                        self._expanded_categories.discard(cn)
                        cb.config(text=cb.cget("text").replace("▾", "▸"))
                    else:
                        tf.pack(fill=tk.X, after=cf)
                        self._expanded_categories.add(cn)
                        cb.config(text=cb.cget("text").replace("▸", "▾"))
                    # Also notify parent
                    if self.on_category_click:
                        self.on_category_click(cn)
                return toggle

            cat_btn.config(
                command=make_toggle(cat_frame, tools_frame, cat_btn, cat_name)
            )

            # Hover effects for category
            cat_btn.bind("<Enter>",
                lambda e, b=cat_btn: b.config(bg=Theme.BG_HOVER))
            cat_btn.bind("<Leave>",
                lambda e, b=cat_btn: b.config(bg=Theme.BG_MEDIUM))

    def _tool_clicked(self, tool_name: str):
        """Handle tool click."""
        if self.on_tool_click:
            self.on_tool_click(tool_name)

    # ── Search ───────────────────────────────────────────────────────

    def _search_focus_in(self, event):
        if self.search_entry.get() == "Search tools...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=Theme.TEXT_PRIMARY)

    def _search_focus_out(self, event):
        if not self.search_entry.get().strip():
            self.search_entry.insert(0, "Search tools...")
            self.search_entry.config(fg=Theme.TEXT_TERTIARY)

    def _search_submit(self, event):
        query = self.search_entry.get().strip()
        if query and query != "Search tools...":
            if self.on_search:
                self.on_search(query)

    def _search_live(self, event):
        """Live search as user types."""
        query = self.search_entry.get().strip()
        if not query or query == "Search tools...":
            # Reset all tool button colors
            for name, btn in self._tool_buttons.items():
                btn.config(fg=Theme.TEXT_SECONDARY)
            return

        # Highlight matching tools
        results = search_tools(query)
        result_names = {t.name for t in results}

        for name, btn in self._tool_buttons.items():
            if name in result_names:
                btn.config(fg=Theme.ACCENT)
            else:
                btn.config(fg=Theme.TEXT_TERTIARY)

    def focus_search(self):
        """Focus the search entry."""
        self.search_entry.focus_set()
        self._search_focus_in(None)

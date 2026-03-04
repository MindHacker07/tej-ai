"""
TejStrike AI - Terminal/Output Panel
Embedded terminal-like widget for displaying tool execution output in real-time.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, List, Dict

from tej.gui.theme import Theme


class TerminalPanel(tk.Frame):
    """
    Terminal-style output panel that shows real-time tool execution output.
    Features: colored output, auto-scroll, copy support, kill button.
    """

    def __init__(self, parent, on_kill=None, **kwargs):
        super().__init__(parent, bg=Theme.BG_DARK, **kwargs)

        self.on_kill = on_kill
        self._build_ui()

    def _build_ui(self):
        """Build the terminal panel UI."""

        # ── Header bar ───────────────────────────────────────────────
        header = tk.Frame(self, bg=Theme.BG_MEDIUM, height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header, text="  ⬛  TERMINAL OUTPUT",
            bg=Theme.BG_MEDIUM, fg=Theme.TEXT_SECONDARY,
            font=Theme.get_font("small", bold=True),
            anchor="w",
        ).pack(side=tk.LEFT, padx=8)

        # Action buttons
        btn_frame = tk.Frame(header, bg=Theme.BG_MEDIUM)
        btn_frame.pack(side=tk.RIGHT, padx=4)

        # Kill button
        self.kill_btn = tk.Button(
            btn_frame, text=" ■ Stop ",
            bg=Theme.ERROR, fg="#ffffff",
            font=Theme.get_font("small"),
            activebackground="#da3633",
            activeforeground="#ffffff",
            relief="flat", cursor="hand2",
            bd=0, padx=6, pady=2,
            command=self._kill,
        )
        self.kill_btn.pack(side=tk.RIGHT, padx=2)

        # Clear button
        clear_btn = tk.Button(
            btn_frame, text=" ✕ Clear ",
            bg=Theme.BG_HOVER, fg=Theme.TEXT_SECONDARY,
            font=Theme.get_font("small"),
            activebackground=Theme.BORDER,
            activeforeground=Theme.TEXT_PRIMARY,
            relief="flat", cursor="hand2",
            bd=0, padx=6, pady=2,
            command=self.clear,
        )
        clear_btn.pack(side=tk.RIGHT, padx=2)

        # Copy button
        copy_btn = tk.Button(
            btn_frame, text=" 📋 Copy ",
            bg=Theme.BG_HOVER, fg=Theme.TEXT_SECONDARY,
            font=Theme.get_font("small"),
            activebackground=Theme.BORDER,
            activeforeground=Theme.TEXT_PRIMARY,
            relief="flat", cursor="hand2",
            bd=0, padx=6, pady=2,
            command=self._copy_output,
        )
        copy_btn.pack(side=tk.RIGHT, padx=2)

        # ── Terminal output area ─────────────────────────────────────
        term_frame = tk.Frame(self, bg="#0a0e14")
        term_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(
            term_frame,
            bg="#0a0e14",
            troughcolor="#0a0e14",
            activebackground=Theme.SCROLLBAR_HOVER,
            highlightbackground="#0a0e14",
            highlightcolor="#0a0e14",
            bd=0, width=8,
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.output = tk.Text(
            term_frame,
            wrap=tk.WORD,
            bg="#0a0e14",
            fg="#b3b1ad",
            font=Theme.get_font("normal", mono=True),
            insertbackground="#0a0e14",
            selectbackground=Theme.ACCENT_DIM,
            selectforeground="#fff",
            highlightthickness=0,
            borderwidth=0,
            padx=12, pady=8,
            state=tk.DISABLED,
            yscrollcommand=scrollbar.set,
        )
        self.output.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.output.yview)

        # ── Configure tags for colored output ────────────────────────
        self.output.tag_configure("command",
                                   foreground=Theme.ACCENT,
                                   font=Theme.get_font("normal", mono=True, bold=True))
        self.output.tag_configure("stdout",
                                   foreground="#b3b1ad")
        self.output.tag_configure("stderr",
                                   foreground=Theme.ERROR)
        self.output.tag_configure("info",
                                   foreground=Theme.TEXT_SECONDARY)
        self.output.tag_configure("success",
                                   foreground=Theme.SUCCESS)
        self.output.tag_configure("warning",
                                   foreground=Theme.WARNING)
        self.output.tag_configure("error",
                                   foreground=Theme.ERROR)
        self.output.tag_configure("highlight",
                                   foreground=Theme.ACCENT,
                                   font=Theme.get_font("normal", mono=True, bold=True))

    # ── Output Methods ───────────────────────────────────────────────

    def append_output(self, text: str, tag: str = "stdout"):
        """Append text to the terminal output."""
        self.output.config(state=tk.NORMAL)

        # Auto-colorize based on content
        if tag == "stdout":
            tag = self._detect_tag(text)

        self.output.insert(tk.END, text, tag)
        self.output.config(state=tk.DISABLED)
        self.output.see(tk.END)

    def _detect_tag(self, text: str) -> str:
        """Auto-detect appropriate tag for output line."""
        lower = text.lower().strip()

        if lower.startswith(("error", "fail", "[!]", "[-]")):
            return "error"
        if lower.startswith(("warning", "warn", "[*]")):
            return "warning"
        if lower.startswith(("[+]", "found", "success")):
            return "success"
        if "open" in lower and ("port" in lower or "/tcp" in lower or "/udp" in lower):
            return "success"
        if "closed" in lower or "filtered" in lower:
            return "warning"
        if lower.startswith(("nmap scan", "starting", "completed", "stats:")):
            return "info"

        return "stdout"

    def show_commands(self, commands: List[Dict[str, str]]):
        """Show suggested commands in the terminal."""
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, "─── Suggested Commands ───\n", "info")
        for i, cmd in enumerate(commands, 1):
            self.output.insert(tk.END, f"[{i}] ", "highlight")
            self.output.insert(tk.END, f"{cmd['description']}\n", "info")
            self.output.insert(tk.END, f"  $ {cmd['command']}\n\n", "command")
        self.output.config(state=tk.DISABLED)
        self.output.see(tk.END)

    def clear(self):
        """Clear the terminal output."""
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.config(state=tk.DISABLED)

    def _copy_output(self):
        """Copy all terminal output to clipboard."""
        content = self.output.get("1.0", "end-1c")
        if content.strip():
            self.clipboard_clear()
            self.clipboard_append(content)

    def _kill(self):
        """Kill running process."""
        if self.on_kill:
            self.on_kill()

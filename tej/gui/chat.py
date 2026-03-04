"""
TejStrike AI - Chat Panel
Chat-style message interface with user/AI message bubbles,
auto-scroll, and input area.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from tej.gui.theme import Theme


class ChatPanel(ttk.Frame):
    """
    Chat interface panel with message bubbles and input area.
    Looks similar to Claude Desktop / ChatGPT interface.
    """

    def __init__(self, parent, on_send=None, on_command=None, **kwargs):
        super().__init__(parent, style="Dark.TFrame", **kwargs)

        self.on_send = on_send
        self.on_command = on_command
        self._messages = []
        self._history = []
        self._history_idx = -1

        self._build_ui()

    def _build_ui(self):
        """Build the chat panel UI."""

        # ── Chat display area ────────────────────────────────────────
        chat_container = tk.Frame(self, bg=Theme.BG_DARK)
        chat_container.pack(fill=tk.BOTH, expand=True)

        # Custom scrollbar
        scrollbar = tk.Scrollbar(
            chat_container,
            bg=Theme.SCROLLBAR_BG,
            troughcolor=Theme.SCROLLBAR_BG,
            activebackground=Theme.SCROLLBAR_HOVER,
            highlightbackground=Theme.BG_DARK,
            highlightcolor=Theme.BG_DARK,
            bd=0, width=10
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.chat_display = tk.Text(
            chat_container,
            wrap=tk.WORD,
            bg=Theme.BG_DARK,
            fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("normal"),
            insertbackground=Theme.BG_DARK,
            selectbackground=Theme.ACCENT_DIM,
            selectforeground="#fff",
            highlightthickness=0,
            borderwidth=0,
            padx=20, pady=12,
            cursor="arrow",
            state=tk.DISABLED,
            yscrollcommand=scrollbar.set,
            spacing1=2, spacing3=2,
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.chat_display.yview)

        # ── Configure text tags for styling ──────────────────────────
        self._setup_tags()

        # ── Separator ────────────────────────────────────────────────
        sep = tk.Frame(self, height=1, bg=Theme.BORDER)
        sep.pack(fill=tk.X)

        # ── Input area ──────────────────────────────────────────────
        input_frame = tk.Frame(self, bg=Theme.BG_MEDIUM, padx=16, pady=12)
        input_frame.pack(fill=tk.X)

        # Input container with rounded look
        input_container = tk.Frame(
            input_frame, bg=Theme.BG_INPUT,
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.ACCENT,
            highlightthickness=1,
            bd=0,
        )
        input_container.pack(fill=tk.X)

        # Input text box
        self.input_box = tk.Text(
            input_container,
            height=2,
            wrap=tk.WORD,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("normal"),
            insertbackground=Theme.TEXT_PRIMARY,
            selectbackground=Theme.ACCENT_DIM,
            selectforeground="#fff",
            highlightthickness=0,
            borderwidth=0,
            padx=12, pady=8,
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Placeholder
        self._placeholder_visible = True
        self._show_placeholder()
        self.input_box.bind("<FocusIn>", self._on_focus_in)
        self.input_box.bind("<FocusOut>", self._on_focus_out)

        # Send button
        self.send_btn = tk.Button(
            input_container,
            text="  ➤  ",
            bg=Theme.ACCENT_DIM,
            fg="#ffffff",
            font=Theme.get_font("medium", bold=True),
            activebackground=Theme.ACCENT,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            borderwidth=0,
            padx=12, pady=4,
            command=self._send,
        )
        self.send_btn.pack(side=tk.RIGHT, padx=(4, 4), pady=4)

        # ── Key bindings ─────────────────────────────────────────────
        self.input_box.bind("<Return>", self._on_enter)
        self.input_box.bind("<Shift-Return>", self._on_shift_enter)
        self.input_box.bind("<Up>", self._on_up)
        self.input_box.bind("<Down>", self._on_down)

        # Hint label
        hint = tk.Label(
            input_frame,
            text="Enter to send • Shift+Enter for new line • /help for commands",
            bg=Theme.BG_MEDIUM,
            fg=Theme.TEXT_TERTIARY,
            font=Theme.get_font("small"),
            anchor="w",
        )
        hint.pack(fill=tk.X, pady=(4, 0))

    def _setup_tags(self):
        """Configure text tags for message styling."""
        d = self.chat_display

        # ── System messages ──────────────────────────────────────────
        d.tag_configure("system_header",
                        foreground=Theme.TEXT_SECONDARY,
                        font=Theme.get_font("small", bold=True),
                        spacing1=8)
        d.tag_configure("system_text",
                        foreground=Theme.TEXT_SECONDARY,
                        font=Theme.get_font("normal"),
                        lmargin1=16, lmargin2=16,
                        spacing3=8)

        # ── User messages ────────────────────────────────────────────
        d.tag_configure("user_header",
                        foreground=Theme.ACCENT,
                        font=Theme.get_font("small", bold=True),
                        spacing1=12)
        d.tag_configure("user_text",
                        foreground=Theme.TEXT_PRIMARY,
                        background=Theme.USER_BUBBLE,
                        font=Theme.get_font("normal"),
                        lmargin1=16, lmargin2=16, rmargin=60,
                        spacing1=2, spacing3=8,
                        relief="flat",
                        borderwidth=0)

        # ── AI messages ──────────────────────────────────────────────
        d.tag_configure("ai_header",
                        foreground=Theme.SUCCESS,
                        font=Theme.get_font("small", bold=True),
                        spacing1=12)
        d.tag_configure("ai_text",
                        foreground=Theme.AI_BUBBLE_TEXT,
                        font=Theme.get_font("normal"),
                        lmargin1=16, lmargin2=16,
                        spacing1=2, spacing3=8)

        # ── Code / command styling ───────────────────────────────────
        d.tag_configure("code",
                        foreground=Theme.TEXT_CODE,
                        font=Theme.get_font("normal", mono=True),
                        background="#1a2332",
                        lmargin1=32, lmargin2=32,
                        spacing1=2, spacing3=2)

        # ── Timestamp ────────────────────────────────────────────────
        d.tag_configure("timestamp",
                        foreground=Theme.TEXT_TERTIARY,
                        font=Theme.get_font("small"))

        # ── Separator ────────────────────────────────────────────────
        d.tag_configure("separator",
                        foreground=Theme.BORDER,
                        font=Theme.get_font("small"),
                        justify="center",
                        spacing1=4, spacing3=4)

        # ── Clickable command ────────────────────────────────────────
        d.tag_configure("clickable",
                        foreground=Theme.ACCENT,
                        font=Theme.get_font("normal", mono=True),
                        underline=True)
        d.tag_bind("clickable", "<Enter>",
                   lambda e: d.config(cursor="hand2"))
        d.tag_bind("clickable", "<Leave>",
                   lambda e: d.config(cursor="arrow"))

    # ── Message Adding ───────────────────────────────────────────────

    def add_message(self, role: str, text: str):
        """
        Add a message to the chat display.
        role: 'user', 'ai', or 'system'
        """
        self._messages.append({"role": role, "text": text, "time": datetime.now()})

        self.chat_display.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")

        if role == "system":
            self.chat_display.insert(tk.END, f"  SYSTEM • {timestamp}\n", "system_header")
            self.chat_display.insert(tk.END, f"  {text}\n\n", "system_text")

        elif role == "user":
            self.chat_display.insert(tk.END, f"  YOU • {timestamp}\n", "user_header")
            # Render user text with code detection
            self._render_text(text, "user_text")
            self.chat_display.insert(tk.END, "\n", "user_text")

        elif role == "ai":
            self.chat_display.insert(tk.END, f"  TEJSTRIKE AI • {timestamp}\n", "ai_header")
            # Render AI text with code detection
            self._render_text(text, "ai_text")
            self.chat_display.insert(tk.END, "\n", "ai_text")

        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def _render_text(self, text: str, base_tag: str):
        """Render text with inline code detection for $ commands."""
        lines = text.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("$ "):
                # Command line — render as clickable code
                self.chat_display.insert(tk.END, f"  {line}\n", ("code",))
            elif stripped.startswith("[") and "] " in stripped:
                # Numbered command suggestion
                self.chat_display.insert(tk.END, f"  {line}\n", (base_tag,))
            else:
                self.chat_display.insert(tk.END, f"  {line}\n", (base_tag,))

    # ── Placeholder ──────────────────────────────────────────────────

    def _show_placeholder(self):
        self.input_box.insert("1.0", "Ask TejStrike anything... (e.g., 'scan 192.168.1.1')")
        self.input_box.config(fg=Theme.TEXT_TERTIARY)
        self._placeholder_visible = True

    def _on_focus_in(self, event):
        if self._placeholder_visible:
            self.input_box.delete("1.0", tk.END)
            self.input_box.config(fg=Theme.TEXT_PRIMARY)
            self._placeholder_visible = False

    def _on_focus_out(self, event):
        content = self.input_box.get("1.0", "end-1c").strip()
        if not content:
            self._show_placeholder()

    # ── Input Handling ───────────────────────────────────────────────

    def _on_enter(self, event):
        """Handle Enter key — send message."""
        self._send()
        return "break"  # Prevent newline

    def _on_shift_enter(self, event):
        """Handle Shift+Enter — insert newline."""
        return None  # Allow default behavior

    def _on_up(self, event):
        """Navigate command history (up)."""
        if self._history:
            if self._history_idx < len(self._history) - 1:
                self._history_idx += 1
            self.input_box.delete("1.0", tk.END)
            self.input_box.insert("1.0", self._history[self._history_idx])
            return "break"

    def _on_down(self, event):
        """Navigate command history (down)."""
        if self._history and self._history_idx > 0:
            self._history_idx -= 1
            self.input_box.delete("1.0", tk.END)
            self.input_box.insert("1.0", self._history[self._history_idx])
        elif self._history_idx <= 0:
            self._history_idx = -1
            self.input_box.delete("1.0", tk.END)
        return "break"

    def _send(self):
        """Send the current input."""
        if self._placeholder_visible:
            return

        text = self.input_box.get("1.0", "end-1c").strip()
        if not text:
            return

        # Add to history
        self._history.insert(0, text)
        self._history_idx = -1

        # Clear input
        self.input_box.delete("1.0", tk.END)

        # Route to appropriate handler
        if text.startswith("/"):
            if self.on_command:
                self.on_command(text)
        else:
            if self.on_send:
                self.on_send(text)

    # ── Utilities ────────────────────────────────────────────────────

    def clear(self):
        """Clear all messages."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self._messages.clear()

    def get_all_text(self) -> str:
        """Get all chat text for export."""
        lines = []
        for msg in self._messages:
            t = msg["time"].strftime("%H:%M:%S")
            role = msg["role"].upper()
            lines.append(f"[{t}] {role}: {msg['text']}")
            lines.append("")
        return "\n".join(lines)

    def focus_input(self):
        """Focus the input box."""
        self.input_box.focus_set()
        if self._placeholder_visible:
            self._on_focus_in(None)

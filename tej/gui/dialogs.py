"""
Tej AI - GUI Dialogs
Modal dialogs for tool info, sessions, settings, and about.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from tej.gui.theme import Theme


class BaseDialog(tk.Toplevel):
    """Base class for Tej modal dialogs."""

    def __init__(self, parent, title="Tej AI", width=500, height=400):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=Theme.BG_DARK)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{px}+{py}")
        self.minsize(width, height)

        # Escape to close
        self.bind("<Escape>", lambda e: self.destroy())


class ToolInfoDialog(BaseDialog):
    """Dialog showing detailed information about a security tool."""

    def __init__(self, parent, tool_info, platform_mgr):
        super().__init__(parent, title=f"Tool: {tool_info.name}", width=550, height=500)
        self.tool = tool_info
        self.platform_mgr = platform_mgr
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=Theme.BG_MEDIUM, padx=20, pady=16)
        header.pack(fill=tk.X)

        color = Theme.get_cat_color(self.tool.category)

        tk.Label(
            header, text=self.tool.name,
            bg=Theme.BG_MEDIUM, fg=color,
            font=Theme.get_font("large", bold=True),
        ).pack(anchor="w")

        # Category badge
        cat_frame = tk.Frame(header, bg=color, padx=8, pady=2)
        cat_frame.pack(anchor="w", pady=(6, 0))
        tk.Label(
            cat_frame,
            text=self.tool.category.replace("_", " ").title(),
            bg=color, fg="#ffffff",
            font=Theme.get_font("small", bold=True),
        ).pack()

        # Content
        content = tk.Frame(self, bg=Theme.BG_DARK, padx=20, pady=16)
        content.pack(fill=tk.BOTH, expand=True)

        # Description
        tk.Label(
            content, text="Description",
            bg=Theme.BG_DARK, fg=Theme.TEXT_SECONDARY,
            font=Theme.get_font("small", bold=True), anchor="w",
        ).pack(fill=tk.X, pady=(0, 4))

        tk.Label(
            content, text=self.tool.description,
            bg=Theme.BG_DARK, fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("normal"),
            wraplength=480, justify="left", anchor="w",
        ).pack(fill=tk.X, pady=(0, 12))

        # Installation status
        check = self.platform_mgr.check_tool(self.tool.name)
        status_color = Theme.SUCCESS if check.available else Theme.ERROR
        status_text = "✓ Installed" if check.available else "✗ Not Installed"

        tk.Label(
            content, text="Status",
            bg=Theme.BG_DARK, fg=Theme.TEXT_SECONDARY,
            font=Theme.get_font("small", bold=True), anchor="w",
        ).pack(fill=tk.X, pady=(0, 4))

        tk.Label(
            content, text=status_text,
            bg=Theme.BG_DARK, fg=status_color,
            font=Theme.get_font("normal", bold=True), anchor="w",
        ).pack(fill=tk.X, pady=(0, 12))

        # Usage examples
        if self.tool.usage_examples:
            tk.Label(
                content, text="Usage Examples",
                bg=Theme.BG_DARK, fg=Theme.TEXT_SECONDARY,
                font=Theme.get_font("small", bold=True), anchor="w",
            ).pack(fill=tk.X, pady=(0, 4))

            for example in self.tool.usage_examples[:5]:
                example_frame = tk.Frame(content, bg="#1a2332", padx=10, pady=4)
                example_frame.pack(fill=tk.X, pady=1)
                tk.Label(
                    example_frame, text=f"$ {example}",
                    bg="#1a2332", fg=Theme.TEXT_CODE,
                    font=Theme.get_font("small", mono=True),
                    anchor="w",
                ).pack(fill=tk.X)

        # Common flags
        if self.tool.common_flags:
            tk.Label(
                content, text="\nCommon Flags",
                bg=Theme.BG_DARK, fg=Theme.TEXT_SECONDARY,
                font=Theme.get_font("small", bold=True), anchor="w",
            ).pack(fill=tk.X, pady=(0, 4))

            flags_text = tk.Text(
                content, height=min(len(self.tool.common_flags), 6),
                bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                font=Theme.get_font("small", mono=True),
                highlightthickness=0, borderwidth=0,
                padx=10, pady=6, wrap=tk.NONE,
            )
            flags_text.pack(fill=tk.X, pady=(0, 8))
            for flag, desc in self.tool.common_flags.items():
                flags_text.insert(tk.END, f"  {flag:12s} {desc}\n")
            flags_text.config(state=tk.DISABLED)

        # Tags
        if self.tool.tags:
            tag_frame = tk.Frame(content, bg=Theme.BG_DARK)
            tag_frame.pack(fill=tk.X, pady=(8, 0))
            for tag in self.tool.tags:
                badge = tk.Frame(tag_frame, bg=Theme.BG_HOVER, padx=8, pady=2)
                badge.pack(side=tk.LEFT, padx=(0, 4))
                tk.Label(
                    badge, text=tag,
                    bg=Theme.BG_HOVER, fg=Theme.TEXT_SECONDARY,
                    font=Theme.get_font("small"),
                ).pack()

        # Close button
        close_frame = tk.Frame(self, bg=Theme.BG_DARK, padx=20, pady=12)
        close_frame.pack(fill=tk.X)
        tk.Button(
            close_frame, text="Close",
            bg=Theme.BG_HOVER, fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("normal"),
            activebackground=Theme.BORDER,
            relief="flat", cursor="hand2", bd=0,
            padx=20, pady=6,
            command=self.destroy,
        ).pack(side=tk.RIGHT)


class SessionDialog(BaseDialog):
    """Dialog for managing sessions."""

    def __init__(self, parent, session_mgr, on_message=None):
        super().__init__(parent, title="Session Manager", width=500, height=400)
        self.session_mgr = session_mgr
        self.on_message = on_message
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=Theme.BG_MEDIUM, padx=20, pady=12)
        header.pack(fill=tk.X)

        tk.Label(
            header, text="📋  Sessions",
            bg=Theme.BG_MEDIUM, fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("large", bold=True),
        ).pack(anchor="w")

        # Session list
        content = tk.Frame(self, bg=Theme.BG_DARK, padx=20, pady=12)
        content.pack(fill=tk.BOTH, expand=True)

        sessions = self.session_mgr.list_sessions()

        if sessions:
            for sess in sessions:
                sess_frame = tk.Frame(content, bg=Theme.BG_LIGHT, padx=12, pady=8)
                sess_frame.pack(fill=tk.X, pady=2)

                tk.Label(
                    sess_frame, text=sess["id"],
                    bg=Theme.BG_LIGHT, fg=Theme.ACCENT,
                    font=Theme.get_font("normal", bold=True), anchor="w",
                ).pack(fill=tk.X)

                info_text = (
                    f"Started: {sess['started']} | "
                    f"Phase: {sess['phase']} | "
                    f"Commands: {sess['commands']}"
                )
                tk.Label(
                    sess_frame, text=info_text,
                    bg=Theme.BG_LIGHT, fg=Theme.TEXT_SECONDARY,
                    font=Theme.get_font("small"), anchor="w",
                ).pack(fill=tk.X)

                # Load button
                sid = sess["id"]
                tk.Button(
                    sess_frame, text="Load",
                    bg=Theme.ACCENT_DIM, fg="#fff",
                    font=Theme.get_font("small"),
                    relief="flat", cursor="hand2", bd=0,
                    padx=10, pady=2,
                    command=lambda s=sid: self._load(s),
                ).pack(anchor="e", pady=(4, 0))
        else:
            tk.Label(
                content, text="No saved sessions found.",
                bg=Theme.BG_DARK, fg=Theme.TEXT_SECONDARY,
                font=Theme.get_font("normal"),
            ).pack(pady=20)

        # Close
        btn_frame = tk.Frame(self, bg=Theme.BG_DARK, padx=20, pady=12)
        btn_frame.pack(fill=tk.X)
        tk.Button(
            btn_frame, text="Close",
            bg=Theme.BG_HOVER, fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("normal"),
            relief="flat", cursor="hand2", bd=0,
            padx=20, pady=6,
            command=self.destroy,
        ).pack(side=tk.RIGHT)

    def _load(self, session_id):
        self.session_mgr.load_session(session_id)
        if self.on_message:
            self.on_message(f"Session loaded: {session_id}")
        self.destroy()


class SettingsDialog(BaseDialog):
    """Settings dialog."""

    def __init__(self, parent, config, config_mgr):
        super().__init__(parent, title="Settings", width=480, height=420)
        self.config = config
        self.config_mgr = config_mgr
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=Theme.BG_MEDIUM, padx=20, pady=12)
        header.pack(fill=tk.X)

        tk.Label(
            header, text="⚙️  Settings",
            bg=Theme.BG_MEDIUM, fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("large", bold=True),
        ).pack(anchor="w")

        content = tk.Frame(self, bg=Theme.BG_DARK, padx=20, pady=16)
        content.pack(fill=tk.BOTH, expand=True)

        # Default target
        tk.Label(
            content, text="Default Target:",
            bg=Theme.BG_DARK, fg=Theme.TEXT_SECONDARY,
            font=Theme.get_font("small", bold=True), anchor="w",
        ).pack(fill=tk.X, pady=(0, 4))

        self.target_var = tk.StringVar(value=self.config.default_target or "")
        target_entry = tk.Entry(
            content, textvariable=self.target_var,
            bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("normal"),
            insertbackground=Theme.TEXT_PRIMARY,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.ACCENT,
            borderwidth=0, relief="flat",
        )
        target_entry.pack(fill=tk.X, pady=(0, 16), ipady=6)

        # Default timeout
        tk.Label(
            content, text="Default Timeout (seconds):",
            bg=Theme.BG_DARK, fg=Theme.TEXT_SECONDARY,
            font=Theme.get_font("small", bold=True), anchor="w",
        ).pack(fill=tk.X, pady=(0, 4))

        self.timeout_var = tk.StringVar(value=str(self.config.default_timeout))
        timeout_entry = tk.Entry(
            content, textvariable=self.timeout_var,
            bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("normal"),
            insertbackground=Theme.TEXT_PRIMARY,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.ACCENT,
            borderwidth=0, relief="flat",
        )
        timeout_entry.pack(fill=tk.X, pady=(0, 16), ipady=6)

        # Output directory
        tk.Label(
            content, text="Output Directory:",
            bg=Theme.BG_DARK, fg=Theme.TEXT_SECONDARY,
            font=Theme.get_font("small", bold=True), anchor="w",
        ).pack(fill=tk.X, pady=(0, 4))

        self.output_var = tk.StringVar(value=self.config.output_dir)
        output_entry = tk.Entry(
            content, textvariable=self.output_var,
            bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("normal"),
            insertbackground=Theme.TEXT_PRIMARY,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.ACCENT,
            borderwidth=0, relief="flat",
        )
        output_entry.pack(fill=tk.X, pady=(0, 16), ipady=6)

        # Auto-session
        self.auto_session_var = tk.BooleanVar(value=self.config.auto_session)
        tk.Checkbutton(
            content, text="Auto-start session on launch",
            variable=self.auto_session_var,
            bg=Theme.BG_DARK, fg=Theme.TEXT_PRIMARY,
            selectcolor=Theme.BG_INPUT,
            activebackground=Theme.BG_DARK,
            activeforeground=Theme.TEXT_PRIMARY,
            font=Theme.get_font("normal"),
        ).pack(fill=tk.X, pady=(0, 8))

        # Verbose
        self.verbose_var = tk.BooleanVar(value=self.config.verbose)
        tk.Checkbutton(
            content, text="Verbose output",
            variable=self.verbose_var,
            bg=Theme.BG_DARK, fg=Theme.TEXT_PRIMARY,
            selectcolor=Theme.BG_INPUT,
            activebackground=Theme.BG_DARK,
            activeforeground=Theme.TEXT_PRIMARY,
            font=Theme.get_font("normal"),
        ).pack(fill=tk.X, pady=(0, 8))

        # Buttons
        btn_frame = tk.Frame(self, bg=Theme.BG_DARK, padx=20, pady=12)
        btn_frame.pack(fill=tk.X)

        tk.Button(
            btn_frame, text="Cancel",
            bg=Theme.BG_HOVER, fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("normal"),
            relief="flat", cursor="hand2", bd=0,
            padx=20, pady=6,
            command=self.destroy,
        ).pack(side=tk.RIGHT, padx=(8, 0))

        tk.Button(
            btn_frame, text="Save",
            bg=Theme.ACCENT_DIM, fg="#ffffff",
            font=Theme.get_font("normal", bold=True),
            activebackground=Theme.ACCENT,
            relief="flat", cursor="hand2", bd=0,
            padx=20, pady=6,
            command=self._save,
        ).pack(side=tk.RIGHT)

    def _save(self):
        self.config.default_target = self.target_var.get().strip() or None
        try:
            self.config.default_timeout = int(self.timeout_var.get())
        except ValueError:
            pass
        self.config.output_dir = self.output_var.get().strip()
        self.config.auto_session = self.auto_session_var.get()
        self.config.verbose = self.verbose_var.get()
        self.config_mgr.config = self.config
        self.config_mgr.save()
        self.destroy()


class AboutDialog(BaseDialog):
    """About dialog."""

    def __init__(self, parent):
        super().__init__(parent, title="About Tej AI", width=420, height=380)
        self._build_ui()

    def _build_ui(self):
        content = tk.Frame(self, bg=Theme.BG_DARK, padx=30, pady=30)
        content.pack(fill=tk.BOTH, expand=True)

        # Logo
        tk.Label(
            content, text="TEJ AI",
            bg=Theme.BG_DARK, fg=Theme.ACCENT,
            font=Theme.get_font("hero", bold=True),
        ).pack(pady=(0, 4))

        tk.Label(
            content, text="AI-Powered Security Tool Orchestrator",
            bg=Theme.BG_DARK, fg=Theme.TEXT_SECONDARY,
            font=Theme.get_font("normal"),
        ).pack(pady=(0, 16))

        # Version
        ver_frame = tk.Frame(content, bg=Theme.ACCENT_DIM, padx=16, pady=4)
        ver_frame.pack()
        tk.Label(
            ver_frame, text="Version 1.0.0",
            bg=Theme.ACCENT_DIM, fg="#ffffff",
            font=Theme.get_font("normal", bold=True),
        ).pack()

        tk.Label(
            content, text="\nKali Linux & Windows Compatible\n"
                          "91+ Security Tools Integrated\n"
                          "Natural Language Interface\n",
            bg=Theme.BG_DARK, fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("normal"),
            justify="center",
        ).pack(pady=(16, 8))

        tk.Label(
            content,
            text="github.com/MindHacker07/tej-ai",
            bg=Theme.BG_DARK, fg=Theme.TEXT_LINK,
            font=Theme.get_font("small"),
            cursor="hand2",
        ).pack(pady=(0, 16))

        tk.Label(
            content, text="© 2026 Tejas Tayde",
            bg=Theme.BG_DARK, fg=Theme.TEXT_TERTIARY,
            font=Theme.get_font("small"),
        ).pack()

        # Close
        tk.Button(
            content, text="Close",
            bg=Theme.BG_HOVER, fg=Theme.TEXT_PRIMARY,
            font=Theme.get_font("normal"),
            relief="flat", cursor="hand2", bd=0,
            padx=20, pady=6,
            command=self.destroy,
        ).pack(side=tk.BOTTOM, pady=(12, 0))

"""
TejStrike AI - Main GUI Application
Desktop application window with sidebar, chat interface, and tool panels.
Supports multi-model LLM integration and MCP server connections.
"""

import os
import sys
import platform
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from tej.gui.theme import Theme
from tej.gui.chat import ChatPanel
from tej.gui.sidebar import Sidebar
from tej.gui.terminal import TerminalPanel
from tej.gui.dialogs import ToolInfoDialog, SessionDialog, AboutDialog, SettingsDialog

from tej.core.engine import TejBrain, TaskCategory
from tej.core.platform_manager import PlatformManager
from tej.core.executor import ToolExecutor, ExecutionConfig
from tej.core.session import SessionManager
from tej.core.agent import TejStrikeAgent
from tej.core.llm_provider import LLMConfig, LLMProvider, AVAILABLE_MODELS, detect_installed_providers
from tej.core.mcp_client import MCPManager
from tej.tools.registry import (
    get_all_tools, get_tools_by_category, search_tools,
    get_all_categories, get_tool_count, TOOL_REGISTRY, ToolInfo
)
from tej.tools.parsers import OutputParserFactory
from tej.utils.config import ConfigManager, LLMSettings


class TejApp:
    """Main TejStrike AI Desktop Application."""

    VERSION = "2.0.0"

    def __init__(self):
        # ── Initialize Backend ───────────────────────────────────────
        self.brain = TejBrain()
        self.platform_mgr = PlatformManager()
        self.executor = ToolExecutor(self.platform_mgr)
        self.config_mgr = ConfigManager()
        self.config = self.config_mgr.load()
        self.session_mgr = SessionManager(self.brain, self.config.output_dir)

        # Initialize AI agent with LLM and MCP support
        self.mcp_manager = MCPManager()
        llm_config = None
        if self.config.llm and self.config.llm.provider:
            try:
                llm_config = LLMConfig(
                    provider=LLMProvider(self.config.llm.provider),
                    model=self.config.llm.model,
                    api_key=self.config.llm.api_key,
                    api_base_url=self.config.llm.api_base_url,
                    temperature=self.config.llm.temperature,
                    max_tokens=self.config.llm.max_tokens,
                )
            except (ValueError, KeyError):
                pass
        self.agent = TejStrikeAgent(self.brain, llm_config, self.mcp_manager)

        # State
        self.current_target = self.config.default_target or ""
        self.is_executing = False
        self.command_history = []

        # ── Build Window ─────────────────────────────────────────────
        self.root = tk.Tk()
        self.root.title("TejStrike AI \u2014 Security Tool Orchestrator")
        self.root.configure(bg=Theme.BG_DARK)

        # Window size & position
        self.root.minsize(Theme.MIN_WIDTH, Theme.MIN_HEIGHT)
        self._center_window(1280, 800)

        # Try to set icon
        self._set_icon()

        # Configure ttk styles
        self._setup_styles()

        # ── Build UI ─────────────────────────────────────────────────
        self._build_menu()
        self._build_layout()

        # ── Wire up output streaming ────────────────────────────────
        self.executor.add_output_callback(self._on_tool_output_line)

        # ── Auto-start session ──────────────────────────────────────
        self.session_mgr.new_session()
        # Determine LLM status
        llm_status = ""
        if self.agent.has_llm:
            llm_status = f"\nLLM: {self.config.llm.provider}/{self.config.llm.model} ✓"
        else:
            llm_status = "\nLLM: Not configured (using built-in engine)"

        self._system_message(
            f"Welcome to TejStrike AI v{self.VERSION}\n"
            f"Platform: {self.platform_mgr.platform.value.title()} | "
            f"Tools registered: {get_tool_count()}"
            f"{llm_status}\n\n"
            "Type a natural language command below — e.g.:\n"
            '  • "scan 192.168.1.1"\n'
            '  • "find subdomains of example.com"\n'
            '  • "crack hashes with john"\n'
            '  • "search sql injection tools"\n\n'
            "Configure LLM: Settings → AI Model (Ctrl+,)"
        )

    # ── Window Helpers ───────────────────────────────────────────────

    def _center_window(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _set_icon(self):
        """Set window icon (skip on error)."""
        try:
            # Use a built-in tkinter icon fallback
            icon_path = os.path.join(
                os.path.dirname(__file__), "assets", "tej_icon.png"
            )
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, img)
        except Exception:
            pass

    # ── TTK Styles ───────────────────────────────────────────────────

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # General
        self.style.configure(".", background=Theme.BG_DARK,
                             foreground=Theme.TEXT_PRIMARY,
                             font=Theme.get_font())

        # Frame
        self.style.configure("Dark.TFrame", background=Theme.BG_DARK)
        self.style.configure("Medium.TFrame", background=Theme.BG_MEDIUM)
        self.style.configure("Card.TFrame", background=Theme.BG_LIGHT,
                             relief="flat")

        # Label
        self.style.configure("Dark.TLabel", background=Theme.BG_DARK,
                             foreground=Theme.TEXT_PRIMARY)
        self.style.configure("Medium.TLabel", background=Theme.BG_MEDIUM,
                             foreground=Theme.TEXT_PRIMARY)
        self.style.configure("Sub.TLabel", background=Theme.BG_MEDIUM,
                             foreground=Theme.TEXT_SECONDARY,
                             font=Theme.get_font("small"))
        self.style.configure("Title.TLabel", background=Theme.BG_DARK,
                             foreground=Theme.TEXT_PRIMARY,
                             font=Theme.get_font("title", bold=True))
        self.style.configure("Accent.TLabel", background=Theme.BG_DARK,
                             foreground=Theme.ACCENT,
                             font=Theme.get_font("normal", bold=True))

        # Button - primary
        self.style.configure("Accent.TButton",
                             background=Theme.ACCENT_DIM,
                             foreground="#ffffff",
                             font=Theme.get_font("normal", bold=True),
                             padding=(16, 8))
        self.style.map("Accent.TButton",
                       background=[("active", Theme.ACCENT),
                                   ("disabled", Theme.BG_HOVER)])

        # Button - secondary
        self.style.configure("Secondary.TButton",
                             background=Theme.BG_HOVER,
                             foreground=Theme.TEXT_PRIMARY,
                             font=Theme.get_font("normal"),
                             padding=(12, 6))
        self.style.map("Secondary.TButton",
                       background=[("active", Theme.BORDER)])

        # Button - danger
        self.style.configure("Danger.TButton",
                             background=Theme.ERROR,
                             foreground="#ffffff",
                             padding=(12, 6))
        self.style.map("Danger.TButton",
                       background=[("active", "#da3633")])

        # Entry
        self.style.configure("Dark.TEntry",
                             fieldbackground=Theme.BG_INPUT,
                             foreground=Theme.TEXT_PRIMARY,
                             insertcolor=Theme.TEXT_PRIMARY,
                             borderwidth=1,
                             relief="solid")

        # Separator
        self.style.configure("Dark.TSeparator",
                             background=Theme.BORDER)

        # Notebook (tabs)
        self.style.configure("Dark.TNotebook",
                             background=Theme.BG_DARK,
                             borderwidth=0)
        self.style.configure("Dark.TNotebook.Tab",
                             background=Theme.BG_MEDIUM,
                             foreground=Theme.TEXT_SECONDARY,
                             padding=(12, 6),
                             font=Theme.get_font("small"))
        self.style.map("Dark.TNotebook.Tab",
                       background=[("selected", Theme.BG_DARK)],
                       foreground=[("selected", Theme.TEXT_PRIMARY)])

        # Progressbar
        self.style.configure("Accent.Horizontal.TProgressbar",
                             troughcolor=Theme.BG_INPUT,
                             background=Theme.ACCENT,
                             borderwidth=0)

    # ── Menu Bar ─────────────────────────────────────────────────────

    def _build_menu(self):
        menubar = tk.Menu(self.root, bg=Theme.BG_MEDIUM,
                          fg=Theme.TEXT_PRIMARY,
                          activebackground=Theme.BG_HOVER,
                          activeforeground=Theme.TEXT_PRIMARY,
                          borderwidth=0, relief="flat")

        # File
        file_menu = tk.Menu(menubar, tearoff=0,
                            bg=Theme.BG_MEDIUM, fg=Theme.TEXT_PRIMARY,
                            activebackground=Theme.ACCENT_DIM,
                            activeforeground="#fff")
        file_menu.add_command(label="New Session", accelerator="Ctrl+N",
                              command=self._new_session)
        file_menu.add_command(label="Save Session", accelerator="Ctrl+S",
                              command=self._save_session)
        file_menu.add_command(label="Load Session...",
                              command=self._load_session)
        file_menu.add_separator()
        file_menu.add_command(label="Export Chat...",
                              command=self._export_chat)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", accelerator="Ctrl+,",
                              command=self._open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", accelerator="Ctrl+Q",
                              command=self._quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Tools
        tools_menu = tk.Menu(menubar, tearoff=0,
                             bg=Theme.BG_MEDIUM, fg=Theme.TEXT_PRIMARY,
                             activebackground=Theme.ACCENT_DIM,
                             activeforeground="#fff")
        tools_menu.add_command(label="Scan System Tools",
                               command=self._scan_tools)
        tools_menu.add_command(label="Search Tools...", accelerator="Ctrl+K",
                               command=self._focus_search)
        tools_menu.add_separator()
        tools_menu.add_command(label="Platform Info",
                               command=self._show_platform)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # View
        view_menu = tk.Menu(menubar, tearoff=0,
                            bg=Theme.BG_MEDIUM, fg=Theme.TEXT_PRIMARY,
                            activebackground=Theme.ACCENT_DIM,
                            activeforeground="#fff")
        self._show_sidebar_var = tk.BooleanVar(value=True)
        self._show_terminal_var = tk.BooleanVar(value=True)
        view_menu.add_checkbutton(label="Show Sidebar",
                                  variable=self._show_sidebar_var,
                                  command=self._toggle_sidebar)
        view_menu.add_checkbutton(label="Show Terminal",
                                  variable=self._show_terminal_var,
                                  command=self._toggle_terminal)
        view_menu.add_separator()
        view_menu.add_command(label="Clear Chat", accelerator="Ctrl+L",
                              command=self._clear_chat)
        menubar.add_cascade(label="View", menu=view_menu)

        # Help
        help_menu = tk.Menu(menubar, tearoff=0,
                            bg=Theme.BG_MEDIUM, fg=Theme.TEXT_PRIMARY,
                            activebackground=Theme.ACCENT_DIM,
                            activeforeground="#fff")
        help_menu.add_command(label="About TejStrike AI",
                              command=self._show_about)
        help_menu.add_command(label="Keyboard Shortcuts",
                              command=self._show_shortcuts)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    # ── Main Layout ──────────────────────────────────────────────────

    def _build_layout(self):
        """Build the three-panel layout: sidebar | chat | terminal."""

        # Main container
        self.main_frame = ttk.Frame(self.root, style="Dark.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # ── Sidebar (left) ──────────────────────────────────────────
        self.sidebar = Sidebar(
            self.main_frame,
            on_tool_click=self._on_tool_click,
            on_category_click=self._on_category_click,
            on_search=self._on_sidebar_search,
        )
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Separator
        sep1 = tk.Frame(self.main_frame, width=1, bg=Theme.BORDER)
        sep1.pack(side=tk.LEFT, fill=tk.Y)

        # ── Right area (chat + terminal vertically) ─────────────────
        self.right_pane = ttk.Frame(self.main_frame, style="Dark.TFrame")
        self.right_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Use PanedWindow for resizable split
        self.vpaned = tk.PanedWindow(
            self.right_pane, orient=tk.VERTICAL,
            bg=Theme.BORDER, sashwidth=3,
            borderwidth=0, relief="flat"
        )
        self.vpaned.pack(fill=tk.BOTH, expand=True)

        # Chat panel (top)
        self.chat_panel = ChatPanel(
            self.vpaned,
            on_send=self._on_user_input,
            on_command=self._on_command,
        )
        self.vpaned.add(self.chat_panel, minsize=300, stretch="always")

        # Terminal panel (bottom)
        self.terminal_panel = TerminalPanel(
            self.vpaned,
            on_kill=self._kill_current,
        )
        self.vpaned.add(self.terminal_panel, minsize=150, stretch="never")

        # ── Status Bar ──────────────────────────────────────────────
        self.status_bar = tk.Frame(self.root, bg=Theme.BG_MEDIUM, height=28)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_bar.pack_propagate(False)

        self.status_label = tk.Label(
            self.status_bar, text=f"Ready — {self.platform_mgr.platform.value.title()}",
            bg=Theme.BG_MEDIUM, fg=Theme.TEXT_SECONDARY,
            font=Theme.get_font("small"), anchor="w", padx=12
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.target_label = tk.Label(
            self.status_bar,
            text=f"Target: {self.current_target or 'not set'}",
            bg=Theme.BG_MEDIUM, fg=Theme.TEXT_SECONDARY,
            font=Theme.get_font("small"), padx=12
        )
        self.target_label.pack(side=tk.RIGHT)

        # Progress bar (hidden by default)
        self.progress = ttk.Progressbar(
            self.status_bar, mode="indeterminate",
            style="Accent.Horizontal.TProgressbar", length=120
        )

        # ── Keyboard Shortcuts ──────────────────────────────────────
        self.root.bind("<Control-n>", lambda e: self._new_session())
        self.root.bind("<Control-s>", lambda e: self._save_session())
        self.root.bind("<Control-q>", lambda e: self._quit())
        self.root.bind("<Control-l>", lambda e: self._clear_chat())
        self.root.bind("<Control-k>", lambda e: self._focus_search())
        self.root.bind("<Control-comma>", lambda e: self._open_settings())
        self.root.bind("<F11>", lambda e: self._toggle_fullscreen())

        self.root.protocol("WM_DELETE_WINDOW", self._quit)

    # ── Chat Helpers ─────────────────────────────────────────────────

    def _system_message(self, text):
        """Add a system message to the chat."""
        self.chat_panel.add_message("system", text)

    def _ai_message(self, text):
        """Add an AI response message."""
        self.chat_panel.add_message("ai", text)

    def _user_message(self, text):
        """Add a user message (echo)."""
        self.chat_panel.add_message("user", text)

    def _set_status(self, text, color=None):
        self.status_label.config(
            text=text,
            fg=color or Theme.TEXT_SECONDARY
        )

    def _start_progress(self):
        self.progress.pack(side=tk.RIGHT, padx=8)
        self.progress.start(15)

    def _stop_progress(self):
        self.progress.stop()
        self.progress.pack_forget()

    # ── User Input Handling ──────────────────────────────────────────

    def _on_user_input(self, text: str):
        """Handle natural language input from the chat input box."""
        text = text.strip()
        if not text:
            return

        self.command_history.append(text)
        self._user_message(text)

        # Check for built-in commands
        lower = text.lower()

        if lower in ("help", "/help"):
            self._show_help()
            return
        if lower.startswith("set target "):
            target = text[11:].strip()
            self.current_target = target
            self.target_label.config(text=f"Target: {target}")
            self.session_mgr.add_target(target)
            self._ai_message(f"✓ Target set to: {target}")
            return
        if lower.startswith("search "):
            query = text[7:].strip()
            self._do_search(query)
            return
        if lower.startswith(("tools", "list tools")):
            self._list_categories_chat()
            return
        if lower.startswith("check "):
            tool_name = text[6:].strip()
            self._check_tool(tool_name)
            return

        # ── Natural Language Processing ─────────────────────────────
        self._process_natural_language(text)

    def _on_command(self, command: str):
        """Handle slash commands from chat."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("/help", "/h"):
            self._show_help()
        elif cmd in ("/target", "/t"):
            if arg:
                self.current_target = arg
                self.target_label.config(text=f"Target: {arg}")
                self._ai_message(f"✓ Target set to: {arg}")
            else:
                self._ai_message(f"Current target: {self.current_target or 'not set'}")
        elif cmd in ("/clear", "/c"):
            self._clear_chat()
        elif cmd in ("/run", "/r"):
            if arg:
                self._execute_raw(arg)
        elif cmd == "/tools":
            self._list_categories_chat()
        elif cmd == "/search":
            if arg:
                self._do_search(arg)
        elif cmd == "/session":
            self._session_info()
        elif cmd == "/platform":
            self._show_platform()
        else:
            self._ai_message(f"Unknown command: {cmd}\nType /help for available commands.")

    def _process_natural_language(self, text: str):
        """Process natural language through TejStrike AI agent."""
        self._set_status("Analyzing...", Theme.ACCENT)
        self._start_progress()

        # Use the agent (LLM if configured, built-in engine otherwise)
        response = self.agent.process(text)

        # Update target if extracted
        if self.current_target:
            self.agent.set_target(self.current_target)

        if response.llm_used:
            # LLM-powered response
            model_tag = f" [{response.model}]" if response.model else ""
            self._ai_message(f"🤖{model_tag}\n{response.text}")
        else:
            # Built-in engine response
            self._ai_message(response.text)

        # Extract and show commands
        commands = response.commands
        if commands:
            cmd_text = "\n⚡ Suggested Commands:"
            for i, cmd in enumerate(commands, 1):
                cmd_text += f"\n  [{i}] {cmd.get('description', '')}\n      $ {cmd['command']}"
            cmd_text += "\n\n💡 Click a command above or type its number to execute."
            self._ai_message(cmd_text)

        self._stop_progress()
        self._set_status("Ready", Theme.TEXT_SECONDARY)

        # Store commands for number-based execution
        self._pending_commands = commands

        # Show in terminal panel
        if commands:
            self.terminal_panel.show_commands(commands)

    def _execute_command(self, cmd_info: dict):
        """Execute a tool command in a background thread."""
        if self.is_executing:
            self._ai_message("⚠ A command is already running. Wait or press Stop.")
            return

        command = cmd_info["command"]
        tool = cmd_info.get("tool", "unknown")

        # Check for placeholders
        if "<" in command and ">" in command:
            self._ai_message(
                f"⚠ Command has unfilled placeholders:\n  $ {command}\n\n"
                "Please provide the missing values. Example:\n"
                "  set target 192.168.1.1"
            )
            return

        self.is_executing = True
        self._set_status(f"Running: {tool}...", Theme.WARNING)
        self._start_progress()
        self._ai_message(f"▶ Executing: $ {command}")
        self.terminal_panel.clear()
        self.terminal_panel.append_output(f"$ {command}\n", "command")

        def _run():
            try:
                config = ExecutionConfig(
                    timeout=self.config.default_timeout,
                    stream_output=True,
                )
                result = self.executor.execute(command, tool_name=tool, config=config)

                # Parse output
                parser = OutputParserFactory.get_parser(tool)
                if parser:
                    result.parsed_data = parser.parse(result.stdout)

                # Record in session
                intent = self.brain.parse_intent(command)
                self.session_mgr.record_execution(intent, result)

                # Analyze and report
                self.root.after(0, self._handle_result, result)

            except Exception as e:
                self.root.after(0, self._ai_message,
                                f"❌ Execution error: {str(e)}")
                self.root.after(0, self._stop_progress)
                self.root.after(0, self._set_status, "Error", Theme.ERROR)
            finally:
                self.is_executing = False
                self.root.after(0, self._stop_progress)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _handle_result(self, result):
        """Handle tool execution result (on main thread)."""
        self._stop_progress()

        # Terminal output is already streamed
        self.terminal_panel.append_output(
            f"\n{'─' * 50}\n"
            f"Exit code: {result.exit_code} | Duration: {result.duration:.1f}s\n",
            "info"
        )

        if result.exit_code == 0:
            self._set_status(
                f"✓ {result.tool_name} completed ({result.duration:.1f}s)",
                Theme.SUCCESS
            )
        else:
            self._set_status(
                f"✗ {result.tool_name} failed (exit: {result.exit_code})",
                Theme.ERROR
            )

        # Analyze output
        analysis = self.brain.analyze_output(result)
        analysis_parts = []

        if analysis["findings"]:
            analysis_parts.append(f"📊 Findings: {len(analysis['findings'])} items detected")
            for f in analysis["findings"][:5]:
                if f.get("type") == "port":
                    analysis_parts.append(
                        f"  • Port {f['port']}/{f['state']}: {f.get('service', 'unknown')}"
                    )
                elif f.get("type") == "hosts_discovered":
                    analysis_parts.append(
                        f"  • Hosts found: {', '.join(f['hosts'][:5])}"
                    )

        # Suggest next steps
        intent = self.brain.parse_intent(result.command)
        suggestions = self.brain.suggest_next_steps(intent, [result])
        if suggestions:
            analysis_parts.append("\n💡 Suggested Next Steps:")
            for s in suggestions[:5]:
                analysis_parts.append(f"  → {s}")

        if analysis_parts:
            self._ai_message("\n".join(analysis_parts))

    def _execute_raw(self, command: str):
        """Execute a raw command."""
        self._execute_command({"command": command, "tool": "raw"})

    def _on_tool_output_line(self, line: str):
        """Callback for real-time tool output streaming."""
        self.root.after(0, self.terminal_panel.append_output, line + "\n", "stdout")

    def _kill_current(self):
        """Kill running process."""
        self.executor.kill_all()
        self.is_executing = False
        self._stop_progress()
        self._set_status("Process terminated", Theme.WARNING)
        self.terminal_panel.append_output("\n[TejStrike] Process killed by user\n", "error")

    # ── Sidebar Handlers ─────────────────────────────────────────────

    def _on_tool_click(self, tool_name: str):
        """Handle clicking a tool in the sidebar."""
        if tool_name in TOOL_REGISTRY:
            ToolInfoDialog(self.root, TOOL_REGISTRY[tool_name], self.platform_mgr)

    def _on_category_click(self, category: str):
        """Handle clicking a category in the sidebar."""
        tools = get_tools_by_category(category)
        if tools:
            lines = [f"🔧 {category.replace('_', ' ').title()} Tools ({len(tools)}):"]
            for t in tools:
                lines.append(f"  • {t.name} — {t.description[:60]}")
            self._ai_message("\n".join(lines))

    def _on_sidebar_search(self, query: str):
        """Handle search from sidebar."""
        self._do_search(query)

    # ── Commands ─────────────────────────────────────────────────────

    def _do_search(self, query: str):
        results = search_tools(query)
        if results:
            lines = [f"🔍 Search results for '{query}' ({len(results)} found):"]
            for t in results[:15]:
                lines.append(f"  • {t.name} [{t.category}] — {t.description[:50]}")
            self._ai_message("\n".join(lines))
        else:
            self._ai_message(f"No tools found matching '{query}'.")

    def _check_tool(self, tool_name: str):
        info = self.platform_mgr.check_tool(tool_name)
        if info.available:
            self._ai_message(
                f"✓ {tool_name} is available\n"
                f"  Path: {info.path or 'N/A'}\n"
                f"  Version: {info.version or 'N/A'}"
            )
        else:
            self._ai_message(
                f"✗ {tool_name} is NOT installed\n"
                f"  Install: {info.install_command or 'apt install ' + tool_name}"
            )

    def _list_categories_chat(self):
        cat_names = get_all_categories()
        lines = [f"📂 Tool Categories ({len(cat_names)}):"]
        for cat_name in sorted(cat_names):
            count = len(get_tools_by_category(cat_name))
            lines.append(f"  • {cat_name.replace('_', ' ').title()} ({count} tools)")
        lines.append(f"\nTotal: {get_tool_count()} tools registered")
        self._ai_message("\n".join(lines))

    def _show_help(self):
        help_text = (
            "💡 TEJSTRIKE AI HELP\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🗣️ Natural Language:\n"
            '  Just type what you want, e.g.: "scan 192.168.1.1"\n\n'
            "⌨️ Slash Commands:\n"
            "  /help          — Show this help\n"
            "  /target <ip>   — Set default target\n"
            "  /run <cmd>     — Execute raw command\n"
            "  /search <q>    — Search tools\n"
            "  /tools         — List categories\n"
            "  /session       — Session info\n"
            "  /platform      — System info\n"
            "  /model         — Show current LLM model\n"
            "  /clear         — Clear chat\n\n"
            "⌨️ Keyboard Shortcuts:\n"
            "  Ctrl+N — New session\n"
            "  Ctrl+S — Save session\n"
            "  Ctrl+K — Focus search\n"
            "  Ctrl+L — Clear chat\n"
            "  Ctrl+Q — Quit\n"
            "  Enter  — Send message\n"
            "  F11    — Toggle fullscreen"
        )
        self._ai_message(help_text)

    def _session_info(self):
        s = self.session_mgr.session
        if s:
            self._ai_message(
                f"📋 Session: {s.session_id}\n"
                f"  Started: {s.started_at}\n"
                f"  Phase: {s.phase}\n"
                f"  Targets: {', '.join(s.targets) or 'none'}\n"
                f"  Tools used: {', '.join(s.tools_used) or 'none'}\n"
                f"  Commands: {len(s.commands_executed)}\n"
                f"  Findings: {len(s.findings)}"
            )

    def _show_platform(self):
        p = self.platform_mgr
        self._ai_message(
            f"🖥️ Platform Information\n"
            f"  OS: {platform.system()} {platform.release()}\n"
            f"  Platform: {p.platform.value}\n"
            f"  Python: {platform.python_version()}\n"
            f"  Machine: {platform.machine()}\n"
            f"  Node: {platform.node()}"
        )

    # ── Menu Actions ─────────────────────────────────────────────────

    def _new_session(self):
        self.session_mgr.new_session()
        self._clear_chat()
        self._system_message("New session started.")

    def _save_session(self):
        path = self.session_mgr.save_session()
        if path:
            self._system_message(f"Session saved: {path}")
        else:
            self._system_message("No active session to save.")

    def _load_session(self):
        SessionDialog(self.root, self.session_mgr, self._system_message)

    def _export_chat(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"tej_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if filepath:
            content = self.chat_panel.get_all_text()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self._system_message(f"Chat exported to: {filepath}")

    def _open_settings(self):
        SettingsDialog(self.root, self.config, self.config_mgr)

    def _scan_tools(self):
        self._system_message("Scanning system for installed tools...")
        self._start_progress()

        def _scan():
            results = self.platform_mgr.scan_all_tools(list(TOOL_REGISTRY.keys()))
            self.root.after(0, self._show_scan_results, results)

        threading.Thread(target=_scan, daemon=True).start()

    def _show_scan_results(self, results):
        self._stop_progress()
        found = [t for t, info in results.items() if info.available]
        missing = [t for t, info in results.items() if not info.available]

        lines = [
            f"🔍 System Tool Scan Complete\n",
            f"  ✓ Found: {len(found)} tools",
            f"  ✗ Missing: {len(missing)} tools\n",
        ]
        if found:
            lines.append("Installed:")
            for t in sorted(found)[:20]:
                lines.append(f"  ✓ {t}")
            if len(found) > 20:
                lines.append(f"  ... and {len(found) - 20} more")

        self._ai_message("\n".join(lines))

    def _clear_chat(self):
        self.chat_panel.clear()

    def _focus_search(self):
        self.sidebar.focus_search()

    def _toggle_sidebar(self):
        if self._show_sidebar_var.get():
            self.sidebar.pack(side=tk.LEFT, fill=tk.Y, before=self.right_pane)
        else:
            self.sidebar.pack_forget()

    def _toggle_terminal(self):
        if self._show_terminal_var.get():
            self.vpaned.add(self.terminal_panel, minsize=150)
        else:
            self.vpaned.forget(self.terminal_panel)

    def _toggle_fullscreen(self):
        current = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not current)

    def _show_about(self):
        AboutDialog(self.root)

    def _show_shortcuts(self):
        self._ai_message(
            "⌨️ Keyboard Shortcuts:\n"
            "  Ctrl+N — New session\n"
            "  Ctrl+S — Save session\n"
            "  Ctrl+K — Focus search bar\n"
            "  Ctrl+L — Clear chat\n"
            "  Ctrl+Q — Quit\n"
            "  Ctrl+, — Settings\n"
            "  F11    — Fullscreen toggle\n"
            "  Enter  — Send message\n"
            "  Shift+Enter — New line in input"
        )

    def _quit(self):
        if self.is_executing:
            self.executor.kill_all()
        self.session_mgr.save_session()
        self.config_mgr.config = self.config
        self.config_mgr.save()
        self.root.destroy()

    # ── Run ──────────────────────────────────────────────────────────

    def run(self):
        """Start the application main loop."""
        self.root.mainloop()

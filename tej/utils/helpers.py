"""
TejStrike AI - Utility Helpers
Common utilities for formatting, colors, and display.
"""

import os
import sys
import platform


class Colors:
    """ANSI color codes for terminal output."""

    # Check if colors are supported
    _enabled = True

    if platform.system() == "Windows":
        try:
            os.system("")  # Enable ANSI on Windows 10+
        except Exception:
            _enabled = False

    # Colors
    RESET = "\033[0m" if _enabled else ""
    BOLD = "\033[1m" if _enabled else ""
    DIM = "\033[2m" if _enabled else ""
    UNDERLINE = "\033[4m" if _enabled else ""
    BLINK = "\033[5m" if _enabled else ""

    # Foreground
    BLACK = "\033[30m" if _enabled else ""
    RED = "\033[31m" if _enabled else ""
    GREEN = "\033[32m" if _enabled else ""
    YELLOW = "\033[33m" if _enabled else ""
    BLUE = "\033[34m" if _enabled else ""
    MAGENTA = "\033[35m" if _enabled else ""
    CYAN = "\033[36m" if _enabled else ""
    WHITE = "\033[37m" if _enabled else ""

    # Bright
    BRIGHT_RED = "\033[91m" if _enabled else ""
    BRIGHT_GREEN = "\033[92m" if _enabled else ""
    BRIGHT_YELLOW = "\033[93m" if _enabled else ""
    BRIGHT_BLUE = "\033[94m" if _enabled else ""
    BRIGHT_MAGENTA = "\033[95m" if _enabled else ""
    BRIGHT_CYAN = "\033[96m" if _enabled else ""
    BRIGHT_WHITE = "\033[97m" if _enabled else ""

    # Background
    BG_RED = "\033[41m" if _enabled else ""
    BG_GREEN = "\033[42m" if _enabled else ""
    BG_YELLOW = "\033[43m" if _enabled else ""
    BG_BLUE = "\033[44m" if _enabled else ""

    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """Apply a color to text."""
        return f"{color}{text}{cls.RESET}"

    @classmethod
    def success(cls, text: str) -> str:
        return cls.colorize(text, cls.BRIGHT_GREEN)

    @classmethod
    def error(cls, text: str) -> str:
        return cls.colorize(text, cls.BRIGHT_RED)

    @classmethod
    def warning(cls, text: str) -> str:
        return cls.colorize(text, cls.BRIGHT_YELLOW)

    @classmethod
    def info(cls, text: str) -> str:
        return cls.colorize(text, cls.BRIGHT_CYAN)

    @classmethod
    def header(cls, text: str) -> str:
        return cls.colorize(text, cls.BOLD + cls.BRIGHT_WHITE)

    @classmethod
    def dim(cls, text: str) -> str:
        return cls.colorize(text, cls.DIM)

    @classmethod
    def accent(cls, text: str) -> str:
        return cls.colorize(text, cls.BRIGHT_MAGENTA)

    @classmethod 
    def severity(cls, level: str) -> str:
        """Color-code severity levels."""
        level = level.lower()
        if level in ("critical", "high"):
            return cls.colorize(f"[{level.upper()}]", cls.BRIGHT_RED + cls.BOLD)
        elif level == "medium":
            return cls.colorize(f"[{level.upper()}]", cls.BRIGHT_YELLOW)
        elif level == "low":
            return cls.colorize(f"[{level.upper()}]", cls.BLUE)
        else:
            return cls.colorize(f"[{level.upper()}]", cls.DIM)


BANNER = f"""{Colors.BRIGHT_CYAN}
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  {Colors.BRIGHT_RED}████████╗{Colors.BRIGHT_WHITE}███████╗{Colors.BRIGHT_GREEN} ██╗{Colors.BRIGHT_YELLOW}███████╗{Colors.BRIGHT_MAGENTA}████████╗{Colors.BRIGHT_CYAN}██████╗ ██╗██╗  ██╗███████╗  ║
║  {Colors.BRIGHT_RED}╚══██╔══╝{Colors.BRIGHT_WHITE}██╔════╝{Colors.BRIGHT_GREEN} ██║{Colors.BRIGHT_YELLOW}██╔════╝{Colors.BRIGHT_MAGENTA}╚══██╔══╝{Colors.BRIGHT_CYAN}██╔══██╗██║██║ ██╔╝██╔════╝  ║
║  {Colors.BRIGHT_RED}   ██║   {Colors.BRIGHT_WHITE}█████╗  {Colors.BRIGHT_GREEN} ██║{Colors.BRIGHT_YELLOW}███████╗{Colors.BRIGHT_MAGENTA}   ██║   {Colors.BRIGHT_CYAN}██████╔╝██║█████╔╝ █████╗    ║
║  {Colors.BRIGHT_RED}   ██║   {Colors.BRIGHT_WHITE}██╔══╝  {Colors.BRIGHT_GREEN} ██║{Colors.BRIGHT_YELLOW}╚════██║{Colors.BRIGHT_MAGENTA}   ██║   {Colors.BRIGHT_CYAN}██╔══██╗██║██╔═██╗ ██╔══╝    ║
║  {Colors.BRIGHT_RED}   ██║   {Colors.BRIGHT_WHITE}███████╗{Colors.BRIGHT_GREEN} ██║{Colors.BRIGHT_YELLOW}███████║{Colors.BRIGHT_MAGENTA}   ██║   {Colors.BRIGHT_CYAN}██║  ██║██║██║  ██╗███████╗  ║
║  {Colors.BRIGHT_RED}   ╚═╝   {Colors.BRIGHT_WHITE}╚══════╝{Colors.BRIGHT_GREEN} ╚═╝{Colors.BRIGHT_YELLOW}╚══════╝{Colors.BRIGHT_MAGENTA}   ╚═╝   {Colors.BRIGHT_CYAN}╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚══════╝  ║
║                                                                      ║
║   {Colors.BRIGHT_WHITE}AI-Powered Security Tool Orchestrator{Colors.BRIGHT_CYAN}                           ║
║   {Colors.DIM}Kali Linux & Windows | v2.0.0 | Multi-Model LLM{Colors.BRIGHT_CYAN}                ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
{Colors.RESET}"""


HELP_TEXT = f"""
{Colors.header("AVAILABLE COMMANDS:")}

  {Colors.accent("Natural Language")}     Just type what you want to do in plain English
                        Examples: "scan 192.168.1.1", "crack these hashes",
                        "find subdomains of example.com"

  {Colors.info("tools")}               List all available tool categories
  {Colors.info("tools <category>")}    List tools in a specific category
  {Colors.info("tool <name>")}         Get detailed info about a specific tool
  {Colors.info("search <query>")}      Search for tools by keyword
  {Colors.info("check <tool>")}        Check if a tool is installed
  {Colors.info("scan-tools")}          Scan system for all available tools

  {Colors.info("session new [name]")}  Start a new assessment session
  {Colors.info("session save")}        Save current session
  {Colors.info("session load <id>")}   Load a previous session
  {Colors.info("session list")}        List all saved sessions
  {Colors.info("session report")}      Generate assessment report
  {Colors.info("session status")}      Show session summary

  {Colors.info("history")}             Show command execution history
  {Colors.info("set target <ip>")}     Set the default target
  {Colors.info("run <command>")}       Execute a raw command directly
  {Colors.info("last")}                Show last command output

  {Colors.info("platform")}            Show platform/system information
  {Colors.info("clear")}               Clear the screen
  {Colors.info("help")}                Show this help message
  {Colors.info("exit/quit")}           Exit TejStrike AI

{Colors.dim("Pro tip: Just describe what you want to do and TejStrike will figure out the rest!")}
{Colors.dim("Configure LLM: set provider <anthropic|openai|groq|ollama>")}
"""


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if platform.system() == 'Windows' else 'clear')


def format_table(headers: list, rows: list, padding: int = 2) -> str:
    """Format data as an aligned text table."""
    if not rows:
        return "  (no data)"

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    # Build table
    lines = []
    # Header
    header_line = ""
    for i, h in enumerate(headers):
        header_line += str(h).ljust(col_widths[i] + padding)
    lines.append(Colors.header(header_line))
    lines.append(Colors.dim("─" * len(header_line)))

    # Rows
    for row in rows:
        line = ""
        for i, cell in enumerate(row):
            if i < len(col_widths):
                line += str(cell).ljust(col_widths[i] + padding)
        lines.append(line)

    return "\n".join(lines)


def truncate(text: str, max_length: int = 80) -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

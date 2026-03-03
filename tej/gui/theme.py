"""
Tej AI - GUI Theme & Styling
Dark theme colors, fonts, and styling constants for the desktop application.
"""


class Theme:
    """Modern dark theme inspired by Claude Desktop / VS Code Dark."""

    # ── Core Colors ──────────────────────────────────────────────────
    BG_DARK = "#0d1117"          # Main background (GitHub dark)
    BG_MEDIUM = "#161b22"        # Sidebar / panels
    BG_LIGHT = "#1c2128"         # Cards / elevated surfaces
    BG_INPUT = "#21262d"         # Input fields
    BG_HOVER = "#30363d"         # Hover state
    BG_ACTIVE = "#388bfd22"      # Active/selected item

    # ── Accent Colors ────────────────────────────────────────────────
    ACCENT = "#58a6ff"           # Primary accent (blue)
    ACCENT_HOVER = "#79c0ff"     # Accent hover
    ACCENT_DIM = "#1f6feb"       # Accent dimmed
    SUCCESS = "#3fb950"          # Green
    WARNING = "#d29922"          # Yellow/Orange
    ERROR = "#f85149"            # Red
    INFO = "#58a6ff"             # Blue

    # ── Text Colors ──────────────────────────────────────────────────
    TEXT_PRIMARY = "#e6edf3"     # Main text
    TEXT_SECONDARY = "#8b949e"   # Muted text
    TEXT_TERTIARY = "#484f58"    # Very muted
    TEXT_LINK = "#58a6ff"        # Link / clickable
    TEXT_CODE = "#79c0ff"        # Code snippets

    # ── Border Colors ────────────────────────────────────────────────
    BORDER = "#30363d"           # Default border
    BORDER_SUBTLE = "#21262d"    # Subtle borders
    BORDER_ACCENT = "#388bfd"    # Focused border

    # ── Chat Bubble Colors ───────────────────────────────────────────
    USER_BUBBLE = "#1f6feb"      # User message background
    USER_BUBBLE_TEXT = "#ffffff"  # User message text
    AI_BUBBLE = "#1c2128"        # AI response background
    AI_BUBBLE_TEXT = "#e6edf3"   # AI response text
    SYSTEM_BUBBLE = "#161b22"    # System message background
    SYSTEM_TEXT = "#8b949e"      # System message text

    #  Tool Category Colors ──────────────────────────────────────────
    CAT_COLORS = {
        "reconnaissance":       "#58a6ff",
        "scanning":            "#3fb950",
        "enumeration":         "#d29922",
        "vulnerability_analysis": "#f85149",
        "exploitation":        "#f85149",
        "post_exploitation":   "#da3633",
        "password_attacks":    "#bc8cff",
        "wireless":            "#79c0ff",
        "web_application":     "#d2a8ff",
        "sniffing_spoofing":   "#f0883e",
        "forensics":           "#56d4dd",
        "reverse_engineering": "#ec6547",
        "social_engineering":  "#db61a2",
    }

    # ── Severity Colors ──────────────────────────────────────────────
    SEV_COLORS = {
        "critical": "#f85149",
        "high":     "#f85149",
        "medium":   "#d29922",
        "low":      "#58a6ff",
        "info":     "#8b949e",
    }

    # ── Font Configuration ───────────────────────────────────────────
    FONT_FAMILY = "Segoe UI"          # Windows fallback
    FONT_FAMILY_LINUX = "Ubuntu"       # Linux primary
    FONT_FAMILY_MONO = "Cascadia Code" # Monospace
    FONT_FAMILY_MONO_LINUX = "Ubuntu Mono"

    FONT_SIZE_SMALL = 10
    FONT_SIZE_NORMAL = 11
    FONT_SIZE_MEDIUM = 13
    FONT_SIZE_LARGE = 16
    FONT_SIZE_TITLE = 22
    FONT_SIZE_HERO = 28

    # ── Dimensions ───────────────────────────────────────────────────
    SIDEBAR_WIDTH = 280
    MIN_WIDTH = 1100
    MIN_HEIGHT = 700
    BORDER_RADIUS = 8
    PADDING_SMALL = 4
    PADDING_MEDIUM = 8
    PADDING_LARGE = 16
    PADDING_XL = 24

    # ── Scrollbar ────────────────────────────────────────────────────
    SCROLLBAR_BG = "#161b22"
    SCROLLBAR_THUMB = "#30363d"
    SCROLLBAR_HOVER = "#484f58"

    @classmethod
    def get_font(cls, size="normal", bold=False, mono=False):
        """Get a font tuple for tkinter."""
        import platform
        is_linux = platform.system() == "Linux"

        if mono:
            family = cls.FONT_FAMILY_MONO_LINUX if is_linux else cls.FONT_FAMILY_MONO
        else:
            family = cls.FONT_FAMILY_LINUX if is_linux else cls.FONT_FAMILY

        sizes = {
            "small": cls.FONT_SIZE_SMALL,
            "normal": cls.FONT_SIZE_NORMAL,
            "medium": cls.FONT_SIZE_MEDIUM,
            "large": cls.FONT_SIZE_LARGE,
            "title": cls.FONT_SIZE_TITLE,
            "hero": cls.FONT_SIZE_HERO,
        }
        sz = sizes.get(size, cls.FONT_SIZE_NORMAL)
        weight = "bold" if bold else "normal"
        return (family, sz, weight)

    @classmethod
    def get_cat_color(cls, category: str) -> str:
        """Get color for a tool category."""
        return cls.CAT_COLORS.get(category, cls.ACCENT)

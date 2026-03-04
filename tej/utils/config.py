"""
TejStrike AI - Configuration Management
Handles configuration loading, saving, and defaults.
Includes LLM provider settings and MCP server configuration.
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict


@dataclass
class LLMSettings:
    """LLM provider configuration."""
    provider: str = ""          # anthropic, openai, groq, ollama
    model: str = ""             # claude-sonnet-4-20250514, gpt-4o, etc.
    api_key: str = ""
    api_base_url: str = ""      # Custom endpoint (Ollama, Azure, etc.)
    temperature: float = 0.3
    max_tokens: int = 4096
    streaming: bool = True


@dataclass
class MCPServerSettings:
    """Single MCP server configuration."""
    name: str = ""
    transport: str = "stdio"    # stdio or sse
    command: str = ""           # For stdio: command to run
    args: List[str] = field(default_factory=list)
    url: str = ""               # For SSE: server URL
    enabled: bool = True


@dataclass
class TejConfig:
    """Main configuration for TejStrike AI."""

    # General settings
    output_dir: str = ""
    auto_save_output: bool = True
    verbose: bool = False
    color_enabled: bool = True

    # Execution settings
    default_timeout: int = 300
    max_threads: int = 10
    confirm_before_execute: bool = True
    stream_output: bool = True

    # Default target settings
    default_target: str = ""
    default_interface: str = ""
    default_wordlist: str = ""

    # Platform settings
    use_sudo: bool = True
    wsl_mode: bool = False

    # Session settings
    auto_session: bool = True
    session_dir: str = ""

    # LLM settings
    llm: LLMSettings = field(default_factory=LLMSettings)

    # MCP server settings
    mcp_servers: List[MCPServerSettings] = field(default_factory=list)

    # Tool-specific settings
    nmap_default_flags: str = "-sV -sC"
    sqlmap_default_flags: str = "--batch"
    hydra_default_threads: int = 16
    gobuster_default_threads: int = 50

    # Wordlist paths
    wordlists: Dict[str, str] = field(default_factory=lambda: {
        "rockyou": "/usr/share/wordlists/rockyou.txt",
        "common": "/usr/share/dirb/wordlists/common.txt",
        "medium": "/usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt",
        "big": "/usr/share/dirb/wordlists/big.txt",
        "subdomains": "/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt"
    })


class ConfigManager:
    """Manages TejStrike AI configuration."""

    DEFAULT_CONFIG_PATHS = {
        "linux": os.path.expanduser("~/.config/tejstrike/config.json"),
        "windows": os.path.join(os.environ.get("APPDATA", ""), "tejstrike", "config.json")
    }

    def __init__(self, config_path: Optional[str] = None):
        self.config = TejConfig()
        
        if config_path:
            self.config_path = config_path
        else:
            import platform as plat
            key = "windows" if plat.system() == "Windows" else "linux"
            self.config_path = self.DEFAULT_CONFIG_PATHS[key]

        self._set_defaults()

    def _set_defaults(self):
        """Set platform-appropriate defaults."""
        import platform as plat
        
        if plat.system() == "Windows":
            self.config.output_dir = os.path.expanduser("~\\tejstrike_output")
            self.config.session_dir = os.path.expanduser("~\\tejstrike_output\\sessions")
            self.config.use_sudo = False
            self.config.default_interface = "Ethernet"
            self.config.wordlists = {
                "rockyou": "C:\\wordlists\\rockyou.txt",
                "common": "C:\\wordlists\\common.txt",
            }
        else:
            self.config.output_dir = os.path.expanduser("~/tejstrike_output")
            self.config.session_dir = os.path.expanduser("~/tejstrike_output/sessions")
            self.config.default_interface = "eth0"

    def load(self) -> TejConfig:
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                # Handle nested LLM settings
                if "llm" in data and isinstance(data["llm"], dict):
                    self.config.llm = LLMSettings(**data.pop("llm"))
                # Handle MCP servers
                if "mcp_servers" in data and isinstance(data["mcp_servers"], list):
                    self.config.mcp_servers = [
                        MCPServerSettings(**s) for s in data.pop("mcp_servers")
                    ]
                for key, value in data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
            except (json.JSONDecodeError, OSError, TypeError):
                pass
        return self.config

    def save(self):
        """Save configuration to file."""
        config_dir = os.path.dirname(self.config_path)
        os.makedirs(config_dir, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(asdict(self.config), f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return getattr(self.config, key, default)

    def set(self, key: str, value: Any):
        """Set a configuration value."""
        if hasattr(self.config, key):
            setattr(self.config, key, value)

    def reset(self):
        """Reset to default configuration."""
        self.config = TejConfig()
        self._set_defaults()

    def to_dict(self) -> Dict[str, Any]:
        """Export config as dictionary."""
        return asdict(self.config)

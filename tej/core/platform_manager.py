"""
Tej AI - Platform Detection & Cross-Platform Support
Handles differences between Kali Linux and Windows environments.
"""

import os
import sys
import shutil
import platform
import subprocess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class Platform(Enum):
    KALI_LINUX = "kali_linux"
    DEBIAN_LINUX = "debian_linux"
    OTHER_LINUX = "other_linux"
    WINDOWS = "windows"
    WSL = "wsl"
    MACOS = "macos"
    UNKNOWN = "unknown"


@dataclass
class ToolAvailability:
    """Represents the availability status of a tool."""
    name: str
    available: bool
    path: Optional[str] = None
    version: Optional[str] = None
    install_command: Optional[str] = None
    platform_notes: str = ""


class PlatformManager:
    """
    Manages cross-platform compatibility between Kali Linux and Windows.
    Handles tool detection, path resolution, and platform-specific commands.
    """

    # Windows-native security tool alternatives
    WINDOWS_ALTERNATIVES = {
        "nmap": {"install": "choco install nmap", "native": True},
        "wireshark": {"install": "choco install wireshark", "native": True},
        "hashcat": {"install": "choco install hashcat", "native": True},
        "john": {"install": "choco install john", "native": True},
        "sqlmap": {"install": "pip install sqlmap", "native": True},
        "gobuster": {"install": "go install github.com/OJ/gobuster/v3@latest", "native": True},
        "ffuf": {"install": "go install github.com/ffuf/ffuf@latest", "native": True},
        "hydra": {"install": "Available via WSL or Cygwin", "native": False},
        "nikto": {"install": "Available via WSL", "native": False},
        "metasploit": {"install": "Download from rapid7.com", "native": True},
        "nuclei": {"install": "go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest", "native": True},
        "burpsuite": {"install": "Download from portswigger.net", "native": True},
        "responder": {"install": "pip install Responder", "native": True},
        "impacket": {"install": "pip install impacket", "native": True},
        "crackmapexec": {"install": "pip install crackmapexec", "native": True},
        "volatility": {"install": "pip install volatility3", "native": True},
        "binwalk": {"install": "pip install binwalk", "native": True},
        "theHarvester": {"install": "pip install theHarvester", "native": True},
        "whatweb": {"install": "Available via WSL", "native": False},
        "amass": {"install": "go install github.com/owasp-amass/amass/v4/...@master", "native": True},
        "ghidra": {"install": "Download from ghidra-sre.org", "native": True},
    }

    # Default wordlist locations
    WORDLISTS = {
        Platform.KALI_LINUX: {
            "rockyou": "/usr/share/wordlists/rockyou.txt",
            "dirb_common": "/usr/share/dirb/wordlists/common.txt",
            "dirbuster_medium": "/usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt",
            "seclists": "/usr/share/seclists/",
            "nmap_scripts": "/usr/share/nmap/scripts/",
        },
        Platform.WINDOWS: {
            "rockyou": "C:\\wordlists\\rockyou.txt",
            "dirb_common": "C:\\wordlists\\common.txt",
            "seclists": "C:\\seclists\\",
        }
    }

    def __init__(self):
        self.platform = self.detect_platform()
        self.is_admin = self._check_admin()
        self._tool_cache: Dict[str, ToolAvailability] = {}

    def detect_platform(self) -> Platform:
        """Detect the current operating system platform."""
        system = platform.system().lower()

        if system == "windows":
            # Check if running inside WSL
            if "microsoft" in platform.release().lower():
                return Platform.WSL
            return Platform.WINDOWS

        elif system == "linux":
            # Check if Kali Linux
            try:
                with open("/etc/os-release", "r") as f:
                    os_info = f.read().lower()
                    if "kali" in os_info:
                        return Platform.KALI_LINUX
                    elif "debian" in os_info or "ubuntu" in os_info:
                        return Platform.DEBIAN_LINUX
            except FileNotFoundError:
                pass
            return Platform.OTHER_LINUX

        elif system == "darwin":
            return Platform.MACOS

        return Platform.UNKNOWN

    def _check_admin(self) -> bool:
        """Check if running with administrative/root privileges."""
        if self.platform == Platform.WINDOWS:
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                return False
        else:
            return os.geteuid() == 0 if hasattr(os, 'geteuid') else False

    def check_tool(self, tool_name: str) -> ToolAvailability:
        """Check if a specific tool is available on the system."""
        if tool_name in self._tool_cache:
            return self._tool_cache[tool_name]

        # Check if tool exists in PATH
        tool_path = shutil.which(tool_name)
        
        # Some tools have alternate names
        alt_names = {
            "metasploit": ["msfconsole", "msf"],
            "burpsuite": ["burpsuite", "BurpSuiteCommunity", "BurpSuitePro"],
            "aircrack-ng": ["aircrack-ng"],
            "john": ["john", "john-the-ripper"],
            "wireshark": ["wireshark", "tshark"],
        }
        
        if not tool_path and tool_name in alt_names:
            for alt in alt_names[tool_name]:
                tool_path = shutil.which(alt)
                if tool_path:
                    break

        # Get version if available
        version = None
        if tool_path:
            version = self._get_tool_version(tool_name, tool_path)

        # Get install command
        install_cmd = self._get_install_command(tool_name)

        result = ToolAvailability(
            name=tool_name,
            available=tool_path is not None,
            path=tool_path,
            version=version,
            install_command=install_cmd,
            platform_notes=self._get_platform_notes(tool_name)
        )

        self._tool_cache[tool_name] = result
        return result

    def _get_tool_version(self, tool_name: str, tool_path: str) -> Optional[str]:
        """Try to get the version of a tool."""
        version_flags = ["--version", "-v", "-V", "version"]
        for flag in version_flags:
            try:
                result = subprocess.run(
                    [tool_path, flag],
                    capture_output=True, text=True, timeout=5
                )
                output = result.stdout or result.stderr
                if output:
                    # Extract first line as version
                    first_line = output.strip().split('\n')[0]
                    if len(first_line) < 200:
                        return first_line
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
                continue
        return None

    def _get_install_command(self, tool_name: str) -> Optional[str]:
        """Get the installation command for a tool based on platform."""
        if self.platform == Platform.KALI_LINUX:
            return f"sudo apt install -y {tool_name}"
        elif self.platform in (Platform.DEBIAN_LINUX, Platform.OTHER_LINUX):
            return f"sudo apt install -y {tool_name}"
        elif self.platform == Platform.WINDOWS:
            if tool_name in self.WINDOWS_ALTERNATIVES:
                return self.WINDOWS_ALTERNATIVES[tool_name]["install"]
            return f"choco install {tool_name}"
        return None

    def _get_platform_notes(self, tool_name: str) -> str:
        """Get platform-specific notes for a tool."""
        if self.platform == Platform.WINDOWS:
            if tool_name in self.WINDOWS_ALTERNATIVES:
                info = self.WINDOWS_ALTERNATIVES[tool_name]
                if not info["native"]:
                    return "Not natively available on Windows. Use WSL or VM."
                return "Available on Windows"
        elif self.platform == Platform.KALI_LINUX:
            return "Pre-installed on Kali Linux"
        return ""

    def scan_all_tools(self, tool_list: List[str]) -> Dict[str, ToolAvailability]:
        """Scan for availability of multiple tools."""
        results = {}
        for tool in tool_list:
            results[tool] = self.check_tool(tool)
        return results

    def get_wordlist_path(self, wordlist_name: str) -> Optional[str]:
        """Get the path to a wordlist based on platform."""
        platform_key = Platform.WINDOWS if self.platform == Platform.WINDOWS else Platform.KALI_LINUX
        wordlists = self.WORDLISTS.get(platform_key, {})
        
        path = wordlists.get(wordlist_name)
        if path and os.path.exists(path):
            return path
        
        # Search common locations
        search_dirs = []
        if self.platform == Platform.WINDOWS:
            search_dirs = [
                "C:\\wordlists", "C:\\tools\\wordlists",
                os.path.expanduser("~\\wordlists")
            ]
        else:
            search_dirs = [
                "/usr/share/wordlists", "/opt/wordlists",
                os.path.expanduser("~/wordlists")
            ]
        
        for dir_path in search_dirs:
            potential = os.path.join(dir_path, f"{wordlist_name}.txt")
            if os.path.exists(potential):
                return potential
        
        return path  # Return default even if not found

    def adapt_command(self, command: str) -> str:
        """Adapt a command for the current platform."""
        if self.platform == Platform.WINDOWS:
            # Convert Linux-style paths to Windows
            command = command.replace("/usr/share/wordlists/", "C:\\wordlists\\")
            command = command.replace("/usr/share/seclists/", "C:\\seclists\\")
            command = command.replace("/tmp/", "%TEMP%\\")
            
            # Some tools need .exe on Windows
            if not any(command.startswith(prefix) for prefix in ["python", "pip"]):
                parts = command.split()
                if parts and not parts[0].endswith(".exe"):
                    exe_path = shutil.which(parts[0] + ".exe")
                    if exe_path:
                        parts[0] = parts[0] + ".exe"
                        command = " ".join(parts)
        
        return command

    def needs_sudo(self, command: str) -> bool:
        """Check if a command needs sudo/admin privileges."""
        sudo_tools = [
            "nmap -sS", "nmap -sU", "nmap -O", "airmon-ng", "airodump-ng",
            "aireplay-ng", "tcpdump", "arpspoof", "ettercap", "bettercap",
            "responder", "netdiscover", "hping3", "macchanger"
        ]
        for tool_cmd in sudo_tools:
            if tool_cmd in command:
                return True
        return False

    def wrap_command(self, command: str) -> str:
        """Wrap command with sudo if needed (Linux) or advise about admin (Windows)."""
        if self.platform != Platform.WINDOWS and self.needs_sudo(command):
            if not self.is_admin and not command.startswith("sudo"):
                command = f"sudo {command}"
        return command

    def get_system_info(self) -> Dict[str, str]:
        """Get system information summary."""
        return {
            "platform": self.platform.value,
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "is_admin": str(self.is_admin),
            "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown"))
        }

#!/usr/bin/env python3
"""
Tej AI - Install Desktop Application (Kali Linux)
Sets up Tej AI as a native desktop application:
- Creates .desktop launcher in /usr/share/applications
- Installs icon
- Registers the application with the desktop environment
"""

import os
import sys
import shutil
import subprocess
import platform


def install_desktop():
    """Install Tej AI as a desktop application on Linux."""
    
    if platform.system() != "Linux":
        print("[!] Desktop installation is for Linux only.")
        print("    On Windows, Tej AI runs via: tej --gui")
        return False

    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Check if running as root
    is_root = os.geteuid() == 0 if hasattr(os, 'geteuid') else False
    
    if is_root:
        desktop_dir = "/usr/share/applications"
        icon_dir = "/usr/share/icons/hicolor/256x256/apps"
        bin_dir = "/usr/local/bin"
    else:
        home = os.path.expanduser("~")
        desktop_dir = os.path.join(home, ".local", "share", "applications")
        icon_dir = os.path.join(home, ".local", "share", "icons", "hicolor", "256x256", "apps")
        bin_dir = os.path.join(home, ".local", "bin")

    os.makedirs(desktop_dir, exist_ok=True)
    os.makedirs(icon_dir, exist_ok=True)
    os.makedirs(bin_dir, exist_ok=True)

    # 2. Find the tej-gui entry point
    tej_gui = shutil.which("tej-gui")
    if not tej_gui:
        # Create a launcher script
        tej_gui = os.path.join(bin_dir, "tej-gui")
        python_path = sys.executable
        with open(tej_gui, "w") as f:
            f.write(f"""#!/bin/bash
# Tej AI - GUI Launcher
exec {python_path} -c "from tej.gui import launch_gui; launch_gui()" "$@"
""")
        os.chmod(tej_gui, 0o755)
        print(f"[+] Created launcher: {tej_gui}")

    # 3. Generate icon
    icon_path = os.path.join(icon_dir, "tej-ai.png")
    xpm_source = os.path.join(script_dir, "gui", "assets", "tej_icon.xpm")
    
    # Generate XPM icon
    from tej.icon_gen import generate_xpm_icon
    generate_xpm_icon()
    
    # Try to convert XPM to PNG, otherwise just copy XPM
    if os.path.exists(xpm_source):
        try:
            from PIL import Image
            img = Image.open(xpm_source)
            img.save(icon_path)
            print(f"[+] Icon installed: {icon_path}")
        except ImportError:
            # Just copy XPM as fallback
            xpm_dest = icon_path.replace(".png", ".xpm")
            shutil.copy2(xpm_source, xpm_dest)
            icon_path = xpm_dest
            print(f"[+] Icon installed (XPM): {icon_path}")

    # 4. Create .desktop file
    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Tej AI
GenericName=Security Tool Orchestrator
Comment=AI-Powered Security Tool Orchestrator for Kali Linux
Exec={tej_gui}
Icon=tej-ai
Terminal=false
Categories=System;Security;Utility;
Keywords=security;pentesting;hacking;kali;ai;nmap;tools;
StartupWMClass=tej-ai
StartupNotify=true
"""
    desktop_path = os.path.join(desktop_dir, "tej-ai.desktop")
    with open(desktop_path, "w") as f:
        f.write(desktop_content)
    os.chmod(desktop_path, 0o644)
    print(f"[+] Desktop entry: {desktop_path}")

    # 5. Update desktop database
    try:
        subprocess.run(
            ["update-desktop-database", desktop_dir],
            capture_output=True, timeout=10
        )
        print("[+] Desktop database updated")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 6. Update icon cache
    try:
        icon_base = os.path.dirname(os.path.dirname(os.path.dirname(icon_dir)))
        subprocess.run(
            ["gtk-update-icon-cache", "-f", icon_base],
            capture_output=True, timeout=10
        )
        print("[+] Icon cache updated")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    print()
    print("=" * 50)
    print("  Tej AI Desktop Application Installed!")
    print("=" * 50)
    print()
    print("  You can now:")
    print(f"  • Find 'Tej AI' in your application menu")
    print(f"  • Run from terminal: tej-gui")
    print(f"  • Run from terminal: tej --gui")
    print()
    
    if not is_root:
        print("  Note: Installed for current user only.")
        print("  Run with sudo for system-wide installation.")
    
    return True


def uninstall_desktop():
    """Remove Tej AI desktop integration."""
    locations = [
        "/usr/share/applications/tej-ai.desktop",
        os.path.expanduser("~/.local/share/applications/tej-ai.desktop"),
        "/usr/share/icons/hicolor/256x256/apps/tej-ai.png",
        os.path.expanduser("~/.local/share/icons/hicolor/256x256/apps/tej-ai.png"),
    ]
    
    for path in locations:
        if os.path.exists(path):
            os.remove(path)
            print(f"[-] Removed: {path}")
    
    print("[+] Desktop integration removed.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--uninstall":
        uninstall_desktop()
    else:
        install_desktop()

#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Tej AI - GUI Desktop Launcher (Linux/Kali)
# ═══════════════════════════════════════════════════════════════
# Launch: ./tej-gui.sh
# Install as app: ./tej-gui.sh --install
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ "$1" == "--install" ]; then
    echo "[*] Installing Tej AI desktop application..."
    python3 -m tej.install_desktop
    exit $?
fi

if [ "$1" == "--uninstall" ]; then
    echo "[*] Removing Tej AI desktop integration..."
    python3 -m tej.install_desktop --uninstall
    exit $?
fi

echo "[*] Launching Tej AI Desktop..."
exec python3 -c "from tej.gui import launch_gui; launch_gui()" "$@"

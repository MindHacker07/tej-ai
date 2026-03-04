#!/usr/bin/env python3
"""
Tej Strike AI - Generate Application Icon
Creates a PNG icon for the desktop application using tkinter canvas.
Run this once to generate the icon file.
"""

import os
import sys


def generate_icon():
    """Generate a simple TejStrike AI icon as PNG using tkinter."""
    try:
        import tkinter as tk
    except ImportError:
        print("tkinter not available, skipping icon generation")
        return

    # Create offscreen window
    root = tk.Tk()
    root.withdraw()

    size = 256
    canvas = tk.Canvas(root, width=size, height=size,
                       bg="#0d1117", highlightthickness=0)
    canvas.pack()

    # Background circle
    margin = 16
    canvas.create_oval(
        margin, margin, size - margin, size - margin,
        fill="#161b22", outline="#30363d", width=3
    )

    # "T" letter — main stroke
    canvas.create_text(
        size // 2, size // 2 - 8,
        text="T",
        font=("Arial", 120, "bold"),
        fill="#58a6ff",
    )

    # Small "ej" text 
    canvas.create_text(
        size // 2 + 32, size // 2 + 40,
        text="ej",
        font=("Arial", 40, "bold"),
        fill="#e6edf3",
    )

    # Small "AI" badge
    canvas.create_rectangle(
        size // 2 + 50, size - margin - 40,
        size - margin - 10, size - margin - 12,
        fill="#1f6feb", outline=""
    )
    canvas.create_text(
        size // 2 + 72, size - margin - 26,
        text="AI",
        font=("Arial", 14, "bold"),
        fill="#ffffff",
    )

    # Save as PostScript then note for user
    assets_dir = os.path.join(os.path.dirname(__file__), "gui", "assets")
    os.makedirs(assets_dir, exist_ok=True)

    # Save as EPS (tkinter can do this natively)
    eps_path = os.path.join(assets_dir, "tej_icon.eps")
    canvas.postscript(file=eps_path, colormode="color")

    # Try to convert to PNG if PIL is available
    png_path = os.path.join(assets_dir, "tej_icon.png")
    try:
        from PIL import Image
        img = Image.open(eps_path)
        img.save(png_path)
        os.remove(eps_path)
        print(f"Icon saved: {png_path}")
    except ImportError:
        print(f"Icon saved as EPS: {eps_path}")
        print("Install Pillow (pip install Pillow) to convert to PNG")

    root.destroy()


def generate_xpm_icon():
    """Generate a simple XPM icon (no dependencies needed)."""
    assets_dir = os.path.join(os.path.dirname(__file__), "gui", "assets")
    os.makedirs(assets_dir, exist_ok=True)

    # Simple 32x32 XPM icon
    xpm_data = '''/* XPM */
static char *tej_icon[] = {
"32 32 6 1",
"  c #0D1117",
". c #161B22",
"+ c #58A6FF",
"@ c #1F6FEB",
"# c #E6EDF3",
"$ c #30363D",
"                                ",
"         $$$$$$$$$$$$$          ",
"       $$...........$$$$       ",
"      $...............$$$      ",
"     $.................$$$     ",
"    $....................$$     ",
"    $.......######......$$     ",
"   $........######.......$    ",
"   $.......########......$    ",
"   $........++++.........$    ",
"   $........++++.........$    ",
"   $........++++.........$    ",
"   $........++++.........$    ",
"   $........++++.........$    ",
"   $........++++.........$    ",
"   $........++++.........$    ",
"    $.......++++........$$    ",
"    $.......++++........$$    ",
"     $......++++.......$$$    ",
"     $......++++.......$$$    ",
"      $...............$$$     ",
"      $...............$$$     ",
"       $$..........$$$$       ",
"       $$..........$$$$       ",
"        $$$......$$$$         ",
"         $$$@@@@$$$$          ",
"          $$@##@$$$           ",
"           $@##@$$            ",
"            @@@@              ",
"            @@@@              ",
"                              ",
"                              "};
'''
    xpm_path = os.path.join(assets_dir, "tej_icon.xpm")
    with open(xpm_path, "w") as f:
        f.write(xpm_data)
    print(f"XPM icon saved: {xpm_path}")
    return xpm_path


if __name__ == "__main__":
    generate_xpm_icon()
    generate_icon()

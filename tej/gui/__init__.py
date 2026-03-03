"""
Tej AI - GUI Desktop Application
Modern dark-themed GUI interface for Tej AI security tool orchestrator.
"""

__all__ = ["launch_gui"]


def launch_gui():
    """Launch the Tej AI GUI application."""
    from tej.gui.app import TejApp
    app = TejApp()
    app.run()

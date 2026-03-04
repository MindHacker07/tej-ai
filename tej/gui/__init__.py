"""
TejStrike AI - GUI Desktop Application
Modern dark-themed GUI interface for TejStrike AI security tool orchestrator.
"""

__all__ = ["launch_gui"]


def launch_gui():
    """Launch the TejStrike AI GUI application."""
    from tej.gui.app import TejApp
    app = TejApp()
    app.run()

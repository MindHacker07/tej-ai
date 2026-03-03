"""
Tej AI - Session Manager
Manages security assessment sessions with state, history, and context.
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict

from tej.core.engine import TaskIntent, ToolResult, TejBrain


@dataclass
class SessionState:
    """Represents the state of a Tej AI session."""
    session_id: str
    started_at: str
    targets: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    commands_executed: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    phase: str = "reconnaissance"  # Current assessment phase


class SessionManager:
    """
    Manages Tej AI sessions - tracks targets, findings, tool usage,
    and maintains context throughout a security assessment.
    """

    PHASES = [
        "reconnaissance",
        "scanning",
        "enumeration",
        "vulnerability_analysis",
        "exploitation",
        "post_exploitation",
        "reporting"
    ]

    def __init__(self, brain: TejBrain, output_dir: str = ""):
        self.brain = brain
        self.output_dir = output_dir or os.path.expanduser("~/tej_output")
        self.session: Optional[SessionState] = None
        self._sessions_dir = os.path.join(self.output_dir, "sessions")
        os.makedirs(self._sessions_dir, exist_ok=True)

    def new_session(self, name: str = "") -> SessionState:
        """Create a new assessment session."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"tej_{name}_{timestamp}" if name else f"tej_{timestamp}"
        
        self.session = SessionState(
            session_id=session_id,
            started_at=datetime.now().isoformat()
        )
        return self.session

    def add_target(self, target: str):
        """Add a target to the current session."""
        if self.session and target not in self.session.targets:
            self.session.targets.append(target)

    def record_execution(self, intent: TaskIntent, result: ToolResult):
        """Record a tool execution in the session."""
        if not self.session:
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "category": intent.category.value,
            "action": intent.action,
            "target": intent.target,
            "tool": result.tool_name,
            "command": result.command,
            "exit_code": result.exit_code,
            "duration": result.duration,
            "output_preview": result.stdout[:500] if result.stdout else ""
        }
        self.session.commands_executed.append(entry)

        if result.tool_name not in self.session.tools_used:
            self.session.tools_used.append(result.tool_name)

        if intent.target and intent.target not in self.session.targets:
            self.session.targets.append(intent.target)

    def add_finding(self, finding_type: str, description: str, 
                    severity: str = "info", data: Dict = None):
        """Add a security finding to the session."""
        if not self.session:
            return

        finding = {
            "timestamp": datetime.now().isoformat(),
            "type": finding_type,
            "description": description,
            "severity": severity,
            "data": data or {}
        }
        self.session.findings.append(finding)

    def add_note(self, note: str):
        """Add a note to the session."""
        if self.session:
            self.session.notes.append(f"[{datetime.now().strftime('%H:%M:%S')}] {note}")

    def set_phase(self, phase: str):
        """Set the current assessment phase."""
        if self.session and phase in self.PHASES:
            self.session.phase = phase

    def next_phase(self) -> str:
        """Advance to the next assessment phase."""
        if not self.session:
            return ""
        
        current_idx = self.PHASES.index(self.session.phase)
        if current_idx < len(self.PHASES) - 1:
            self.session.phase = self.PHASES[current_idx + 1]
        return self.session.phase

    def save_session(self) -> str:
        """Save the current session to disk."""
        if not self.session:
            return ""

        filepath = os.path.join(
            self._sessions_dir, 
            f"{self.session.session_id}.json"
        )
        
        with open(filepath, 'w') as f:
            json.dump(asdict(self.session), f, indent=2, default=str)
        
        return filepath

    def load_session(self, session_id: str) -> Optional[SessionState]:
        """Load a session from disk."""
        filepath = os.path.join(self._sessions_dir, f"{session_id}.json")
        
        if not os.path.exists(filepath):
            return None

        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.session = SessionState(**data)
        return self.session

    def list_sessions(self) -> List[Dict[str, str]]:
        """List all saved sessions."""
        sessions = []
        for filename in os.listdir(self._sessions_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self._sessions_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    sessions.append({
                        "id": data.get("session_id", filename),
                        "started": data.get("started_at", "unknown"),
                        "targets": len(data.get("targets", [])),
                        "commands": len(data.get("commands_executed", [])),
                        "phase": data.get("phase", "unknown")
                    })
                except (json.JSONDecodeError, OSError):
                    pass
        return sessions

    def generate_report(self) -> str:
        """Generate a text report of the current session."""
        if not self.session:
            return "No active session."

        report = []
        report.append("=" * 70)
        report.append("TEJ AI - SECURITY ASSESSMENT REPORT")
        report.append("=" * 70)
        report.append(f"Session: {self.session.session_id}")
        report.append(f"Started: {self.session.started_at}")
        report.append(f"Phase: {self.session.phase}")
        report.append(f"Report Generated: {datetime.now().isoformat()}")
        report.append("")

        # Targets
        report.append("-" * 40)
        report.append("TARGETS")
        report.append("-" * 40)
        for t in self.session.targets:
            report.append(f"  • {t}")
        report.append("")

        # Tools Used
        report.append("-" * 40)
        report.append("TOOLS USED")
        report.append("-" * 40)
        for tool in self.session.tools_used:
            report.append(f"  • {tool}")
        report.append("")

        # Commands Executed
        report.append("-" * 40)
        report.append(f"COMMANDS EXECUTED ({len(self.session.commands_executed)})")
        report.append("-" * 40)
        for cmd in self.session.commands_executed:
            status = "✓" if cmd.get("exit_code") == 0 else "✗"
            report.append(f"  [{status}] {cmd.get('command', 'N/A')}")
            report.append(f"      Duration: {cmd.get('duration', 0):.2f}s")
        report.append("")

        # Findings
        report.append("-" * 40)
        report.append(f"FINDINGS ({len(self.session.findings)})")
        report.append("-" * 40)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_findings = sorted(
            self.session.findings,
            key=lambda f: severity_order.get(f.get("severity", "info"), 5)
        )
        for f in sorted_findings:
            sev = f.get("severity", "info").upper()
            report.append(f"  [{sev}] {f.get('description', 'N/A')}")
        report.append("")

        # Notes
        if self.session.notes:
            report.append("-" * 40)
            report.append("NOTES")
            report.append("-" * 40)
            for note in self.session.notes:
                report.append(f"  {note}")
            report.append("")

        report.append("=" * 70)
        report.append("End of Report - Generated by Tej AI")
        report.append("=" * 70)

        return "\n".join(report)

    def get_session_summary(self) -> Dict[str, Any]:
        """Get a quick summary of the current session."""
        if not self.session:
            return {"status": "no_session"}

        return {
            "session_id": self.session.session_id,
            "phase": self.session.phase,
            "targets": len(self.session.targets),
            "tools_used": len(self.session.tools_used),
            "commands_run": len(self.session.commands_executed),
            "findings": len(self.session.findings),
            "notes": len(self.session.notes)
        }

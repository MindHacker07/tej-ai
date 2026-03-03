"""
Tej AI - Tool Executor
Handles executing security tools, capturing output, and managing processes.
"""

import os
import sys
import time
import signal
import threading
import subprocess
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from queue import Queue
from datetime import datetime

from tej.core.engine import ToolResult
from tej.core.platform_manager import PlatformManager, Platform


@dataclass 
class ExecutionConfig:
    """Configuration for tool execution."""
    timeout: int = 300  # 5 minutes default
    capture_output: bool = True
    stream_output: bool = True
    working_dir: Optional[str] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    shell: bool = True
    sudo: bool = False


class ToolExecutor:
    """
    Executes security tools with proper handling, output capture,
    timeout management, and cross-platform support.
    """

    def __init__(self, platform_manager: PlatformManager):
        self.platform = platform_manager
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.execution_log: List[Dict[str, Any]] = []
        self.output_callbacks: List[Callable] = []
        self._output_dir = self._setup_output_dir()

    def _setup_output_dir(self) -> str:
        """Create output directory for tool results."""
        if self.platform.platform == Platform.WINDOWS:
            base = os.path.expanduser("~\\tej_output")
        else:
            base = os.path.expanduser("~/tej_output")
        
        os.makedirs(base, exist_ok=True)
        return base

    def execute(self, command: str, tool_name: str = "unknown",
                config: Optional[ExecutionConfig] = None) -> ToolResult:
        """
        Execute a tool command and capture results.
        """
        if config is None:
            config = ExecutionConfig()

        # Adapt command for platform
        command = self.platform.adapt_command(command)
        
        # Add sudo if needed
        if config.sudo or self.platform.needs_sudo(command):
            command = self.platform.wrap_command(command)

        start_time = time.time()
        stdout_data = []
        stderr_data = []

        # Log execution
        exec_entry = {
            "tool": tool_name,
            "command": command,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "timeout": config.timeout,
                "shell": config.shell
            }
        }

        try:
            # Set up environment
            env = os.environ.copy()
            env.update(config.env_vars)

            # Execute the command
            process = subprocess.Popen(
                command,
                shell=config.shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=config.working_dir,
                bufsize=1
            )

            # Track running process
            proc_id = f"{tool_name}_{int(start_time)}"
            self.running_processes[proc_id] = process

            # Read output with timeout
            if config.stream_output:
                stdout_text, stderr_text = self._stream_output(
                    process, config.timeout, stdout_data
                )
            else:
                try:
                    stdout_text, stderr_text = process.communicate(
                        timeout=config.timeout
                    )
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout_text, stderr_text = process.communicate()
                    stderr_text += "\n[Tej] Command timed out after {}s".format(
                        config.timeout
                    )

            # Remove from running
            self.running_processes.pop(proc_id, None)

            duration = time.time() - start_time
            exit_code = process.returncode

            result = ToolResult(
                tool_name=tool_name,
                command=command,
                exit_code=exit_code if exit_code is not None else -1,
                stdout=stdout_text,
                stderr=stderr_text,
                duration=duration
            )

            # Save output to file
            self._save_output(tool_name, result)

            exec_entry["exit_code"] = result.exit_code
            exec_entry["duration"] = duration
            exec_entry["output_lines"] = len(stdout_text.split('\n'))

        except FileNotFoundError:
            result = ToolResult(
                tool_name=tool_name,
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"[Tej] Tool '{tool_name}' not found. "
                       f"Install it with: {self.platform._get_install_command(tool_name)}",
                duration=time.time() - start_time
            )
            exec_entry["error"] = "Tool not found"

        except PermissionError:
            result = ToolResult(
                tool_name=tool_name,
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"[Tej] Permission denied. Try running with sudo/admin privileges.",
                duration=time.time() - start_time
            )
            exec_entry["error"] = "Permission denied"

        except Exception as e:
            result = ToolResult(
                tool_name=tool_name,
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"[Tej] Execution error: {str(e)}",
                duration=time.time() - start_time
            )
            exec_entry["error"] = str(e)

        self.execution_log.append(exec_entry)
        return result

    def _stream_output(self, process: subprocess.Popen, 
                       timeout: int, stdout_collector: List[str]) -> tuple:
        """Stream output from process with timeout."""
        stdout_lines = []
        stderr_lines = []
        
        def read_stdout():
            try:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        stdout_lines.append(line)
                        stdout_collector.append(line)
                        # Notify callbacks
                        for callback in self.output_callbacks:
                            try:
                                callback(line.rstrip())
                            except Exception:
                                pass
            except (ValueError, OSError):
                pass

        def read_stderr():
            try:
                for line in iter(process.stderr.readline, ''):
                    if line:
                        stderr_lines.append(line)
            except (ValueError, OSError):
                pass

        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()

        # Wait with timeout
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            stderr_lines.append(f"\n[Tej] Command timed out after {timeout}s\n")

        stdout_thread.join(timeout=2)
        stderr_thread.join(timeout=2)

        return ''.join(stdout_lines), ''.join(stderr_lines)

    def _save_output(self, tool_name: str, result: ToolResult):
        """Save tool output to a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{tool_name}_{timestamp}.txt"
        filepath = os.path.join(self._output_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"{'='*60}\n")
                f.write(f"Tej AI - Tool Output Report\n")
                f.write(f"{'='*60}\n")
                f.write(f"Tool: {result.tool_name}\n")
                f.write(f"Command: {result.command}\n")
                f.write(f"Exit Code: {result.exit_code}\n")
                f.write(f"Duration: {result.duration:.2f}s\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"{'='*60}\n\n")
                f.write("--- STDOUT ---\n")
                f.write(result.stdout)
                if result.stderr:
                    f.write("\n\n--- STDERR ---\n")
                    f.write(result.stderr)
                f.write(f"\n{'='*60}\n")
        except OSError:
            pass

    def execute_chain(self, commands: List[Dict[str, str]], 
                      stop_on_error: bool = True) -> List[ToolResult]:
        """Execute a chain of commands sequentially."""
        results = []
        for cmd_info in commands:
            result = self.execute(
                cmd_info["command"],
                tool_name=cmd_info.get("tool", "unknown")
            )
            results.append(result)
            if stop_on_error and result.exit_code != 0:
                break
        return results

    def kill_process(self, proc_id: str) -> bool:
        """Kill a running process."""
        if proc_id in self.running_processes:
            try:
                process = self.running_processes[proc_id]
                process.kill()
                del self.running_processes[proc_id]
                return True
            except Exception:
                return False
        return False

    def kill_all(self):
        """Kill all running processes."""
        for proc_id in list(self.running_processes.keys()):
            self.kill_process(proc_id)

    def add_output_callback(self, callback: Callable):
        """Add a callback for real-time output streaming."""
        self.output_callbacks.append(callback)

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the execution log."""
        return self.execution_log.copy()

    def get_output_dir(self) -> str:
        """Get the output directory path."""
        return self._output_dir

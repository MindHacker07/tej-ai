"""
Tej AI - Interactive Shell
Main interactive command-line interface for Tej AI.
"""

import os
import sys
import time
import readline
import traceback
from typing import Optional, List

from tej.core.engine import TejBrain, TaskCategory
from tej.core.platform_manager import PlatformManager
from tej.core.executor import ToolExecutor, ExecutionConfig
from tej.core.session import SessionManager
from tej.tools.registry import (
    get_all_tools, get_tools_by_category, get_tools_by_tag,
    search_tools, get_all_categories, get_tool_count, TOOL_REGISTRY
)
from tej.tools.parsers import OutputParserFactory
from tej.utils.helpers import (
    Colors, BANNER, HELP_TEXT, clear_screen, format_table, truncate
)
from tej.utils.config import ConfigManager


class TejShell:
    """
    Interactive AI-powered security shell.
    Processes natural language input and orchestrates Kali Linux tools.
    """

    def __init__(self):
        # Initialize core components
        self.brain = TejBrain()
        self.platform_mgr = PlatformManager()
        self.executor = ToolExecutor(self.platform_mgr)
        self.config_mgr = ConfigManager()
        self.config = self.config_mgr.load()
        self.session_mgr = SessionManager(
            self.brain, self.config.output_dir
        )

        # State
        self.running = True
        self.default_target: Optional[str] = self.config.default_target or None
        self.last_result = None
        self.last_commands = []
        self.command_history: List[str] = []

        # Auto-start session
        if self.config.auto_session:
            self.session_mgr.new_session()

        # Setup readline history
        self._setup_readline()

    def _setup_readline(self):
        """Configure readline for command history and tab completion."""
        try:
            history_file = os.path.join(
                self.config.output_dir, ".tej_history"
            )
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            try:
                readline.read_history_file(history_file)
            except FileNotFoundError:
                pass
            readline.set_history_length(1000)

            # Tab completion
            tool_names = list(TOOL_REGISTRY.keys())
            commands = [
                "tools", "tool", "search", "check", "scan-tools",
                "session", "history", "set", "run", "last",
                "platform", "clear", "help", "exit", "quit",
                "new", "save", "load", "list", "report", "status"
            ]
            all_completions = tool_names + commands

            def completer(text, state):
                options = [c for c in all_completions if c.startswith(text)]
                return options[state] if state < len(options) else None

            readline.set_completer(completer)
            readline.parse_and_bind("tab: complete")
        except Exception:
            pass  # readline not available (Windows without pyreadline)

    def start(self):
        """Start the interactive Tej AI shell."""
        clear_screen()
        print(BANNER)
        self._print_status()
        print()

        while self.running:
            try:
                prompt = self._build_prompt()
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue

                self.command_history.append(user_input)
                self._process_input(user_input)

            except KeyboardInterrupt:
                print(f"\n{Colors.warning('Use \"exit\" to quit Tej AI.')}")
            except EOFError:
                self._do_exit()
            except Exception as e:
                print(f"\n{Colors.error(f'Error: {str(e)}')}")
                if self.config.verbose:
                    traceback.print_exc()

        # Cleanup
        self._cleanup()

    def _build_prompt(self) -> str:
        """Build the command prompt string."""
        parts = [Colors.BRIGHT_RED + "tej" + Colors.RESET]
        
        # Show target if set
        if self.default_target:
            parts.append(Colors.DIM + "@" + Colors.BRIGHT_CYAN + 
                        self.default_target + Colors.RESET)
        
        # Show session phase
        if self.session_mgr.session:
            phase = self.session_mgr.session.phase[:5]
            parts.append(Colors.DIM + f"({phase})" + Colors.RESET)

        return " ".join(parts) + Colors.BRIGHT_GREEN + " > " + Colors.RESET

    def _print_status(self):
        """Print system status on startup."""
        info = self.platform_mgr.get_system_info()
        admin_str = Colors.success("Yes") if info["is_admin"] == "True" else Colors.warning("No")
        
        print(f"  {Colors.dim('Platform:')} {Colors.info(info['platform'])}")
        print(f"  {Colors.dim('System:')} {info['os']} {info['architecture']}")
        print(f"  {Colors.dim('Admin/Root:')} {admin_str}")
        print(f"  {Colors.dim('Tools DB:')} {Colors.info(str(get_tool_count()))} tools registered")
        print(f"  {Colors.dim('Output:')} {self.executor.get_output_dir()}")
        print(f"\n  {Colors.dim('Type')} {Colors.info('help')} {Colors.dim('for commands or just describe what you want to do.')}")

    def _process_input(self, user_input: str):
        """Process user input - either a command or natural language."""
        parts = user_input.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Built-in commands
        command_map = {
            "help": lambda: print(HELP_TEXT),
            "exit": self._do_exit,
            "quit": self._do_exit,
            "clear": clear_screen,
            "cls": clear_screen,
            "tools": lambda: self._cmd_tools(args),
            "tool": lambda: self._cmd_tool_info(args),
            "search": lambda: self._cmd_search(args),
            "check": lambda: self._cmd_check(args),
            "scan-tools": lambda: self._cmd_scan_tools(),
            "session": lambda: self._cmd_session(args),
            "history": lambda: self._cmd_history(),
            "set": lambda: self._cmd_set(args),
            "run": lambda: self._cmd_run(args),
            "last": lambda: self._cmd_last(),
            "platform": lambda: self._cmd_platform(),
        }

        if cmd in command_map:
            command_map[cmd]()
        else:
            # Natural language processing
            self._process_natural_language(user_input)

    # ---- Built-in Commands ----

    def _cmd_tools(self, args: list):
        """List tools by category."""
        if args:
            # Show tools in specific category
            category = args[0].lower()
            tools = get_tools_by_category(category)
            if not tools:
                # Try as tag
                tools = get_tools_by_tag(category)
            
            if tools:
                print(f"\n{Colors.header(f'Tools - {category.title()}')}")
                rows = []
                for t in tools:
                    status = "✓" if self.platform_mgr.check_tool(t.name).available else "✗"
                    status_colored = Colors.success(status) if status == "✓" else Colors.error(status)
                    rows.append([status_colored, t.name, truncate(t.description, 60)])
                print(format_table(["", "Tool", "Description"], rows))
            else:
                print(Colors.warning(f"No tools found for category: {category}"))
                print(f"Available categories: {', '.join(get_all_categories())}")
        else:
            # Show all categories
            print(f"\n{Colors.header('Tool Categories')}")
            categories = get_all_categories()
            for cat in sorted(categories):
                tools = get_tools_by_category(cat)
                print(f"  {Colors.accent(cat.ljust(25))} {Colors.dim(f'{len(tools)} tools')}")
            print(f"\n{Colors.dim(f'Total: {get_tool_count()} tools | Use \"tools <category>\" for details')}")

    def _cmd_tool_info(self, args: list):
        """Show detailed tool information."""
        if not args:
            print(Colors.warning("Usage: tool <name>"))
            return
        
        tool_name = args[0]
        help_info = self.brain.get_tool_help(tool_name)
        
        if tool_name in TOOL_REGISTRY:
            tool = TOOL_REGISTRY[tool_name]
            availability = self.platform_mgr.check_tool(tool_name)
            
            print(f"\n{Colors.header(f'Tool: {tool.name}')}")
            print(f"  {Colors.dim('Category:')} {tool.category}")
            print(f"  {Colors.dim('Description:')} {tool.description}")
            
            status = Colors.success("Installed") if availability.available else Colors.error("Not installed")
            print(f"  {Colors.dim('Status:')} {status}")
            if availability.version:
                print(f"  {Colors.dim('Version:')} {availability.version}")
            if availability.path:
                print(f"  {Colors.dim('Path:')} {availability.path}")
            if not availability.available and availability.install_command:
                print(f"  {Colors.dim('Install:')} {Colors.info(availability.install_command)}")
            
            if tool.usage_examples:
                print(f"\n  {Colors.dim('Examples:')}")
                for ex in tool.usage_examples:
                    print(f"    {Colors.info(ex)}")
            
            if tool.common_flags:
                print(f"\n  {Colors.dim('Common Flags:')}")
                for flag, desc in tool.common_flags.items():
                    print(f"    {Colors.accent(flag.ljust(15))} {desc}")
            
            print(f"\n  {Colors.dim('Platforms:')} {', '.join(tool.platforms)}")
            print(f"  {Colors.dim('Root required:')} {'Yes' if tool.requires_root else 'No'}")
            print(f"  {Colors.dim('Tags:')} {', '.join(tool.tags)}")
        else:
            print(Colors.warning(f"Tool '{tool_name}' not in registry. Try 'search {tool_name}'."))

    def _cmd_search(self, args: list):
        """Search for tools."""
        if not args:
            print(Colors.warning("Usage: search <query>"))
            return
        
        query = " ".join(args)
        results = search_tools(query)
        
        if results:
            print(f"\n{Colors.header(f'Search results for \"{query}\"')}")
            rows = []
            for t in results:
                rows.append([t.name, t.category, truncate(t.description, 50)])
            print(format_table(["Tool", "Category", "Description"], rows))
        else:
            print(Colors.warning(f"No tools found matching: {query}"))

    def _cmd_check(self, args: list):
        """Check if a tool is installed."""
        if not args:
            print(Colors.warning("Usage: check <tool>"))
            return
        
        tool_name = args[0]
        result = self.platform_mgr.check_tool(tool_name)
        
        if result.available:
            print(Colors.success(f"✓ {tool_name} is installed"))
            if result.path:
                print(f"  Path: {result.path}")
            if result.version:
                print(f"  Version: {result.version}")
        else:
            print(Colors.error(f"✗ {tool_name} is NOT installed"))
            if result.install_command:
                print(f"  Install: {Colors.info(result.install_command)}")
            if result.platform_notes:
                print(f"  Note: {result.platform_notes}")

    def _cmd_scan_tools(self):
        """Scan system for all registered tools."""
        print(f"\n{Colors.header('Scanning system for tools...')}")
        all_tools = get_all_tools()
        installed = 0
        missing = 0
        
        rows = []
        for name, tool in sorted(all_tools.items()):
            avail = self.platform_mgr.check_tool(name)
            if avail.available:
                installed += 1
                status = Colors.success("✓ Installed")
            else:
                missing += 1
                status = Colors.error("✗ Missing")
            rows.append([name, tool.category, status])
        
        print(format_table(["Tool", "Category", "Status"], rows))
        print(f"\n{Colors.success(f'Installed: {installed}')} | {Colors.error(f'Missing: {missing}')} | Total: {len(all_tools)}")

    def _cmd_session(self, args: list):
        """Session management commands."""
        if not args:
            print(Colors.warning("Usage: session <new|save|load|list|report|status>"))
            return
        
        subcmd = args[0].lower()
        
        if subcmd == "new":
            name = args[1] if len(args) > 1 else ""
            session = self.session_mgr.new_session(name)
            print(Colors.success(f"New session started: {session.session_id}"))
        
        elif subcmd == "save":
            path = self.session_mgr.save_session()
            if path:
                print(Colors.success(f"Session saved: {path}"))
            else:
                print(Colors.warning("No active session to save."))
        
        elif subcmd == "load":
            if len(args) < 2:
                print(Colors.warning("Usage: session load <session_id>"))
                return
            session = self.session_mgr.load_session(args[1])
            if session:
                print(Colors.success(f"Session loaded: {session.session_id}"))
            else:
                print(Colors.error(f"Session not found: {args[1]}"))
        
        elif subcmd == "list":
            sessions = self.session_mgr.list_sessions()
            if sessions:
                rows = [[s["id"], s["started"][:19], str(s["targets"]), 
                         str(s["commands"]), s["phase"]] for s in sessions]
                print(format_table(
                    ["Session ID", "Started", "Targets", "Commands", "Phase"],
                    rows
                ))
            else:
                print(Colors.dim("No saved sessions found."))
        
        elif subcmd == "report":
            report = self.session_mgr.generate_report()
            print(report)
            # Also save to file
            if self.session_mgr.session:
                report_path = os.path.join(
                    self.executor.get_output_dir(),
                    f"report_{self.session_mgr.session.session_id}.txt"
                )
                with open(report_path, 'w') as f:
                    f.write(report)
                print(Colors.success(f"\nReport saved: {report_path}"))
        
        elif subcmd == "status":
            summary = self.session_mgr.get_session_summary()
            if summary.get("status") == "no_session":
                print(Colors.warning("No active session."))
            else:
                print(f"\n{Colors.header('Session Status')}")
                for key, val in summary.items():
                    print(f"  {Colors.dim(key + ':')} {val}")
        
        elif subcmd == "phase":
            if len(args) > 1:
                self.session_mgr.set_phase(args[1])
                print(Colors.success(f"Phase set to: {args[1]}"))
            else:
                next_phase = self.session_mgr.next_phase()
                print(Colors.info(f"Advanced to phase: {next_phase}"))

    def _cmd_history(self):
        """Show execution history."""
        history = self.executor.get_execution_history()
        if not history:
            print(Colors.dim("No commands executed yet."))
            return
        
        print(f"\n{Colors.header('Execution History')}")
        for i, entry in enumerate(history[-20:], 1):
            status = Colors.success("✓") if entry.get("exit_code") == 0 else Colors.error("✗")
            tool = entry.get("tool", "unknown")
            cmd = truncate(entry.get("command", ""), 60)
            dur = f"{entry.get('duration', 0):.1f}s"
            print(f"  {status} [{Colors.accent(tool)}] {cmd} {Colors.dim(dur)}")

    def _cmd_set(self, args: list):
        """Set configuration values."""
        if len(args) < 2:
            print(Colors.warning("Usage: set <key> <value>"))
            print(f"  {Colors.info('target')} <ip/domain>  - Set default target")
            print(f"  {Colors.info('interface')} <iface>    - Set network interface")
            print(f"  {Colors.info('wordlist')} <path>      - Set default wordlist")
            print(f"  {Colors.info('timeout')} <seconds>    - Set default timeout")
            print(f"  {Colors.info('verbose')} on/off       - Toggle verbose mode")
            return
        
        key = args[0].lower()
        value = " ".join(args[1:])
        
        if key == "target":
            self.default_target = value
            self.session_mgr.add_target(value)
            print(Colors.success(f"Target set: {value}"))
        elif key == "interface":
            self.config.default_interface = value
            print(Colors.success(f"Interface set: {value}"))
        elif key == "wordlist":
            self.config.default_wordlist = value
            print(Colors.success(f"Wordlist set: {value}"))
        elif key == "timeout":
            self.config.default_timeout = int(value)
            print(Colors.success(f"Timeout set: {value}s"))
        elif key == "verbose":
            self.config.verbose = value.lower() in ("on", "true", "yes", "1")
            print(Colors.success(f"Verbose: {'on' if self.config.verbose else 'off'}"))
        else:
            print(Colors.warning(f"Unknown setting: {key}"))

    def _cmd_run(self, args: list):
        """Execute a raw command."""
        if not args:
            print(Colors.warning("Usage: run <command>"))
            return
        
        command = " ".join(args)
        self._execute_command(command, command.split()[0])

    def _cmd_last(self):
        """Show last command result."""
        if self.last_result:
            print(f"\n{Colors.header(f'Last: {self.last_result.tool_name}')}")
            print(f"{Colors.dim(f'Command: {self.last_result.command}')}")
            print(f"{Colors.dim(f'Exit: {self.last_result.exit_code} | Duration: {self.last_result.duration:.2f}s')}")
            print(f"\n{self.last_result.stdout}")
            if self.last_result.stderr:
                print(f"\n{Colors.error('STDERR:')}\n{self.last_result.stderr}")
        else:
            print(Colors.dim("No previous command output."))

    def _cmd_platform(self):
        """Show platform information."""
        info = self.platform_mgr.get_system_info()
        print(f"\n{Colors.header('Platform Information')}")
        for key, val in info.items():
            print(f"  {Colors.dim(key + ':'):<20} {val}")

    # ---- Natural Language Processing ----

    def _process_natural_language(self, user_input: str):
        """Process natural language input using the AI brain."""
        
        # Override target if default is set
        intent = self.brain.parse_intent(user_input)
        
        if not intent.target and self.default_target:
            intent.target = self.default_target

        # Show understanding
        print(f"\n{Colors.dim('Understanding:')}")
        print(f"  {Colors.dim('Category:')} {Colors.info(intent.category.value)}")
        print(f"  {Colors.dim('Action:')} {intent.action}")
        if intent.target:
            print(f"  {Colors.dim('Target:')} {Colors.accent(intent.target)}")
        print(f"  {Colors.dim('Confidence:')} {intent.confidence:.0%}")
        print(f"  {Colors.dim('Tools:')} {', '.join(intent.tools_suggested[:5])}")

        # Build commands
        commands = self.brain.build_command(intent)
        
        if not commands:
            print(Colors.warning("\nCouldn't determine the right command. Try being more specific."))
            print(Colors.dim("Example: 'scan ports on 192.168.1.1' or 'brute force ssh on target'"))
            return

        # Display proposed commands
        print(f"\n{Colors.header('Proposed Commands:')}")
        for i, cmd_info in enumerate(commands, 1):
            print(f"  {Colors.accent(f'[{i}]')} {Colors.info(cmd_info['command'])}")
            print(f"      {Colors.dim(cmd_info['description'])}")
        
        self.last_commands = commands

        # Ask for confirmation
        print(f"\n{Colors.dim('Options:')} "
              f"{Colors.info('y')}=execute all, "
              f"{Colors.info('1-' + str(len(commands)))}=execute specific, "
              f"{Colors.info('e')}=edit, "
              f"{Colors.info('n')}=cancel")
        
        try:
            choice = input(f"{Colors.BRIGHT_GREEN}  > {Colors.RESET}").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print(Colors.dim("\nCancelled."))
            return

        if choice in ('y', 'yes'):
            for cmd_info in commands:
                self._execute_command(
                    cmd_info["command"], cmd_info["tool"]
                )
        elif choice.isdigit() and 1 <= int(choice) <= len(commands):
            cmd_info = commands[int(choice) - 1]
            self._execute_command(cmd_info["command"], cmd_info["tool"])
        elif choice == 'e':
            self._edit_and_execute(commands)
        elif choice in ('n', 'no', ''):
            print(Colors.dim("Cancelled."))
        else:
            print(Colors.warning("Invalid choice."))

    def _edit_and_execute(self, commands: list):
        """Let user edit a command before executing."""
        print(Colors.dim("Enter the command to execute (or blank to cancel):"))
        try:
            edited = input(f"{Colors.BRIGHT_GREEN}  cmd> {Colors.RESET}").strip()
            if edited:
                tool = edited.split()[0] if edited else "custom"
                self._execute_command(edited, tool)
        except (KeyboardInterrupt, EOFError):
            print(Colors.dim("\nCancelled."))

    def _execute_command(self, command: str, tool_name: str):
        """Execute a command with output display."""
        # Check if tool has placeholder values
        if "<" in command and ">" in command:
            print(Colors.warning("\n⚠ Command contains placeholder values (marked with < >)."))
            print(Colors.dim("Please provide the missing values:"))
            
            import re
            placeholders = re.findall(r'<(\w+)>', command)
            for ph in placeholders:
                try:
                    value = input(f"  {Colors.accent(ph)}: ").strip()
                    if value:
                        command = command.replace(f"<{ph}>", value)
                    else:
                        print(Colors.dim("Cancelled."))
                        return
                except (KeyboardInterrupt, EOFError):
                    print(Colors.dim("\nCancelled."))
                    return

        print(f"\n{Colors.header('Executing:')} {Colors.info(command)}")
        print(Colors.dim("─" * 60))

        # Set up real-time output
        def output_callback(line):
            print(f"  {line}")

        self.executor.add_output_callback(output_callback)

        # Execute
        config = ExecutionConfig(
            timeout=self.config.default_timeout,
            stream_output=True
        )
        
        result = self.executor.execute(command, tool_name, config)
        self.last_result = result

        # Remove callback (prevent duplicates)
        if output_callback in self.executor.output_callbacks:
            self.executor.output_callbacks.remove(output_callback)

        # Show results summary
        print(Colors.dim("─" * 60))
        
        if result.exit_code == 0:
            print(Colors.success(f"✓ Completed in {result.duration:.2f}s"))
        else:
            print(Colors.error(f"✗ Exit code: {result.exit_code} ({result.duration:.2f}s)"))
            if result.stderr and "[Tej]" in result.stderr:
                print(Colors.error(result.stderr))

        # Parse and analyze output
        analysis = self.brain.analyze_output(result)
        
        if analysis["findings"]:
            print(f"\n{Colors.header('Findings:')}")
            for finding in analysis["findings"]:
                if finding.get("type") == "port":
                    state_color = Colors.success if finding["state"] == "open" else Colors.dim
                    print(f"  {state_color(finding['state'])} "
                          f"{finding['port']}/{finding.get('service', 'unknown')}")
                elif finding.get("type") == "hosts_discovered":
                    print(f"  Hosts: {', '.join(finding['hosts'][:10])}")
                else:
                    print(f"  {finding}")

        if analysis["recommendations"]:
            print(f"\n{Colors.header('Recommendations:')}")
            for rec in analysis["recommendations"][:5]:
                print(f"  → {rec}")

        # Suggest next steps
        if self.last_result and self.last_result.exit_code == 0:
            intent = self.brain.parse_intent(command)
            suggestions = self.brain.suggest_next_steps(intent, [result])
            if suggestions:
                print(f"\n{Colors.header('Next Steps:')}")
                for i, sug in enumerate(suggestions[:5], 1):
                    print(f"  {Colors.dim(f'{i}.')} {sug}")

        # Record in session
        if self.session_mgr.session:
            intent = self.brain.parse_intent(command)
            self.session_mgr.record_execution(intent, result)
            
            for finding in analysis["findings"]:
                self.session_mgr.add_finding(
                    finding.get("type", "general"),
                    str(finding),
                    analysis.get("severity", "info")
                )

    def _do_exit(self):
        """Exit Tej AI."""
        # Save session
        if self.session_mgr.session:
            path = self.session_mgr.save_session()
            if path:
                print(Colors.dim(f"Session saved: {path}"))

        # Save config
        self.config_mgr.save()

        # Save readline history
        try:
            history_file = os.path.join(self.config.output_dir, ".tej_history")
            readline.write_history_file(history_file)
        except Exception:
            pass

        # Kill any running processes
        self.executor.kill_all()

        print(f"\n{Colors.accent('Tej AI')} - {Colors.dim('Stay sharp. Stay ethical.')}")
        self.running = False

    def _cleanup(self):
        """Cleanup on exit."""
        self.executor.kill_all()

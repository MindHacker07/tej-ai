#!/usr/bin/env python3
"""
Tej AI - Main Entry Point
AI-Powered Security Tool Orchestrator for Kali Linux & Windows
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(
        prog="tej",
        description="Tej AI - AI-Powered Security Tool Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tej                          Start interactive shell
  tej --scan 192.168.1.1       Quick port scan
  tej --tool nmap              Get tool information
  tej --search "sql injection" Search for tools
  tej --list-tools             List all tools
  tej --check nmap             Check if tool is installed
  tej --platform               Show platform info
        """
    )

    parser.add_argument(
        "--scan", metavar="TARGET",
        help="Quick scan a target (nmap -sV -sC)"
    )
    parser.add_argument(
        "--tool", metavar="NAME",
        help="Get information about a specific tool"
    )
    parser.add_argument(
        "--search", metavar="QUERY",
        help="Search for security tools"
    )
    parser.add_argument(
        "--list-tools", action="store_true",
        help="List all registered tools"
    )
    parser.add_argument(
        "--list-categories", action="store_true",
        help="List tool categories"
    )
    parser.add_argument(
        "--check", metavar="TOOL",
        help="Check if a tool is installed"
    )
    parser.add_argument(
        "--scan-tools", action="store_true",
        help="Scan system for all available tools"
    )
    parser.add_argument(
        "--platform", action="store_true",
        help="Show platform information"
    )
    parser.add_argument(
        "--run", metavar="COMMAND", nargs=argparse.REMAINDER,
        help="Execute a command directly"
    )
    parser.add_argument(
        "--version", action="version",
        version="Tej AI v1.0.0"
    )
    parser.add_argument(
        "--gui", action="store_true",
        help="Launch GUI desktop application"
    )
    parser.add_argument(
        "--install-desktop", action="store_true",
        help="Install as desktop application (Linux)"
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable colored output"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # GUI mode
    if args.gui:
        from tej.gui import launch_gui
        launch_gui()
        return

    # Install desktop application (Linux)
    if args.install_desktop:
        from tej.install_desktop import install_desktop
        install_desktop()
        return

    # Handle CLI-only commands without starting the shell
    if args.list_tools or args.list_categories or args.search or \
       args.tool or args.check or args.scan_tools or args.platform or args.scan:
        _handle_cli_command(args)
    elif args.run:
        _handle_run_command(args)
    else:
        # Start interactive shell
        try:
            from tej.cli.shell import TejShell
            shell = TejShell()
            if args.verbose:
                shell.config.verbose = True
            shell.start()
        except ImportError as e:
            print(f"Error loading Tej AI: {e}")
            print("Make sure all dependencies are installed: pip install -r requirements.txt")
            sys.exit(1)


def _handle_cli_command(args):
    """Handle one-shot CLI commands."""
    from tej.utils.helpers import Colors, format_table, truncate
    from tej.tools.registry import (
        get_all_tools, get_tools_by_category, get_all_categories,
        search_tools, get_tool_count, TOOL_REGISTRY
    )
    from tej.core.platform_manager import PlatformManager

    if args.list_tools:
        tools = get_all_tools()
        rows = [[t.name, t.category, truncate(t.description, 55)] 
                for t in sorted(tools.values(), key=lambda x: x.category)]
        print(f"\n{Colors.header(f'Tej AI - All Tools ({get_tool_count()})')}\n")
        print(format_table(["Tool", "Category", "Description"], rows))

    elif args.list_categories:
        categories = get_all_categories()
        for cat in sorted(categories):
            tools = get_tools_by_category(cat)
            print(f"  {Colors.accent(cat.ljust(25))} {len(tools)} tools")

    elif args.search:
        results = search_tools(args.search)
        if results:
            rows = [[t.name, t.category, truncate(t.description, 50)] for t in results]
            print(format_table(["Tool", "Category", "Description"], rows))
        else:
            print(Colors.warning(f"No tools found for: {args.search}"))

    elif args.tool:
        if args.tool in TOOL_REGISTRY:
            tool = TOOL_REGISTRY[args.tool]
            print(f"\n{Colors.header(tool.name)}")
            print(f"  {tool.description}")
            print(f"  Category: {tool.category}")
            if tool.usage_examples:
                print(f"  Examples:")
                for ex in tool.usage_examples:
                    print(f"    {Colors.info(ex)}")
        else:
            print(Colors.warning(f"Tool not found: {args.tool}"))

    elif args.check:
        pm = PlatformManager()
        result = pm.check_tool(args.check)
        if result.available:
            print(Colors.success(f"✓ {args.check} is installed"))
            if result.version:
                print(f"  Version: {result.version}")
        else:
            print(Colors.error(f"✗ {args.check} is NOT installed"))
            if result.install_command:
                print(f"  Install: {result.install_command}")

    elif args.scan_tools:
        pm = PlatformManager()
        tools = get_all_tools()
        installed = 0
        for name in sorted(tools.keys()):
            avail = pm.check_tool(name)
            status = Colors.success("✓") if avail.available else Colors.error("✗")
            print(f"  {status} {name}")
            if avail.available:
                installed += 1
        print(f"\n  {installed}/{len(tools)} tools installed")

    elif args.platform:
        pm = PlatformManager()
        info = pm.get_system_info()
        for k, v in info.items():
            print(f"  {k}: {v}")

    elif args.scan:
        from tej.core.executor import ToolExecutor
        from tej.core.engine import TejBrain
        
        pm = PlatformManager()
        executor = ToolExecutor(pm)
        brain = TejBrain()
        
        print(Colors.info(f"Quick scanning {args.scan}..."))
        result = executor.execute(f"nmap -sV -sC {args.scan}", "nmap")
        print(result.stdout)
        if result.stderr:
            print(Colors.error(result.stderr))


def _handle_run_command(args):
    """Handle direct command execution."""
    from tej.core.platform_manager import PlatformManager
    from tej.core.executor import ToolExecutor
    from tej.utils.helpers import Colors

    command = " ".join(args.run)
    if not command:
        print("Usage: tej --run <command>")
        return

    pm = PlatformManager()
    executor = ToolExecutor(pm)
    
    tool_name = command.split()[0]
    print(Colors.info(f"Executing: {command}"))
    result = executor.execute(command, tool_name)
    print(result.stdout)
    if result.stderr:
        print(Colors.error(result.stderr))
    sys.exit(result.exit_code)


if __name__ == "__main__":
    main()

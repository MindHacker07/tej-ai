# TejStrike AI

## AI-Powered Security Tool Orchestrator for Kali Linux & Windows

TejStrike AI is an intelligent security assistant that integrates and communicates with **all Kali Linux tools**. It understands natural language queries via LLMs (Claude, GPT, Groq, Ollama) or its built-in engine, automatically selects the right tools, builds commands, executes them, and analyzes results — all from a single unified interface. It also supports MCP server connectivity for extended tool capabilities.

---

## Features

- **Multi-Model LLM Support** — Connect to Claude (Anthropic), GPT (OpenAI), Groq, or Ollama for intelligent query interpretation
- **Natural Language Interface** — Just describe what you want to do: _"scan ports on 192.168.1.1"_, _"find subdomains of example.com"_, _"crack these hashes with rockyou"_
- **MCP Server Connectivity** — Extend tool capabilities by connecting to Model Context Protocol servers
- **Interactive AI Agent** — Orchestrates LLM + built-in engine + MCP tools seamlessly
- **95+ Security Tools Integrated** — Covers all Kali Linux tool categories
- **Smart Tool Selection** — AI picks the best tool and flags for your task
- **Output Parsing & Analysis** — Automatically extracts findings from tool output
- **Intelligent Next Steps** — Suggests follow-up actions based on results
- **Cross-Platform** — Works on Kali Linux, Debian, Ubuntu, and Windows
- **Session Management** — Track assessments with targets, findings, and reports
- **Built-in Fallback Engine** — Works without any LLM API key using the built-in keyword engine
- **Desktop GUI** — Full tkinter desktop application with chat interface

---

## Quick Start

### On Kali Linux

```bash
cd /opt/kali    # or wherever you extracted
chmod +x tej.sh
./tej.sh
```

### On Windows

```
Double-click tej.bat
# OR
python tej_ai.py
```

### Install as CLI Tool

```bash
pip install -e .
tejstrike    # now available globally
```

### Install with LLM Support

```bash
pip install -e ".[anthropic]"    # Claude support
pip install -e ".[openai]"       # GPT support
pip install -e ".[groq]"         # Groq support
pip install -e ".[all-llm]"      # All LLM providers
```

---

## Usage

### Interactive Shell

```
$ tejstrike

╔══════════════════════════════════════════════════════════╗
║  ████████╗███████╗     ██╗███████╗████████╗██████╗      ║
║  ╚══██╔══╝██╔════╝     ██║██╔════╝╚══██╔══╝██╔══██╗    ║
║     ██║   █████╗       ██║███████╗   ██║   ██████╔╝     ║
║     ██║   ██╔══╝  ██   ██║╚════██║   ██║   ██╔══██╗    ║
║     ██║   ███████╗╚█████╔╝███████║   ██║   ██║  ██║    ║
║     ╚═╝   ╚══════╝ ╚════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝   ║
║   Multi-Model LLM Security Orchestrator [v2.0]          ║
╚══════════════════════════════════════════════════════════╝

tejstrike > scan 192.168.1.1
  Understanding:
    Category: scanning
    Action: scan
    Target: 192.168.1.1
    Tools: nmap, masscan, rustscan

  Proposed Commands:
    [1] nmap -sC -sV -O -A -p- 192.168.1.1

  Options: y=execute, 1=specific, e=edit, n=cancel
  > y

  Executing: nmap -sC -sV -O -A -p- 192.168.1.1
  ────────────────────────────────────
  22/tcp   open  ssh     OpenSSH 8.9
  80/tcp   open  http    Apache 2.4.52
  443/tcp  open  https   Apache 2.4.52
  ────────────────────────────────────
  ✓ Completed in 45.2s

  Findings:
    open 22/ssh
    open 80/http
    open 443/https

  Next Steps:
    1. Run nikto/gobuster against web service on port 80
    2. Try SSH brute force with hydra on port 22
    3. Run whatweb to fingerprint the web application
```

### Natural Language Examples

```
tejstrike > find subdomains of example.com
tejstrike > brute force ssh on 10.0.0.5 with rockyou
tejstrike > check for sql injection on http://target.com/page?id=1
tejstrike > enumerate smb shares on 192.168.1.100
tejstrike > crack this hash file hashes.txt
tejstrike > scan wifi networks
tejstrike > generate a reverse shell payload for windows
tejstrike > search for apache 2.4 exploits
tejstrike > analyze memory dump evidence.raw
tejstrike > fuzz directories on http://target.com
```

### CLI One-Liners

```bash
tejstrike --scan 192.168.1.1              # Quick nmap scan
tejstrike --tool nmap                      # Tool info
tejstrike --search "sql injection"         # Search tools
tejstrike --list-tools                     # All tools
tejstrike --check sqlmap                   # Check installation
tejstrike --scan-tools                     # Scan all tool availability
tejstrike --run nmap -sV 10.0.0.1         # Direct execution
tejstrike --platform                       # System info
```

---

## Tool Categories & Coverage

| Category                   | Tools    | Examples                                      |
| -------------------------- | -------- | --------------------------------------------- |
| **Reconnaissance**         | 14 tools | nmap, theHarvester, amass, recon-ng, shodan   |
| **Scanning**               | 5 tools  | nmap, masscan, rustscan, zmap, hping3         |
| **Vulnerability Analysis** | 9 tools  | nikto, nuclei, wpscan, searchsploit, openvas  |
| **Web Application**        | 12 tools | sqlmap, burpsuite, gobuster, ffuf, zaproxy    |
| **Password Attacks**       | 10 tools | john, hashcat, hydra, medusa, cewl            |
| **Exploitation**           | 4 tools  | metasploit, msfvenom, beef-xss, SET           |
| **Post-Exploitation**      | 6 tools  | mimikatz, bloodhound, empire, chisel          |
| **Wireless**               | 8 tools  | aircrack-ng, wifite, bettercap, reaver        |
| **Sniffing & Spoofing**    | 6 tools  | wireshark, tcpdump, responder, ettercap       |
| **Enumeration**            | 7 tools  | enum4linux, crackmapexec, impacket, smbclient |
| **Forensics**              | 7 tools  | autopsy, volatility, binwalk, steghide        |
| **Reverse Engineering**    | 8 tools  | ghidra, radare2, gdb, apktool, jadx           |

---

## Architecture

```
tej/
├── __init__.py          # Package init
├── __main__.py          # python -m tej support
├── main.py              # Entry point & CLI argument parser
├── core/
│   ├── engine.py        # AI brain - NLP, intent parsing, command building
│   ├── platform_manager.py  # Cross-platform detection & adaptation
│   ├── executor.py      # Tool execution with output capture
│   ├── session.py       # Session management & reporting
│   ├── llm_provider.py  # Multi-model LLM abstraction (Claude, GPT, Groq, Ollama)
│   ├── mcp_client.py    # MCP server connectivity (stdio & SSE)
│   └── agent.py         # Interactive AI agent orchestrator
├── tools/
│   ├── registry.py      # 95+ tool definitions & metadata
│   └── parsers.py       # Output parsers (nmap, hydra, sqlmap, etc.)
├── cli/
│   └── shell.py         # Interactive shell interface
├── gui/
│   ├── app.py           # Desktop GUI application
│   ├── chat.py          # Chat interface panel
│   ├── sidebar.py       # Tool sidebar
│   ├── terminal.py      # Terminal output panel
│   ├── dialogs.py       # Settings & about dialogs (LLM config)
│   └── theme.py         # Dark theme styling
└── utils/
    ├── helpers.py        # Colors, formatting, display utilities
    └── config.py         # Configuration management (LLM, MCP settings)
```

---

## Key Commands

| Command            | Description                        |
| ------------------ | ---------------------------------- |
| `tools`            | List all tool categories           |
| `tools <category>` | List tools in a category           |
| `tool <name>`      | Detailed tool information          |
| `search <query>`   | Search tools by keyword            |
| `check <tool>`     | Check if tool is installed         |
| `scan-tools`       | System-wide tool availability scan |
| `session new`      | Start new assessment session       |
| `session save`     | Save current session               |
| `session report`   | Generate assessment report         |
| `set target <ip>`  | Set default target                 |
| `run <command>`    | Execute raw command                |
| `history`          | View execution history             |
| `help`             | Show all commands                  |

---

## Session & Reporting

TejStrike tracks your entire assessment workflow:

```
tejstrike > session new pentest_client
  New session started: tejstrike_pentest_client_20260303_120000

tejstrike > set target 10.0.0.5
tejstrike > scan 10.0.0.5
tejstrike > enumerate smb on 10.0.0.5
tejstrike > ...

tejstrike > session report

  ══════════════════════════════════════════════
  TEJSTRIKE AI - SECURITY ASSESSMENT REPORT
  ══════════════════════════════════════════════
  Session: tejstrike_pentest_client_20260303_120000
  Targets: 10.0.0.5
  Tools Used: nmap, enum4linux, ...

  FINDINGS (5)
  [HIGH] Open SMB shares with anonymous access
  [MEDIUM] Outdated Apache version detected
  ...
```

---

## Configuration

Config is auto-saved to:

- **Linux**: `~/.config/tejstrike/config.json`
- **Windows**: `%APPDATA%\tejstrike\config.json`

Configurable settings:

- Default target, interface, wordlists
- Execution timeout, thread limits
- Auto-session, output directory
- Tool-specific default flags

---

## Requirements

- **Python 3.8+** (no external packages needed!)
- **Kali Linux** (for full tool availability) or **Windows** (supported tools)

---

## License

MIT License

---

_TejStrike AI — Stay sharp. Stay ethical. Use responsibly for authorized testing only._

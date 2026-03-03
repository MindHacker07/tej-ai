# Tej AI

## AI-Powered Security Tool Orchestrator for Kali Linux & Windows

Tej AI is an intelligent security assistant that integrates and communicates with **all Kali Linux tools**. It understands natural language commands, automatically selects the right tools, builds commands, executes them, and analyzes results — all from a single unified interface.

---

## Features

- **Natural Language Interface** — Just describe what you want to do: _"scan ports on 192.168.1.1"_, _"find subdomains of example.com"_, _"crack these hashes with rockyou"_
- **95+ Security Tools Integrated** — Covers all Kali Linux tool categories
- **Smart Tool Selection** — AI picks the best tool and flags for your task
- **Output Parsing & Analysis** — Automatically extracts findings from tool output
- **Intelligent Next Steps** — Suggests follow-up actions based on results
- **Cross-Platform** — Works on Kali Linux, Debian, Ubuntu, and Windows
- **Session Management** — Track assessments with targets, findings, and reports
- **Zero Dependencies** — Built entirely with Python standard library

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
tej    # now available globally
```

---

## Usage

### Interactive Shell

```
$ tej

╔══════════════════════════════════════════════════════════╗
║   ████████╗███████╗     ██╗                             ║
║   ╚══██╔══╝██╔════╝     ██║                             ║
║      ██║   █████╗       ██║                             ║
║      ██║   ██╔══╝  ██   ██║                             ║
║      ██║   ███████╗╚█████╔╝                             ║
║      ╚═╝   ╚══════╝ ╚════╝                              ║
║   AI-Powered Security Tool Orchestrator                  ║
╚══════════════════════════════════════════════════════════╝

tej > scan 192.168.1.1
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
tej > find subdomains of example.com
tej > brute force ssh on 10.0.0.5 with rockyou
tej > check for sql injection on http://target.com/page?id=1
tej > enumerate smb shares on 192.168.1.100
tej > crack this hash file hashes.txt
tej > scan wifi networks
tej > generate a reverse shell payload for windows
tej > search for apache 2.4 exploits
tej > analyze memory dump evidence.raw
tej > fuzz directories on http://target.com
```

### CLI One-Liners

```bash
tej --scan 192.168.1.1              # Quick nmap scan
tej --tool nmap                      # Tool info
tej --search "sql injection"         # Search tools
tej --list-tools                     # All tools
tej --check sqlmap                   # Check installation
tej --scan-tools                     # Scan all tool availability
tej --run nmap -sV 10.0.0.1         # Direct execution
tej --platform                       # System info
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
│   └── session.py       # Session management & reporting
├── tools/
│   ├── registry.py      # 95+ tool definitions & metadata
│   └── parsers.py       # Output parsers (nmap, hydra, sqlmap, etc.)
├── cli/
│   └── shell.py         # Interactive shell interface
└── utils/
    ├── helpers.py        # Colors, formatting, display utilities
    └── config.py         # Configuration management
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

Tej tracks your entire assessment workflow:

```
tej > session new pentest_client
  New session started: tej_pentest_client_20260303_120000

tej > set target 10.0.0.5
tej > scan 10.0.0.5
tej > enumerate smb on 10.0.0.5
tej > ...

tej > session report

  ══════════════════════════════════════════════
  TEJ AI - SECURITY ASSESSMENT REPORT
  ══════════════════════════════════════════════
  Session: tej_pentest_client_20260303_120000
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

- **Linux**: `~/.config/tej/config.json`
- **Windows**: `%APPDATA%\tej\config.json`

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

_Tej AI — Stay sharp. Stay ethical. Use responsibly for authorized testing only._

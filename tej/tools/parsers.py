"""
TejStrike AI - Output Parsers
Intelligent parsers for security tool output.
"""

import re
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ParsedPort:
    port: int
    protocol: str
    state: str
    service: str
    version: str = ""
    extra_info: str = ""


@dataclass
class ParsedHost:
    ip: str
    hostname: str = ""
    mac: str = ""
    os_guess: str = ""
    ports: List[ParsedPort] = field(default_factory=list)
    state: str = "up"


class NmapParser:
    """Parse nmap output (text and XML)."""

    @staticmethod
    def parse_text(output: str) -> Dict[str, Any]:
        """Parse nmap text output."""
        result = {"hosts": [], "summary": ""}

        current_host = None
        for line in output.split('\n'):
            line = line.strip()

            # Host line
            host_match = re.match(
                r'Nmap scan report for\s+(?:(\S+)\s+\()?(\d+\.\d+\.\d+\.\d+)\)?',
                line
            )
            if host_match:
                if current_host:
                    result["hosts"].append(current_host)
                hostname = host_match.group(1) or ""
                ip = host_match.group(2)
                current_host = ParsedHost(ip=ip, hostname=hostname)
                continue

            # Simple host line (just IP)
            host_match2 = re.match(r'Nmap scan report for\s+(\S+)', line)
            if host_match2 and not current_host:
                addr = host_match2.group(1)
                current_host = ParsedHost(ip=addr)
                continue

            # Port line
            port_match = re.match(
                r'(\d+)/(tcp|udp)\s+(open|closed|filtered)\s+(\S+)\s*(.*)',
                line
            )
            if port_match and current_host:
                port = ParsedPort(
                    port=int(port_match.group(1)),
                    protocol=port_match.group(2),
                    state=port_match.group(3),
                    service=port_match.group(4),
                    version=port_match.group(5).strip()
                )
                current_host.ports.append(port)
                continue

            # OS detection
            os_match = re.match(r'OS details:\s+(.*)', line)
            if os_match and current_host:
                current_host.os_guess = os_match.group(1)
                continue

            # MAC
            mac_match = re.match(r'MAC Address:\s+(\S+)', line)
            if mac_match and current_host:
                current_host.mac = mac_match.group(1)
                continue

        if current_host:
            result["hosts"].append(current_host)

        # Summary line
        summary_match = re.search(r'Nmap done:.*', output)
        if summary_match:
            result["summary"] = summary_match.group(0)

        return result

    @staticmethod
    def parse_xml(xml_content: str) -> Dict[str, Any]:
        """Parse nmap XML output."""
        result = {"hosts": [], "summary": ""}
        try:
            root = ET.fromstring(xml_content)
            for host_elem in root.findall('host'):
                addr_elem = host_elem.find('address')
                ip = addr_elem.get('addr', '') if addr_elem is not None else ''
                
                hostname = ""
                hostnames = host_elem.find('hostnames')
                if hostnames is not None:
                    hn = hostnames.find('hostname')
                    if hn is not None:
                        hostname = hn.get('name', '')

                host = ParsedHost(ip=ip, hostname=hostname)
                
                ports_elem = host_elem.find('ports')
                if ports_elem is not None:
                    for port_elem in ports_elem.findall('port'):
                        state_elem = port_elem.find('state')
                        service_elem = port_elem.find('service')
                        
                        port = ParsedPort(
                            port=int(port_elem.get('portid', 0)),
                            protocol=port_elem.get('protocol', ''),
                            state=state_elem.get('state', '') if state_elem is not None else '',
                            service=service_elem.get('name', '') if service_elem is not None else '',
                            version=service_elem.get('version', '') if service_elem is not None else ''
                        )
                        host.ports.append(port)
                
                result["hosts"].append(host)
        except ET.ParseError:
            pass
        return result


class HydraParser:
    """Parse Hydra output."""

    @staticmethod
    def parse(output: str) -> Dict[str, Any]:
        result = {"credentials": [], "attempts": 0, "service": ""}

        for line in output.split('\n'):
            cred_match = re.search(
                r'\[(\d+)\]\[(\S+)\]\s+host:\s+(\S+)\s+login:\s+(\S+)\s+password:\s+(\S+)',
                line
            )
            if cred_match:
                result["credentials"].append({
                    "port": int(cred_match.group(1)),
                    "service": cred_match.group(2),
                    "host": cred_match.group(3),
                    "username": cred_match.group(4),
                    "password": cred_match.group(5)
                })
            
            attempts_match = re.search(r'(\d+)\s+valid password', line)
            if attempts_match:
                result["attempts"] = int(attempts_match.group(1))

        return result


class GobusterParser:
    """Parse Gobuster output."""

    @staticmethod
    def parse(output: str) -> Dict[str, Any]:
        result = {"directories": [], "files": [], "total": 0}

        for line in output.split('\n'):
            dir_match = re.match(r'/(\S+)\s+\(Status:\s+(\d+)\)', line)
            if dir_match:
                entry = {
                    "path": "/" + dir_match.group(1),
                    "status": int(dir_match.group(2))
                }
                if entry["status"] in [200, 301, 302, 403]:
                    result["directories"].append(entry)
                    result["total"] += 1

        return result


class SQLMapParser:
    """Parse SQLMap output."""

    @staticmethod
    def parse(output: str) -> Dict[str, Any]:
        result = {
            "vulnerable": False,
            "injection_points": [],
            "databases": [],
            "tables": [],
            "dbms": ""
        }

        if "is vulnerable" in output.lower() or "injectable" in output.lower():
            result["vulnerable"] = True

        # Extract DBMS
        dbms_match = re.search(r'back-end DBMS:\s+(\S+)', output)
        if dbms_match:
            result["dbms"] = dbms_match.group(1)

        # Extract databases
        db_matches = re.findall(r'\[\*\]\s+(\S+)', output)
        result["databases"] = db_matches

        # Injection type
        inj_matches = re.findall(r'Type:\s+(.*)', output)
        result["injection_points"] = inj_matches

        return result


class JohnParser:
    """Parse John the Ripper output."""

    @staticmethod
    def parse(output: str) -> Dict[str, Any]:
        result = {"cracked": [], "total": 0}

        for line in output.split('\n'):
            # John shows cracked passwords as: password (username)
            crack_match = re.match(r'(\S+)\s+\((\S+)\)', line)
            if crack_match:
                result["cracked"].append({
                    "password": crack_match.group(1),
                    "username": crack_match.group(2)
                })
                result["total"] += 1

        return result


class OutputParserFactory:
    """Factory for selecting the right parser based on tool name."""

    PARSERS = {
        "nmap": NmapParser,
        "hydra": HydraParser,
        "gobuster": GobusterParser,
        "sqlmap": SQLMapParser,
        "john": JohnParser,
    }

    @classmethod
    def get_parser(cls, tool_name: str):
        """Get the appropriate parser for a tool."""
        # Normalize tool name
        name = tool_name.lower().replace("-", "").replace("_", "")
        for key, parser in cls.PARSERS.items():
            if key in name:
                return parser
        return None

    @classmethod
    def parse_output(cls, tool_name: str, output: str) -> Optional[Dict[str, Any]]:
        """Parse output using the appropriate parser."""
        parser = cls.get_parser(tool_name)
        if parser:
            return parser.parse(output) if hasattr(parser, 'parse') else parser.parse_text(output)
        return None

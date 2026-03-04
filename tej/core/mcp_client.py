"""
TejStrike AI - MCP (Model Context Protocol) Client
Allows users to connect TejStrike AI to MCP servers for extended tool access.
Supports stdio and SSE transports.
"""

import os
import json
import subprocess
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class MCPTransport(Enum):
    """MCP server transport types."""
    STDIO = "stdio"
    SSE = "sse"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection."""
    name: str
    transport: MCPTransport = MCPTransport.STDIO
    command: str = ""           # For stdio: command to start server
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    url: str = ""               # For SSE: server URL
    enabled: bool = True
    description: str = ""


@dataclass
class MCPTool:
    """A tool exposed by an MCP server."""
    name: str
    description: str
    server_name: str
    input_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPToolResult:
    """Result from calling an MCP tool."""
    content: str
    is_error: bool = False
    raw: Any = None


class MCPStdioConnection:
    """
    MCP connection over stdio transport.
    Communicates with MCP server via stdin/stdout JSON-RPC.
    """

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._lock = threading.Lock()
        self._response_handlers: Dict[int, Any] = {}
        self._reader_thread: Optional[threading.Thread] = None
        self._connected = False

    def connect(self) -> bool:
        """Start the MCP server process and initialize."""
        try:
            env = os.environ.copy()
            env.update(self.config.env)

            cmd = [self.config.command] + self.config.args

            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                bufsize=1,
            )

            # Start reader thread
            self._reader_thread = threading.Thread(
                target=self._read_responses, daemon=True
            )
            self._reader_thread.start()

            # Send initialize request
            result = self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "tejstrike-ai",
                    "version": "2.0.0",
                },
            })

            if result:
                # Send initialized notification
                self._send_notification("notifications/initialized", {})
                self._connected = True
                return True

        except FileNotFoundError:
            pass
        except Exception:
            pass

        return False

    def disconnect(self):
        """Disconnect from the MCP server."""
        self._connected = False
        if self.process:
            try:
                self.process.stdin.close()
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

    def list_tools(self) -> List[MCPTool]:
        """List available tools from the MCP server."""
        result = self._send_request("tools/list", {})
        tools = []
        if result and "tools" in result:
            for tool_data in result["tools"]:
                tools.append(MCPTool(
                    name=tool_data.get("name", ""),
                    description=tool_data.get("description", ""),
                    server_name=self.config.name,
                    input_schema=tool_data.get("inputSchema", {}),
                ))
        return tools

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Call a tool on the MCP server."""
        result = self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })

        if result:
            content_parts = result.get("content", [])
            text_parts = []
            for part in content_parts:
                if part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
                elif part.get("type") == "image":
                    text_parts.append("[image data]")
                else:
                    text_parts.append(str(part))

            return MCPToolResult(
                content="\n".join(text_parts),
                is_error=result.get("isError", False),
                raw=result,
            )

        return MCPToolResult(content="No response from MCP server", is_error=True)

    def _send_request(self, method: str, params: Dict) -> Optional[Dict]:
        """Send a JSON-RPC request and wait for response."""
        with self._lock:
            self._request_id += 1
            req_id = self._request_id

        message = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }

        event = threading.Event()
        response_holder = {"result": None}

        self._response_handlers[req_id] = (event, response_holder)

        try:
            line = json.dumps(message) + "\n"
            self.process.stdin.write(line)
            self.process.stdin.flush()

            # Wait for response with timeout
            if event.wait(timeout=30):
                return response_holder["result"]
        except Exception:
            pass
        finally:
            self._response_handlers.pop(req_id, None)

        return None

    def _send_notification(self, method: str, params: Dict):
        """Send a JSON-RPC notification (no response expected)."""
        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        try:
            line = json.dumps(message) + "\n"
            self.process.stdin.write(line)
            self.process.stdin.flush()
        except Exception:
            pass

    def _read_responses(self):
        """Background thread to read responses from MCP server."""
        try:
            for line in iter(self.process.stdout.readline, ""):
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    req_id = data.get("id")
                    if req_id and req_id in self._response_handlers:
                        event, holder = self._response_handlers[req_id]
                        holder["result"] = data.get("result")
                        event.set()
                except json.JSONDecodeError:
                    pass
        except (ValueError, OSError):
            pass

    @property
    def is_connected(self) -> bool:
        return self._connected and self.process is not None and self.process.poll() is None


class MCPSSEConnection:
    """
    MCP connection over SSE (Server-Sent Events) transport.
    Connects to an MCP server via HTTP SSE.
    """

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self._connected = False
        self._session_url = ""
        self._tools_cache: List[MCPTool] = []

    def connect(self) -> bool:
        """Connect to the SSE MCP server."""
        import urllib.request
        import urllib.error

        try:
            # GET the SSE endpoint to establish connection
            req = urllib.request.Request(
                self.config.url,
                headers={"Accept": "text/event-stream"},
            )
            # For SSE we'd need async handling; simplified version:
            resp = urllib.request.urlopen(req, timeout=10)
            if resp.status == 200:
                self._connected = True
                # Read the endpoint URL from SSE
                for line_bytes in resp:
                    line = line_bytes.decode().strip()
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data.startswith("http"):
                            self._session_url = data
                            break
                return True
        except Exception:
            pass
        return False

    def disconnect(self):
        self._connected = False

    def list_tools(self) -> List[MCPTool]:
        """List tools from SSE MCP server."""
        if self._tools_cache:
            return self._tools_cache

        result = self._post_request("tools/list", {})
        tools = []
        if result and "tools" in result:
            for tool_data in result["tools"]:
                tools.append(MCPTool(
                    name=tool_data.get("name", ""),
                    description=tool_data.get("description", ""),
                    server_name=self.config.name,
                    input_schema=tool_data.get("inputSchema", {}),
                ))
        self._tools_cache = tools
        return tools

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Call a tool via SSE MCP server."""
        result = self._post_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })

        if result:
            content_parts = result.get("content", [])
            text_parts = [
                p.get("text", str(p))
                for p in content_parts
                if isinstance(p, dict)
            ]
            return MCPToolResult(
                content="\n".join(text_parts),
                is_error=result.get("isError", False),
                raw=result,
            )

        return MCPToolResult(content="No response from MCP server", is_error=True)

    def _post_request(self, method: str, params: Dict) -> Optional[Dict]:
        """Send a POST request to the MCP session endpoint."""
        import urllib.request
        import urllib.error

        if not self._session_url:
            return None

        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }).encode()

        try:
            req = urllib.request.Request(
                self._session_url,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                return data.get("result")
        except Exception:
            return None

    @property
    def is_connected(self) -> bool:
        return self._connected


class MCPManager:
    """
    Manages multiple MCP server connections.
    Aggregates tools from all connected servers.
    """

    def __init__(self):
        self.servers: Dict[str, MCPServerConfig] = {}
        self.connections: Dict[str, Any] = {}  # MCPStdioConnection | MCPSSEConnection
        self._all_tools: List[MCPTool] = []

    def add_server(self, config: MCPServerConfig):
        """Register an MCP server configuration."""
        self.servers[config.name] = config

    def remove_server(self, name: str):
        """Remove and disconnect an MCP server."""
        self.disconnect_server(name)
        self.servers.pop(name, None)

    def connect_server(self, name: str) -> bool:
        """Connect to a specific MCP server."""
        config = self.servers.get(name)
        if not config or not config.enabled:
            return False

        if config.transport == MCPTransport.STDIO:
            conn = MCPStdioConnection(config)
        elif config.transport == MCPTransport.SSE:
            conn = MCPSSEConnection(config)
        else:
            return False

        if conn.connect():
            self.connections[name] = conn
            self._refresh_tools()
            return True

        return False

    def disconnect_server(self, name: str):
        """Disconnect from a specific MCP server."""
        conn = self.connections.pop(name, None)
        if conn:
            conn.disconnect()
        self._refresh_tools()

    def connect_all(self) -> Dict[str, bool]:
        """Connect to all enabled MCP servers."""
        results = {}
        for name, config in self.servers.items():
            if config.enabled:
                results[name] = self.connect_server(name)
        return results

    def disconnect_all(self):
        """Disconnect from all MCP servers."""
        for name in list(self.connections.keys()):
            self.disconnect_server(name)

    def get_all_tools(self) -> List[MCPTool]:
        """Get all tools from all connected MCP servers."""
        return self._all_tools.copy()

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Call an MCP tool, routing to the correct server."""
        for tool in self._all_tools:
            if tool.name == tool_name:
                conn = self.connections.get(tool.server_name)
                if conn and conn.is_connected:
                    return conn.call_tool(tool_name, arguments)
                return MCPToolResult(
                    content=f"Server '{tool.server_name}' is not connected",
                    is_error=True,
                )

        return MCPToolResult(
            content=f"Tool '{tool_name}' not found on any MCP server",
            is_error=True,
        )

    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get connection status for all servers."""
        status = {}
        for name, config in self.servers.items():
            conn = self.connections.get(name)
            is_connected = conn.is_connected if conn else False
            tool_count = len([t for t in self._all_tools if t.server_name == name])
            status[name] = {
                "enabled": config.enabled,
                "connected": is_connected,
                "transport": config.transport.value,
                "tools": tool_count,
                "description": config.description,
            }
        return status

    def _refresh_tools(self):
        """Refresh tool list from all connected servers."""
        tools = []
        for name, conn in self.connections.items():
            if conn.is_connected:
                try:
                    server_tools = conn.list_tools()
                    tools.extend(server_tools)
                except Exception:
                    pass
        self._all_tools = tools

    def load_config(self, config_data: List[Dict[str, Any]]):
        """Load MCP server configurations from config data."""
        for entry in config_data:
            transport = MCPTransport.STDIO
            if entry.get("transport") == "sse":
                transport = MCPTransport.SSE

            config = MCPServerConfig(
                name=entry.get("name", ""),
                transport=transport,
                command=entry.get("command", ""),
                args=entry.get("args", []),
                env=entry.get("env", {}),
                url=entry.get("url", ""),
                enabled=entry.get("enabled", True),
                description=entry.get("description", ""),
            )
            if config.name:
                self.add_server(config)

    def save_config(self) -> List[Dict[str, Any]]:
        """Export MCP server configurations for saving."""
        configs = []
        for name, config in self.servers.items():
            configs.append({
                "name": config.name,
                "transport": config.transport.value,
                "command": config.command,
                "args": config.args,
                "env": config.env,
                "url": config.url,
                "enabled": config.enabled,
                "description": config.description,
            })
        return configs

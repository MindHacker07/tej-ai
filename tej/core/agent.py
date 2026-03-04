"""
TejStrike AI - Interactive AI Agent
Orchestrates LLM-powered security analysis with tool execution.
Interprets natural language via Claude/GPT, builds commands,
executes tools, analyzes results, and suggests next steps.
"""

import re
import json
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

from tej.core.engine import TejBrain, TaskIntent, ToolResult
from tej.core.llm_provider import (
    LLMConfig, LLMProvider, BaseLLMClient, LLMResponse,
    create_llm_client, TEJSTRIKE_SYSTEM_PROMPT,
)
from tej.core.mcp_client import MCPManager, MCPTool


@dataclass
class AgentAction:
    """An action the agent wants to take."""
    action_type: str  # "execute", "suggest", "analyze", "explain", "mcp_call"
    tool: str = ""
    command: str = ""
    description: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class AgentResponse:
    """Complete response from the AI agent."""
    text: str                                   # Full text response
    actions: List[AgentAction] = field(default_factory=list)  # Extracted actions
    commands: List[Dict[str, str]] = field(default_factory=list)  # Extracted commands
    analysis: str = ""                          # Analysis summary
    next_steps: List[str] = field(default_factory=list)
    llm_used: bool = False
    model: str = ""
    tokens_used: int = 0
    duration: float = 0.0


class TejStrikeAgent:
    """
    Interactive AI agent that combines:
    1. LLM intelligence (Claude, GPT, etc.) for natural language understanding
    2. Built-in TejBrain for tool selection and command building
    3. MCP server tools for extended capabilities
    4. Tool execution and output analysis
    """

    def __init__(
        self,
        brain: TejBrain,
        llm_config: Optional[LLMConfig] = None,
        mcp_manager: Optional[MCPManager] = None,
    ):
        self.brain = brain
        self.llm_config = llm_config
        self.llm_client: Optional[BaseLLMClient] = None
        self.mcp_manager = mcp_manager or MCPManager()

        # Initialize LLM client if configured
        if llm_config and llm_config.is_configured():
            self.llm_client = create_llm_client(llm_config)

        # Conversation state
        self.target: Optional[str] = None
        self.session_context: List[str] = []

    def configure_llm(self, config: LLMConfig):
        """Configure or reconfigure the LLM client."""
        self.llm_config = config
        if config.is_configured():
            self.llm_client = create_llm_client(config)
        else:
            self.llm_client = None

    def test_llm_connection(self) -> bool:
        """Test if the LLM connection is working."""
        if self.llm_client:
            return self.llm_client.test_connection()
        return False

    @property
    def has_llm(self) -> bool:
        """Check if LLM is available."""
        return self.llm_client is not None

    @property
    def has_mcp(self) -> bool:
        """Check if any MCP servers are connected."""
        return bool(self.mcp_manager.get_all_tools())

    def process(self, user_input: str, tool_output: str = "") -> AgentResponse:
        """
        Process user input and return an intelligent response.
        Uses LLM if available, falls back to built-in engine.
        """
        start_time = time.time()

        if self.llm_client:
            response = self._process_with_llm(user_input, tool_output)
        else:
            response = self._process_with_brain(user_input, tool_output)

        response.duration = time.time() - start_time
        return response

    def stream_process(self, user_input: str, callback: Callable[[str], None],
                       tool_output: str = "") -> AgentResponse:
        """
        Process user input with streaming response via callback.
        Each token is passed to the callback as it arrives.
        """
        start_time = time.time()

        if self.llm_client:
            response = self._stream_with_llm(user_input, callback, tool_output)
        else:
            # Built-in engine doesn't stream - send all at once
            response = self._process_with_brain(user_input, tool_output)
            callback(response.text)

        response.duration = time.time() - start_time
        return response

    def analyze_output(self, tool_name: str, output: str) -> AgentResponse:
        """Analyze tool output using LLM for intelligent insights."""
        if self.llm_client:
            prompt = (
                f"Analyze this {tool_name} output and provide:\n"
                f"1. Key findings (vulnerabilities, open ports, credentials, etc.)\n"
                f"2. Risk assessment\n"
                f"3. Recommended next steps\n\n"
                f"Tool output:\n```\n{output[:6000]}\n```"
            )
            try:
                llm_response = self.llm_client.chat(prompt)
                return AgentResponse(
                    text=llm_response.content,
                    llm_used=True,
                    model=llm_response.model,
                    tokens_used=llm_response.tokens_used,
                )
            except Exception as e:
                # Fall back to built-in analysis
                pass

        # Built-in analysis
        mock_result = ToolResult(
            tool_name=tool_name,
            command="",
            exit_code=0,
            stdout=output,
            stderr="",
        )
        analysis = self.brain.analyze_output(mock_result)
        text = self._format_brain_analysis(analysis)
        return AgentResponse(text=text, llm_used=False)

    # ─── LLM Processing ─────────────────────────────────────────────

    def _process_with_llm(self, user_input: str, tool_output: str = "") -> AgentResponse:
        """Process input using the LLM."""
        # Build context for the LLM
        context = self._build_context(user_input, tool_output)

        # Add MCP tools context if available
        mcp_context = self._build_mcp_context()
        if mcp_context:
            context += f"\n\n{mcp_context}"

        try:
            llm_response = self.llm_client.chat(user_input, context=context)

            # Extract commands from LLM response
            commands = self._extract_commands(llm_response.content)
            next_steps = self._extract_next_steps(llm_response.content)

            return AgentResponse(
                text=llm_response.content,
                commands=commands,
                next_steps=next_steps,
                llm_used=True,
                model=llm_response.model,
                tokens_used=llm_response.tokens_used,
            )
        except ImportError as e:
            return AgentResponse(
                text=f"LLM package not installed: {str(e)}\n\n"
                     f"Install with:\n"
                     f"  pip install anthropic  (for Claude)\n"
                     f"  pip install openai     (for GPT)\n\n"
                     f"Falling back to built-in engine...",
                llm_used=False,
            )
        except Exception as e:
            # Fall back to built-in engine
            fallback = self._process_with_brain(user_input, tool_output)
            fallback.text = (
                f"LLM error: {str(e)}\n"
                f"Falling back to built-in analysis:\n\n"
                + fallback.text
            )
            return fallback

    def _stream_with_llm(self, user_input: str, callback: Callable[[str], None],
                         tool_output: str = "") -> AgentResponse:
        """Stream LLM response token by token."""
        context = self._build_context(user_input, tool_output)

        mcp_context = self._build_mcp_context()
        if mcp_context:
            context += f"\n\n{mcp_context}"

        full_text = ""
        try:
            for token in self.llm_client.stream_chat(user_input, context=context):
                full_text += token
                callback(token)

            commands = self._extract_commands(full_text)
            next_steps = self._extract_next_steps(full_text)

            return AgentResponse(
                text=full_text,
                commands=commands,
                next_steps=next_steps,
                llm_used=True,
                model=self.llm_config.model if self.llm_config else "",
            )
        except Exception as e:
            fallback = self._process_with_brain(user_input, tool_output)
            callback(f"\n\n[LLM Error: {e}]\nFalling back to built-in engine:\n\n")
            callback(fallback.text)
            return fallback

    # ─── Built-in Brain Processing ───────────────────────────────────

    def _process_with_brain(self, user_input: str, tool_output: str = "") -> AgentResponse:
        """Process input using the built-in TejBrain engine."""
        intent = self.brain.parse_intent(user_input)

        # Apply default target
        if not intent.target and self.target:
            intent.target = self.target

        # Build commands
        commands_raw = self.brain.build_command(intent)

        # Format response
        text_parts = []
        cat_name = intent.category.value.replace("_", " ").title()
        conf_pct = int(intent.confidence * 100)

        text_parts.append(f"Category: {cat_name} (confidence: {conf_pct}%)")
        text_parts.append(f"Action: {intent.action}")

        if intent.target:
            text_parts.append(f"Target: {intent.target}")

        text_parts.append(f"Suggested tools: {', '.join(intent.tools_suggested[:5])}")

        if commands_raw:
            text_parts.append("\nRecommended Commands:")
            for i, cmd in enumerate(commands_raw, 1):
                text_parts.append(f"  [{i}] {cmd['description']}")
                text_parts.append(f"      $ {cmd['command']}")

        # Analyze tool output if provided
        if tool_output:
            mock_result = ToolResult(
                tool_name=intent.tools_suggested[0] if intent.tools_suggested else "unknown",
                command="",
                exit_code=0,
                stdout=tool_output,
                stderr="",
            )
            analysis = self.brain.analyze_output(mock_result)
            suggestions = self.brain.suggest_next_steps(intent, [mock_result])

            if analysis["findings"]:
                text_parts.append(f"\nFindings: {len(analysis['findings'])} items")
            if suggestions:
                text_parts.append("\nSuggested Next Steps:")
                for s in suggestions[:5]:
                    text_parts.append(f"  -> {s}")

        commands = [
            {"tool": c.get("tool", ""), "command": c["command"],
             "description": c.get("description", "")}
            for c in commands_raw
        ]

        return AgentResponse(
            text="\n".join(text_parts),
            commands=commands,
            llm_used=False,
        )

    # ─── Context Building ────────────────────────────────────────────

    def _build_context(self, user_input: str, tool_output: str = "") -> str:
        """Build context for the LLM from current state."""
        parts = []

        # Target info
        if self.target:
            parts.append(f"Current target: {self.target}")

        # Intent from built-in engine (helps ground the LLM)
        intent = self.brain.parse_intent(user_input)
        if intent.confidence > 0.2:
            parts.append(
                f"Built-in engine analysis: category={intent.category.value}, "
                f"action={intent.action}, "
                f"suggested_tools={','.join(intent.tools_suggested[:5])}"
            )

        # Previous tool output
        if tool_output:
            # Truncate very long outputs
            truncated = tool_output[:4000]
            if len(tool_output) > 4000:
                truncated += f"\n\n[... truncated, full output is {len(tool_output)} chars]"
            parts.append(f"Previous tool output:\n{truncated}")

        # Session context
        if self.session_context:
            parts.append("Session history:")
            for ctx in self.session_context[-5:]:
                parts.append(f"  - {ctx}")

        return "\n\n".join(parts) if parts else ""

    def _build_mcp_context(self) -> str:
        """Build MCP tools context for the LLM."""
        mcp_tools = self.mcp_manager.get_all_tools()
        if not mcp_tools:
            return ""

        lines = ["Available MCP tools (call via MCP server):"]
        for tool in mcp_tools[:20]:
            lines.append(f"  - {tool.name}: {tool.description} [server: {tool.server_name}]")

        return "\n".join(lines)

    # ─── Response Parsing ────────────────────────────────────────────

    def _extract_commands(self, text: str) -> List[Dict[str, str]]:
        """Extract executable commands from LLM response text."""
        commands = []

        # Match code blocks with commands
        code_blocks = re.findall(r'```(?:bash|sh|shell|command)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        for block in code_blocks:
            for line in block.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('//'):
                    # Remove $ prefix if present
                    if line.startswith('$ '):
                        line = line[2:]
                    tool = line.split()[0] if line.split() else "unknown"
                    commands.append({
                        "tool": tool,
                        "command": line,
                        "description": f"Run {tool}",
                    })

        # Also match inline $ commands
        inline_cmds = re.findall(r'^\s*\$\s+(.+)$', text, re.MULTILINE)
        for cmd in inline_cmds:
            cmd = cmd.strip()
            if cmd and not any(c["command"] == cmd for c in commands):
                tool = cmd.split()[0] if cmd.split() else "unknown"
                commands.append({
                    "tool": tool,
                    "command": cmd,
                    "description": f"Run {tool}",
                })

        return commands

    def _extract_next_steps(self, text: str) -> List[str]:
        """Extract suggested next steps from LLM response."""
        steps = []

        # Look for numbered lists after "next steps" heading
        next_steps_match = re.search(
            r'(?:next\s+steps?|recommendations?|suggested\s+actions?)[:\s]*\n((?:\s*[-*\d.]+\s+.+\n?)+)',
            text, re.IGNORECASE
        )
        if next_steps_match:
            for line in next_steps_match.group(1).strip().split('\n'):
                line = re.sub(r'^\s*[-*\d.]+\s*', '', line).strip()
                if line:
                    steps.append(line)

        return steps

    def _format_brain_analysis(self, analysis: Dict[str, Any]) -> str:
        """Format built-in brain analysis as readable text."""
        parts = []

        if analysis.get("findings"):
            parts.append(f"Findings ({len(analysis['findings'])} items):")
            for f in analysis["findings"][:10]:
                if f.get("type") == "port":
                    parts.append(f"  Port {f['port']}/{f['state']}: {f.get('service', 'unknown')}")
                elif f.get("type") == "hosts_discovered":
                    parts.append(f"  Hosts: {', '.join(f['hosts'][:5])}")
                else:
                    parts.append(f"  {f}")

        if analysis.get("recommendations"):
            parts.append("\nRecommendations:")
            for r in analysis["recommendations"]:
                parts.append(f"  -> {r}")

        if analysis.get("severity", "info") != "info":
            parts.append(f"\nSeverity: {analysis['severity'].upper()}")

        return "\n".join(parts) if parts else "No significant findings detected."

    # ─── State Management ────────────────────────────────────────────

    def set_target(self, target: str):
        """Set the current target."""
        self.target = target
        self.session_context.append(f"Target set: {target}")

    def add_session_context(self, context: str):
        """Add context to the session."""
        self.session_context.append(context)
        # Keep only last 20 entries
        if len(self.session_context) > 20:
            self.session_context = self.session_context[-20:]

    def clear_context(self):
        """Clear all context and conversation history."""
        self.session_context.clear()
        if self.llm_client:
            self.llm_client.clear_history()

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "llm_configured": self.has_llm,
            "llm_provider": self.llm_config.provider.value if self.llm_config else "none",
            "llm_model": self.llm_config.model if self.llm_config else "",
            "mcp_tools": len(self.mcp_manager.get_all_tools()),
            "mcp_servers": len(self.mcp_manager.connections),
            "target": self.target or "not set",
            "context_entries": len(self.session_context),
        }

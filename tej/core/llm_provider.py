"""
TejStrike AI - LLM Provider Module
Multi-model support for Claude (Opus, Sonnet), GPT-4, GPT-3.5, and local models.
Interprets natural language queries, provides intelligent security analysis,
and powers the interactive AI agent.
"""

import os
import json
import time
import re
from typing import Dict, List, Optional, Any, Generator
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


class LLMProvider(Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"
    GROQ = "groq"
    LOCAL = "local"
    NONE = "none"  # Fallback to built-in engine


class LLMModel(Enum):
    """Known model identifiers."""
    # Anthropic
    CLAUDE_OPUS = "claude-opus-4-20250514"
    CLAUDE_SONNET = "claude-sonnet-4-20250514"
    CLAUDE_HAIKU = "claude-haiku-4-20250514"
    # OpenAI
    GPT_4O = "gpt-4o"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-3.5-turbo"
    O1 = "o1"
    O1_MINI = "o1-mini"
    # Groq
    LLAMA3_70B = "llama3-70b-8192"
    MIXTRAL = "mixtral-8x7b-32768"
    # Ollama / Local
    LOCAL_CUSTOM = "local-custom"


@dataclass
class LLMConfig:
    """Configuration for an LLM connection."""
    provider: LLMProvider = LLMProvider.NONE
    model: str = ""
    api_key: str = ""
    api_base_url: str = ""
    max_tokens: int = 4096
    temperature: float = 0.3
    system_prompt: str = ""
    timeout: int = 60
    stream: bool = True

    def is_configured(self) -> bool:
        """Check if LLM is properly configured."""
        if self.provider == LLMProvider.NONE:
            return False
        if self.provider in (LLMProvider.ANTHROPIC, LLMProvider.OPENAI, LLMProvider.GROQ):
            return bool(self.api_key and self.model)
        if self.provider in (LLMProvider.OLLAMA, LLMProvider.LOCAL):
            return bool(self.api_base_url and self.model)
        return False


@dataclass
class LLMMessage:
    """A single message in a conversation."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM."""
    content: str
    model: str = ""
    provider: str = ""
    tokens_used: int = 0
    finish_reason: str = ""
    duration: float = 0.0
    raw: Any = None


# ─── System Prompt for TejStrike AI Agent ────────────────────────────────

TEJSTRIKE_SYSTEM_PROMPT = """You are TejStrike AI — an expert AI-powered security tool orchestrator for Kali Linux.

Your capabilities:
1. **Interpret natural language security queries** and translate them into precise Kali Linux tool commands.
2. **Select the best tools** for any given security task (scanning, exploitation, enumeration, etc.).
3. **Build commands** with correct flags, targets, and parameters.
4. **Analyze tool output** and provide actionable intelligence.
5. **Suggest next steps** in a penetration testing workflow.

Context: You have access to 90+ Kali Linux security tools organized by category:
- Reconnaissance: nmap, theHarvester, amass, recon-ng, whois, dig, shodan
- Scanning: nmap, masscan, rustscan
- Web Application: sqlmap, gobuster, ffuf, nikto, burpsuite, nuclei, wfuzz
- Vulnerability Analysis: nikto, wpscan, nuclei, searchsploit, openvas
- Exploitation: metasploit, msfvenom, searchsploit, beef-xss
- Password Attacks: john, hashcat, hydra, medusa, cewl, crunch
- Wireless: aircrack-ng, wifite, bettercap, reaver, kismet
- Sniffing/Spoofing: wireshark, tcpdump, ettercap, responder, mitmproxy
- Post-Exploitation: mimikatz, bloodhound, empire, chisel, proxychains
- Forensics: autopsy, volatility, binwalk, steghide, exiftool
- Reverse Engineering: ghidra, radare2, gdb, apktool

Rules:
- ALWAYS format tool commands as executable shell commands
- Wrap each command in a code block: ```command```
- Explain WHY you chose specific tools and flags
- Warn about commands that need root/sudo
- Include target placeholders like <TARGET> when not specified
- Suggest multiple approaches when applicable (quick vs thorough)
- After analysis, always suggest logical next steps
- Be concise but thorough — focus on actionable output
- For ethical/legal compliance: remind users to only test authorized targets

Response format for tool suggestions:
1. Brief analysis of the request
2. Recommended command(s) with explanations
3. Expected output / what to look for
4. Suggested next steps
"""


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.conversation: List[LLMMessage] = []
        if config.system_prompt:
            self.conversation.append(LLMMessage(role="system", content=config.system_prompt))
        elif TEJSTRIKE_SYSTEM_PROMPT:
            self.conversation.append(LLMMessage(role="system", content=TEJSTRIKE_SYSTEM_PROMPT))

    @abstractmethod
    def chat(self, message: str, context: str = "") -> LLMResponse:
        """Send a message and get a response."""
        pass

    @abstractmethod
    def stream_chat(self, message: str, context: str = "") -> Generator[str, None, None]:
        """Stream a response token by token."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the LLM connection works."""
        pass

    def add_context(self, context: str):
        """Add context to the conversation."""
        self.conversation.append(LLMMessage(role="user", content=f"[Context]: {context}"))

    def clear_history(self):
        """Clear conversation history, keeping system prompt."""
        system_msgs = [m for m in self.conversation if m.role == "system"]
        self.conversation = system_msgs

    def _build_messages(self, message: str, context: str = "") -> List[Dict]:
        """Build message list for API call."""
        messages = []
        for msg in self.conversation:
            messages.append({"role": msg.role, "content": msg.content})

        if context:
            messages.append({"role": "user", "content": f"[Tool Output Context]:\n{context}"})
        messages.append({"role": "user", "content": message})
        return messages


class AnthropicClient(BaseLLMClient):
    """Client for Anthropic Claude models (Opus, Sonnet, Haiku)."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.config.api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. Run: pip install anthropic"
                )
        return self._client

    def chat(self, message: str, context: str = "") -> LLMResponse:
        client = self._get_client()
        messages = self._build_messages(message, context)

        # Separate system from messages for Anthropic API
        system_content = ""
        api_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_content += msg["content"] + "\n"
            else:
                api_messages.append(msg)

        start = time.time()
        response = client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_content.strip(),
            messages=api_messages,
        )
        duration = time.time() - start

        content = response.content[0].text if response.content else ""

        # Track conversation
        self.conversation.append(LLMMessage(role="user", content=message))
        self.conversation.append(LLMMessage(role="assistant", content=content))

        return LLMResponse(
            content=content,
            model=self.config.model,
            provider="anthropic",
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason or "",
            duration=duration,
            raw=response,
        )

    def stream_chat(self, message: str, context: str = "") -> Generator[str, None, None]:
        client = self._get_client()
        messages = self._build_messages(message, context)

        system_content = ""
        api_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_content += msg["content"] + "\n"
            else:
                api_messages.append(msg)

        full_response = ""
        with client.messages.stream(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_content.strip(),
            messages=api_messages,
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                yield text

        self.conversation.append(LLMMessage(role="user", content=message))
        self.conversation.append(LLMMessage(role="assistant", content=full_response))

    def test_connection(self) -> bool:
        try:
            client = self._get_client()
            response = client.messages.create(
                model=self.config.model,
                max_tokens=50,
                messages=[{"role": "user", "content": "Say 'connected' in one word."}],
            )
            return bool(response.content)
        except Exception:
            return False


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI GPT models (GPT-4, GPT-3.5, o1)."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import openai
                kwargs = {"api_key": self.config.api_key}
                if self.config.api_base_url:
                    kwargs["base_url"] = self.config.api_base_url
                self._client = openai.OpenAI(**kwargs)
            except ImportError:
                raise ImportError(
                    "openai package not installed. Run: pip install openai"
                )
        return self._client

    def chat(self, message: str, context: str = "") -> LLMResponse:
        client = self._get_client()
        messages = self._build_messages(message, context)

        start = time.time()
        response = client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        duration = time.time() - start

        content = response.choices[0].message.content if response.choices else ""

        self.conversation.append(LLMMessage(role="user", content=message))
        self.conversation.append(LLMMessage(role="assistant", content=content))

        return LLMResponse(
            content=content,
            model=self.config.model,
            provider="openai",
            tokens_used=response.usage.total_tokens if response.usage else 0,
            finish_reason=response.choices[0].finish_reason if response.choices else "",
            duration=duration,
            raw=response,
        )

    def stream_chat(self, message: str, context: str = "") -> Generator[str, None, None]:
        client = self._get_client()
        messages = self._build_messages(message, context)

        full_response = ""
        stream = client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_response += text
                yield text

        self.conversation.append(LLMMessage(role="user", content=message))
        self.conversation.append(LLMMessage(role="assistant", content=full_response))

    def test_connection(self) -> bool:
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Say 'connected' in one word."}],
                max_tokens=20,
            )
            return bool(response.choices)
        except Exception:
            return False


class OllamaClient(BaseLLMClient):
    """Client for Ollama local models."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.api_base_url or "http://localhost:11434"

    def chat(self, message: str, context: str = "") -> LLMResponse:
        import urllib.request
        import urllib.error

        messages = self._build_messages(message, context)

        payload = json.dumps({
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }).encode()

        start = time.time()
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
            data = json.loads(resp.read().decode())

        duration = time.time() - start
        content = data.get("message", {}).get("content", "")

        self.conversation.append(LLMMessage(role="user", content=message))
        self.conversation.append(LLMMessage(role="assistant", content=content))

        return LLMResponse(
            content=content,
            model=self.config.model,
            provider="ollama",
            duration=duration,
            raw=data,
        )

    def stream_chat(self, message: str, context: str = "") -> Generator[str, None, None]:
        import urllib.request

        messages = self._build_messages(message, context)

        payload = json.dumps({
            "model": self.config.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }).encode()

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        full_response = ""
        with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
            for line in resp:
                if line:
                    data = json.loads(line.decode())
                    text = data.get("message", {}).get("content", "")
                    if text:
                        full_response += text
                        yield text

        self.conversation.append(LLMMessage(role="user", content=message))
        self.conversation.append(LLMMessage(role="assistant", content=full_response))

    def test_connection(self) -> bool:
        import urllib.request
        import urllib.error
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False


class GroqClient(BaseLLMClient):
    """Client for Groq fast inference API."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.config.api_key)
            except ImportError:
                # Fall back to OpenAI-compatible API
                try:
                    import openai
                    self._client = openai.OpenAI(
                        api_key=self.config.api_key,
                        base_url="https://api.groq.com/openai/v1",
                    )
                except ImportError:
                    raise ImportError(
                        "Install groq or openai package: pip install groq"
                    )
        return self._client

    def chat(self, message: str, context: str = "") -> LLMResponse:
        client = self._get_client()
        messages = self._build_messages(message, context)

        start = time.time()
        response = client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        duration = time.time() - start

        content = response.choices[0].message.content if response.choices else ""

        self.conversation.append(LLMMessage(role="user", content=message))
        self.conversation.append(LLMMessage(role="assistant", content=content))

        return LLMResponse(
            content=content,
            model=self.config.model,
            provider="groq",
            tokens_used=response.usage.total_tokens if response.usage else 0,
            duration=duration,
            raw=response,
        )

    def stream_chat(self, message: str, context: str = "") -> Generator[str, None, None]:
        client = self._get_client()
        messages = self._build_messages(message, context)

        full_response = ""
        stream = client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_response += text
                yield text

        self.conversation.append(LLMMessage(role="user", content=message))
        self.conversation.append(LLMMessage(role="assistant", content=full_response))

    def test_connection(self) -> bool:
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Say 'connected'."}],
                max_tokens=10,
            )
            return bool(response.choices)
        except Exception:
            return False


# ─── Factory ─────────────────────────────────────────────────────────────

def create_llm_client(config: LLMConfig) -> Optional[BaseLLMClient]:
    """Create an LLM client based on configuration."""
    if not config.is_configured():
        return None

    providers = {
        LLMProvider.ANTHROPIC: AnthropicClient,
        LLMProvider.OPENAI: OpenAIClient,
        LLMProvider.OLLAMA: OllamaClient,
        LLMProvider.GROQ: GroqClient,
        LLMProvider.LOCAL: OllamaClient,  # Local models use Ollama-compatible API
    }

    client_class = providers.get(config.provider)
    if client_class:
        return client_class(config)
    return None


# ─── Available Models ────────────────────────────────────────────────────

AVAILABLE_MODELS: Dict[str, List[Dict[str, str]]] = {
    "anthropic": [
        {"id": "claude-opus-4-20250514", "name": "Claude Opus 4", "description": "Most capable, best for complex security analysis"},
        {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "description": "Fast and intelligent, great balance"},
        {"id": "claude-haiku-4-20250514", "name": "Claude Haiku 4", "description": "Fastest, good for quick queries"},
    ],
    "openai": [
        {"id": "gpt-4o", "name": "GPT-4o", "description": "Latest multimodal model"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "Fast GPT-4 variant"},
        {"id": "gpt-4", "name": "GPT-4", "description": "Original GPT-4"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Fast and affordable"},
        {"id": "o1", "name": "o1", "description": "Advanced reasoning"},
        {"id": "o1-mini", "name": "o1 Mini", "description": "Efficient reasoning"},
    ],
    "groq": [
        {"id": "llama3-70b-8192", "name": "LLaMA 3 70B", "description": "Fast open-source model"},
        {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "description": "MoE architecture"},
    ],
    "ollama": [
        {"id": "llama3", "name": "LLaMA 3", "description": "Local LLaMA 3"},
        {"id": "mistral", "name": "Mistral", "description": "Local Mistral"},
        {"id": "codellama", "name": "Code LLaMA", "description": "Code-focused"},
        {"id": "deepseek-coder", "name": "DeepSeek Coder", "description": "Code generation"},
    ],
}


def get_available_providers() -> List[Dict[str, str]]:
    """Get list of available LLM providers."""
    return [
        {"id": "anthropic", "name": "Anthropic (Claude)", "description": "Claude Opus, Sonnet, Haiku"},
        {"id": "openai", "name": "OpenAI (GPT)", "description": "GPT-4o, GPT-4, GPT-3.5"},
        {"id": "groq", "name": "Groq", "description": "Ultra-fast inference (LLaMA, Mixtral)"},
        {"id": "ollama", "name": "Ollama (Local)", "description": "Run models locally"},
        {"id": "none", "name": "Built-in Engine", "description": "No LLM, use keyword matching"},
    ]


def get_models_for_provider(provider: str) -> List[Dict[str, str]]:
    """Get available models for a provider."""
    return AVAILABLE_MODELS.get(provider, [])


def detect_installed_providers() -> List[str]:
    """Detect which LLM provider packages are installed."""
    installed = []
    try:
        import anthropic
        installed.append("anthropic")
    except ImportError:
        pass
    try:
        import openai
        installed.append("openai")
    except ImportError:
        pass
    try:
        from groq import Groq
        installed.append("groq")
    except ImportError:
        pass
    # Ollama doesn't need a package - uses HTTP
    installed.append("ollama")
    return installed

"""
Runtime configuration helpers for the DeepSeek chatbot.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class MissingAPIKeyError(RuntimeError):
    """Raised when the DeepSeek API key is missing."""


@dataclass(frozen=True)
class DeepSeekSettings:
    """
    Holds configuration required to talk to the DeepSeek API.
    """

    api_key: str
    base_url: str = "https://api.deepseek.com"
    chat_path: str = "/chat/completions"

    @property
    def endpoint(self) -> str:
        return f"{self.base_url.rstrip('/')}{self.chat_path}"


@dataclass(frozen=True)
class MCPSettings:
    """
    Holds configuration for the Google Maps MCP server.
    """

    url: str = "http://localhost:3000"
    api_key: str | None = None

    @property
    def endpoint(self) -> str:
        return f"{self.url.rstrip('/')}/mcp"


def load_settings() -> DeepSeekSettings:
    """
    Load settings from the environment.
    """

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise MissingAPIKeyError(
            "Environment variable DEEPSEEK_API_KEY is required."
        )
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    chat_path = os.getenv("DEEPSEEK_CHAT_PATH", "/chat/completions")
    return DeepSeekSettings(api_key=api_key, base_url=base_url, chat_path=chat_path)


def load_mcp_settings() -> MCPSettings:
    """
    Load MCP settings from the environment.
    MCP server URL and Google Maps API key are optional.
    """
    url = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    return MCPSettings(url=url, api_key=api_key)



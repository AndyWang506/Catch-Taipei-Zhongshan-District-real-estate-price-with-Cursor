"""
Thin client around the DeepSeek REST API.
"""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Literal, Mapping, MutableMapping, Optional, Sequence, Union

import requests

from .config import DeepSeekSettings, load_settings

Role = Literal["system", "user", "assistant"]


@dataclass
class MessagePayload:
    role: Role
    content: Union[str, Sequence[Mapping[str, str]]]


class DeepSeekClient:
    """
    High-level helper for the DeepSeek chat completions API.
    """

    def __init__(
        self,
        settings: Optional[DeepSeekSettings] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self._settings = settings or load_settings()
        self._session = session or requests.Session()

    def _headers(self) -> MutableMapping[str, str]:
        return {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _image_to_part(image_path: Path) -> Mapping[str, str]:
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            raise ValueError(f"Could not infer MIME type for {image_path}")
        data = image_path.read_bytes()
        encoded = base64.b64encode(data).decode("utf-8")
        return {"type": "image_base64", "mime": mime_type, "data": encoded}

    def build_multimodal_message(
        self,
        text: str,
        image_paths: Optional[Iterable[Union[str, Path]]] = None,
    ) -> MessagePayload:
        """
        Build a user message with optional image attachments.
        """

        parts: List[Mapping[str, str]] = [{"type": "text", "text": text}]
        if image_paths:
            for raw_path in image_paths:
                path = Path(raw_path).expanduser().resolve()
                parts.append(self._image_to_part(path))
        return MessagePayload(role="user", content=parts)

    def chat(
        self,
        messages: Sequence[MessagePayload],
        *,
        model: str = "deepseek-chat",
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Mapping[str, object]:
        """
        Send a chat completion request, returning parsed JSON.
        """

        payload: MutableMapping[str, object] = {
            "model": model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in messages
            ],
            "stream": stream,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        response = self._session.post(
            self._settings.endpoint,
            headers=self._headers(),
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()



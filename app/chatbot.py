"""
High-level chatbot wrapper built on top of the DeepSeek client.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple, Union

from .deepseek_client import DeepSeekClient, MessagePayload


class DeepSeekChatbot:
    """
    Maintains conversation state with the DeepSeek API.
    """

    def __init__(
        self,
        *,
        system_prompt: str = "You are a helpful AI assistant.",
        client: Optional[DeepSeekClient] = None,
    ) -> None:
        self._client = client or DeepSeekClient()
        self._history: List[MessagePayload] = []
        if system_prompt:
            self._history.append(
                MessagePayload(role="system", content=system_prompt)
            )

    @property
    def history(self) -> Sequence[MessagePayload]:
        return tuple(self._history)

    def reset(self) -> None:
        """
        Reset the conversation history, preserving the system prompt.
        """

        system_messages = [
            message for message in self._history if message.role == "system"
        ]
        self._history = list(system_messages)

    def send_text(
        self,
        text: str,
        *,
        model: str = "deepseek-chat",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Tuple[str, dict]:
        """
        Send a plain text message.
        """

        user_message = MessagePayload(role="user", content=text)
        return self._send(user_message, model=model, temperature=temperature, max_tokens=max_tokens)

    def send_with_images(
        self,
        text: str,
        image_paths: Optional[Iterable[str]] = None,
        *,
        model: str = "deepseek-chat",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Tuple[str, dict]:
        """
        Send a message that contains text plus one or more images.
        """

        user_message = self._client.build_multimodal_message(
            text, image_paths=image_paths
        )
        return self._send(user_message, model=model, temperature=temperature, max_tokens=max_tokens)

    def _send(
        self,
        message: MessagePayload,
        *,
        model: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
    ) -> Tuple[str, dict]:
        self._history.append(message)
        response = self._client.chat(
            self._history,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response["choices"][0]
        assistant_content = choice["message"]["content"]
        self._history.append(
            MessagePayload(role="assistant", content=assistant_content)
        )
        usage = response.get("usage", {})
        return str(assistant_content), usage



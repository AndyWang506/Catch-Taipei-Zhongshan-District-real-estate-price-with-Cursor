"""
Example CLI for interacting with the DeepSeek chatbot.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional

from .chatbot import DeepSeekChatbot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chat with the DeepSeek multimodal model."
    )
    parser.add_argument(
        "prompt",
        help="User prompt to send to the model.",
    )
    parser.add_argument(
        "--image",
        dest="images",
        action="append",
        default=None,
        help="Optional image path(s) to include with the prompt. Can be repeated.",
    )
    parser.add_argument(
        "--model",
        default="deepseek-chat",
        help="DeepSeek model to use.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Sampling temperature for generation.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Maximum number of tokens in the response.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the raw API response metadata.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    chatbot = DeepSeekChatbot()
    if args.images:
        response, usage = chatbot.send_with_images(
            args.prompt,
            image_paths=[Path(img) for img in args.images],
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
    else:
        response, usage = chatbot.send_text(
            args.prompt,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )

    print(response)
    if args.pretty and usage:
        print("\n--- Usage ---")
        print(json.dumps(usage, indent=2))


if __name__ == "__main__":
    main()



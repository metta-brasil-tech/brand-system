"""Test doubles for anthropic.types.Message.

Lets unit tests mock client.messages.create and drive generator.py /
validator.py's response-parsing code (_text_of, _extract_json) without ever
calling the real Anthropic API -- zero cost, zero network, deterministic.
"""

from __future__ import annotations

import json


class FakeBlock:
    def __init__(self, text: str, type: str = "text") -> None:
        self.type = type
        self.text = text


class FakeMessage:
    def __init__(self, content: list[FakeBlock], stop_reason: str = "end_turn") -> None:
        self.content = content
        self.stop_reason = stop_reason


def json_message(data: dict) -> FakeMessage:
    """Fake Message whose text block is the JSON-encoded data -- what
    generator._extract_json / validator._extract_json expect to parse."""
    return FakeMessage(content=[FakeBlock(json.dumps(data, ensure_ascii=False))])


def text_message(text: str) -> FakeMessage:
    """Fake Message with a plain prose text block (e.g. the LinkedIn
    adaptation, which returns text, not JSON)."""
    return FakeMessage(content=[FakeBlock(text)])


def empty_message() -> FakeMessage:
    """Reproduces the thinking-only response bug noted throughout generator.py
    and validator.py: no text block, only a non-text block, stop_reason
    max_tokens -- _text_of must raise RuntimeError, not crash on next()."""
    return FakeMessage(
        content=[FakeBlock("...", type="thinking")], stop_reason="max_tokens"
    )

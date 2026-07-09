from __future__ import annotations

from typing import Any

from application.context_builder.interfaces import ContextLayer


class ConversationContextLayer(ContextLayer):
    def __init__(self, enabled: bool = True, max_messages: int = 50) -> None:
        self._enabled = enabled
        self._max_messages = max_messages

    @property
    def name(self) -> str:
        return "conversation"

    @property
    def priority(self) -> int:
        return 2

    async def build(self, **kwargs: Any) -> dict[str, Any]:
        conversation = kwargs.get("conversation")
        if conversation is None:
            return {
                "conversation_id": kwargs.get("conversation_id", ""),
                "state": kwargs.get("conversation_state", "unknown"),
                "summary": kwargs.get("conversation_summary", ""),
                "message_count": 0,
                "messages": [],
            }

        messages = getattr(conversation, "messages", [])
        max_msgs = kwargs.get("max_messages", self._max_messages)
        message_list = []
        for msg in messages[-max_msgs:]:
            msg_type = getattr(msg, "message_type", "user")
            if hasattr(msg_type, "value"):
                msg_type = msg_type.value
            message_list.append({
                "role": msg_type,
                "content": getattr(msg, "content", ""),
                "token_count": getattr(msg, "token_count", 0),
            })

        conv_state = getattr(conversation, "state", "unknown")
        if hasattr(conv_state, "value"):
            conv_state = conv_state.value

        return {
            "conversation_id": str(getattr(conversation, "conversation_id", "")),
            "state": conv_state,
            "summary": getattr(conversation, "summary", None) or "",
            "message_count": len(messages),
            "messages": message_list,
            "metadata": {
                "created_at": str(getattr(conversation, "created_at", "")),
                "updated_at": str(getattr(conversation, "updated_at", "")),
                "message_count": len(messages),
            },
        }

    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_max_messages(self, max_messages: int) -> None:
        self._max_messages = max_messages

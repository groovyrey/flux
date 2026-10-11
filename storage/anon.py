from __future__ import annotations

from dataclasses import dataclass
from itertools import count

MAX_CONVERSATIONS = 5000


@dataclass(frozen=True, slots=True)
class Conversation:
    id: int
    sender_id: int
    target_id: int

    def other(self, user_id: int) -> int | None:
        if user_id == self.sender_id:
            return self.target_id
        if user_id == self.target_id:
            return self.sender_id
        return None


_conversations: dict[int, Conversation] = {}
_ids = count(1)


def create_conversation(sender_id: int, target_id: int) -> Conversation:
    if len(_conversations) >= MAX_CONVERSATIONS:
        _conversations.pop(next(iter(_conversations)), None)
    conversation = Conversation(id=next(_ids), sender_id=sender_id, target_id=target_id)
    _conversations[conversation.id] = conversation
    return conversation


def get_conversation(conversation_id: int) -> Conversation | None:
    return _conversations.get(conversation_id)

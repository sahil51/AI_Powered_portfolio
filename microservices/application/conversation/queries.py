from dataclasses import dataclass


@dataclass
class GetConversationQuery:
    conversation_id: str


@dataclass
class GetActiveConversationsQuery:
    user_id: str
    limit: int = 10


@dataclass
class GetConversationHistoryQuery:
    user_id: str
    skip: int = 0
    limit: int = 20


@dataclass
class SearchConversationsQuery:
    user_id: str | None = None
    session_id: str | None = None
    state: str | None = None
    skip: int = 0
    limit: int = 20

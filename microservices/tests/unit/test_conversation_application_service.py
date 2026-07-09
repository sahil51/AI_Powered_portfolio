from unittest.mock import AsyncMock

import pytest

from application.conversation.commands import (
    CancelConversationCommand,
    CompleteConversationCommand,
    CreateConversationCommand,
    PauseConversationCommand,
    ResumeConversationCommand,
    StoreMessageCommand,
)
from application.conversation.queries import GetConversationQuery
from application.conversation.service import ConversationApplicationService
from domain.conversation.aggregate import Conversation
from domain.conversation.factory import ConversationFactory
from domain.conversation.state import ConversationState
from domain.conversation.value_objects import (
    ConversationId,
    ConversationMetadata,
    MessageType,
)


class TestConversationApplicationService:
    def setup_method(self) -> None:
        self.repository = AsyncMock()
        self.service = ConversationApplicationService(
            repository=self.repository,
            factory=ConversationFactory(),
        )

    async def test_create_conversation(self):
        self.repository.save = AsyncMock()
        command = CreateConversationCommand(
            user_id="user-1",
            session_id="session-1",
            identity_source="anonymous",
        )
        conversation = await self.service.create_conversation(command)
        assert conversation.user_id == "user-1"
        assert conversation.state == ConversationState.ACTIVE
        self.repository.save.assert_awaited_once()

    async def test_create_with_metadata(self):
        self.repository.save = AsyncMock()
        metadata = ConversationMetadata(title="Support Chat", tags=["support"])
        command = CreateConversationCommand(
            user_id="user-1",
            session_id="session-1",
            metadata=metadata,
        )
        conversation = await self.service.create_conversation(command)
        assert conversation.metadata.title == "Support Chat"

    async def test_store_message(self):
        self.repository.save = AsyncMock()
        conv = Conversation(conversation_id=ConversationId(), user_id="user-1")
        conv.activate()
        self.repository.get_by_id_str = AsyncMock(return_value=conv)

        command = StoreMessageCommand(
            conversation_id=str(conv.conversation_id),
            content="Hello world",
            message_type=MessageType.USER,
        )
        result = await self.service.store_message(command)
        assert result.message_count == 1
        assert result.messages[0].content == "Hello world"

    async def test_store_message_conversation_not_found(self):
        self.repository.get_by_id_str = AsyncMock(return_value=None)

        command = StoreMessageCommand(
            conversation_id="nonexistent",
            content="Hello",
            message_type=MessageType.USER,
        )
        from domain.conversation.validator import ConversationValidationError
        with pytest.raises(ConversationValidationError):
            await self.service.store_message(command)

    async def test_pause_conversation(self):
        conv = Conversation(conversation_id=ConversationId(), user_id="user-1")
        conv.activate()
        self.repository.get_by_id_str = AsyncMock(return_value=conv)
        self.repository.save = AsyncMock()

        command = PauseConversationCommand(
            conversation_id=str(conv.conversation_id),
            reason="Need information",
        )
        result = await self.service.pause_conversation(command)
        assert result.state == ConversationState.PAUSED

    async def test_resume_conversation(self):
        conv = Conversation(conversation_id=ConversationId(), user_id="user-1")
        conv.activate()
        conv.pause()
        self.repository.get_by_id_str = AsyncMock(return_value=conv)
        self.repository.save = AsyncMock()

        command = ResumeConversationCommand(
            conversation_id=str(conv.conversation_id),
        )
        result = await self.service.resume_conversation(command)
        assert result.state == ConversationState.ACTIVE

    async def test_complete_conversation(self):
        conv = Conversation(conversation_id=ConversationId(), user_id="user-1")
        conv.activate()
        self.repository.get_by_id_str = AsyncMock(return_value=conv)
        self.repository.save = AsyncMock()

        command = CompleteConversationCommand(
            conversation_id=str(conv.conversation_id),
            summary="Completed successfully",
        )
        result = await self.service.complete_conversation(command)
        assert result.state == ConversationState.COMPLETED
        assert result.summary == "Completed successfully"

    async def test_cancel_conversation(self):
        conv = Conversation(conversation_id=ConversationId(), user_id="user-1")
        conv.activate()
        self.repository.get_by_id_str = AsyncMock(return_value=conv)
        self.repository.save = AsyncMock()

        command = CancelConversationCommand(
            conversation_id=str(conv.conversation_id),
            reason="User cancelled",
        )
        result = await self.service.cancel_conversation(command)
        assert result.state == ConversationState.CANCELLED

    async def test_get_conversation(self):
        conv = Conversation(conversation_id=ConversationId(), user_id="user-1")
        self.repository.get_by_id_str = AsyncMock(return_value=conv)

        query = GetConversationQuery(conversation_id=str(conv.conversation_id))
        result = await self.service.get_conversation(query)
        assert result is not None
        assert result.user_id == "user-1"

    async def test_get_conversation_not_found(self):
        self.repository.get_by_id_str = AsyncMock(return_value=None)
        query = GetConversationQuery(conversation_id="nonexistent")
        result = await self.service.get_conversation(query)
        assert result is None

    async def test_get_active_count(self):
        self.repository.count_active_by_user = AsyncMock(return_value=3)
        count = await self.service.get_active_count("user-1")
        assert count == 3

    async def test_process_timeouts(self):
        conv = Conversation(conversation_id=ConversationId(), user_id="user-1")
        conv.activate()
        self.repository.expire_idle = AsyncMock(return_value=[conv])
        self.repository.save = AsyncMock()

        expired = await self.service.process_timeouts()
        assert len(expired) == 1
        assert expired[0].user_id == "user-1"

    async def test_process_archives(self):
        self.repository.archive_old = AsyncMock(return_value=5)
        count = await self.service.process_archives()
        assert count == 5

    async def test_get_conversation_summary(self):
        conv = Conversation(conversation_id=ConversationId(), user_id="user-1")
        conv.activate()
        conv.complete(summary="Great conversation")
        self.repository.get_by_id_str = AsyncMock(return_value=conv)

        summary = await self.service.get_conversation_summary(str(conv.conversation_id))
        assert summary is not None
        assert summary["summary"] == "Great conversation"

    async def test_get_conversation_summary_not_found(self):
        self.repository.get_by_id_str = AsyncMock(return_value=None)
        summary = await self.service.get_conversation_summary("nonexistent")
        assert summary is None

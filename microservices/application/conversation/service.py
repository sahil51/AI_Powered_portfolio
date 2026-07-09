from collections.abc import Sequence

from application.conversation.commands import (
    ArchiveConversationCommand,
    CancelConversationCommand,
    CompleteConversationCommand,
    CreateConversationCommand,
    PauseConversationCommand,
    ResumeConversationCommand,
    StoreMessageCommand,
)
from application.conversation.queries import (
    GetActiveConversationsQuery,
    GetConversationHistoryQuery,
    GetConversationQuery,
    SearchConversationsQuery,
)
from domain.conversation.aggregate import Conversation
from domain.conversation.domain_service import ConversationDomainService
from domain.conversation.factory import ConversationFactory
from domain.conversation.repository import ConversationRepository
from domain.conversation.validator import ConversationValidationError, ConversationValidator
from domain.conversation.value_objects import (
    Message,
    MessageId,
    ParticipantId,
)


class ConversationApplicationService:
    def __init__(
        self,
        repository: ConversationRepository,
        factory: ConversationFactory | None = None,
        domain_service: ConversationDomainService | None = None,
        validator: ConversationValidator | None = None,
    ) -> None:
        self._repository = repository
        self._factory = factory or ConversationFactory()
        self._domain_service = domain_service or ConversationDomainService()
        self._validator = validator or ConversationValidator()

    async def create_conversation(self, command: CreateConversationCommand) -> Conversation:
        conversation = self._factory.create(
            user_id=command.user_id,
            session_id=command.session_id,
            identity_source=command.identity_source,
            metadata=command.metadata,
            correlation_id=command.correlation_id,
        )
        await self._repository.save(conversation)
        return conversation

    async def store_message(self, command: StoreMessageCommand) -> Conversation:
        conversation = await self._repository.get_by_id_str(command.conversation_id)
        if conversation is None:
            raise ConversationValidationError(f"Conversation not found: {command.conversation_id}")

        message = Message(
            message_id=MessageId(),
            conversation_id=conversation.conversation_id,
            message_type=command.message_type,
            content=command.content,
            participant_id=ParticipantId(value=command.participant_id) if command.participant_id else None,
            correlation_id=command.correlation_id or conversation.correlation_id,
            token_count=command.token_count,
            metadata=command.metadata,
        )
        conversation.add_message(message)
        await self._repository.save(conversation)
        return conversation

    async def pause_conversation(self, command: PauseConversationCommand) -> Conversation:
        conversation = await self._get_conversation(command.conversation_id)
        conversation.pause(reason=command.reason)
        await self._repository.save(conversation)
        return conversation

    async def resume_conversation(self, command: ResumeConversationCommand) -> Conversation:
        conversation = await self._get_conversation(command.conversation_id)
        conversation.resume()
        await self._repository.save(conversation)
        return conversation

    async def complete_conversation(self, command: CompleteConversationCommand) -> Conversation:
        conversation = await self._get_conversation(command.conversation_id)
        conversation.complete(summary=command.summary)
        await self._repository.save(conversation)
        return conversation

    async def cancel_conversation(self, command: CancelConversationCommand) -> Conversation:
        conversation = await self._get_conversation(command.conversation_id)
        conversation.cancel(reason=command.reason)
        await self._repository.save(conversation)
        return conversation

    async def archive_conversation(self, command: ArchiveConversationCommand) -> Conversation:
        conversation = await self._get_conversation(command.conversation_id)
        conversation.archive(reason=command.reason)
        await self._repository.save(conversation)
        return conversation

    async def get_conversation(self, query: GetConversationQuery) -> Conversation | None:
        return await self._repository.get_by_id_str(query.conversation_id)

    async def get_active_conversations(self, query: GetActiveConversationsQuery) -> Sequence[Conversation]:
        return await self._repository.get_active_by_user(query.user_id, query.limit)

    async def get_conversation_history(self, query: GetConversationHistoryQuery) -> tuple[Sequence[Conversation], int]:
        return await self._repository.get_paginated(
            skip=query.skip,
            limit=query.limit,
            user_id=query.user_id,
        )

    async def search_conversations(self, query: SearchConversationsQuery) -> tuple[Sequence[Conversation], int]:
        return await self._repository.get_paginated(
            skip=query.skip,
            limit=query.limit,
            user_id=query.user_id,
            state=query.state,
            session_id=query.session_id,
        )

    async def get_conversation_summary(self, conversation_id: str) -> dict | None:
        conversation = await self._repository.get_by_id_str(conversation_id)
        if conversation is None:
            return None
        from application.conversation.serializer import ConversationSerializer
        return ConversationSerializer.summary_to_dict(conversation)

    async def process_timeouts(self) -> list[Conversation]:
        expired = await self._repository.expire_idle()
        for conversation in expired:
            conversation.expire()
            await self._repository.save(conversation)
        return expired

    async def process_archives(self) -> int:
        return await self._repository.archive_old()

    async def get_active_count(self, user_id: str) -> int:
        return await self._repository.count_active_by_user(user_id)

    async def _get_conversation(self, conversation_id: str) -> Conversation:
        conversation = await self._repository.get_by_id_str(conversation_id)
        if conversation is None:
            raise ConversationValidationError(f"Conversation not found: {conversation_id}")
        return conversation

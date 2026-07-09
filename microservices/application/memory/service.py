from collections.abc import Sequence

from application.memory.commands import (
    ArchiveMemoryCommand,
    ChangeConfidenceCommand,
    ChangeImportanceCommand,
    CreateMemoryCommand,
    DeleteMemoryCommand,
    MergeMemoryCommand,
    RestoreMemoryCommand,
    UpdateMemoryCommand,
)
from application.memory.queries import (
    GetMemoryQuery,
    GetUserMemoriesQuery,
    SearchMemoriesQuery,
)
from domain.memory.aggregate import Memory
from domain.memory.domain_service import MemoryDomainService
from domain.memory.factory import MemoryFactory
from domain.memory.repository import MemoryRepository
from domain.memory.validator import MemoryValidationError


class MemoryApplicationService:
    def __init__(
        self,
        repository: MemoryRepository,
        factory: MemoryFactory | None = None,
        domain_service: MemoryDomainService | None = None,
    ) -> None:
        self._repository = repository
        self._factory = factory or MemoryFactory()
        self._domain_service = domain_service or MemoryDomainService()

    async def create_memory(self, command: CreateMemoryCommand) -> Memory:
        memory = self._factory.create(
            user_id=command.user_id,
            value=command.value,
            category=command.category,
            scope=command.scope,
            key=command.key,
            conversation_id=command.conversation_id,
            session_id=command.session_id,
            memory_type=command.memory_type,
            priority=command.priority,
            confidence=command.confidence,
            importance=command.importance,
            source=command.source,
            correlation_id=command.correlation_id,
            tags=command.tags,
            metadata=command.metadata,
        )

        current_count = await self._repository.count_by_user(command.user_id, command.scope)
        if not self._domain_service.can_add_memory(memory, current_count):
            raise MemoryValidationError("Memory limit exceeded for this scope")

        await self._repository.save(memory)
        return memory

    async def update_memory(self, command: UpdateMemoryCommand) -> Memory:
        memory = await self._get_memory(command.memory_id)
        memory.update_value(command.value, command.confidence)
        await self._repository.save(memory)
        return memory

    async def merge_memories(self, command: MergeMemoryCommand) -> Memory:
        target = await self._get_memory(command.target_memory_id)
        source = await self._get_memory(command.source_memory_id)
        target.merge(source)
        await self._repository.save(target)
        if source.status.value != "deleted":
            source.delete(reason="merged_into_" + str(target.memory_id))
            await self._repository.save(source)
        return target

    async def archive_memory(self, command: ArchiveMemoryCommand) -> Memory:
        memory = await self._get_memory(command.memory_id)
        memory.archive(reason=command.reason)
        await self._repository.save(memory)
        return memory

    async def restore_memory(self, command: RestoreMemoryCommand) -> Memory:
        memory = await self._get_memory(command.memory_id)
        memory.restore()
        await self._repository.save(memory)
        return memory

    async def delete_memory(self, command: DeleteMemoryCommand) -> Memory:
        memory = await self._get_memory(command.memory_id)
        memory.delete(reason=command.reason)
        await self._repository.save(memory)
        return memory

    async def change_confidence(self, command: ChangeConfidenceCommand) -> Memory:
        memory = await self._get_memory(command.memory_id)
        memory.change_confidence(command.new_confidence)
        await self._repository.save(memory)
        return memory

    async def change_importance(self, command: ChangeImportanceCommand) -> Memory:
        memory = await self._get_memory(command.memory_id)
        memory.change_importance(command.new_importance)
        await self._repository.save(memory)
        return memory

    async def get_memory(self, query: GetMemoryQuery) -> Memory | None:
        return await self._repository.get_by_id_str(query.memory_id)

    async def get_user_memories(self, query: GetUserMemoriesQuery) -> Sequence[Memory]:
        return await self._repository.get_by_user(
            user_id=query.user_id,
            category=query.category,
            scope=query.scope,
            limit=query.limit,
        )

    async def search_memories(self, query: SearchMemoriesQuery) -> Sequence[Memory]:
        return await self._repository.search_metadata(
            user_id=query.user_id,
            query=query.query,
            limit=query.limit,
        )

    async def get_memory_summary(self, memory_id: str) -> dict | None:
        memory = await self._repository.get_by_id_str(memory_id)
        if memory is None:
            return None
        return {
            "memory_id": str(memory.memory_id),
            "category": memory.category.value,
            "scope": memory.scope.value,
            "status": memory.status.value,
            "confidence": memory.confidence.value,
            "importance": memory.importance.value,
            "record_count": memory.record_count,
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
            "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
        }

    async def process_expirations(self) -> list[Memory]:
        expired = await self._repository.expire_old()
        for memory in expired:
            memory.expire()
            await self._repository.save(memory)
        return expired

    async def _get_memory(self, memory_id: str) -> Memory:
        memory = await self._repository.get_by_id_str(memory_id)
        if memory is None:
            raise MemoryValidationError(f"Memory not found: {memory_id}")
        return memory

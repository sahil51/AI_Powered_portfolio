from __future__ import annotations

from application.ai.manager import ProviderManager
from application.context_builder.builder import ContextBuilder
from application.context_builder.factory import ContextFactory
from application.conversation.service import ConversationApplicationService
from application.memory.retrieval_service import MemoryRetrievalService
from application.pipeline.models import PipelineConfiguration
from application.pipeline.pipeline import AIResponsePipeline
from application.pipeline.validator import PipelineValidator
from application.prompts.registry import PromptRegistry


class PipelineFactory:
    @staticmethod
    def create_default_pipeline(
        conversation_service: ConversationApplicationService,
        memory_service: MemoryRetrievalService,
        prompt_registry: PromptRegistry,
        provider_manager: ProviderManager,
        config: PipelineConfiguration | None = None,
    ) -> AIResponsePipeline:
        context_builder = ContextFactory.create_default_builder()
        context_builder.register_default_layers()
        return AIResponsePipeline(
            conversation_service=conversation_service,
            memory_service=memory_service,
            context_builder=context_builder,
            prompt_registry=prompt_registry,
            provider_manager=provider_manager,
            config=config or PipelineConfiguration(),
            validator=PipelineValidator(),
        )

    @staticmethod
    def create_pipeline(
        conversation_service: ConversationApplicationService,
        memory_service: MemoryRetrievalService,
        context_builder: ContextBuilder,
        prompt_registry: PromptRegistry,
        provider_manager: ProviderManager,
        config: PipelineConfiguration | None = None,
    ) -> AIResponsePipeline:
        return AIResponsePipeline(
            conversation_service=conversation_service,
            memory_service=memory_service,
            context_builder=context_builder,
            prompt_registry=prompt_registry,
            provider_manager=provider_manager,
            config=config or PipelineConfiguration(),
            validator=PipelineValidator(),
        )

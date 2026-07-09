from __future__ import annotations

import logging
import time
from typing import Any

from application.ai.manager import ProviderManager
from application.ai.models import CompletionRequest, Usage
from application.context_builder.builder import ContextBuilder
from application.context_builder.models import BuiltContext
from application.conversation.queries import GetConversationQuery
from application.conversation.service import ConversationApplicationService
from application.memory.retrieval_service import MemoryRetrievalService
from application.pipeline.exceptions import (
    PipelineBudgetExceededError,
    PipelineContextError,
    PipelinePromptError,
    PipelineProviderError,
    PipelineValidationError,
)
from application.pipeline.models import (
    PipelineConfiguration,
    PipelineContext,
    PipelineResult,
    PipelineStage,
    PipelineStageResult,
)
from application.pipeline.validator import PipelineValidator
from application.prompts.registry import PromptRegistry

logger = logging.getLogger("ai_assistant")


class AIResponsePipeline:
    def __init__(
        self,
        conversation_service: ConversationApplicationService,
        memory_service: MemoryRetrievalService,
        context_builder: ContextBuilder,
        prompt_registry: PromptRegistry,
        provider_manager: ProviderManager,
        config: PipelineConfiguration | None = None,
        validator: PipelineValidator | None = None,
    ) -> None:
        self._conversation_service = conversation_service
        self._memory_service = memory_service
        self._context_builder = context_builder
        self._prompt_registry = prompt_registry
        self._provider_manager = provider_manager
        self._config = config or PipelineConfiguration()
        self._validator = validator or PipelineValidator()

    @property
    def config(self) -> PipelineConfiguration:
        return self._config

    async def orchestrate(self, ctx: PipelineContext) -> PipelineResult:
        start = time.time()
        stage_results: list[PipelineStageResult] = []
        warnings: list[str] = []

        r1 = await self._validate_input(ctx, warnings)
        stage_results.append(r1)

        conversation = None
        r2 = await self._load_conversation(ctx, warnings)
        stage_results.append(r2)
        if r2.success:
            conversation = r2.data.get("conversation")

        memories = None
        r3 = await self._load_memory(ctx, warnings)
        stage_results.append(r3)
        if r3.success:
            memories = r3.data.get("memories")

        built_context = None
        r4 = await self._build_context(ctx, conversation, memories, warnings)
        stage_results.append(r4)
        if r4.success:
            built_context = r4.data.get("built_context")

        r5 = await self._load_prompt(ctx, warnings)
        stage_results.append(r5)
        if r5.success:
            r5.data.get("prompt_content")

        rendered_prompt = None
        r6 = await self._render_prompt(ctx, warnings)
        stage_results.append(r6)
        if r6.success:
            rendered_prompt = r6.data.get("rendered_prompt")

        r7 = await self._estimate_tokens(ctx, built_context, rendered_prompt, warnings)
        stage_results.append(r7)
        estimated_prompt = r7.data.get("estimated_prompt_tokens", 0)

        if self._config.budget_validation:
            r8 = await self._validate_budget(ctx, estimated_prompt, warnings)
            stage_results.append(r8)

        r9 = await self._select_provider(ctx, warnings)
        stage_results.append(r9)
        provider_name = r9.data.get("provider", "")
        model_name = r9.data.get("model", "")

        response = None
        r10 = await self._generate(ctx, provider_name, model_name, rendered_prompt, warnings)
        stage_results.append(r10)
        if r10.success:
            response = r10.data.get("completion_response")

        if response and self._config.response_validation:
            r11 = await self._validate_response(ctx, response, warnings)
            stage_results.append(r11)

        if response and self._config.post_processing:
            r12 = await self._post_process(ctx, response, warnings)
            stage_results.append(r12)

        elapsed = (time.time() - start) * 1000

        if response is None:
            raise PipelineProviderError("Generation returned no response", stage="generate")

        usage = response.usage or Usage()

        r13 = await self._collect_metrics(ctx, provider_name, model_name, usage, elapsed, warnings)
        stage_results.append(r13)

        return PipelineResult(
            content=response.content,
            provider=provider_name,
            model=model_name,
            latency_ms=elapsed,
            token_usage=usage,
            estimated_cost=usage.cost,
            finish_reason=response.finish_reason,
            correlation_id=ctx.correlation_id,
            trace_id=ctx.trace_id,
            warnings=warnings,
            stage_results=stage_results,
            metadata=ctx.metadata,
            streaming=ctx.streaming,
        )

    async def _validate_input(self, ctx: PipelineContext, warnings: list[str]) -> PipelineStageResult:
        stage = PipelineStage.VALIDATE_INPUT
        t0 = time.time()
        try:
            errors = self._validator.validate(ctx)
            if errors:
                raise PipelineValidationError(detail="; ".join(errors))
            return PipelineStageResult(stage=stage, success=True, latency_ms=(time.time() - t0) * 1000)
        except PipelineValidationError:
            raise
        except Exception as e:
            return PipelineStageResult(stage=stage, success=False, latency_ms=(time.time() - t0) * 1000, error=str(e))

    async def _load_conversation(self, ctx: PipelineContext, warnings: list[str]) -> PipelineStageResult:
        stage = PipelineStage.LOAD_CONVERSATION
        t0 = time.time()
        try:
            query = GetConversationQuery(conversation_id=ctx.conversation_id)
            conversation = await self._conversation_service.get_conversation(query)
            if conversation is None:
                warnings.append(f"Conversation {ctx.conversation_id} not found")
            return PipelineStageResult(
                stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
                data={"conversation": conversation},
            )
        except Exception as e:
            warnings.append(f"Conversation load failed: {e}")
            return PipelineStageResult(
                stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
                data={"conversation": None},
            )

    async def _load_memory(self, ctx: PipelineContext, warnings: list[str]) -> PipelineStageResult:
        stage = PipelineStage.LOAD_MEMORY
        t0 = time.time()
        try:
            memories = await self._memory_service.get_user_memories(user_id=ctx.user_id, limit=50)
            return PipelineStageResult(
                stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
                data={"memories": memories},
            )
        except Exception as e:
            warnings.append(f"Memory load failed: {e}")
            return PipelineStageResult(
                stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
                data={"memories": []},
            )

    async def _build_context(
        self, ctx: PipelineContext, conversation: Any, memories: Any, warnings: list[str],
    ) -> PipelineStageResult:
        stage = PipelineStage.BUILD_CONTEXT
        t0 = time.time()
        try:
            kwargs: dict[str, Any] = {
                "user_id": ctx.user_id,
                "session_id": ctx.session_id,
            }
            if conversation is not None:
                kwargs["conversation"] = conversation
            if memories is not None:
                kwargs["memories"] = memories
            built = await self._context_builder.build(**kwargs)
            return PipelineStageResult(
                stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
                data={"built_context": built},
            )
        except Exception as e:
            raise PipelineContextError(detail=f"Context build failed: {e}", stage=stage) from e

    async def _load_prompt(self, ctx: PipelineContext, warnings: list[str]) -> PipelineStageResult:
        stage = PipelineStage.LOAD_PROMPT
        t0 = time.time()
        try:
            content = await self._prompt_registry.get(ctx.prompt_name, ctx.prompt_version)
            return PipelineStageResult(
                stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
                data={"prompt_content": content},
            )
        except Exception as e:
            raise PipelinePromptError(detail=f"Prompt load failed: {e}", stage=stage) from e

    async def _render_prompt(self, ctx: PipelineContext, warnings: list[str]) -> PipelineStageResult:
        stage = PipelineStage.RENDER_PROMPT
        t0 = time.time()
        try:
            rendered = await self._prompt_registry.render(ctx.prompt_name, ctx.prompt_variables, ctx.prompt_version)
            return PipelineStageResult(
                stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
                data={"rendered_prompt": rendered},
            )
        except Exception as e:
            warnings.append(f"Prompt render failed, using template: {e}")
            template = await self._prompt_registry.get(ctx.prompt_name, ctx.prompt_version)
            return PipelineStageResult(
                stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
                data={"rendered_prompt": template},
            )

    async def _estimate_tokens(
        self, ctx: PipelineContext, context: BuiltContext | None, rendered_prompt: str | None, warnings: list[str],
    ) -> PipelineStageResult:
        stage = PipelineStage.ESTIMATE_TOKENS
        t0 = time.time()
        context_tokens = context.metadata.total_tokens if context else 0
        prompt_len = len(rendered_prompt or "")
        estimated = max(context_tokens, prompt_len // 4)
        return PipelineStageResult(
            stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
            data={"context_tokens": context_tokens, "estimated_prompt_tokens": estimated},
        )

    async def _validate_budget(
        self, ctx: PipelineContext, estimated_prompt: int, warnings: list[str],
    ) -> PipelineStageResult:
        stage = PipelineStage.VALIDATE_BUDGET
        t0 = time.time()
        max_tokens = self._context_builder.budget.max_tokens
        if max_tokens <= 0:
            return PipelineStageResult(stage=stage, success=True, latency_ms=(time.time() - t0) * 1000)
        output_tokens = ctx.resolve_max_tokens(self._config.max_output_tokens)
        total_needed = estimated_prompt + output_tokens
        if max_tokens < total_needed:
            raise PipelineBudgetExceededError(
                detail=(
                    f"Budget {max_tokens} < needed {total_needed} "
                    f"(prompt={estimated_prompt}, output={output_tokens})"
                ),
                stage=stage,
            )
        return PipelineStageResult(stage=stage, success=True, latency_ms=(time.time() - t0) * 1000)

    async def _select_provider(self, ctx: PipelineContext, warnings: list[str]) -> PipelineStageResult:
        stage = PipelineStage.SELECT_PROVIDER
        t0 = time.time()
        provider_name: str | None = ctx.provider_override or self._config.default_provider
        model_name: str | None = ctx.model_override

        if provider_name:
            try:
                provider = self._provider_manager.registry.get(provider_name)
                if model_name is None:
                    model_name = provider.get_default_model()
                return PipelineStageResult(
                    stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
                    data={"provider": provider_name, "model": model_name or ""},
                )
            except Exception as e:
                warnings.append(f"Provider {provider_name} not found: {e}")

        try:
            provider = self._provider_manager.registry.get()
            provider_name = provider.name
            if model_name is None:
                model_name = provider.get_default_model()
        except Exception as e:
            raise PipelineProviderError(detail=f"No provider available: {e}", stage=stage) from e
        return PipelineStageResult(
            stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
            data={"provider": provider_name, "model": model_name or ""},
        )

    async def _generate(
        self, ctx: PipelineContext, provider_name: str, model_name: str,
        rendered_prompt: str | None, warnings: list[str],
    ) -> PipelineStageResult:
        stage = PipelineStage.GENERATE
        t0 = time.time()
        system_prompt = ctx.prompt_variables.get("_system_prompt")
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if rendered_prompt:
            messages.append({"role": "user", "content": rendered_prompt})
        if not messages:
            messages.append({"role": "user", "content": "Hello"})

        request = CompletionRequest(
            model=model_name,
            system_prompt=system_prompt,
            messages=messages,
            temperature=ctx.resolve_temperature(self._config.temperature),
            max_tokens=ctx.resolve_max_tokens(self._config.max_output_tokens),
            top_p=ctx.resolve_top_p(self._config.top_p),
            timeout=self._config.timeout,
            stream=ctx.streaming,
            user=ctx.user_id,
            metadata={
                "conversation_id": ctx.conversation_id,
                "correlation_id": ctx.correlation_id or "",
                "trace_id": ctx.trace_id or "",
            },
        )
        try:
            response = await self._provider_manager.generate(request, provider_name)
            return PipelineStageResult(
                stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
                data={"completion_response": response},
            )
        except Exception as e:
            raise PipelineProviderError(detail=f"Generation failed: {e}", stage=stage) from e

    async def _validate_response(self, ctx: PipelineContext, response: Any, warnings: list[str]) -> PipelineStageResult:
        stage = PipelineStage.VALIDATE_RESPONSE
        t0 = time.time()
        from application.response_validation.validator import ResponseValidator
        validator = ResponseValidator()
        report = validator.validate(response.content)
        if not report.passed:
            for key, result in report.results.items():
                if result.errors:
                    warnings.extend([f"{key}: {e}" for e in result.errors])
        return PipelineStageResult(
            stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
        )

    async def _post_process(self, ctx: PipelineContext, response: Any, warnings: list[str]) -> PipelineStageResult:
        stage = PipelineStage.POST_PROCESS
        t0 = time.time()
        from application.response_validation.normalizer import ResponseNormalizer
        from application.response_validation.sanitizer import ResponseSanitizer
        normalizer = ResponseNormalizer()
        sanitizer = ResponseSanitizer()
        content = response.content
        content = normalizer.normalize(content)
        content = sanitizer.sanitize(content)
        response.content = content
        return PipelineStageResult(
            stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
        )

    async def _collect_metrics(
        self, ctx: PipelineContext, provider: str, model: str, usage: Usage, elapsed: float, warnings: list[str],
    ) -> PipelineStageResult:
        stage = PipelineStage.COLLECT_METRICS
        t0 = time.time()
        return PipelineStageResult(
            stage=stage, success=True, latency_ms=(time.time() - t0) * 1000,
        )

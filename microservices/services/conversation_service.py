import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker

from agents.confirmation.handler import ConfirmationHandler
from agents.intent.classifier import IntentClassifier
from agents.state.graph_state import GraphState
from agents.workflow.graph import ExecutiveAssistantGraph
from infrastructure.llm.litellm_client import LiteLLMClient
from memory.long_term.service import LongTermMemory
from memory.short_term.service import ShortTermMemory
from monitoring.logger import logger
from rag.retrieval.service import RetrievalService


class ConversationService:
    def __init__(
        self,
        llm: LiteLLMClient,
        short_term_memory: ShortTermMemory,
        long_term_memory: LongTermMemory,
        retrieval_service: RetrievalService,
        session_factory: async_sessionmaker | None = None,
    ):
        self.llm = llm
        self.short_term_memory = short_term_memory
        self.long_term_memory = long_term_memory
        self.retrieval_service = retrieval_service

        self.intent_classifier = IntentClassifier(llm)
        self.confirmation_handler = ConfirmationHandler(llm)
        self.graph = ExecutiveAssistantGraph(
            llm=llm,
            intent_classifier=self.intent_classifier,
            confirmation_handler=self.confirmation_handler,
            short_term_memory=short_term_memory,
            long_term_memory=long_term_memory,
            retrieval_service=retrieval_service,
            session_factory=session_factory,
        )

    async def process_message(
        self,
        user_id: str,
        message: str,
        user_type: str = "visitor",
        conversation_id: str | None = None,
    ) -> dict:
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        state = GraphState(
            conversation_id=conversation_id,
            user_id=user_id,
            user_type=user_type,
            user_message=message,
            intent=None,
            collected_data={},
            pending_fields=[],
            missing_fields=[],
            confirmation_pending=False,
            confirmed_data=None,
            edit_field=None,
            edit_value=None,
            tool_calls=[],
            tool_results=[],
            current_workflow=None,
            workflow_state="idle",
            rag_context=[],
            portfolio_context="",
            response="",
            error=None,
            next_action=None,
            needs_tool=False,
            memory_context={},
        )

        result = await self.graph.run(state)

        response = result.get("response", "")
        needs_confirmation = result.get("confirmation_pending", False)
        workflow_state = result.get("workflow_state", "idle")

        logger.info(
            "Conversation processed",
            extra={
                "conversation_id": conversation_id,
                "intent": result.get("intent"),
                "workflow_state": workflow_state,
                "has_response": bool(response),
            },
        )

        return {
            "conversation_id": conversation_id,
            "response": response,
            "needs_confirmation": needs_confirmation,
            "workflow_state": workflow_state,
            "intent": result.get("intent"),
            "collected_data": result.get("collected_data", {}),
        }

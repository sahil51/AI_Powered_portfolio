from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import async_sessionmaker

from agents.confirmation.handler import ConfirmationHandler
from agents.intent.classifier import IntentClassifier
from agents.state.graph_state import GraphState
from domain.enums.intent import IntentType
from domain.enums.workflow_state import WorkflowState
from infrastructure.llm.litellm_client import LiteLLMClient
from memory.long_term.service import LongTermMemory
from memory.short_term.service import ShortTermMemory
from monitoring.logger import logger
from prompts.system.executive_assistant import SYSTEM_PROMPT
from rag.portfolio.service import PortfolioDataService
from rag.retrieval.service import RetrievalService


class ExecutiveAssistantGraph:
    def __init__(
        self,
        llm: LiteLLMClient,
        intent_classifier: IntentClassifier,
        confirmation_handler: ConfirmationHandler,
        short_term_memory: ShortTermMemory,
        long_term_memory: LongTermMemory,
        retrieval_service: RetrievalService,
        session_factory: async_sessionmaker | None = None,
    ):
        self.llm = llm
        self.intent_classifier = intent_classifier
        self.confirmation_handler = confirmation_handler
        self.short_term_memory = short_term_memory
        self.long_term_memory = long_term_memory
        self.retrieval_service = retrieval_service
        self._session_factory = session_factory
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(GraphState)

        workflow.add_node("classify_intent", self.classify_intent)
        workflow.add_node("load_memory", self.load_memory)
        workflow.add_node("load_portfolio_context", self.load_portfolio_context)
        workflow.add_node("retrieve_context", self.retrieve_context)
        workflow.add_node("check_tool_need", self.check_tool_need)
        workflow.add_node("collect_information", self.collect_information)
        workflow.add_node("validate_information", self.validate_information)
        workflow.add_node("handle_confirmation", self.handle_confirmation)
        workflow.add_node("execute_tool", self.execute_tool)
        workflow.add_node("generate_response", self.generate_response)
        workflow.add_node("update_memory", self.update_memory)
        workflow.add_node("handle_error", self.handle_error)

        workflow.set_entry_point("load_memory")

        workflow.add_edge("load_memory", "classify_intent")
        workflow.add_edge("classify_intent", "load_portfolio_context")
        workflow.add_edge("load_portfolio_context", "retrieve_context")
        workflow.add_edge("retrieve_context", "check_tool_need")

        workflow.add_conditional_edges(
            "check_tool_need",
            self.route_tool_need,
            {
                "collect_information": "collect_information",
                "generate_response": "generate_response",
            },
        )

        workflow.add_conditional_edges(
            "collect_information",
            self.route_after_collection,
            {
                "validate_information": "validate_information",
                "generate_response": "generate_response",
            },
        )

        workflow.add_conditional_edges(
            "validate_information",
            self.route_after_validation,
            {
                "handle_confirmation": "handle_confirmation",
                "collect_information": "collect_information",
            },
        )

        workflow.add_conditional_edges(
            "handle_confirmation",
            self.route_confirmation,
            {
                "execute_tool": "execute_tool",
                "collect_information": "collect_information",
                "generate_response": "generate_response",
            },
        )

        workflow.add_conditional_edges(
            "execute_tool",
            self.route_after_tool,
            {
                "generate_response": "generate_response",
                "handle_error": "handle_error",
            },
        )

        workflow.add_edge("generate_response", "update_memory")
        workflow.add_edge("update_memory", END)
        workflow.add_edge("handle_error", "generate_response")

        return workflow.compile()

    async def classify_intent(self, state: GraphState) -> dict:
        existing_intent = state.get("intent")
        workflow_intents = [
            IntentType.SCHEDULE_INTERVIEW.value,
            IntentType.SCHEDULE_CONSULTATION.value,
            IntentType.BECOME_LEAD.value,
        ]
        if existing_intent in workflow_intents and state.get("workflow_state") in [
            WorkflowState.COLLECTING.value, WorkflowState.CONFIRMING.value,
        ]:
            logger.info(f"Keeping existing workflow intent: {existing_intent}", extra={"conversation_id": state["conversation_id"]})
            return {"intent": existing_intent}

        intent = await self.intent_classifier.classify(
            state["user_message"],
            state["user_type"],
        )
        logger.info(f"Classified intent: {intent.value}", extra={"conversation_id": state["conversation_id"]})
        return {"intent": intent.value}

    async def load_memory(self, state: GraphState) -> dict:
        session_data = await self.short_term_memory.get_session_data(state["user_id"])
        user_profile = await self.long_term_memory.get_user_by_id(state["user_id"])
        conv_state = await self.short_term_memory.get_conversation_state(state["conversation_id"])

        updates = {}

        if conv_state:
            if conv_state.current_intent:
                updates["intent"] = conv_state.current_intent
            if conv_state.collected_data:
                updates["collected_data"] = conv_state.collected_data
            if conv_state.current_workflow:
                updates["current_workflow"] = conv_state.current_workflow
            if conv_state.workflow_state:
                updates["workflow_state"] = conv_state.workflow_state
            if conv_state.confirmation_pending:
                updates["confirmation_pending"] = conv_state.confirmation_pending

        memory_context = {
            "session": session_data or {},
            "profile": user_profile.model_dump() if user_profile else {},
            "conversation": conv_state.model_dump() if conv_state else {},
        }
        updates["memory_context"] = memory_context
        return updates

    async def load_portfolio_context(self, state: GraphState) -> dict:
        if not self._session_factory:
            return {"portfolio_context": "Portfolio Data:\nNo database session available for portfolio data."}

        try:
            async with self._session_factory() as session:
                service = PortfolioDataService(session)
                context = await service.fetch_all()
                return {"portfolio_context": context or "Portfolio Data:\nNo portfolio data found."}
        except Exception as e:
            logger.warning(f"Failed to load portfolio context: {e}")
            return {"portfolio_context": "Portfolio Data:\nUnable to load portfolio data at this time."}

    async def retrieve_context(self, state: GraphState) -> dict:
        info_intents = [
            IntentType.VIEW_PROJECTS.value, IntentType.LEARN_ABOUT.value,
            IntentType.TECHNICAL_QUESTION.value, IntentType.VIEW_EXPERIENCE.value,
            IntentType.VIEW_RESUME.value, IntentType.GENERAL_QUESTION.value,
            IntentType.QUESTION_ANSWERING.value, IntentType.UNKNOWN.value,
        ]
        if state["intent"] in info_intents:
            results = await self.retrieval_service.retrieve(state["user_message"])
            return {"rag_context": results}
        return {"rag_context": []}

    async def check_tool_need(self, state: GraphState) -> dict:
        needs_tool = state["intent"] in [
            IntentType.SCHEDULE_INTERVIEW.value,
            IntentType.SCHEDULE_CONSULTATION.value,
            IntentType.BECOME_LEAD.value,
        ]
        return {"needs_tool": needs_tool}

    async def collect_information(self, state: GraphState) -> dict:
        intent = state["intent"]
        collected = state["collected_data"]
        message = state["user_message"]

        if intent == IntentType.SCHEDULE_INTERVIEW.value or intent == IntentType.SCHEDULE_CONSULTATION.value:
            required_fields = [
                "full_name", "email", "contact_number", "company_name",
                "company_address", "meeting_purpose", "preferred_date",
                "preferred_time", "timezone", "meeting_type",
            ]
            missing = [f for f in required_fields if f not in collected]
            extracted = await self._extract_meeting_fields(message, collected)
            collected.update(extracted)
            missing = [f for f in required_fields if f not in collected]

            if missing:
                next_field = missing[0]
                prompt = f"Please provide your {next_field.replace('_', ' ')}."
                return {"collected_data": collected, "missing_fields": missing, "response": prompt, "workflow_state": WorkflowState.COLLECTING.value}

            return {"collected_data": collected, "missing_fields": [], "workflow_state": WorkflowState.VALIDATING.value}

        if intent == IntentType.BECOME_LEAD.value:
            lead_fields = ["full_name", "email", "company"]
            missing = [f for f in lead_fields if f not in collected]
            extracted = await self._extract_lead_fields(message, collected)
            collected.update(extracted)
            missing = [f for f in lead_fields if f not in collected]

            if missing:
                next_field = missing[0]
                prompt = f"Please provide your {next_field.replace('_', ' ')}."
                return {"collected_data": collected, "missing_fields": missing, "response": prompt}

            return {"collected_data": collected, "missing_fields": [], "workflow_state": WorkflowState.VALIDATING.value}

        return {"workflow_state": WorkflowState.IDLE.value}

    async def validate_information(self, state: GraphState) -> dict:
        data = state["collected_data"]
        errors = []

        if "email" in data and "@" not in data["email"]:
            errors.append("Please provide a valid email address.")
        if "contact_number" in data and len(data["contact_number"]) < 7:
            errors.append("Please provide a valid contact number.")
        if "full_name" in data and len(data["full_name"]) < 2:
            errors.append("Please provide your full name.")

        if errors:
            return {"error": errors[0], "workflow_state": WorkflowState.COLLECTING.value}

        return {"workflow_state": WorkflowState.CONFIRMING.value}

    async def handle_confirmation(self, state: GraphState) -> dict:
        if state["confirmation_pending"]:
            action = self.confirmation_handler.parse_confirmation_response(state["user_message"])
            if action["action"] == "confirm":
                return {"confirmed_data": state["collected_data"], "confirmation_pending": False, "workflow_state": WorkflowState.EXECUTING.value}
            elif action["action"] == "edit":
                return {"confirmation_pending": False, "workflow_state": WorkflowState.COLLECTING.value, "edit_field": action.get("field")}
            elif action["action"] == "cancel":
                return {"response": "No problem! Let me know if you need anything else.", "workflow_state": WorkflowState.IDLE.value, "collected_data": {}}

        summary = await self.confirmation_handler.generate_confirmation_summary(state["collected_data"])
        return {"response": summary, "confirmation_pending": True, "workflow_state": WorkflowState.CONFIRMING.value}

    async def execute_tool(self, state: GraphState) -> dict:
        intent = state["intent"]
        data = state["confirmed_data"] or state["collected_data"]

        from tasks.meeting_tasks import schedule_meeting_task
        from tasks.notification_tasks import create_lead_task

        try:
            if intent in [IntentType.SCHEDULE_INTERVIEW.value, IntentType.SCHEDULE_CONSULTATION.value]:
                task = schedule_meeting_task.delay(data)
                result = {"task_id": task.id, "status": "submitted"}
                return {"tool_results": [result], "current_workflow": "meeting_scheduling", "workflow_state": WorkflowState.COMPLETED.value}

            if intent == IntentType.BECOME_LEAD.value:
                task = create_lead_task.delay(data)
                result = {"task_id": task.id, "status": "submitted"}
                return {"tool_results": [result], "current_workflow": "lead_creation", "workflow_state": WorkflowState.COMPLETED.value}

            return {"error": "Unknown intent for tool execution", "workflow_state": WorkflowState.FAILED.value}

        except Exception as e:
            logger.error(f"Tool execution failed: {e}", extra={"conversation_id": state["conversation_id"]})
            return {"error": str(e), "workflow_state": WorkflowState.FAILED.value}

    async def generate_response(self, state: GraphState) -> dict:
        if state.get("response"):
            return {}

        portfolio_context = state.get("portfolio_context", "")
        system_prompt = SYSTEM_PROMPT.replace("{{PORTFOLIO_CONTEXT}}", portfolio_context)

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        conv_history = state.get("memory_context", {}).get("conversation", {}).get("messages", [])
        for msg in conv_history:
            if isinstance(msg, dict):
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

        messages.append({"role": "user", "content": state["user_message"]})

        if state.get("rag_context"):
            context = "\n\n".join(state["rag_context"])
            messages.insert(1, {"role": "system", "content": f"Relevant context:\n{context}"})

        try:
            response = await self.llm.generate_with_tools(messages, tools=[])
            content = response.choices[0].message.content or ""
            content = self._strip_markdown(content)
            return {"response": content}
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return {"response": "I apologize, but I'm experiencing a temporary issue. Please try again in a moment."}

    async def update_memory(self, state: GraphState) -> dict:
        if state.get("response"):
            from domain.models.conversation import Message
            conv_state = await self.short_term_memory.get_conversation_state(state["conversation_id"])
            if not conv_state:
                from domain.models.conversation import ConversationState
                conv_state = ConversationState(
                    conversation_id=state["conversation_id"],
                    user_id=state["user_id"],
                )
            user_msg = Message(role="user", content=state["user_message"])
            assistant_msg = Message(role="assistant", content=state["response"])
            conv_state.messages.append(user_msg)
            conv_state.messages.append(assistant_msg)
            conv_state.current_intent = state.get("intent")
            conv_state.collected_data = state.get("collected_data", {})
            conv_state.current_workflow = state.get("current_workflow")
            conv_state.workflow_state = state.get("workflow_state", "idle")
            conv_state.confirmation_pending = state.get("confirmation_pending", False)
            await self.short_term_memory.save_conversation_state(conv_state)
        return {}

    def _strip_markdown(self, text: str) -> str:
        import re
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^-\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'\|', ' ', text)
        return text.strip()

    async def handle_error(self, state: GraphState) -> dict:
        error = state.get("error", "Unknown error occurred")
        logger.error(f"Workflow error: {error}", extra={"conversation_id": state["conversation_id"]})
        return {
            "response": f"I encountered an issue: {error}. Please try again or contact support.",
            "workflow_state": WorkflowState.FAILED.value,
        }

    def route_tool_need(self, state: GraphState) -> str:
        if state.get("needs_tool"):
            return "collect_information"
        return "generate_response"

    def route_after_collection(self, state: GraphState) -> str:
        if not state.get("missing_fields"):
            return "validate_information"
        return "generate_response"

    def route_after_validation(self, state: GraphState) -> str:
        if state.get("error"):
            return "collect_information"
        return "handle_confirmation"

    def route_confirmation(self, state: GraphState) -> str:
        if state.get("confirmation_pending") and not state.get("confirmed_data"):
            return "generate_response"
        if state.get("confirmed_data"):
            return "execute_tool"
        return "collect_information"

    def route_after_tool(self, state: GraphState) -> str:
        if state.get("error"):
            return "handle_error"
        return "generate_response"

    async def _extract_meeting_fields(self, message: str, existing: dict) -> dict:
        extracted = {}
        prompt = f"Extract meeting details from this message. Return as JSON with keys: full_name, email, contact_number, company_name, company_address, meeting_purpose, preferred_date, preferred_time, timezone, meeting_type. Message: {message}. Already have: {existing}. Only include fields found in the message."
        try:
            result = await self.llm.generate(
                system_prompt="Extract structured data from messages. Return only JSON.",
                user_prompt=prompt,
                temperature=0.1,
                max_tokens=300,
            )
            import json
            parsed = json.loads(result.strip().strip("```json").strip("```").strip())
            for k, v in parsed.items():
                if v and k not in existing:
                    extracted[k] = v
        except Exception as e:
            logger.warning(f"Meeting field extraction failed: {e}", extra={"conversation_id": existing.get("conversation_id", "")})
        return extracted

    async def _extract_lead_fields(self, message: str, existing: dict) -> dict:
        extracted = {}
        prompt = f"Extract lead details from this message. Return as JSON with keys: full_name, email, company. Message: {message}. Already have: {existing}. Only include fields found in the message."
        try:
            result = await self.llm.generate(
                system_prompt="Extract structured data from messages. Return only JSON.",
                user_prompt=prompt,
                temperature=0.1,
                max_tokens=200,
            )
            import json
            parsed = json.loads(result.strip().strip("```json").strip("```").strip())
            for k, v in parsed.items():
                if v and k not in existing:
                    extracted[k] = v
        except Exception as e:
            logger.warning(f"Lead field extraction failed: {e}", extra={"conversation_id": existing.get("conversation_id", "")})
        return extracted

    async def run(self, state: GraphState) -> GraphState:
        return await self.graph.ainvoke(state)

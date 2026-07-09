from typing import Optional

from typing_extensions import TypedDict


class GraphState(TypedDict):
    conversation_id: str
    user_id: str
    user_type: str
    user_message: str
    intent: Optional[str]
    collected_data: dict
    pending_fields: list[str]
    missing_fields: list[str]
    confirmation_pending: bool
    confirmed_data: Optional[dict]
    edit_field: Optional[str]
    edit_value: Optional[str]
    tool_calls: list[dict]
    tool_results: list[dict]
    current_workflow: Optional[str]
    workflow_state: str
    rag_context: list[str]
    portfolio_context: str
    response: str
    error: Optional[str]
    next_action: Optional[str]
    needs_tool: bool
    memory_context: dict

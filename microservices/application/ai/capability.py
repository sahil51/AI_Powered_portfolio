from enum import Enum


class ProviderCapability(str, Enum):
    COMPLETION = "completion"
    STREAMING = "streaming"
    JSON_MODE = "json_mode"
    FUNCTION_CALLING = "function_calling"
    TOOL_CALLING = "tool_calling"
    PARALLEL_TOOL_CALLING = "parallel_tool_calling"
    EMBEDDINGS = "embeddings"
    TOKEN_COUNTING = "token_counting"
    HEALTH_CHECK = "health_check"
    COST_ESTIMATION = "cost_estimation"
    CONTEXT_WINDOW = "context_window"
    STRUCTURED_OUTPUT = "structured_output"
    VISION = "vision"
    MULTI_TURN = "multi_turn"

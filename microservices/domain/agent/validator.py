from domain.agent.aggregate import Agent
from domain.agent.policies import AgentPolicies, default_agent_policies
from domain.agent.state import AgentStatus
from domain.agent.value_objects import AgentCapability, AgentPriority, AgentType


class AgentValidationError(Exception):
    pass


class AgentValidator:
    def __init__(self, policies: AgentPolicies | None = None) -> None:
        self._policies = policies or default_agent_policies

    def validate_create(self, name: str, agent_type: AgentType) -> None:
        if not name or not name.strip():
            raise AgentValidationError("Agent name is required")
        if agent_type not in AgentType:
            raise AgentValidationError(f"Invalid agent type: {agent_type}")

    def validate_agent_type(self, agent_type: AgentType) -> None:
        if agent_type not in AgentType:
            raise AgentValidationError(f"Invalid agent type: {agent_type}")

    def validate_capability(self, capability: AgentCapability) -> None:
        if capability not in AgentCapability:
            raise AgentValidationError(f"Invalid capability: {capability}")

    def validate_priority(self, priority: AgentPriority) -> None:
        if priority not in AgentPriority:
            raise AgentValidationError(f"Invalid priority: {priority}")

    def validate_start(self, agent: Agent) -> None:
        if not agent.can_execute:
            raise AgentValidationError(f"Agent {agent.agent_id} cannot start in state {agent.status.value}")

    def validate_pause(self, agent: Agent) -> None:
        if agent.status not in (AgentStatus.RUNNING, AgentStatus.WAITING):
            msg = f"Agent {agent.agent_id} cannot pause in state {agent.status.value}"
            raise AgentValidationError(msg)

    def validate_cancel(self, agent: Agent) -> None:
        if agent.is_terminal:
            msg = f"Agent {agent.agent_id} is already in terminal state {agent.status.value}"
            raise AgentValidationError(msg)

    def validate_config(self, config: dict) -> None:
        if not isinstance(config, dict):
            raise AgentValidationError("Agent config must be a dictionary")
        if "timeout" in config and not isinstance(config["timeout"], (int, float)):
            raise AgentValidationError("Agent config timeout must be a number")

    def validate_heartbeat(self, agent: Agent) -> None:
        if agent.is_terminal:
            raise AgentValidationError(f"Agent {agent.agent_id} is in terminal state, cannot heartbeat")

    def validate_recovery(self, agent: Agent) -> None:
        if agent.status != AgentStatus.FAILED:
            raise AgentValidationError(f"Agent {agent.agent_id} is not in failed state, cannot recover")

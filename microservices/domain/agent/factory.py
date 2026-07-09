from domain.agent.aggregate import Agent
from domain.agent.policies import AgentPolicies, default_agent_policies
from domain.agent.state import AgentStateMachine, AgentStatus
from domain.agent.validator import AgentValidator
from domain.agent.value_objects import (
    AgentCapability,
    AgentHealthStatus,
    AgentId,
    AgentMetadata,
    AgentPriority,
    AgentType,
)


class AgentFactory:
    def __init__(self, validator: AgentValidator | None = None) -> None:
        self._validator = validator or AgentValidator()

    def create(
        self,
        name: str,
        agent_type: AgentType = AgentType.CUSTOM,
        capabilities: set[AgentCapability] | None = None,
        priority: AgentPriority = AgentPriority.MEDIUM,
        metadata: AgentMetadata | None = None,
        policies: AgentPolicies | None = None,
        correlation_id: str | None = None,
        config: dict | None = None,
    ) -> Agent:
        self._validator.validate_create(name, agent_type)

        agent = Agent(
            agent_id=AgentId(),
            name=name,
            agent_type=agent_type,
            capabilities=capabilities or set(),
            priority=priority,
            metadata=metadata or AgentMetadata(),
            state_machine=AgentStateMachine(),
            health_status=AgentHealthStatus.UNKNOWN,
            policies=policies or default_agent_policies,
            correlation_id=correlation_id,
            config=config or {},
        )
        return agent

    def restore(
        self,
        agent_id: str,
        name: str,
        agent_type: AgentType,
        status: str = "created",
        capabilities: set[AgentCapability] | None = None,
        priority: AgentPriority = AgentPriority.MEDIUM,
        metadata: AgentMetadata | None = None,
        health_status: str = "unknown",
        correlation_id: str | None = None,
        session_id: str | None = None,
        config: dict | None = None,
        checkpoint: dict | None = None,
        error_count: int = 0,
        created_at: object = None,
        updated_at: object = None,
        started_at: object = None,
        completed_at: object = None,
        version: int = 1,
    ) -> Agent:
        import datetime

        aid = AgentId()
        aid.__dict__["value"] = agent_id

        agent = Agent(
            agent_id=aid,
            name=name,
            agent_type=agent_type,
            capabilities=capabilities or set(),
            priority=priority,
            metadata=metadata or AgentMetadata(),
            state_machine=AgentStateMachine(AgentStatus(status)),
            health_status=AgentHealthStatus(health_status),
            correlation_id=correlation_id,
            session_id=session_id,
            config=config or {},
            checkpoint=checkpoint or {},
            error_count=error_count,
            created_at=created_at or datetime.datetime.now(datetime.timezone.utc),
            updated_at=updated_at or datetime.datetime.now(datetime.timezone.utc),
            started_at=started_at,
            completed_at=completed_at,
            version=version,
        )
        return agent

import pytest

from domain.agent.aggregate import Agent
from domain.agent.factory import AgentFactory
from domain.agent.state import AgentStatus
from domain.agent.validator import AgentValidationError
from domain.agent.value_objects import (
    AgentCapability,
    AgentMetadata,
    AgentPriority,
    AgentType,
    AgentVersion,
)


class TestAgentFactory:
    def setup_method(self):
        self.factory = AgentFactory()

    def test_create_basic_agent(self):
        agent = self.factory.create(name="test-agent", agent_type=AgentType.CONVERSATION)
        assert isinstance(agent, Agent)
        assert agent.name == "test-agent"
        assert agent.agent_type == AgentType.CONVERSATION
        assert agent.status == AgentStatus.CREATED

    def test_create_with_all_fields(self):
        agent = self.factory.create(
            name="full-agent",
            agent_type=AgentType.ANALYSIS,
            capabilities={AgentCapability.ANALYSIS, AgentCapability.CONVERSATION},
            priority=AgentPriority.HIGH,
            metadata=AgentMetadata(
                display_name="Full Agent",
                description="An agent with all fields",
                version=AgentVersion(2, 0, 0),
            ),
            correlation_id="corr-123",
            config={"timeout": 60},
        )
        assert agent.name == "full-agent"
        assert agent.agent_type == AgentType.ANALYSIS
        assert AgentCapability.ANALYSIS in agent.capabilities
        assert agent.priority == AgentPriority.HIGH
        assert agent.metadata.display_name == "Full Agent"
        assert agent.correlation_id == "corr-123"
        assert agent.config == {"timeout": 60}

    def test_create_raises_on_empty_name(self):
        with pytest.raises(AgentValidationError):
            self.factory.create(name="", agent_type=AgentType.CUSTOM)

    def test_create_raises_on_invalid_type(self):
        with pytest.raises(AgentValidationError):
            self.factory.create(name="test", agent_type="invalid")  # type: ignore

    def test_create_default_priority(self):
        agent = self.factory.create(name="default", agent_type=AgentType.MEMORY)
        assert agent.priority == AgentPriority.MEDIUM

    def test_create_empty_capabilities(self):
        agent = self.factory.create(name="no-caps", agent_type=AgentType.CUSTOM)
        assert len(agent.capabilities) == 0

    def test_restore_agent(self):
        agent = self.factory.restore(
            agent_id="agent-123",
            name="restored-agent",
            agent_type=AgentType.WORKFLOW,
            status="running",
            capabilities={AgentCapability.WORKFLOW_EXECUTION},
            priority=AgentPriority.CRITICAL,
            session_id="session-1",
            config={"timeout": 120},
            checkpoint={"step": 5},
            error_count=2,
            version=3,
        )
        assert str(agent.agent_id) == "agent-123"
        assert agent.name == "restored-agent"
        assert agent.agent_type == AgentType.WORKFLOW
        assert agent.status == AgentStatus.RUNNING
        assert agent.session_id == "session-1"
        assert agent.config == {"timeout": 120}
        assert agent.checkpoint == {"step": 5}
        assert agent.error_count == 2
        assert agent.version == 3

    def test_restore_with_defaults(self):
        agent = self.factory.restore(
            agent_id="agent-456",
            name="minimal-restore",
            agent_type=AgentType.CONVERSATION,
        )
        assert agent.status == AgentStatus.CREATED
        assert agent.version == 1
        assert agent.error_count == 0

    def test_factory_with_custom_validator(self):
        from domain.agent.validator import AgentValidator
        validator = AgentValidator()
        factory = AgentFactory(validator=validator)
        agent = factory.create(name="validated", agent_type=AgentType.CONFIRMATION)
        assert agent.name == "validated"

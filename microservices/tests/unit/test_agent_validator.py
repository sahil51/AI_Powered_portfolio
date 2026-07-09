import pytest

from domain.agent.aggregate import Agent
from domain.agent.validator import AgentValidationError, AgentValidator
from domain.agent.value_objects import AgentType


class TestAgentValidator:
    def setup_method(self):
        self.validator = AgentValidator()

    def test_validate_create_valid(self):
        self.validator.validate_create("test-agent", AgentType.CONVERSATION)

    def test_validate_create_empty_name(self):
        with pytest.raises(AgentValidationError, match="Agent name is required"):
            self.validator.validate_create("", AgentType.CUSTOM)

    def test_validate_create_blank_name(self):
        with pytest.raises(AgentValidationError, match="Agent name is required"):
            self.validator.validate_create("   ", AgentType.CUSTOM)

    def test_validate_start_runnable(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        self.validator.validate_start(agent)

    def test_validate_start_not_runnable(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        with pytest.raises(AgentValidationError):
            self.validator.validate_start(agent)

    def test_validate_pause_runnable(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.start()
        self.validator.validate_pause(agent)

    def test_validate_pause_not_runnable(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        with pytest.raises(AgentValidationError):
            self.validator.validate_pause(agent)

    def test_validate_cancel_terminal(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.start()
        agent.complete()
        with pytest.raises(AgentValidationError):
            self.validator.validate_cancel(agent)

    def test_validate_cancel_not_terminal(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        self.validator.validate_cancel(agent)

    def test_validate_config_valid(self):
        self.validator.validate_config({"timeout": 60})

    def test_validate_config_invalid_type(self):
        with pytest.raises(AgentValidationError):
            self.validator.validate_config("not-a-dict")  # type: ignore

    def test_validate_config_invalid_timeout(self):
        with pytest.raises(AgentValidationError):
            self.validator.validate_config({"timeout": "60"})

    def test_validate_heartbeat_terminal(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.start()
        agent.complete()
        with pytest.raises(AgentValidationError):
            self.validator.validate_heartbeat(agent)

    def test_validate_heartbeat_active(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        self.validator.validate_heartbeat(agent)

    def test_validate_recovery_not_failed(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        with pytest.raises(AgentValidationError):
            self.validator.validate_recovery(agent)

    def test_validate_recovery_failed(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.fail()
        self.validator.validate_recovery(agent)

    def test_validate_agent_type_valid(self):
        self.validator.validate_agent_type(AgentType.CONVERSATION)

    def test_validate_agent_type_invalid(self):
        with pytest.raises(AgentValidationError):
            self.validator.validate_agent_type("invalid")  # type: ignore

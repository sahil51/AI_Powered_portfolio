import pytest

from domain.agent.aggregate import Agent
from domain.agent.state import AgentStateMachine, AgentStatus, IllegalAgentTransitionError
from domain.agent.value_objects import AgentCapability, AgentType


class TestAgentAggregate:
    def test_create_agent(self):
        agent = Agent(name="test-agent", agent_type=AgentType.CUSTOM)
        assert agent.name == "test-agent"
        assert agent.agent_type == AgentType.CUSTOM
        assert agent.status == AgentStatus.CREATED
        assert agent.version == 1
        assert len(agent.capabilities) == 0

    def test_initialize_agent(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize(session_id="session-1")
        assert agent.status == AgentStatus.INITIALIZED
        assert agent.session_id == "session-1"
        assert agent.version == 2

    def test_start_agent(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.start()
        assert agent.status == AgentStatus.RUNNING
        assert agent.is_active
        assert agent.started_at is not None

    def test_pause_agent(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.start()
        agent.pause(reason="waiting_input")
        assert agent.status == AgentStatus.PAUSED

    def test_resume_agent(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.start()
        agent.pause()
        agent.resume(reason="input_received")
        assert agent.status == AgentStatus.RUNNING

    def test_complete_agent(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.start()
        agent.complete(result="done")
        assert agent.status == AgentStatus.COMPLETED
        assert agent.is_terminal
        assert agent.completed_at is not None

    def test_cancel_agent(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.cancel(reason="user_requested")
        assert agent.status == AgentStatus.CANCELLED
        assert agent.is_terminal

    def test_fail_agent(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.fail(error="Something went wrong", recoverable=True)
        assert agent.status == AgentStatus.FAILED
        assert agent.error_count == 1

    def test_archive_agent(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.start()
        agent.complete()
        agent.archive(reason="retention")
        assert agent.status == AgentStatus.ARCHIVED

    def test_restart_failed_agent(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.fail(error="error")
        agent.restart(session_id="session-2")
        assert agent.status == AgentStatus.INITIALIZED
        assert agent.session_id == "session-2"
        assert agent.started_at is None

    def test_record_heartbeat(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.record_heartbeat()
        assert agent.last_heartbeat is not None
        events = agent.drain_events()
        assert any(type(e).__name__ == "AgentHeartbeat" for e in events)

    def test_save_checkpoint(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.save_checkpoint({"step": 1, "data": "test"})
        assert agent.checkpoint == {"step": 1, "data": "test"}

    def test_cannot_start_from_created(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        with pytest.raises(IllegalAgentTransitionError):
            agent.start()

    def test_cannot_pause_from_initialized(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        with pytest.raises(IllegalAgentTransitionError):
            agent.pause()

    def test_cannot_complete_from_created(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        with pytest.raises(IllegalAgentTransitionError):
            agent.complete()

    def test_cannot_restart_non_failed(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        with pytest.raises(IllegalAgentTransitionError):
            agent.restart()

    def test_has_capability(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION,
                      capabilities={AgentCapability.CONVERSATION, AgentCapability.MEMORY_MANAGEMENT})
        assert agent.has_capability(AgentCapability.CONVERSATION)
        assert agent.has_capability(AgentCapability.MEMORY_MANAGEMENT)
        assert not agent.has_capability(AgentCapability.WORKFLOW_EXECUTION)

    def test_can_execute(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        assert not agent.can_execute
        agent.initialize()
        assert agent.can_execute

    def test_drain_events(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        events = agent.drain_events()
        assert len(events) >= 1
        assert agent.events == []

    def test_full_lifecycle(self):
        agent = Agent(name="test", agent_type=AgentType.ANALYSIS)
        agent.initialize("session-1")
        agent.start()
        agent.pause("wait")
        agent.resume("continue")
        agent.complete("analysis done")
        agent.archive("cleanup")
        assert agent.status == AgentStatus.ARCHIVED

    def test_fail_then_restart_lifecycle(self):
        agent = Agent(name="test", agent_type=AgentType.WORKFLOW)
        agent.initialize()
        agent.start()
        agent.fail("timeout")
        assert agent.status == AgentStatus.FAILED
        agent.restart("session-2")
        agent.start()
        agent.complete("succeeded")
        assert agent.status == AgentStatus.COMPLETED

    def test_elapsed_seconds(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        assert agent.elapsed_seconds == 0.0
        agent.initialize()
        agent.start()
        elapsed = agent.elapsed_seconds
        assert elapsed >= 0

    def test_multiple_failures_increment_count(self):
        agent = Agent(name="test", agent_type=AgentType.CONVERSATION)
        agent.initialize()
        agent.start()
        agent.fail("error1")
        assert agent.error_count == 1
        agent.restart()
        agent.start()
        agent.fail("error2")
        assert agent.error_count == 2

    @staticmethod
    def _make_agent() -> Agent:
        return Agent(name="test", agent_type=AgentType.CUSTOM)


class TestAgentStateMachine:
    def test_initial_state(self):
        sm = AgentStateMachine()
        assert sm.current_state == AgentStatus.CREATED

    def test_transition_to_initialized(self):
        sm = AgentStateMachine()
        sm.transition_to(AgentStatus.INITIALIZED)
        assert sm.current_state == AgentStatus.INITIALIZED

    def test_invalid_transition_raises(self):
        sm = AgentStateMachine()
        with pytest.raises(IllegalAgentTransitionError):
            sm.transition_to(AgentStatus.COMPLETED)

    def test_terminal_states(self):
        assert AgentStateMachine(AgentStatus.COMPLETED).is_terminal()
        assert AgentStateMachine(AgentStatus.CANCELLED).is_terminal()
        assert AgentStateMachine(AgentStatus.ARCHIVED).is_terminal()
        assert not AgentStateMachine(AgentStatus.RUNNING).is_terminal()

    def test_is_active(self):
        assert AgentStateMachine(AgentStatus.RUNNING).is_active()
        assert AgentStateMachine(AgentStatus.WAITING).is_active()
        assert not AgentStateMachine(AgentStatus.PAUSED).is_active()
        assert not AgentStateMachine(AgentStatus.CREATED).is_active()

    def test_can_execute(self):
        assert AgentStateMachine(AgentStatus.INITIALIZED).can_execute()
        assert AgentStateMachine(AgentStatus.RUNNING).can_execute()
        assert AgentStateMachine(AgentStatus.PAUSED).can_execute()
        assert not AgentStateMachine(AgentStatus.COMPLETED).can_execute()

    def test_can_modify(self):
        assert AgentStateMachine(AgentStatus.CREATED).can_modify()
        assert AgentStateMachine(AgentStatus.RUNNING).can_modify()
        assert not AgentStateMachine(AgentStatus.COMPLETED).can_modify()
        assert not AgentStateMachine(AgentStatus.ARCHIVED).can_modify()

    def test_full_lifecycle_transitions(self):
        sm = AgentStateMachine()
        sm.transition_to(AgentStatus.INITIALIZED)
        sm.transition_to(AgentStatus.RUNNING)
        sm.transition_to(AgentStatus.PAUSED)
        sm.transition_to(AgentStatus.RUNNING)
        sm.transition_to(AgentStatus.COMPLETED)
        sm.transition_to(AgentStatus.ARCHIVED)
        assert sm.current_state == AgentStatus.ARCHIVED

    def test_allowed_transitions_from_running(self):
        sm = AgentStateMachine(AgentStatus.RUNNING)
        allowed = sm.allowed_transitions()
        assert AgentStatus.PAUSED in allowed
        assert AgentStatus.WAITING in allowed
        assert AgentStatus.COMPLETED in allowed
        assert AgentStatus.CANCELLED in allowed
        assert AgentStatus.FAILED in allowed
        assert AgentStatus.CREATED not in allowed

    def test_no_transitions_from_archived(self):
        sm = AgentStateMachine(AgentStatus.ARCHIVED)
        allowed = sm.allowed_transitions()
        assert len(allowed) == 0

    def test_transition_with_event_creation(self):
        sm = AgentStateMachine()
        event = sm.transition_to(AgentStatus.INITIALIZED)
        assert event is not None
        assert type(event).__name__ == "AgentInitialized"

    def test_transition_without_event(self):
        sm = AgentStateMachine(AgentStatus.CREATED)
        event = sm.transition_to(AgentStatus.FAILED)
        assert event is None

    def test_failed_to_initialized_restart(self):
        sm = AgentStateMachine(AgentStatus.FAILED)
        event = sm.transition_to(AgentStatus.INITIALIZED)
        assert event is not None

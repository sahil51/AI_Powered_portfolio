
from application.agent.factory import AgentBuilder, AgentLoader, AgentResolver
from application.agent.registry import AgentRegistration, AgentRegistry
from domain.agent.value_objects import AgentCapability, AgentPriority, AgentType
from tests.unit.test_agent_registry import MockAgent


class TestAgentBuilder:
    def test_build_basic(self):
        builder = AgentBuilder()
        agent = MockAgent("builder-1", "Built Agent", AgentType.CONVERSATION)
        registration = (builder
                        .with_name("Built Agent")
                        .with_type(AgentType.CONVERSATION)
                        .with_capabilities(AgentCapability.CONVERSATION)
                        .with_priority(AgentPriority.HIGH)
                        .with_display_name("Display Name")
                        .with_description("A built agent")
                        .with_version("2.0.0")
                        .build(agent))
        assert registration.name == "Built Agent"
        assert registration.agent_type == AgentType.CONVERSATION
        assert AgentCapability.CONVERSATION in registration.capabilities
        assert registration.priority == AgentPriority.HIGH
        assert registration.version == "2.0.0"

    def test_build_with_metadata(self):
        builder = AgentBuilder()
        agent = MockAgent("builder-2", "Meta Agent", AgentType.WORKFLOW)
        registration = (builder
                        .with_name("Meta Agent")
                        .with_type(AgentType.WORKFLOW)
                        .with_metadata({"key": "value"})
                        .build(agent))
        assert registration.metadata.get("key") == "value"

    def test_build_defaults(self):
        builder = AgentBuilder()
        agent = MockAgent("builder-3", "Default Agent", AgentType.CUSTOM)
        registration = (builder
                        .with_name("Default Agent")
                        .with_type(AgentType.CUSTOM)
                        .build(agent))
        assert registration.priority == AgentPriority.MEDIUM
        assert registration.version == "1.0.0"


class TestAgentResolver:
    def test_resolve_by_id(self):
        registry = AgentRegistry()
        resolver = AgentResolver(registry)
        agent = MockAgent("resolve-1", "Resolvable")
        registry.register(AgentRegistration(agent=agent))
        resolved = resolver.resolve_by_id("resolve-1")
        assert resolved.agent_id == "resolve-1"

    def test_resolve_by_type(self):
        registry = AgentRegistry()
        resolver = AgentResolver(registry)
        agent = MockAgent("resolve-2", "Type Agent", AgentType.CONVERSATION)
        registry.register(AgentRegistration(agent=agent, agent_type=AgentType.CONVERSATION))
        agents = resolver.resolve_by_type(AgentType.CONVERSATION)
        assert len(agents) == 1

    def test_resolve_by_capability(self):
        registry = AgentRegistry()
        resolver = AgentResolver(registry)
        agent = MockAgent("resolve-3", "Cap Agent", capabilities={AgentCapability.CONVERSATION})
        registry.register(AgentRegistration(agent=agent, capabilities={AgentCapability.CONVERSATION}))
        agents = resolver.resolve_by_capability(AgentCapability.CONVERSATION)
        assert len(agents) == 1

    def test_resolve_default(self):
        registry = AgentRegistry()
        resolver = AgentResolver(registry)
        agent = MockAgent("resolve-4", "Default Agent", AgentType.CONVERSATION)
        registry.register(AgentRegistration(agent=agent, agent_type=AgentType.CONVERSATION))
        default = resolver.resolve_default(AgentType.CONVERSATION)
        assert default is not None
        assert default.agent_id == "resolve-4"

    def test_resolve_default_no_match(self):
        registry = AgentRegistry()
        resolver = AgentResolver(registry)
        default = resolver.resolve_default(AgentType.CONVERSATION)
        assert default is None

    def test_registry_property(self):
        registry = AgentRegistry()
        resolver = AgentResolver(registry)
        assert resolver.registry is registry


class TestAgentLoader:
    def test_load_agent(self):
        loader = AgentLoader()
        data = {
            "agent_id": "load-1",
            "name": "Loaded Agent",
            "agent_type": "conversation",
            "status": "running",
            "capabilities": ["conversation", "memory_management"],
            "priority": "high",
            "session_id": "session-1",
            "config": {"timeout": 60},
            "checkpoint": {"step": 1},
            "error_count": 2,
            "version": 3,
        }
        agent = loader.load(data)
        assert str(agent.agent_id) == "load-1"
        assert agent.name == "Loaded Agent"
        assert agent.agent_type == AgentType.CONVERSATION
        assert agent.status.value == "running"
        assert len(agent.capabilities) == 2
        assert agent.config == {"timeout": 60}
        assert agent.checkpoint == {"step": 1}
        assert agent.error_count == 2
        assert agent.version == 3

    def test_load_minimal(self):
        loader = AgentLoader()
        data = {
            "agent_id": "load-2",
            "name": "Minimal",
            "agent_type": "custom",
        }
        agent = loader.load(data)
        assert agent.name == "Minimal"
        assert agent.status.value == "created"
        assert agent.error_count == 0
        assert agent.version == 1

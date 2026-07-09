
from application.context_builder.layers.conversation import ConversationContextLayer
from application.context_builder.layers.identity import IdentityContextLayer
from application.context_builder.layers.knowledge import KnowledgeContextLayer
from application.context_builder.layers.memory import MemoryContextLayer
from application.context_builder.layers.system import SystemContextLayer
from application.context_builder.layers.tool import ToolContextLayer
from application.context_builder.layers.workflow import WorkflowContextLayer


class TestSystemContextLayer:
    def test_name(self):
        layer = SystemContextLayer()
        assert layer.name == "system"
        assert layer.priority == 0

    async def test_build(self):
        layer = SystemContextLayer(system_prompt="You are a helpful assistant.")
        result = await layer.build()
        assert result["prompt"] == "You are a helpful assistant."

    async def test_build_with_kwargs(self):
        layer = SystemContextLayer()
        result = await layer.build(system_prompt="Override")
        assert result["prompt"] == "Override"

    def test_enable_disable(self):
        layer = SystemContextLayer(enabled=False)
        assert not layer.is_enabled()
        layer.set_enabled(True)
        assert layer.is_enabled()


class TestIdentityContextLayer:
    def test_name(self):
        layer = IdentityContextLayer()
        assert layer.name == "identity"
        assert layer.priority == 1

    async def test_build_without_context(self):
        layer = IdentityContextLayer()
        result = await layer.build(user_id="user-1", session_id="sess-1")
        assert result["user_id"] == "user-1"
        assert result["session_id"] == "sess-1"


class TestConversationContextLayer:
    def test_name(self):
        layer = ConversationContextLayer()
        assert layer.name == "conversation"
        assert layer.priority == 2

    async def test_build_without_conversation(self):
        layer = ConversationContextLayer()
        result = await layer.build()
        assert result["message_count"] == 0
        assert result["messages"] == []


class TestMemoryContextLayer:
    def test_name(self):
        layer = MemoryContextLayer()
        assert layer.name == "memory"
        assert layer.priority == 3

    async def test_build_without_memories(self):
        layer = MemoryContextLayer()
        result = await layer.build()
        assert result["total_count"] == 0
        assert result["included_count"] == 0

    def test_set_max_memories(self):
        layer = MemoryContextLayer(max_memories=50)
        assert layer._max_memories == 50
        layer.set_max_memories(100)
        assert layer._max_memories == 100


class TestWorkflowContextLayer:
    def test_name(self):
        layer = WorkflowContextLayer()
        assert layer.name == "workflow"
        assert layer.priority == 4

    async def test_build(self):
        layer = WorkflowContextLayer()
        result = await layer.build(workflow_id="wf-1", workflow_state="running")
        assert result["workflow_id"] == "wf-1"
        assert result["workflow_state"] == "running"


class TestKnowledgeContextLayer:
    def test_name(self):
        layer = KnowledgeContextLayer()
        assert layer.name == "knowledge"
        assert layer.priority == 5

    def test_default_disabled(self):
        layer = KnowledgeContextLayer()
        assert not layer.is_enabled()

    async def test_build(self):
        layer = KnowledgeContextLayer(enabled=True)
        result = await layer.build()
        assert result["documents"] == []


class TestToolContextLayer:
    def test_name(self):
        layer = ToolContextLayer()
        assert layer.name == "tool"
        assert layer.priority == 6

    def test_default_disabled(self):
        layer = ToolContextLayer()
        assert not layer.is_enabled()

    async def test_build(self):
        layer = ToolContextLayer(enabled=True)
        result = await layer.build(tool_results=[{"name": "calendar"}])
        assert result["tool_count"] == 1

import pytest

from application.prompts.cache import PromptCache
from application.prompts.exceptions import PromptVersionNotFoundError
from application.prompts.loader import FilesystemPromptLoader
from application.prompts.metadata import PromptStatus
from application.prompts.registry import PromptRegistry
from application.prompts.renderer import PromptRenderer
from application.prompts.validator import PromptValidator


class TestPromptRegistry:
    def setup_method(self):
        self.loader = FilesystemPromptLoader(base_path="prompts")
        self.registry = PromptRegistry(
            loader=self.loader,
            renderer=PromptRenderer(strict=True),
            validator=PromptValidator(),
            cache=PromptCache(),
        )

    def test_initial_count(self):
        assert self.registry.count == 0

    async def test_load_registry(self):
        count = await self.registry.load_registry()
        assert count > 0

    async def test_load_and_get(self):
        await self.registry.load_registry()
        content = await self.registry.get("system.system")
        assert len(content) > 0
        assert "{{user_name}}" in content

    async def test_get_nonexistent_raises(self):
        with pytest.raises(PromptVersionNotFoundError):
            await self.registry.get("nonexistent.prompt")

    async def test_list_prompts(self):
        await self.registry.load_registry()
        prompts = self.registry.list_prompts()
        assert len(prompts) > 0

    async def test_list_by_category(self):
        await self.registry.load_registry()
        system_prompts = self.registry.list_prompts(category="system")
        assert len(system_prompts) > 0

    async def test_get_metadata(self):
        await self.registry.load_registry()
        meta = self.registry.get_metadata("system.system")
        assert meta is not None
        assert meta.category == "system"

    async def test_register_prompt(self):
        meta = await self.registry.register_prompt(
            name="test.custom",
            category="system",
            content="Hello {{name}}",
            version="1.0.0",
            status=PromptStatus.DRAFT,
        )
        assert meta.name == "test.custom"
        assert self.registry.count == 1

    async def test_deprecate(self):
        await self.registry.register_prompt(name="test.prompt", category="system", content="test")
        assert self.registry.deprecate("test.prompt")
        meta = self.registry.get_metadata("test.prompt")
        assert meta.status == PromptStatus.DEPRECATED

    def test_deprecate_nonexistent(self):
        assert not self.registry.deprecate("nonexistent")

    async def test_activate(self):
        await self.registry.register_prompt(name="test.prompt", category="system", content="test", version="1.0.0")
        assert self.registry.activate("test.prompt", "1.0.0")
        meta = self.registry.get_metadata("test.prompt")
        assert meta.status == PromptStatus.ACTIVE

    async def test_get_version_history(self):
        await self.registry.register_prompt(name="test.prompt", category="system", content="v1", version="1.0.0")
        await self.registry.register_prompt(name="test.prompt", category="system", content="v2", version="2.0.0")
        history = self.registry.get_version_history("test.prompt")
        assert len(history) == 2

    async def test_get_latest_version(self):
        await self.registry.register_prompt(name="test.prompt", category="system", content="v1", version="1.0.0")
        await self.registry.register_prompt(name="test.prompt", category="system", content="v2", version="2.0.0")
        assert self.registry.get_latest_version("test.prompt") == "2.0.0"

    async def test_render(self):
        await self.registry.register_prompt(name="test.greet", category="system", content="Hello {{name}}!")
        result = await self.registry.render("test.greet", {"name": "World"})
        assert result == "Hello World!"

    async def test_metrics(self):
        await self.registry.load_registry()
        assert self.registry.metrics.total_loads > 0

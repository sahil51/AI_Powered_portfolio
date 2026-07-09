from application.prompts.cache import PromptCache


class TestPromptCache:
    def setup_method(self):
        self.cache = PromptCache()

    async def test_get_miss(self):
        result = await self.cache.get("test.prompt")
        assert result is None

    async def test_set_and_get(self):
        await self.cache.set("test.prompt", "hello world")
        result = await self.cache.get("test.prompt")
        assert result == "hello world"

    async def test_versioned(self):
        await self.cache.set("test.prompt", "v1", version="1.0.0")
        await self.cache.set("test.prompt", "v2", version="2.0.0")
        assert await self.cache.get("test.prompt", version="1.0.0") == "v1"
        assert await self.cache.get("test.prompt", version="2.0.0") == "v2"

    async def test_invalidate(self):
        await self.cache.set("test.prompt", "hello")
        await self.cache.invalidate("test.prompt")
        assert await self.cache.get("test.prompt") is None

    async def test_invalidate_all(self):
        await self.cache.set("a", "1")
        await self.cache.set("b", "2")
        await self.cache.invalidate_all()
        assert await self.cache.get("a") is None
        assert await self.cache.get("b") is None

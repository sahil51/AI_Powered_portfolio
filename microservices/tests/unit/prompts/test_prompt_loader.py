import pytest

from application.prompts.exceptions import PromptLoadError
from application.prompts.loader import FilesystemPromptLoader


class TestFilesystemPromptLoader:
    def setup_method(self):
        self.loader = FilesystemPromptLoader(base_path="prompts")

    async def test_exists_true(self):
        exists = await self.loader.exists("system/system_v1.md")
        assert exists

    async def test_exists_false(self):
        exists = await self.loader.exists("nonexistent.md")
        assert not exists

    async def test_load_existing(self):
        content, content_hash = await self.loader.load("system/system_v1.md")
        assert len(content) > 0
        assert len(content_hash) == 16

    async def test_load_nonexistent_raises(self):
        with pytest.raises(PromptLoadError):
            await self.loader.load("nonexistent/file.md")

    async def test_list_paths(self):
        paths = await self.loader.list_paths("system")
        assert len(paths) > 0
        assert any("system_v1.md" in p for p in paths)

    async def test_list_paths_nonexistent(self):
        paths = await self.loader.list_paths("nonexistent")
        assert paths == []

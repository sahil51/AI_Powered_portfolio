from application.prompts.manifest import PromptManifest
from application.prompts.metadata import PromptMetadata, PromptStatus


class TestPromptManifest:
    def test_defaults(self):
        manifest = PromptManifest()
        assert manifest.version == "1.0"
        assert manifest.prompts == []

    def test_to_dict(self):
        meta = PromptMetadata(name="test", category="system", status=PromptStatus.ACTIVE)
        manifest = PromptManifest(prompts=[meta])
        d = manifest.to_dict()
        assert d["total_count"] == 1
        assert d["active_count"] == 1

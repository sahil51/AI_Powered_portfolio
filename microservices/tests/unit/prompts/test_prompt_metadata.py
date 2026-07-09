from application.prompts.metadata import PromptMetadata, PromptStatus, PromptVariable


class TestPromptVariable:
    def test_defaults(self):
        var = PromptVariable(name="test")
        assert var.name == "test"
        assert var.required
        assert var.default is None


class TestPromptMetadata:
    def test_defaults(self):
        meta = PromptMetadata(name="test")
        assert meta.name == "test"
        assert meta.status == PromptStatus.DRAFT
        assert meta.version == "1.0.0"

    def test_to_dict(self):
        meta = PromptMetadata(
            name="test.prompt",
            category="system",
            version="2.0.0",
            status=PromptStatus.ACTIVE,
        )
        d = meta.to_dict()
        assert d["name"] == "test.prompt"
        assert d["category"] == "system"
        assert d["version"] == "2.0.0"
        assert d["status"] == "active"

    def test_status_enum(self):
        assert PromptStatus.DRAFT.value == "draft"
        assert PromptStatus.ACTIVE.value == "active"
        assert PromptStatus.DEPRECATED.value == "deprecated"
        assert PromptStatus.ARCHIVED.value == "archived"

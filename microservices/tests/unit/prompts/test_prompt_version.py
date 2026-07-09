from application.prompts.version import PromptVersion


class TestPromptVersion:
    def test_defaults(self):
        ver = PromptVersion()
        assert ver.version == "1.0.0"
        assert ver.content == ""

    def test_to_dict(self):
        ver = PromptVersion(version="2.0.0", content="hello", content_hash="abc123")
        d = ver.to_dict()
        assert d["version"] == "2.0.0"
        assert d["content_hash"] == "abc123"

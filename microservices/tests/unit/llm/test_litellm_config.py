from infrastructure.llm.lite_llm_config import LiteLLMConfiguration


class TestLiteLLMConfiguration:
    def test_defaults(self):
        config = LiteLLMConfiguration()
        assert config.primary_model == ""
        assert config.fallback_models == []
        assert config.api_keys == {}
        assert config.timeout == 30.0
        assert config.max_retries == 3

    def test_get_api_key(self):
        config = LiteLLMConfiguration(api_keys={"gemini": "test-key"})
        assert config.get_api_key("gemini") == "test-key"
        assert config.get_api_key("nonexistent") == ""

    def test_get_base_url(self):
        config = LiteLLMConfiguration(base_urls={"cerebras": "https://api.cerebras.ai"})
        assert config.get_base_url("cerebras") == "https://api.cerebras.ai"
        assert config.get_base_url("nonexistent") == ""

    def test_from_settings(self):
        config = LiteLLMConfiguration.from_settings()
        assert config.primary_model == "gemini/gemini-2.0-flash"

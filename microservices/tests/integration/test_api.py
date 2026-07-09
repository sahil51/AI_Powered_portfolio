import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
async def client():
    from unittest.mock import AsyncMock, MagicMock, patch
    from infrastructure.cache.connection import redis_manager
    from infrastructure.llm.litellm_client import LiteLLMClient
    from rag.embeddings.service import EmbeddingService
    from application.di.container import container
    from application.prompts.registry import PromptRegistry
    from observability.manager import ObservabilityManager
    from security.manager import SecurityManager

    # Mock Redis client
    mock_client = AsyncMock()
    mock_client.exists.return_value = 0
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    mock_client.set.return_value = True
    mock_client.delete.return_value = True
    mock_client.expire.return_value = True
    mock_client.ttl.return_value = 3600

    redis_manager._client = mock_client
    redis_manager._connected = True

    # Setup mock Database Session Factory to bypass DB connection errors
    mock_db_session = AsyncMock()
    
    class MockSessionContext:
        async def __aenter__(self):
            return mock_db_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_session_factory = MagicMock(return_value=MockSessionContext())
    app.state.db_session = mock_session_factory

    # Register mock prompt registry and managers in DI container if not present
    if not container.registry.has(PromptRegistry):
        prompt_reg = PromptRegistry()
        prompt_reg.initialize = AsyncMock()
        prompt_reg.render = AsyncMock(return_value="Mock Prompt Content")
        container.register_instance(PromptRegistry, prompt_reg)
        
    if not container.registry.has(ObservabilityManager):
        mock_obs_mgr = MagicMock()
        mock_aggregator = MagicMock()
        mock_aggregator.readiness.return_value = {"status": "ready"}
        mock_aggregator.startup.return_value = {"status": "started", "uptime_seconds": 10.0}
        mock_obs_mgr.health_aggregator = mock_aggregator
        container.register_instance(ObservabilityManager, mock_obs_mgr)
        
    if not container.registry.has(SecurityManager):
        container.register_instance(SecurityManager, MagicMock())

    # Mock choice / response helper for LLM
    class MockChoiceMessage:
        content = "Mock response content"
    class MockChoice:
        message = MockChoiceMessage()
    class MockResponse:
        choices = [MockChoice()]

    # Patch EmbeddingService and LiteLLMClient to avoid network/credentials errors
    with patch.object(EmbeddingService, "__init__", lambda self: None), \
         patch.object(EmbeddingService, "embed_text", AsyncMock(return_value=[0.1] * 1536)), \
         patch.object(EmbeddingService, "embed_batch", AsyncMock(side_effect=lambda texts: [[0.1] * 1536] * len(texts))), \
         patch.object(LiteLLMClient, "__init__", lambda self: None), \
         patch.object(LiteLLMClient, "acompletion", AsyncMock(return_value=MockResponse())), \
         patch.object(LiteLLMClient, "generate", AsyncMock(return_value="Mock response content")):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


@pytest.mark.asyncio
async def test_ready_endpoint(client):
    response = await client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_chat_message(client):
    response = await client.post(
        "/chat/message/sync",
        json={
            "message": "Hello, I'd like to learn about Sahil",
            "user_type": "visitor",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "conversation_id" in data


@pytest.mark.asyncio
async def test_meeting_types(client):
    response = await client.get("/meetings/types")
    assert response.status_code == 200
    data = response.json()
    assert "meeting_types" in data
    assert len(data["meeting_types"]) == 3

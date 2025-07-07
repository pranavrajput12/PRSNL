import pytest
from fastapi.testclient import TestClient
from fastapi import WebSocket
from app.main import app
from app.core.websocket_manager import manager
from unittest.mock import patch, AsyncMock

client = TestClient(app)

@pytest.mark.asyncio
async def test_websocket_connection():
    with client.websocket_connect("/ws/ai-stream/test_client") as websocket:
        assert "test_client" in manager.active_connections
    assert "test_client" not in manager.active_connections

@pytest.mark.asyncio
async def test_websocket_send_and_receive():
    with client.websocket_connect("/ws/ai-stream/test_client") as websocket:
        with patch('app.services.llm_processor.LLMProcessor') as MockLLMProcessor:
            mock_instance = MockLLMProcessor.return_value
            mock_instance.stream_process.return_value = AsyncMock()
            mock_instance.stream_process.return_value.__aiter__.return_value = ["chunk1", "chunk2"]

            websocket.send_json({"content": "test content"})

            response1 = await websocket.receive_json()
            assert response1 == {"chunk": "chunk1"}

            response2 = await websocket.receive_json()
            assert response2 == {"chunk": "chunk2"}

    assert "test_client" not in manager.active_connections
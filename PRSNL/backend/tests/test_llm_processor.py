import pytest
import httpx
import json
from unittest.mock import AsyncMock, patch, call
from app.services.llm_processor import LLMProcessor, ProcessedContent
from app.config import settings

@pytest.mark.asyncio
async def test_llm_processor_init(mocker):
    settings.AZURE_OPENAI_API_KEY = "test_key"
    
    mock_ollama_client = AsyncMock()
    mock_ollama_client.aclose = AsyncMock()
    mock_azure_client = AsyncMock()
    mock_azure_client.aclose = AsyncMock()
    
    mocker.patch('app.services.llm_processor.httpx.AsyncClient', side_effect=[mock_ollama_client, mock_azure_client])

    processor = LLMProcessor()

    mock_ollama_client.assert_called_once_with(base_url=settings.OLLAMA_BASE_URL, timeout=60.0)
    mock_azure_client.assert_called_once_with(
        timeout=60.0,
        headers={
            "api-key": settings.AZURE_OPENAI_API_KEY,
            "Content-Type": "application/json"
        }
    )
    await processor.__aexit__(None, None, None)

@pytest.mark.asyncio
async def test_stream_process_ollama_success(mocker):
    settings.AZURE_OPENAI_API_KEY = None # Ensure Ollama is used

    mock_ollama_client = AsyncMock()
    mock_ollama_client.aclose = AsyncMock()
    mock_ollama_client.stream.return_value.__aenter__.return_value = AsyncMock()
    mock_ollama_client.stream.return_value.__aexit__.return_value = None
    mocker.patch('app.services.llm_processor.httpx.AsyncClient', return_value=mock_ollama_client)

    processor = LLMProcessor()
    
    async def async_iter_bytes_generator():
        yield b'{"response": "chunk1"}\n'
        yield b'{"response": "chunk2"}\n'

    mock_ollama_client.stream.return_value.aiter_bytes = async_iter_bytes_generator()
    
    chunks = []
    async for chunk in processor.stream_process("test content"):
        chunks.append(chunk)
    
    assert chunks == ["chunk1", "chunk2"]
    mock_ollama_client.stream.assert_called_once()
    await processor.__aexit__(None, None, None)

@pytest.mark.asyncio
async def test_stream_process_azure_success(mocker):
    settings.AZURE_OPENAI_API_KEY = "test_key" # Ensure Azure is used

    mock_ollama_client = AsyncMock()
    mock_ollama_client.aclose = AsyncMock()
    mock_azure_client = AsyncMock()
    mock_azure_client.aclose = AsyncMock()
    mock_azure_client.stream.return_value.__aenter__.return_value = AsyncMock()
    mock_azure_client.stream.return_value.__aexit__.return_value = None
    mocker.patch('app.services.llm_processor.httpx.AsyncClient', side_effect=[mock_ollama_client, mock_azure_client])

    processor = LLMProcessor()
    
    async def async_iter_bytes_generator():
        yield b'data: {"choices": [{"delta": {"content": "azure_chunk1"}}]}\n\n'
        yield b'data: {"choices": [{"delta": {"content": "azure_chunk2"}}]}\n\n'
        yield b'data: [DONE]\n\n'

    mock_azure_client.stream.return_value.aiter_bytes = async_iter_bytes_generator()
    
    chunks = []
    async for chunk in processor.stream.process("test content"):
        chunks.append(chunk)
    
    assert chunks == ["azure_chunk1", "azure_chunk2"]
    mock_azure_client.stream.assert_called_once()
    await processor.__aexit__(None, None, None)

@pytest.mark.asyncio
async def test_stream_process_ollama_fallback_to_azure(mocker):
    settings.AZURE_OPENAI_API_KEY = "test_key"

    mock_ollama_client = AsyncMock()
    mock_ollama_client.aclose = AsyncMock()
    mock_ollama_client.stream.return_value.__aenter__.return_value = AsyncMock()
    mock_ollama_client.stream.return_value.__aexit__.return_value = None
    mock_ollama_client.stream.return_value.aiter_bytes.side_effect = httpx.RequestError("Ollama error", request=httpx.Request("GET", "http://test.com"))

    mock_azure_client = AsyncMock()
    mock_azure_client.aclose = AsyncMock()
    mock_azure_client.stream.return_value.__aenter__.return_value = AsyncMock()
    mock_azure_client.stream.return_value.__aexit__.return_value = None
    
    mocker.patch('app.services.llm_processor.httpx.AsyncClient', side_effect=[mock_ollama_client, mock_azure_client])

    processor = LLMProcessor()
    
    async def async_iter_bytes_azure_generator():
        yield b'data: {"choices": [{"delta": {"content": "azure_fallback_chunk"}}]}\n\n'
        yield b'data: [DONE]\n\n'

    mock_azure_client.stream.return_value.aiter_bytes = async_iter_bytes_azure_generator()
    
    chunks = []
    async for chunk in processor.stream.process("test content"):
        chunks.append(chunk)
    
    assert chunks == ["azure_fallback_chunk"]
    mock_ollama_client.stream.assert_called_once()
    mock_azure_client.stream.assert_called_once()
    await processor.__aexit__(None, None, None)

@pytest.mark.asyncio
async def test_stream_process_no_provider_available(mocker):
    settings.AZURE_OPENAI_API_KEY = None

    mock_ollama_client = AsyncMock()
    mock_ollama_client.aclose = AsyncMock()
    mock_ollama_client.stream.return_value.__aenter__.return_value = AsyncMock()
    mock_ollama_client.stream.return_value.__aexit__.return_value = None
    mock_ollama_client.stream.return_value.aiter_bytes.side_effect = httpx.RequestError("Ollama error", request=httpx.Request("GET", "http://test.com"))
    
    mocker.patch('app.services.llm_processor.httpx.AsyncClient', return_value=mock_ollama_client)

    processor = LLMProcessor()
    
    chunks = []
    async for chunk in processor.stream_process("test content"):
        chunks.append(chunk)
    
    assert chunks == [json.dumps({"error": "No streaming provider available"})]
    await processor.__aexit__(None, None, None)

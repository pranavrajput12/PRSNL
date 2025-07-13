import pytest

from app.services.embedding_service import EmbeddingService


@pytest.mark.asyncio
async def test_embedding_service_init():
    service = EmbeddingService()
    assert service is not None
    await service.__aexit__(None, None, None)

@pytest.mark.asyncio
async def test_generate_embedding_empty_text():
    service = EmbeddingService()
    embedding = await service.generate_embedding("")
    assert embedding is None
    await service.__aexit__(None, None, None)

@pytest.mark.asyncio
async def test_batch_generate_empty_list():
    service = EmbeddingService()
    embeddings = await service.batch_generate([])
    assert embeddings == []
    await service.__aexit__(None, None, None)

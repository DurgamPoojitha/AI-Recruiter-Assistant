from backend.services.embedding_service import get_embedding_service

def test_singleton_embedding_service():
    service1 = get_embedding_service()
    service2 = get_embedding_service()
    
    # Both instances should be the exact same object
    assert service1 is service2

def test_embedding_cache():
    service = get_embedding_service()
    # Assuming text isn't empty, it should return an embedding
    emb1 = service.get_embedding("test resume")
    emb2 = service.get_embedding("test resume")
    
    # Due to caching and deterministic behavior of the dummy text
    assert emb1 is not None
    assert emb2 is not None
    assert (emb1 == emb2).all()

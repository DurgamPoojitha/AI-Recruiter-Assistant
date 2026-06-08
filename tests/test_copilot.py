import pytest
import os
from backend.services.copilot_service import answer_copilot_query, get_copilot_memory
from backend.services.rag_service import get_rag_service

def test_rag_service_initialization():
    # RAG service should initialize properly
    rag = get_rag_service()
    assert rag is not None
    assert rag.embeddings is not None
    
def test_copilot_missing_openai_key(monkeypatch):
    # Ensure OPENAI_API_KEY is not set
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    response = answer_copilot_query("Who knows Python?")
    assert "OpenAI API Key is missing" in response

def test_copilot_memory():
    # Ensure memory is properly stored per session
    mem1 = get_copilot_memory("session1")
    mem2 = get_copilot_memory("session2")
    mem1_again = get_copilot_memory("session1")
    
    assert mem1 is not mem2
    assert mem1 is mem1_again

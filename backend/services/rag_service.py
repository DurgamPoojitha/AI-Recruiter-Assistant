import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from backend.core.config import settings
from backend.core.logging import logger

class RAGService:
    def __init__(self):
        self.vector_store_path = "data/faiss_index"
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
        self.vector_store = None
        self._load_or_create_index()

    def _load_or_create_index(self):
        try:
            if os.path.exists(self.vector_store_path):
                self.vector_store = FAISS.load_local(
                    self.vector_store_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True # Required for local loading in newer FAISS
                )
                logger.info("Loaded existing FAISS vector store.")
            else:
                # Initialize an empty index with a dummy document
                dummy_doc = Document(page_content="empty", metadata={"source": "init"})
                self.vector_store = FAISS.from_documents([dummy_doc], self.embeddings)
                self.vector_store.save_local(self.vector_store_path)
                logger.info("Created new FAISS vector store.")
        except Exception as e:
            logger.error(f"Failed to load or create FAISS index: {e}")
            raise e

    def index_candidate_resume(self, candidate_id: int, candidate_name: str, raw_text: str):
        """
        Chunks the resume text and adds it to the FAISS index.
        """
        # Basic chunking (for a real app, use RecursiveCharacterTextSplitter)
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = splitter.split_text(raw_text)
        documents = [
            Document(
                page_content=chunk, 
                metadata={"candidate_id": candidate_id, "name": candidate_name, "source": "resume"}
            ) 
            for chunk in chunks
        ]
        
        if self.vector_store:
            self.vector_store.add_documents(documents)
            self.vector_store.save_local(self.vector_store_path)
            logger.info(f"Indexed {len(documents)} chunks for candidate {candidate_name} (ID: {candidate_id}).")

    def get_retriever(self):
        if self.vector_store:
            return self.vector_store.as_retriever(search_kwargs={"k": 5})
        return None

# Global accessor
_rag_service_instance = None

def get_rag_service() -> RAGService:
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RAGService()
    return _rag_service_instance

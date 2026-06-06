import threading
from functools import lru_cache
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
from backend.core.config import settings
from backend.core.logging import logger

class EmbeddingService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(EmbeddingService, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}...")
        self.tokenizer = AutoTokenizer.from_pretrained(settings.EMBEDDING_MODEL_NAME)
        self.model = AutoModel.from_pretrained(settings.EMBEDDING_MODEL_NAME)
        self.model.eval()
        logger.info("Embedding model loaded successfully.")

    @lru_cache(maxsize=1000)
    def get_embedding(self, text: str):
        """
        Generate dense vector embedding for a given text.
        Results are cached to avoid re-encoding the same text.
        """
        if not text:
            return None
            
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings.numpy()

    def compute_semantic_score(self, resume_text: str, job_desc_text: str) -> float:
        """
        Compute Cosine Similarity between resume and job description.
        Returns a score between 0 and 100.
        """
        if not resume_text or not job_desc_text:
            return 0.0
            
        resume_emb = self.get_embedding(resume_text)
        job_emb = self.get_embedding(job_desc_text)
        
        if resume_emb is None or job_emb is None:
            return 0.0
        
        similarity = cosine_similarity(resume_emb, job_emb)[0][0]
        score = max(0, min(100, float(similarity) * 100))
        return round(score, 2)

# Global accessor
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()

def generate_recommendations(missing_skills, jd_experience, resume_experience):
    recommendations = []
    
    if resume_experience < jd_experience:
        recommendations.append(f"Experience Gap: The job mentions {jd_experience} years of experience, but we found {resume_experience} years on your resume.")
        
    if missing_skills:
        core_missing = missing_skills[:4]
        recommendations.append(f"Focus on acquiring core missing skills: {', '.join(core_missing).title()}")
        if len(missing_skills) > 4:
            recommendations.append(f"Familiarize yourself with {len(missing_skills) - 4} other secondary skills mentioned.")
    
    if not recommendations:
        recommendations.append("Your resume looks like an outstanding match for this role!")
        
    return recommendations

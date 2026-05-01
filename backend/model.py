from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity

# Load lightweight transformer model suitable for sentence similarity
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

def get_embedding(text):
    """
    Generate dense vector embedding for a given text using Hugging Face transformers.
    Uses mean pooling on the last hidden state.
    """
    # Tokenize input text
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    
    # Compute token embeddings
    with torch.no_grad():
        outputs = model(**inputs)
        
    # Implement Mean Pooling to get a single vector per sentence
    # outputs.last_hidden_state has shape (batch_size, sequence_length, hidden_size)
    embeddings = outputs.last_hidden_state.mean(dim=1)
    
    return embeddings.numpy()

def compute_semantic_score(resume_text, job_desc_text):
    """
    Compute Cosine Similarity between resume and job description.
    Returns a score between 0 and 100.
    """
    if not resume_text or not job_desc_text:
        return 0.0
        
    resume_emb = get_embedding(resume_text)
    job_emb = get_embedding(job_desc_text)
    
    # Compute cosine similarity
    similarity = cosine_similarity(resume_emb, job_emb)[0][0]
    
    # Convert to percentage and clamp between 0 and 100
    score = max(0, min(100, float(similarity) * 100))
    return round(score, 2)

def generate_recommendations(missing_skills, jd_experience, resume_experience):
    """
    Generate smarter recommendations based on missing skills and experience gaps.
    """
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

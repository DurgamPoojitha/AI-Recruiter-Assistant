# AI Recruiter Assistant | Resume-to-Job Matching System

A complete end-to-end AI project that takes a candidate’s resume and a job description as input, parses the text, extracts skills using NLP keyword heuristics, and computes a Cosine Similarity match score using a Hugging Face Transformer model (`sentence-transformers/all-MiniLM-L6-v2`).

Features:
- Match score out of 100%
- Extracted Matched Skills & Missing Skills
- AI Recommendations to improve the resume

## Architecture
- **Backend**: FastAPI
- **NLP**: Hugging Face `transformers`, `torch`, `scikit-learn`
- **Frontend**: Vanilla HTML/CSS/JS (Lightweight, Glassmorphism design)
- **Local Dashboard**: Streamlit (Alternative interface)

---

## 🛠️ Step-by-Step Local Setup

### 1. Requirements

Ensure you have Python 3.9+ installed.

```bash
# Clone the repository logic onto your path /home/poojitha/Documents/AIProject
cd /home/poojitha/Documents/AIProject

# Install Requirements
pip install -r requirements.txt
```

*(Note: The first time you run the backend or streamlit, HuggingFace transformers will download the model weights (approx ~91MB for `all-MiniLM-L6-v2`).)*

### 2. Running the System (API + Vanilla Frontend)

**Start the Backend (FastAPI):**
```bash
uvicorn backend.main:app --reload
```
The API will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000)

**Start the Frontend:**
Since the frontend uses basic HTML/JS, you can simply run a python web server in another terminal, targeting the `frontend` folder:
```bash
cd frontend
python -m http.server 8080
```
Then navigate to [http://127.0.0.1:8080](http://127.0.0.1:8080) in your browser.

### 3. Running the Streamlit Dashboard (Alternative)
You can test the exact same functionality using the builtin Streamlit app:
```bash
streamlit run app.py
```

---

## 🚀 Deployment Guide

### Backend Deployment (Render / Railway / Hugging Face Spaces)
The backend does not require a database, so it is stateless and extremely easy to deploy.

**For Render / Railway:**
1. Upload this entire directory to a GitHub repository.
2. Link the repository to Render/Railway as a "Web Service".
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn backend.main:app --host 0.0.0.1 --port $PORT`

**For Hugging Face Spaces:**
1. Create a "Docker" space.
2. In the space configuration, use FastAPI.
(*Optionally, HF spaces also allow building pure `streamlit` spaces by merely pushing the `app.py` script as the center of the configuration*)

### Frontend Deployment (Netlify / Vercel)
The `<root>/frontend/` directory is entirely static markup.
1. Inside the `frontend/script.js` file, modify the `localhost:8000` URL to point to your new backend API deployed on Render/Railway.
2. Drag and drop the `frontend` folder into Netlify.
3. Done. The static file serving will act beautifully on modern CDNs.

---

## Output Example
If you pass "I know python, java, sql and docker" against "Seeking senior python engineers with extensive aws experience.":
```json
{
  "match_score": 58.2,
  "matched_skills": ["python"],
  "missing_skills": ["aws"],
  "recommendations": ["Consider adding experience or taking a course in Aws"]
}
```
*(The scores dynamically map via the semantic context captured by Mini-LM.)*

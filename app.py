import streamlit as st
import pandas as pd
from backend.utils import extract_text_from_file, preprocess_text, load_skills, extract_skills
from backend.model import compute_match_score, generate_recommendations

# --- Dashboard Configuration ---
st.set_page_config(page_title="AI Recruiter | Resume Matcher", page_icon="🤖", layout="wide")

# Modern UI Styling
st.markdown("""
    <style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #6366f1; color: white; border: none; }
    .stButton>button:hover { background-color: #4f46e5; }
    .metric-card { background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 20px; text-align: center; }
    .score-text { font-size: 3rem; font-weight: bold; background: linear-gradient(to right, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .pill { display: inline-block; padding: 5px 12px; margin: 4px; border-radius: 20px; font-size: 0.9rem; font-weight: 500; }
    .pill-success { background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .pill-warning { background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
    </style>
""", unsafe_allow_html=True)

# Load global skills once
@st.cache_data
def get_global_skills():
    return load_skills()

PREDEFINED_SKILLS = get_global_skills()

# --- Main App ---
st.title("🤖 AI Recruiter Assistant")
st.markdown("Smart Resume-to-Job Matching System powered by internal Transformers NLP Logic.")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF or TXT file", type=["pdf", "txt"])

with col2:
    st.subheader("2. Job Description")
    job_desc = st.text_area("Paste the target job description here...", height=150)

if st.button("Analyze Match"):
    if uploaded_file is not None and job_desc:
        with st.spinner("Analyzing resume using NLP Transformers..."):
            try:
                # 1. Extract Text
                file_bytes = uploaded_file.read()
                raw_text = extract_text_from_file(file_bytes, uploaded_file.name)
                
                # 2. Preprocess
                clean_resume = preprocess_text(raw_text)
                clean_jd = preprocess_text(job_desc)
                
                # 3. Extract Skills
                resume_skills = set(extract_skills(clean_resume, PREDEFINED_SKILLS))
                jd_skills = set(extract_skills(clean_jd, PREDEFINED_SKILLS))
                
                matched_skills = list(resume_skills.intersection(jd_skills))
                missing_skills = list(jd_skills.difference(resume_skills))
                
                # 4. Compute Match Score
                match_score = compute_match_score(clean_resume, clean_jd)
                
                # 5. Recommendations
                recommendations = generate_recommendations(missing_skills)
                
                st.success("Analysis Complete!")
                
                # --- Display Results ---
                st.markdown("---")
                res_col1, res_col2 = st.columns([1, 2])
                
                with res_col1:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.markdown("<h3>Match Score</h3>", unsafe_allow_html=True)
                    st.markdown(f"<div class='score-text'>{match_score}%</div>", unsafe_allow_html=True)
                    if match_score >= 80:
                        st.info("Excellent Match!")
                    elif match_score >= 50:
                        st.warning("Good Match, but missing some key skills.")
                    else:
                        st.error("Low Match. Major skills missing.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                with res_col2:
                    st.markdown("### 🎯 Skill Analysis")
                    
                    st.markdown("**Matched Skills:**")
                    if matched_skills:
                        pills_html = "".join([f"<span class='pill pill-success'>{skill}</span>" for skill in matched_skills])
                        st.markdown(pills_html, unsafe_allow_html=True)
                    else:
                        st.write("None found.")
                        
                    st.markdown("<br>**Missing Skills:**", unsafe_allow_html=True)
                    if missing_skills:
                        pills_html = "".join([f"<span class='pill pill-warning'>{skill}</span>" for skill in missing_skills])
                        st.markdown(pills_html, unsafe_allow_html=True)
                    else:
                        st.write("None found.")
                        
                    st.markdown("### 💡 Recommendations")
                    for rec in recommendations:
                        st.markdown(f"- {rec}")
                        
            except Exception as e:
                st.error(f"Error processing document: {str(e)}")
    else:
        st.warning("Please upload a resume and provide a job description.")

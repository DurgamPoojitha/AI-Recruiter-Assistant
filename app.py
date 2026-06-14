import streamlit as st
import pandas as pd
import sqlite3
import json
import plotly.express as px
import plotly.graph_objects as go
from backend.utils import extract_text_from_file, preprocess_text, load_skills
from backend.parsers.resume_parser import parse_resume
from backend.parsers.jd_parser import parse_jd
from backend.services.matching_service import calculate_match, generate_comparison_summary
from backend.parsers.ats_analyzer import analyze_resume_ats
from backend.api.routes.matches import recalculate_job_matches, ScoringWeights
from backend.repositories import (
    init_db,
    insert_job,
    insert_candidate,
    insert_match_result,
    get_job_rankings,
    get_candidate_details,
    get_pipeline_summary,
    update_candidate_status,
    add_candidate_note,
    get_candidate_notes
)
from backend.services.ai_service import (
    generate_interview_questions,
    rewrite_bullet_point,
    analyze_skill_gaps,
    generate_recruiter_report
)
from backend.services.copilot_service import answer_copilot_query
from backend.services.rag_service import get_rag_service
from backend.report_generator import generate_candidate_html_report
from backend.core.auth_component import get_auth_token_from_hash
from backend.api.dependencies import verify_jwt
import os

# Initialize database
init_db()

# --- Auth0 Setup ---
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")
LOGIN_URL = f"https://{AUTH0_DOMAIN}/authorize?response_type=token&client_id={AUTH0_CLIENT_ID}&redirect_uri=http://localhost:8501/&audience={AUTH0_API_AUDIENCE}&scope=openid profile email"

get_auth_token_from_hash()

st.sidebar.markdown("### 🔒 Authentication")
if "auth0_token" not in st.session_state:
    st.sidebar.markdown(f'<a href="{LOGIN_URL}" target="_self"><button style="width:100%; padding:10px; background-color:#4f46e5; color:white; border:none; border-radius:5px; cursor:pointer;">Login with Auth0</button></a>', unsafe_allow_html=True)
    st.sidebar.warning("Please login to access enterprise features.")
else:
    token = st.session_state["auth0_token"]
    try:
        user_payload = verify_jwt(token)
        roles = user_payload.get(f"{AUTH0_API_AUDIENCE}/roles", [])
        if not roles:
            roles = user_payload.get("roles", ["Recruiter"]) # Fallback MVP role
        org_id = user_payload.get(f"{AUTH0_API_AUDIENCE}/org_id", 1)
        
        st.session_state["user"] = {"roles": roles if isinstance(roles, list) else [roles], "org_id": org_id, "sub": user_payload.get("sub")}
        st.sidebar.success(f"Logged in!")
        st.sidebar.write(f"**Roles:** {', '.join(st.session_state['user']['roles'])}")
        st.sidebar.write(f"**Org ID:** {org_id}")
        
        if st.sidebar.button("Logout"):
            del st.session_state["auth0_token"]
            st.rerun()
    except Exception as e:
        st.sidebar.error("Session expired or invalid. Please login again.")
        if st.sidebar.button("Clear Session"):
            del st.session_state["auth0_token"]
            st.rerun()

# --- Dashboard Configuration ---
st.set_page_config(page_title="AI Recruiter | Matcher, ATS & Analytics Suite", page_icon="🤖", layout="wide")

if "user" not in st.session_state:
    st.info("Please log in via the sidebar to access the Enterprise AI Recruiter Platform.")
    st.stop()

st.title("🤖 AI Recruiter Assistant (Enterprise Phase 6)")
# Modern UI Styling with Dark / Neon Accents
st.markdown("""
    <style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #6366f1; color: white; border: none; font-weight: 600; padding: 10px; }
    .stButton>button:hover { background-color: #4f46e5; border: none; }
    .metric-card { 
        background: rgba(30, 41, 59, 0.7); 
        border: 1px solid rgba(99, 102, 241, 0.2); 
        border-radius: 12px; 
        padding: 20px; 
        text-align: center; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .score-text { 
        font-size: 3.5rem; 
        font-weight: 800; 
        background: linear-gradient(to right, #818cf8, #c084fc); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        margin: 10px 0;
    }
    .pill { 
        display: inline-block; 
        padding: 6px 14px; 
        margin: 5px; 
        border-radius: 20px; 
        font-size: 0.85rem; 
        font-weight: 600; 
    }
    .pill-success { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .pill-warning { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .feedback-box {
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .feedback-success { background: rgba(16, 185, 129, 0.1); border-left: 5px solid #10b981; }
    .feedback-warning { background: rgba(239, 68, 68, 0.1); border-left: 5px solid #ef4444; }
    .recommendation-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(192, 132, 252, 0.15) 100%);
        border: 1px solid rgba(165, 180, 252, 0.3);
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
    }
    .comp-container {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 25px;
        margin-top: 20px;
    }
    .card-highlight {
        background: rgba(99, 102, 241, 0.05);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .chip-btn {
        background-color: rgba(99, 102, 241, 0.1);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 20px;
        color: #818cf8;
        padding: 6px 15px;
        font-size: 0.9rem;
        cursor: pointer;
        display: inline-block;
        margin: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Load global skills once
@st.cache_data
def get_global_skills():
    return load_skills()

PREDEFINED_SKILLS = get_global_skills()

# Initialize session state for workflow results
if 'job_id' not in st.session_state:
    st.session_state['job_id'] = None
if 'rankings' not in st.session_state:
    st.session_state['rankings'] = []
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# --- Main Tabs Layout ---
st.title("🤖 AI Recruiter Assistant")
st.markdown("Smart Resume-to-Job Matching, ATS Optimization, Bulk Workflows & Recruiter Analytics.")

tab_single_match, tab_single_ats, tab_recruiter_workflow, tab_ats_pipeline, tab_advanced_ai, tab_analytics, tab_copilot = st.tabs([
    "🎯 Single Job Matcher", 
    "📊 Single ATS Optimizer", 
    "💼 Recruiter Workflow (Rank & Compare)",
    "🚦 ATS Pipeline Dashboard",
    "💡 Advanced AI Tools",
    "📈 Analytics Dashboard",
    "💬 Recruiter Copilot"
])

# --- TAB 1: Single Job Matcher (Phase 1) ---
with tab_single_match:
    st.subheader("Match a Candidate against a Job Description")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        uploaded_file = st.file_uploader("Upload Candidate Resume (PDF/TXT)", type=["pdf", "txt"], key="single_match_resume")
    with col2:
        job_desc = st.text_area("Paste Job Description...", height=130, key="single_match_jd")
        
    if st.button("Analyze Single Match"):
        if uploaded_file is not None and job_desc:
            with st.spinner("Analyzing match..."):
                try:
                    file_bytes = uploaded_file.read()
                    raw_text = extract_text_from_file(file_bytes, uploaded_file.name)
                    
                    parsed_resume = parse_resume(raw_text, PREDEFINED_SKILLS)
                    parsed_jd = parse_jd(job_desc, PREDEFINED_SKILLS)
                    
                    clean_resume = preprocess_text(raw_text)
                    clean_jd = preprocess_text(job_desc)
                    
                    match_analysis = calculate_match(parsed_resume, parsed_jd, clean_resume, clean_jd)
                    
                    st.success("Analysis Complete!")
                    st.markdown("### 🧬 Suitability Breakdown")
                    
                    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
                    m_col1.markdown(f"<div class='metric-card'><h4>Overall Match</h4><div class='score-text'>{match_analysis.final_score}%</div><p style='color:#a5b4fc; font-weight:600;'>Weighted</p></div>", unsafe_allow_html=True)
                    m_col2.markdown(f"<div class='metric-card'><h4>Semantic Match</h4><div class='score-text' style='font-size:2.5rem; color:#818cf8;'>{match_analysis.semantic_score}%</div><p style='color:#94a3b8;'>40% Weight</p></div>", unsafe_allow_html=True)
                    m_col3.markdown(f"<div class='metric-card'><h4>Skills Match</h4><div class='score-text' style='font-size:2.5rem; color:#a78bfa;'>{match_analysis.skill_score}%</div><p style='color:#94a3b8;'>30% Weight</p></div>", unsafe_allow_html=True)
                    m_col4.markdown(f"<div class='metric-card'><h4>Experience Match</h4><div class='score-text' style='font-size:2.5rem; color:#c084fc;'>{match_analysis.experience_score}%</div><p style='color:#94a3b8;'>20% Weight</p></div>", unsafe_allow_html=True)
                    m_col5.markdown(f"<div class='metric-card'><h4>Education Match</h4><div class='score-text' style='font-size:2.5rem; color:#f472b6;'>{match_analysis.education_score}%</div><p style='color:#94a3b8;'>10% Weight</p></div>", unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    det_col1, det_col2 = st.columns([1, 1])
                    with det_col1:
                        st.markdown("**Matched Skills:**")
                        if match_analysis.matched_skills:
                            pills_html = "".join([f"<span class='pill pill-success'>{skill}</span>" for skill in match_analysis.matched_skills])
                            st.markdown(pills_html, unsafe_allow_html=True)
                        else:
                            st.write("None found.")
                            
                        st.markdown("<br>**Missing Skills:**", unsafe_allow_html=True)
                        if match_analysis.missing_skills:
                            pills_html = "".join([f"<span class='pill pill-warning'>{skill}</span>" for skill in match_analysis.missing_skills])
                            st.markdown(pills_html, unsafe_allow_html=True)
                        else:
                            st.write("None found.")
                            
                    with det_col2:
                        st.markdown("### 💡 AI Recommendations")
                        st.markdown(f"<div class='recommendation-card'><strong>Explanation:</strong><br>{match_analysis.explanation}</div>", unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"Error matching resume: {str(e)}")
        else:
            st.warning("Please upload a resume and paste a job description.")

# --- TAB 2: Single ATS Optimizer (Phase 2) ---
with tab_single_ats:
    st.subheader("Evaluate Resume Structural ATS Compliance")
    
    uploaded_ats_file = st.file_uploader("Upload Resume (PDF/TXT)", type=["pdf", "txt"], key="single_ats_resume")
    
    if st.button("Analyze ATS Compliance"):
        if uploaded_ats_file is not None:
            with st.spinner("Checking ATS compliance..."):
                try:
                    file_bytes = uploaded_ats_file.read()
                    raw_text = extract_text_from_file(file_bytes, uploaded_ats_file.name)
                    
                    parsed_resume = parse_resume(raw_text, PREDEFINED_SKILLS)
                    ats_analysis = analyze_resume_ats(raw_text, parsed_resume, uploaded_ats_file.name)
                    
                    st.success("Analysis Complete!")
                    
                    ats_col1, ats_col2 = st.columns([1, 1.2])
                    with ats_col1:
                        fig_gauge = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = ats_analysis.ats_score,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': "ATS Score", 'font': {'size': 20, 'color': "#f8fafc"}},
                            gauge = {
                                'axis': {'range': [None, 100], 'tickcolor': "#94a3b8"},
                                'bar': {'color': "#6366f1"},
                                'bgcolor': "rgba(30, 41, 59, 0.5)",
                                'steps': [
                                    {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.15)'},
                                    {'range': [50, 80], 'color': 'rgba(245, 158, 11, 0.15)'},
                                    {'range': [80, 100], 'color': 'rgba(16, 185, 129, 0.15)'}
                                ],
                            }
                        ))
                        fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "#f8fafc"}, height=320)
                        st.plotly_chart(fig_gauge, use_container_width=True)
                        
                    with ats_col2:
                        breakdown = ats_analysis.strength_breakdown
                        categories = ['Tech Skills', 'Projects', 'Experience', 'Achievements', 'Certifications']
                        scores = [breakdown.technical_skills, breakdown.projects, breakdown.experience, breakdown.achievements, breakdown.certifications]
                        
                        fig_bar = px.bar(
                            pd.DataFrame(dict(Score=scores, Category=categories)), 
                            x='Score', y='Category', orientation='h',
                            title="Category Strengths", color='Score',
                            color_continuous_scale=['#f43f5e', '#fbbf24', '#10b981'], range_x=[0, 100]
                        )
                        fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(30, 41, 59, 0.3)', font_color="#f8fafc", height=320, coloraxis_showscale=False)
                        st.plotly_chart(fig_bar, use_container_width=True)
                        
                    st.markdown("---")
                    
                    f_col1, f_col2 = st.columns(2)
                    with f_col1:
                        st.markdown("**🛡️ Strengths:**")
                        for s in ats_analysis.strengths:
                            st.markdown(f"<div class='feedback-box feedback-success'>👍 {s}</div>", unsafe_allow_html=True)
                    with f_col2:
                        st.markdown("**⚠️ Areas of Improvement:**")
                        for w in ats_analysis.weaknesses:
                            st.markdown(f"<div class='feedback-box feedback-warning'>💡 {w}</div>", unsafe_allow_html=True)
                            
                    st.markdown("---")
                    risk_color = "#10b981" if ats_analysis.risk_level == "Low" else ("#f59e0b" if ats_analysis.risk_level == "Medium" else "#ef4444")
                    st.markdown(f"**🚨 Candidate Risk Analyzer**: <span style='color:{risk_color}; font-weight:bold;'>{ats_analysis.risk_level} Risk</span>", unsafe_allow_html=True)
                    if ats_analysis.risk_factors:
                        for rf in ats_analysis.risk_factors:
                            st.markdown(f"- {rf}")
                    else:
                        st.markdown("- No significant risks detected.")
                        
                    st.markdown(f"<div class='recommendation-card'><h3>Recruiter Decision</h3><p>{ats_analysis.recommendation}</p></div>", unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error analyzing ATS: {str(e)}")
        else:
            st.warning("Please upload a resume first.")

# --- TAB 3: Recruiter Workflow (Phase 3) ---
with tab_recruiter_workflow:
    st.subheader("Bulk Candidate Processing & Comparative Ranking")
    
    col_bulk1, col_bulk2 = st.columns([1, 1])
    with col_bulk1:
        uploaded_resumes = st.file_uploader(
            "Upload Candidate Resumes (Select Multiple)", 
            type=["pdf", "txt"], 
            accept_multiple_files=True, 
            key="bulk_uploader"
        )
    with col_bulk2:
        job_desc_bulk = st.text_area("Target Position Description / Requirements...", height=130, key="bulk_jd")
        
    if st.button("Run Bulk Match & Ranking Engine"):
        if uploaded_resumes and job_desc_bulk:
            with st.spinner("Processing all resumes and indexing in SQLite database..."):
                try:
                    # 1. Insert Job
                    job_title = job_desc_bulk.strip().split("\n")[0][:60]
                    if not job_title:
                        job_title = "Position Requirements Match"
                    
                    org_id = st.session_state.get("user", {}).get("org_id", 1)
                    job_id = insert_job(job_title, job_desc_bulk, org_id)
                    st.session_state['job_id'] = job_id
                    
                    parsed_jd = parse_jd(job_desc_bulk, PREDEFINED_SKILLS)
                    clean_jd = preprocess_text(job_desc_bulk)
                    
                    # 2. Process each resume
                    for resume in uploaded_resumes:
                        file_bytes = resume.read()
                        raw_resume_text = extract_text_from_file(file_bytes, resume.name)
                        
                        parsed_resume = parse_resume(raw_resume_text, PREDEFINED_SKILLS)
                        clean_resume = preprocess_text(raw_resume_text)
                        
                        scoring_details = calculate_match(parsed_resume, parsed_jd, clean_resume, clean_jd)
                        ats_results = analyze_resume_ats(raw_resume_text, parsed_resume, resume.name)
                        
                        # Store in Database
                        candidate_id = insert_candidate(parsed_resume, raw_text=raw_resume_text, filename=resume.name, org_id=org_id)
                        
                        # Index candidate in RAG FAISS Vector Store
                        get_rag_service().index_candidate_resume(candidate_id, parsed_resume.name, raw_resume_text)
                        
                        insert_match_result(
                            candidate_id=candidate_id,
                            job_id=job_id,
                            scoring=scoring_details,
                            ats_score=ats_results.ats_score,
                            strengths=ats_results.strengths,
                            weaknesses=ats_results.weaknesses,
                            recommendation=ats_results.recommendation,
                            strength_breakdown=ats_results.strength_breakdown
                        )
                        
                    # 3. Retrieve Rankings
                    st.session_state['rankings'] = get_job_rankings(job_id)
                    st.success("Ranking successfully created and stored in SQLite database!")
                    
                except Exception as e:
                    st.error(f"Bulk parsing failed: {str(e)}")
        else:
            st.warning("Please upload at least one candidate resume and define the job description.")
            
    # Show rankings table and comparison tool if rankings exist
    if st.session_state['rankings']:
        st.markdown("---")
        st.markdown("### 🎛️ Dynamic Scoring Engine")
        st.write("Adjust the importance of each metric and instantly recalibrate the pipeline.")
        
        col_w1, col_w2, col_w3, col_w4 = st.columns(4)
        w_sem = col_w1.slider("Semantic Match", 0, 100, 40)
        w_skill = col_w2.slider("Skills Match", 0, 100, 30)
        w_exp = col_w3.slider("Experience Match", 0, 100, 20)
        w_edu = col_w4.slider("Education Match", 0, 100, 10)
        
        if st.button("🔄 Recalibrate Pipeline"):
            total_w = w_sem + w_skill + w_exp + w_edu
            if total_w != 100:
                st.warning(f"Weights must sum to 100. Current sum: {total_w}")
            else:
                with st.spinner("Recalculating match scores..."):
                    try:
                        weights = ScoringWeights(
                            semantic=w_sem/100,
                            skill=w_skill/100,
                            experience=w_exp/100,
                            education=w_edu/100
                        )
                        response = recalculate_job_matches(st.session_state['job_id'], weights)
                        st.session_state['rankings'] = [r.dict() for r in response.rankings]
                        st.success("Pipeline recalibrated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Recalibration failed: {str(e)}")

        st.markdown("### 📋 Ranked Candidate Shortlist")
        
        df_rankings = pd.DataFrame(st.session_state['rankings'])
        
        # Display short summary columns
        display_df = df_rankings[['rank', 'name', 'match_score', 'ats_score']].rename(columns={
            'rank': 'Rank',
            'name': 'Candidate Name',
            'match_score': 'Weighted Match Score',
            'ats_score': 'ATS Compliance Score'
        })
        
        # Format percentages
        display_df['Weighted Match Score'] = display_df['Weighted Match Score'].apply(lambda x: f"{x}%")
        display_df['ATS Compliance Score'] = display_df['ATS Compliance Score'].apply(lambda x: f"{x}%")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # --- Comparison Section ---
        st.markdown("---")
        st.markdown("### 🔄 Candidate Comparison Tool")
        st.write("Select any two candidates to compare their strengths side-by-side:")
        
        rankings_list = st.session_state['rankings']
        
        col_comp1, col_comp2 = st.columns(2)
        with col_comp1:
            cand_a = st.selectbox(
                "Select Candidate A", 
                options=rankings_list, 
                format_func=lambda x: f"Rank {x['rank']}: {x['name']} ({x['match_score']}%)",
                index=0
            )
        with col_comp2:
            default_index = 1 if len(rankings_list) > 1 else 0
            cand_b = st.selectbox(
                "Select Candidate B", 
                options=rankings_list, 
                format_func=lambda x: f"Rank {x['rank']}: {x['name']} ({x['match_score']}%)",
                index=default_index
            )
            
        if cand_a and cand_b:
            job_id = st.session_state['job_id']
            a_details = get_candidate_details(cand_a['candidate_id'], job_id)
            b_details = get_candidate_details(cand_b['candidate_id'], job_id)
            
            if a_details and b_details:
                st.markdown("<div class='comp-container'>", unsafe_allow_html=True)
                
                # Side-by-side metric comparison cards
                c1, c2, c3 = st.columns([1, 1, 1])
                with c2:
                    st.markdown(f"<h4 style='text-align:center; color:#818cf8;'>{a_details['name']}</h4>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<h4 style='text-align:center; color:#c084fc;'>{b_details['name']}</h4>", unsafe_allow_html=True)
                
                # Rows comparisons
                metrics = [
                    ("Match Suitability Score", f"{a_details['match_score']}%", f"{b_details['match_score']}%"),
                    ("ATS Structural Compliance", f"{a_details['ats_score']}%", f"{b_details['ats_score']}%"),
                    ("Total Experience Years", f"{a_details['total_experience_years']} yrs", f"{b_details['total_experience_years']} yrs"),
                    ("Highest Academic Degree", a_details['highest_education_level'], b_details['highest_education_level']),
                    ("Number of Skills", str(len(a_details['skills'])), str(len(b_details['skills']))),
                    ("Number of Certifications", str(len(a_details['certifications'])), str(len(b_details['certifications'])))
                ]
                
                for label, val_a, val_b in metrics:
                    r1, r2, r3 = st.columns([1, 1, 1])
                    r1.markdown(f"**{label}**")
                    r2.markdown(f"<div style='text-align:center; font-size:1.1rem;'>{val_a}</div>", unsafe_allow_html=True)
                    r3.markdown(f"<div style='text-align:center; font-size:1.1rem;'>{val_b}</div>", unsafe_allow_html=True)
                    st.markdown("<hr style='margin:5px 0; opacity:0.1;'>", unsafe_allow_html=True)
                
                # Plotly Radar Chart for Explainability
                st.markdown("#### 📊 Candidate Skills & Experience Radar")
                
                # Need to fetch the 4 sub-scores for both candidates. Since we only stored final_score in get_candidate_details originally, we need to fetch them from the db directly for the radar.
                conn = sqlite3.connect("data/recruiter.db")
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT semantic_score, skill_score, experience_score, education_score FROM match_results WHERE candidate_id = ? AND job_id = ?", (cand_a['candidate_id'], job_id))
                a_scores = cursor.fetchone()
                cursor.execute("SELECT semantic_score, skill_score, experience_score, education_score FROM match_results WHERE candidate_id = ? AND job_id = ?", (cand_b['candidate_id'], job_id))
                b_scores = cursor.fetchone()
                conn.close()
                
                if a_scores and b_scores:
                    categories = ['Semantic', 'Skills', 'Experience', 'Education']
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=[a_scores['semantic_score'], a_scores['skill_score'], a_scores['experience_score'], a_scores['education_score']],
                        theta=categories,
                        fill='toself',
                        name=a_details['name']
                    ))
                    fig.add_trace(go.Scatterpolar(
                        r=[b_scores['semantic_score'], b_scores['skill_score'], b_scores['experience_score'], b_scores['education_score']],
                        theta=categories,
                        fill='toself',
                        name=b_details['name']
                    ))
                    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Compare skills lists
                r1, r2, r3 = st.columns([1, 1, 1])
                r1.markdown("**Key Skills Profile**")
                
                pills_a = "".join([f"<span class='pill pill-success' style='padding:3px 8px; font-size:0.75rem;'>{s}</span>" for s in a_details['skills'][:10]])
                r2.markdown(pills_a or "None found", unsafe_allow_html=True)
                
                pills_b = "".join([f"<span class='pill pill-warning' style='padding:3px 8px; font-size:0.75rem; color:#f472b6; background:rgba(244,114,182,0.15); border:1px solid rgba(244,114,182,0.3);'>{s}</span>" for s in b_details['skills'][:10]])
                r3.markdown(pills_b or "None found", unsafe_allow_html=True)
                
                st.markdown("---")
                summary_text = generate_comparison_summary(a_details, b_details)
                st.markdown(f"<h4>📝 AI Recruiter Comparison Summary</h4>"
                            f"<p style='font-size:1.1rem; line-height:1.6; font-style:italic;'>\"{summary_text}\"</p>", 
                            unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 4: Advanced AI Tools (Phase 4) ---
with tab_advanced_ai:
    st.subheader("💡 Premium Recruiter NLP Toolkits")
    
    # Sub-tabs for tools
    tool_q_gen, tool_bullet, tool_gap, tool_report = st.tabs([
        "❓ Interview Question Generator",
        "✍️ Resume Bullet Rewriter",
        "🛣️ Skill Gap Roadmap",
        "📄 AI Recruiter Report Card"
    ])
    
    # Check if there are parsed candidates in session state
    active_candidates = st.session_state['rankings']
    
    # 1. Interview Question Generator
    with tool_q_gen:
        st.markdown("### ❓ Custom Skill-Based Question Bank")
        st.write("Generates questions customized to candidate technical proficiencies across beginner, intermediate, and advanced levels.")
        
        selected_skills = []
        
        if active_candidates:
            selected_cand = st.selectbox(
                "Populate Skills from Candidate Profile:",
                options=active_candidates,
                format_func=lambda x: f"{x['name']} (Rank {x['rank']})",
                key="skills_cand_qgen"
            )
            if selected_cand:
                cand_details = get_candidate_details(selected_cand['candidate_id'], st.session_state['job_id'])
                if cand_details:
                    selected_skills = cand_details['skills']
                    st.write(f"Loaded skills: {', '.join([s.title() for s in selected_skills])}")
        
        if not selected_skills:
            custom_skills_input = st.text_input(
                "Or manually enter comma-separated skills:", 
                placeholder="Python, SQL, AWS, Docker",
                key="manual_skills_qgen"
            )
            if custom_skills_input:
                selected_skills = [s.strip() for s in custom_skills_input.split(",") if s.strip()]
                
        if selected_skills:
            questions_data = generate_interview_questions(selected_skills)
            
            for skill_name, levels in questions_data.items():
                with st.expander(f"Skill: {skill_name}"):
                    lev_col1, lev_col2, lev_col3 = st.columns(3)
                    with lev_col1:
                        st.markdown("**🟢 Beginner Level:**")
                        for q in levels["Beginner"]:
                            st.write(f"- {q}")
                    with lev_col2:
                        st.markdown("**🟡 Intermediate Level:**")
                        for q in levels["Intermediate"]:
                            st.write(f"- {q}")
                    with lev_col3:
                        st.markdown("**🔴 Advanced Level:**")
                        for q in levels["Advanced"]:
                            st.write(f"- {q}")
        else:
            st.info("Upload candidates in Tab 3 or type custom skills above to generate questions.")
            
    # 2. Resume Bullet Rewriter
    with tool_bullet:
        st.markdown("### ✍️ Resume Bullet Optimizer")
        st.write("Transform basic duty descriptions into impactful, result-oriented statements.")
        
        weak_bullet = st.text_input(
            "Enter a weak or task-oriented bullet point from your resume:",
            placeholder="wrote python script to fetch data from database",
            key="weak_bullet_input"
        )
        
        if st.button("Rewrite Bullet Point", key="btn_rewrite_bullet") and weak_bullet:
            improved_versions = rewrite_bullet_point(weak_bullet)
            
            st.markdown("#### 🚀 Achievement-Oriented Re-writes:")
            
            headers = ["📊 Metric-Focused", "📈 Scale/Volume-Focused", "👑 Leadership & Impact"]
            colors = ["#10b981", "#6366f1", "#c084fc"]
            
            for title, bullet_text, color in zip(headers, improved_versions, colors):
                st.markdown(
                    f"<div class='card-highlight' style='border-left: 5px solid {color};'>"
                    f"<strong>{title}</strong><br><span style='font-size:1.05rem;'>\"{bullet_text}\"</span>"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                
    # 3. Skill Gap Analyzer
    with tool_gap:
        st.markdown("### 🛣️ Learning Roadmaps & Missing Skills Bridge")
        st.write("Analyzes candidate skill gaps relative to the role and maps out customized study programs.")
        
        if active_candidates:
            selected_cand_gap = st.selectbox(
                "Select Candidate Profile for Gap Analysis:",
                options=active_candidates,
                format_func=lambda x: f"{x['name']} (Rank {x['rank']})",
                key="gap_cand_selector"
            )
            
            if selected_cand_gap:
                cand_details = get_candidate_details(selected_cand_gap['candidate_id'], st.session_state['job_id'])
                if cand_details and st.session_state['job_id']:
                    job_id = st.session_state['job_id']
                    
                    # Compute missing skills
                    conn = sqlite3.connect("data/recruiter.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT description FROM jobs WHERE id = ?", (job_id,))
                    jd_row = cursor.fetchone()
                    conn.close()
                    
                    missing_skills_list = []
                    if jd_row:
                        parsed_jd = parse_jd(jd_row[0], PREDEFINED_SKILLS)
                        all_jd_skills = set([s.lower() for s in parsed_jd.required_skills + parsed_jd.preferred_skills])
                        candidate_skills = set([s.lower() for s in cand_details['skills']])
                        missing_skills_list = list(all_jd_skills.difference(candidate_skills))
                            
                    if missing_skills_list:
                        st.markdown(f"#### 🔍 Identified Skill Gaps ({len(missing_skills_list)})")
                        pills_html = "".join([f"<span class='pill pill-warning'>{skill}</span>" for skill in missing_skills_list])
                        st.markdown(pills_html, unsafe_allow_html=True)
                        st.write("")
                        
                        roadmaps = analyze_skill_gaps(missing_skills_list)
                        
                        for skill_name, roadmap_data in roadmaps.items():
                            with st.expander(f"Roadmap & Suggested courses for: {skill_name}"):
                                col_road1, col_road2 = st.columns(2)
                                with col_road1:
                                    st.markdown("**📅 2-Week Study Timeline:**")
                                    for step in roadmap_data["roadmap"]:
                                        st.write(step)
                                with col_road2:
                                    st.markdown("**🎓 Recommended Certifications/Courses:**")
                                    for course in roadmap_data["courses"]:
                                        st.write(f"- {course}")
                    else:
                        st.success("Outstanding! The candidate matches all technology requirements defined in the job description.")
        else:
            st.info("Upload candidates and run bulk analysis in Tab 3 to visualize skill gap timelines.")
            
    # 4. AI Recruiter Report
    with tool_report:
        st.markdown("### 📄 Candidate Hiring Scorecard")
        st.write("Summarizes candidate qualifications, structural suitability, and interview guidelines in a unified scorecard.")
        
        if active_candidates:
            selected_cand_report = st.selectbox(
                "Select Candidate Profile for Scorecard Report:",
                options=active_candidates,
                format_func=lambda x: f"{x['name']} (Rank {x['rank']})",
                key="report_cand_selector"
            )
            
            if selected_cand_report:
                cand_details = get_candidate_details(selected_cand_report['candidate_id'], st.session_state['job_id'])
                if cand_details:
                    job_id = st.session_state['job_id']
                    
                    # Compute missing skills
                    conn = sqlite3.connect("data/recruiter.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT description FROM jobs WHERE id = ?", (job_id,))
                    jd_row = cursor.fetchone()
                    conn.close()
                    
                    missing_skills_list = []
                    if jd_row:
                        parsed_jd = parse_jd(jd_row[0], PREDEFINED_SKILLS)
                        all_jd_skills = set([s.lower() for s in parsed_jd.required_skills + parsed_jd.preferred_skills])
                        candidate_skills = set([s.lower() for s in cand_details['skills']])
                        missing_skills_list = list(all_jd_skills.difference(candidate_skills))
                        
                    # Generate report data
                    report = generate_recruiter_report(
                        name=cand_details["name"],
                        education=cand_details["highest_education_level"],
                        experience_years=cand_details["total_experience_years"],
                        skills=cand_details["skills"],
                        missing_skills=missing_skills_list
                    )
                    
                    st.markdown("<div class='recommendation-card'>", unsafe_allow_html=True)
                    st.markdown(f"<h2>Hiring Report Card: {cand_details['name']}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<h4>Match Score: {cand_details['match_score']}% | ATS Score: {cand_details['ats_score']}%</h4>", unsafe_allow_html=True)
                    
                    # Highlight badge
                    badge_color = "#ef4444"
                    if report["suitability_rating"] == "Strong Buy":
                        badge_color = "#10b981"
                    elif report["suitability_rating"] == "Recommended":
                        badge_color = "#3b82f6"
                        
                    st.markdown(f"<span style='background-color:{badge_color}; color:white; padding:5px 12px; border-radius:20px; font-weight:bold; font-size:1.1rem;'>{report['suitability_rating']}</span>", unsafe_allow_html=True)
                    
                    st.markdown("<br><br><strong>Recruiter Summary:</strong>", unsafe_allow_html=True)
                    st.write(report["summary"])
                    
                    rep_col1, rep_col2 = st.columns(2)
                    with rep_col1:
                        st.markdown("**🛡️ Core Competencies:**")
                        for tech in report["core_technologies"][:6]:
                            st.markdown(f"- {tech}")
                    with rep_col2:
                        st.markdown("**⚠️ Skill Shortages:**")
                        if report["missing_technologies"]:
                            for tech in report["missing_technologies"][:6]:
                                st.markdown(f"- {tech}")
                        else:
                            st.write("None identified.")
                            
                    st.markdown("---")
                    st.markdown("### 🎙️ Suggested Interview Focus Guidelines:")
                    for area in report["interview_focus_areas"]:
                        st.markdown(f"- {area}")
                    
                    # Download HTML Report button (Print-to-PDF ready)
                    st.markdown("---")
                    conn = sqlite3.connect("data/recruiter.db")
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT final_score, ats_score, strengths, weaknesses, recommendation FROM match_results WHERE candidate_id = ? AND job_id = ?", (cand_details['id'], job_id))
                    mr_row = cursor.fetchone()
                    conn.close()
                    
                    if mr_row:
                        mr_dict = {
                            "final_score": mr_row["final_score"],
                            "ats_score": mr_row["ats_score"],
                            "strengths": json.loads(mr_row["strengths"]) if mr_row["strengths"] else [],
                            "weaknesses": json.loads(mr_row["weaknesses"]) if mr_row["weaknesses"] else [],
                            "recommendation": mr_row["recommendation"],
                            "missing_skills": missing_skills_list
                        }
                        html_data = generate_candidate_html_report(cand_details, mr_dict, generate_interview_questions(cand_details["skills"]))
                        st.download_button(
                            label="📥 Download Candidate Scorecard Report (HTML / PDF-Ready)",
                            data=html_data,
                            file_name=f"recruiter_report_{cand_details['name'].replace(' ', '_')}.html",
                            mime="text/html"
                        )
                    
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Upload candidates and run bulk analysis in Tab 3 to view printable recruiter report cards.")

# --- TAB 5: Analytics Dashboard (Phase 5) ---
with tab_analytics:
    st.subheader("📊 Recruiter Pipeline Analytics Dashboard")
    
    # Query database totals
    conn = sqlite3.connect("data/recruiter.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM candidates")
    total_candidates = cursor.fetchone()[0]
    
    avg_ats = 0.0
    avg_match = 0.0
    
    if total_candidates > 0:
        cursor.execute("SELECT AVG(ats_score), AVG(final_score) FROM match_results")
        avg_ats_row, avg_match_row = cursor.fetchone()
        avg_ats = round(avg_ats_row or 0.0, 1)
        avg_match = round(avg_match_row or 0.0, 1)
        
    conn.close()
    
    # Display top analytics metrics cards
    st.markdown("### 🧬 Pipeline Metrics")
    met_col1, met_col2, met_col3 = st.columns(3)
    with met_col1:
        st.markdown(f"<div class='metric-card'><h4>Total Candidates Indexed</h4><div class='score-text'>{total_candidates}</div><p style='color:#94a3b8;'>Profiles in SQLite Database</p></div>", unsafe_allow_html=True)
    with met_col2:
        st.markdown(f"<div class='metric-card'><h4>Average Match Score</h4><div class='score-text' style='color:#a78bfa;'>{avg_match}%</div><p style='color:#94a3b8;'>Role suitability average</p></div>", unsafe_allow_html=True)
    with met_col3:
        st.markdown(f"<div class='metric-card'><h4>Average ATS Score</h4><div class='score-text' style='color:#10b981;'>{avg_ats}%</div><p style='color:#94a3b8;'>Completeness compliance average</p></div>", unsafe_allow_html=True)
        
    if total_candidates > 0:
        st.markdown("---")
        st.markdown("### 📈 Hiring Funnel & Pipeline Analytics")
        
        # We need a job selector to show the funnel for a specific job, or aggregate
        conn = sqlite3.connect("data/recruiter.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM jobs WHERE org_id = ?", (st.session_state.get("user", {}).get("org_id", 1),))
        available_jobs = cursor.fetchall()
        conn.close()
        
        if available_jobs:
            job_opts = {f"Job {j[0]}: {j[1]}": j[0] for j in available_jobs}
            selected_job = st.selectbox("Select Job to View Pipeline Funnel", list(job_opts.keys()))
            
            pipeline_data = get_pipeline_summary(job_opts[selected_job])
            
            # Aggregate the pipeline for the funnel
            funnel_stages = ["Applied", "Screening", "Interview", "Offer", "Hired"]
            funnel_counts = [len(pipeline_data.get(stage, [])) for stage in funnel_stages]
            
            fig_funnel = go.Figure(go.Funnel(
                y = funnel_stages,
                x = funnel_counts,
                textposition = "inside",
                textinfo = "value+percent initial",
                marker = {"color": ["#4f46e5", "#8b5cf6", "#d946ef", "#ec4899", "#f43f5e"]}
            ))
            fig_funnel.update_layout(title_text="Candidate Drop-off Funnel", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
            st.plotly_chart(fig_funnel, use_container_width=True)
            
            st.markdown("---")
        
        st.markdown("### 📊 Distributions & Talent Breakdown")
        
        # Load all scores for distributions
        conn = sqlite3.connect("data/recruiter.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.name, mr.final_score, mr.ats_score, c.skills
            FROM match_results mr
            JOIN candidates c ON mr.candidate_id = c.id
        """)
        rows = cursor.fetchall()
        conn.close()
        
        df_analytics = pd.DataFrame([dict(r) for r in rows])
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # 1. Match score histogram
            fig_hist_match = px.histogram(
                df_analytics, x="final_score", nbins=10,
                title="Job Suitability Match Distribution",
                labels={"final_score": "Match Score (%)"},
                color_discrete_sequence=["#818cf8"]
            )
            fig_hist_match.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(30, 41, 59, 0.3)', font_color="#f8fafc")
            st.plotly_chart(fig_hist_match, use_container_width=True)
            
        with chart_col2:
            # 2. ATS score distribution
            fig_hist_ats = px.histogram(
                df_analytics, x="ats_score", nbins=10,
                title="ATS Completeness Score Distribution",
                labels={"ats_score": "ATS Score (%)"},
                color_discrete_sequence=["#10b981"]
            )
            fig_hist_ats.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(30, 41, 59, 0.3)', font_color="#f8fafc")
            st.plotly_chart(fig_hist_ats, use_container_width=True)
            
        chart_col3, chart_col4 = st.columns(2)
        
        with chart_col3:
            # 3. Top candidate skill distribution
            # Count skills frequencies
            all_skills = []
            for s_str in df_analytics["skills"]:
                if s_str:
                    all_skills.extend(json.loads(s_str))
            
            df_skills_freq = pd.Series(all_skills).value_counts().reset_index()
            df_skills_freq.columns = ["Skill", "Frequency"]
            
            fig_skills_bar = px.bar(
                df_skills_freq.head(10), x="Frequency", y="Skill",
                orientation='h', title="Top 10 Technical Skills in Pipeline",
                color="Frequency", color_continuous_scale="dense"
            )
            fig_skills_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(30, 41, 59, 0.3)', font_color="#f8fafc", coloraxis_showscale=False)
            st.plotly_chart(fig_skills_bar, use_container_width=True)
            
        with chart_col4:
            # 4. Horizontal Rankings Bar Chart
            fig_rank_bar = px.bar(
                df_analytics.sort_values(by="final_score", ascending=True),
                x="final_score", y="name",
                title="Candidate Match Rankings Compare",
                labels={"final_score": "Match Score (%)", "name": "Candidate"},
                color="final_score", color_continuous_scale=['#f43f5e', '#fbbf24', '#10b981']
            )
            fig_rank_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(30, 41, 59, 0.3)', font_color="#f8fafc", coloraxis_showscale=False)
            st.plotly_chart(fig_rank_bar, use_container_width=True)
    else:
        st.info("No analytics data loaded. Upload candidate resumes and job descriptions to populate charts.")

# --- TAB 6: Recruiter Copilot (Phase 5) ---
with tab_copilot:
    st.subheader("💬 Recruiter Copilot Assistant")
    st.write("Ask your data-aware Copilot chatbot specific questions about candidates, missing skills, and pipeline rankings.")
    
    # Render quick queries chips
    st.write("**Quick Prompts:**")
    chips_col = st.container()
    
    # Prompt Input
    copilot_query = st.chat_input("Ask your Recopilot (e.g. Which candidates know AWS?)...")
    
    # Handle sample chip buttons click
    # Streamlit buttons in container columns
    col_chip1, col_chip2, col_chip3, col_chip4 = st.columns(4)
    if col_chip1.button("Why is Candidate A ranked first?", key="chip_1"):
        copilot_query = "Why is Candidate A ranked first?"
    if col_chip2.button("Which candidates know AWS?", key="chip_2"):
        copilot_query = "Which candidates know AWS?"
    if col_chip3.button("Compare top candidates.", key="chip_3"):
        copilot_query = "Compare top candidates."
    if col_chip4.button("Show missing skills trends.", key="chip_4"):
        copilot_query = "Show missing skills trends."
        
    # Render Chat History
    for msg in st.session_state['chat_history']:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Process user query
    if copilot_query:
        # Append User message
        st.session_state['chat_history'].append({"role": "user", "content": copilot_query})
        with st.chat_message("user"):
            st.markdown(copilot_query)
            
        with st.spinner("Retrieving database details..."):
            # Use a static session ID for this user session
            reply = answer_copilot_query(copilot_query, st.session_state['job_id'], session_id="streamlit_user_session")
            
            # Append Assistant response
            st.session_state['chat_history'].append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)
                st.rerun()

# --- TAB: ATS Pipeline Dashboard (Phase 2) ---
with tab_ats_pipeline:
    st.subheader("🚦 Enterprise ATS Pipeline Dashboard")
    st.write("Drag and drop is simulated via status selection. View candidates across the 8 recruitment stages.")
    
    if st.session_state['job_id']:
        job_id = st.session_state['job_id']
        pipeline = get_pipeline_summary(job_id)
        
        stages = ["Applied", "Screening", "Interview Scheduled", "Technical Round", "HR Round", "Offer", "Hired", "Rejected"]
        
        # Display KanBan columns
        cols = st.columns(len(stages))
        for idx, stage in enumerate(stages):
            with cols[idx]:
                st.markdown(f"**{stage}** ({len(pipeline.get(stage, []))})")
                for cand in pipeline.get(stage, []):
                    st.markdown(
                        f"""<div class='metric-card' style='padding:10px; margin-bottom:10px; text-align:left; border-top:3px solid #6366f1;'>
                        <strong>{cand['name']}</strong><br>
                        <span style='font-size:0.8rem; color:#94a3b8;'>Match: {cand['match_score']}%</span>
                        </div>""", 
                        unsafe_allow_html=True
                    )
                    
        st.markdown("---")
        st.markdown("### 📝 Manage Candidate Status & Notes")
        
        all_candidates = st.session_state['rankings']
        if all_candidates:
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                selected_cand = st.selectbox(
                    "Select Candidate:",
                    options=all_candidates,
                    format_func=lambda x: f"{x['name']} (Rank {x['rank']})"
                )
                if selected_cand:
                    new_status = st.selectbox("Update Status:", stages, index=0)
                    if st.button("Update Status"):
                        update_candidate_status(selected_cand['candidate_id'], job_id, new_status, recruiter_id=1) # dummy recruiter 1
                        st.success(f"Status updated to {new_status}!")
                        st.rerun()
            
            with m_col2:
                if selected_cand:
                    st.markdown("**Recruiter Notes:**")
                    notes = get_candidate_notes(selected_cand['candidate_id'])
                    if notes:
                        for n in notes:
                            st.info(f"**{n['recruiter_name'] or 'Recruiter'}:** {n['note_text']}  \n*{n['created_at']}*")
                    else:
                        st.write("No notes yet.")
                        
                    new_note = st.text_area("Add a Note:")
                    if st.button("Save Note"):
                        if new_note:
                            add_candidate_note(selected_cand['candidate_id'], 1, new_note)
                            st.success("Note added!")
                            st.rerun()
                            
            st.markdown("---")
            st.markdown("### 📧 AI Email Automation")
            st.write("Generate personalized communication based on candidate ATS context.")
            
            if selected_cand:
                from backend.services.communication_service import EmailType
                from backend.api.routes.communication import draft_email, EmailDraftRequest, send_email, SendEmailRequest
                
                e_col1, e_col2 = st.columns([1, 2])
                with e_col1:
                    email_type_str = st.selectbox("Select Email Type:", [e.value for e in EmailType])
                    email_context = st.text_area("Additional Context (e.g., 'Include calendar link'):")
                    
                    if st.button("Generate Email Draft"):
                        with st.spinner("AI is crafting the perfect email..."):
                            try:
                                draft_payload = EmailDraftRequest(email_type=EmailType(email_type_str), context=email_context)
                                draft_res = draft_email(selected_cand['candidate_id'], job_id, draft_payload)
                                st.session_state['current_email_subject'] = draft_res.subject
                                st.session_state['current_email_body'] = draft_res.body
                            except Exception as e:
                                st.error(f"Failed to draft email: {e}")
                
                with e_col2:
                    if 'current_email_subject' in st.session_state:
                        final_subject = st.text_input("Subject Line:", st.session_state['current_email_subject'])
                        final_body = st.text_area("Email Body:", st.session_state['current_email_body'], height=250)
                        
                        if st.button("🚀 Send Email (Simulated)"):
                            try:
                                # For demonstration, we assume a mock email like "candidate@example.com"
                                send_payload = SendEmailRequest(subject=final_subject, body=final_body, to_email="candidate@example.com")
                                send_email(send_payload)
                                st.success("Email successfully dispatched via provider!")
                            except Exception as e:
                                st.error(f"Failed to send email: {e}")
    else:
        st.info("Upload candidates and run bulk analysis in Tab 3 to view the ATS pipeline.")

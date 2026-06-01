import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from backend.utils import extract_text_from_file, preprocess_text, load_skills
from backend.parsers.resume_parser import parse_resume
from backend.parsers.jd_parser import parse_jd
from backend.scoring import calculate_match
from backend.parsers.ats_analyzer import analyze_resume_ats

# --- Dashboard Configuration ---
st.set_page_config(page_title="AI Recruiter | Resume Matcher & ATS Optimizer", page_icon="🤖", layout="wide")

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
    </style>
""", unsafe_allow_html=True)

# Load global skills once
@st.cache_data
def get_global_skills():
    return load_skills()

PREDEFINED_SKILLS = get_global_skills()

# --- Main Header ---
st.title("🤖 AI Recruiter Assistant")
st.markdown("Smart Resume-to-Job Matching & ATS Optimization Hub powered by internal NLP logic.")

# --- File Inputs ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF or TXT file", type=["pdf", "txt"])

with col2:
    st.subheader("2. Job Description")
    job_desc = st.text_area("Paste the target job description here...", height=130)

if st.button("Run Full Recruitment Analysis"):
    if uploaded_file is not None:
        with st.spinner("Analyzing resume structure and computing job matching..."):
            try:
                # 1. Extract Text
                file_bytes = uploaded_file.read()
                raw_text = extract_text_from_file(file_bytes, uploaded_file.name)
                
                # 2. Parse Structures
                parsed_resume = parse_resume(raw_text, PREDEFINED_SKILLS)
                parsed_jd = parse_jd(job_desc, PREDEFINED_SKILLS) if job_desc else None
                
                # 3. Analyze ATS (Phase 2)
                ats_analysis = analyze_resume_ats(raw_text, parsed_resume, uploaded_file.name)
                
                # 4. Analyze Job Matching (Phase 1) - Only if job description is provided
                match_analysis = None
                if job_desc:
                    clean_resume = preprocess_text(raw_text)
                    clean_jd = preprocess_text(job_desc)
                    match_analysis = calculate_match(
                        resume=parsed_resume,
                        jd=parsed_jd,
                        clean_resume_text=clean_resume,
                        clean_jd_text=clean_jd
                    )
                
                st.success("Analysis Complete!")
                
                # Setup Tabs
                if match_analysis:
                    tab1, tab2 = st.tabs(["🎯 Job Match Analysis", "📊 ATS Resume Optimizer"])
                else:
                    tab1 = None
                    # If no JD is provided, default directly to ATS tab
                    st.info("Provide a Job Description to enable Job Match Analysis.")
                    tab2_container = st.container()
                
                # --- Tab 1: Job Matcher (Phase 1) ---
                if match_analysis and tab1:
                    with tab1:
                        st.markdown("### 🧬 Weighted Suitability Breakdown")
                        
                        # Top level metrics
                        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
                        with m_col1:
                            st.markdown(
                                f"<div class='metric-card'><h4>Overall Match</h4><div class='score-text'>{match_analysis.final_score}%</div><p style='color:#a5b4fc; font-weight:600;'>Weighted Total</p></div>", 
                                unsafe_allow_html=True
                            )
                        with m_col2:
                            st.markdown(
                                f"<div class='metric-card'><h4>Semantic Match</h4><div class='score-text' style='font-size:2.5rem; color:#818cf8;'>{match_analysis.semantic_score}%</div><p style='color:#94a3b8;'>40% Weight</p></div>", 
                                unsafe_allow_html=True
                            )
                        with m_col3:
                            st.markdown(
                                f"<div class='metric-card'><h4>Skills Match</h4><div class='score-text' style='font-size:2.5rem; color:#a78bfa;'>{match_analysis.skill_score}%</div><p style='color:#94a3b8;'>30% Weight</p></div>", 
                                unsafe_allow_html=True
                            )
                        with m_col4:
                            st.markdown(
                                f"<div class='metric-card'><h4>Experience Match</h4><div class='score-text' style='font-size:2.5rem; color:#c084fc;'>{match_analysis.experience_score}%</div><p style='color:#94a3b8;'>20% Weight</p></div>", 
                                unsafe_allow_html=True
                            )
                        with m_col5:
                            st.markdown(
                                f"<div class='metric-card'><h4>Education Match</h4><div class='score-text' style='font-size:2.5rem; color:#f472b6;'>{match_analysis.education_score}%</div><p style='color:#94a3b8;'>10% Weight</p></div>", 
                                unsafe_allow_html=True
                            )
                            
                        st.markdown("---")
                        
                        det_col1, det_col2 = st.columns([1, 1])
                        
                        with det_col1:
                            st.markdown("### 🎯 Skill & Requirement Gap Analysis")
                            
                            st.markdown("**Matched Skills (Skills present in both JD and Resume):**")
                            if match_analysis.matched_skills:
                                pills_html = "".join([f"<span class='pill pill-success'>{skill}</span>" for skill in match_analysis.matched_skills])
                                st.markdown(pills_html, unsafe_allow_html=True)
                            else:
                                st.write("None found.")
                                
                            st.markdown("<br>**Missing Skills (Skills in JD but missing in Resume):**", unsafe_allow_html=True)
                            if match_analysis.missing_skills:
                                pills_html = "".join([f"<span class='pill pill-warning'>{skill}</span>" for skill in match_analysis.missing_skills])
                                st.markdown(pills_html, unsafe_allow_html=True)
                            else:
                                st.write("None found.")
                                
                        with det_col2:
                            st.markdown("### 💡 AI Recommendations")
                            st.markdown(f"<div class='recommendation-card'><strong>Explanation:</strong><br>{match_analysis.explanation}</div>", unsafe_allow_html=True)
                            
                            # Additional suggestions
                            st.markdown("<br>**Action Items:**", unsafe_allow_html=True)
                            if match_analysis.missing_skills:
                                st.markdown(f"- Add missing skills to resume if you have them: **{', '.join(match_analysis.missing_skills[:3]).title()}**")
                            if parsed_resume.total_experience_years < parsed_jd.experience_requirements:
                                st.markdown(f"- Target roles requiring **{parsed_resume.total_experience_years} years** or elaborate more on your project/internship years.")
                            if match_analysis.final_score >= 80:
                                st.markdown("- Standout applicant! Review company culture and prepare technical stories.")
                
                # --- Tab 2: ATS Optimizer (Phase 2) ---
                ats_tab = tab2 if match_analysis else tab2_container
                with ats_tab:
                    st.markdown("### 📊 ATS structural Integrity Check")
                    
                    ats_col1, ats_col2 = st.columns([1, 1.2])
                    
                    with ats_col1:
                        # 1. Circular gauge chart for ATS Score
                        fig_gauge = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = ats_analysis.ats_score,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': "ATS Structural Score", 'font': {'size': 20, 'color': "#f8fafc"}},
                            gauge = {
                                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#94a3b8"},
                                'bar': {'color': "#6366f1"},
                                'bgcolor': "rgba(30, 41, 59, 0.5)",
                                'borderwidth': 2,
                                'bordercolor': "rgba(99, 102, 241, 0.3)",
                                'steps': [
                                    {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.15)'},
                                    {'range': [50, 80], 'color': 'rgba(245, 158, 11, 0.15)'},
                                    {'range': [80, 100], 'color': 'rgba(16, 185, 129, 0.15)'}
                                ],
                            }
                        ))
                        fig_gauge.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font={'color': "#f8fafc", 'family': "Arial"},
                            height=320,
                            margin=dict(l=20, r=20, t=50, b=20)
                        )
                        st.plotly_chart(fig_gauge, use_container_width=True)
                        
                    with ats_col2:
                        # 2. Horizontal Bar Chart for Strength breakdown
                        breakdown = ats_analysis.strength_breakdown
                        categories = ['Tech Skills', 'Projects', 'Experience', 'Achievements', 'Certifications']
                        scores = [
                            breakdown.technical_skills,
                            breakdown.projects,
                            breakdown.experience,
                            breakdown.achievements,
                            breakdown.certifications
                        ]
                        
                        df_strength = pd.DataFrame(dict(
                            Score=scores,
                            Category=categories
                        ))
                        
                        fig_bar = px.bar(
                            df_strength, 
                            x='Score', 
                            y='Category', 
                            orientation='h',
                            title="Resume Category Strengths",
                            color='Score',
                            color_continuous_scale=['#f43f5e', '#fbbf24', '#10b981'],
                            range_x=[0, 100]
                        )
                        
                        fig_bar.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(30, 41, 59, 0.3)',
                            font_color="#f8fafc",
                            height=320,
                            margin=dict(l=20, r=20, t=50, b=20),
                            coloraxis_showscale=False
                        )
                        
                        fig_bar.update_yaxes(gridcolor='rgba(255,255,255,0.05)')
                        fig_bar.update_xaxes(gridcolor='rgba(255,255,255,0.05)')
                        
                        st.plotly_chart(fig_bar, use_container_width=True)
                        
                    st.markdown("---")
                    
                    # AI Recruiter Feedback Layout
                    st.markdown("### 📋 AI Recruiter Feedback")
                    f_col1, f_col2 = st.columns(2)
                    
                    with f_col1:
                        st.markdown("**🛡️ Detected Strengths:**")
                        for s in ats_analysis.strengths:
                            st.markdown(
                                f"<div class='feedback-box feedback-success'>👍 {s}</div>", 
                                unsafe_allow_html=True
                            )
                            
                    with f_col2:
                        st.markdown("**⚠️ Areas of Improvement:**")
                        for w in ats_analysis.weaknesses:
                            st.markdown(
                                f"<div class='feedback-box feedback-warning'>💡 {w}</div>", 
                                unsafe_allow_html=True
                            )
                            
                    # Hiring Recommendation
                    st.markdown("<div class='recommendation-card'><h3>💼 Recruiter Decision Summary</h3>"
                                f"<p style='font-size:1.15rem; line-height:1.6;'>{ats_analysis.recommendation}</p></div>", 
                                unsafe_allow_html=True)
                    
                    # Extra details from parser
                    st.markdown("<br><h4>🔎 Extracted Metadata</h4>", unsafe_allow_html=True)
                    meta_col1, meta_col2, meta_col3 = st.columns(3)
                    with meta_col1:
                        st.info(f"**Contact Name:** {parsed_resume.name or 'Not Found'}")
                        st.info(f"**Contact Email:** {parsed_resume.email or 'Not Found'}")
                    with meta_col2:
                        st.info(f"**Contact Phone:** {parsed_resume.phone or 'Not Found'}")
                        st.info(f"**Highest Education:** {parsed_resume.highest_education_level or 'Not Found'}")
                    with meta_col3:
                        st.info(f"**Years of Experience:** {parsed_resume.total_experience_years} years")
                        st.info(f"**Total Extracted Skills:** {len(parsed_resume.skills)}")

            except Exception as e:
                st.error(f"Error processing document: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    else:
        st.warning("Please upload a resume to proceed with analysis.")

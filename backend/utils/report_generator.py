import json
from typing import Dict, Any, List

def generate_candidate_html_report(
    candidate: Dict[str, Any],
    match_result: Dict[str, Any],
    questions: Dict[str, Dict[str, List[str]]]
) -> str:
    """
    Renders a clean, corporate, print-friendly candidate report in HTML.
    Includes print stylesheets so it converts to PDF perfectly via browser print.
    """
    
    # Format skills lists
    skills_html = "".join([f"<span class='pill pill-success'>{s.title()}</span>" for s in candidate['skills']])
    missing_skills = match_result.get('missing_skills', [])
    missing_html = "".join([f"<span class='pill pill-warning'>{s.title()}</span>" for s in missing_skills]) if missing_skills else "None"
    
    # Format strengths and weaknesses
    strengths_list = match_result.get('strengths', [])
    strengths_html = "".join([f"<li>👍 {s}</li>" for s in strengths_list]) if strengths_list else "<li>No specific strengths recorded.</li>"
    
    weaknesses_list = match_result.get('weaknesses', [])
    weaknesses_html = "".join([f"<li>💡 {s}</li>" for s in weaknesses_list]) if weaknesses_list else "<li>No specific areas of improvement recorded.</li>"
    
    # Format interview questions
    questions_html = ""
    for skill, levels in questions.items():
        questions_html += f"""
        <div class='skill-section'>
            <h4>Technology: {skill}</h4>
            <div class='q-grid'>
                <div class='q-level'>
                    <h5>Green / Beginner</h5>
                    <ul>{"".join([f"<li>{q}</li>" for q in levels['Beginner']])}</ul>
                </div>
                <div class='q-level'>
                    <h5>Yellow / Intermediate</h5>
                    <ul>{"".join([f"<li>{q}</li>" for q in levels['Intermediate']])}</ul>
                </div>
                <div class='q-level'>
                    <h5>Red / Advanced</h5>
                    <ul>{"".join([f"<li>{q}</li>" for q in levels['Advanced']])}</ul>
                </div>
            </div>
        </div>
        """
        
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Recruitment Report Card - {candidate['name']}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                color: #1e293b;
                line-height: 1.5;
                margin: 40px;
                background-color: #ffffff;
            }}
            .header {{
                border-bottom: 3px solid #6366f1;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                margin: 0;
                color: #0f172a;
                font-size: 2.2rem;
            }}
            .header p {{
                margin: 5px 0 0 0;
                color: #64748b;
                font-size: 1.1rem;
            }}
            .score-container {{
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
            }}
            .score-card {{
                flex: 1;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                background-color: #f8fafc;
            }}
            .score-card h3 {{
                margin: 0;
                color: #64748b;
                font-size: 1rem;
                text-transform: uppercase;
            }}
            .score-num {{
                font-size: 3rem;
                font-weight: bold;
                color: #6366f1;
                margin: 10px 0;
            }}
            .section {{
                margin-bottom: 35px;
                page-break-inside: avoid;
            }}
            .section h3 {{
                border-bottom: 1px solid #cbd5e1;
                padding-bottom: 8px;
                color: #0f172a;
                font-size: 1.3rem;
                margin-bottom: 15px;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }}
            .info-item strong {{
                color: #475569;
            }}
            .pill {{
                display: inline-block;
                padding: 4px 10px;
                margin: 3px;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: bold;
            }}
            .pill-success {{
                background-color: #d1fae5;
                color: #065f46;
                border: 1px solid #a7f3d0;
            }}
            .pill-warning {{
                background-color: #fef3c7;
                color: #92400e;
                border: 1px solid #fde68a;
            }}
            .feedback-lists {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }}
            .feedback-column ul {{
                padding-left: 20px;
                margin: 0;
            }}
            .feedback-column li {{
                margin-bottom: 8px;
            }}
            .recommendation-banner {{
                background-color: #eff6ff;
                border-left: 6px solid #3b82f6;
                padding: 15px;
                border-radius: 0 8px 8px 0;
                margin-top: 15px;
            }}
            .skill-section {{
                margin-bottom: 25px;
                page-break-inside: avoid;
            }}
            .skill-section h4 {{
                margin: 0 0 10px 0;
                color: #334155;
            }}
            .q-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 15px;
            }}
            .q-level {{
                background: #f8fafc;
                border: 1px solid #f1f5f9;
                border-radius: 6px;
                padding: 12px;
            }}
            .q-level h5 {{
                margin: 0 0 8px 0;
                font-size: 0.95rem;
                color: #475569;
            }}
            .q-level ul {{
                padding-left: 15px;
                margin: 0;
                font-size: 0.85rem;
            }}
            .q-level li {{
                margin-bottom: 6px;
            }}
            
            /* Print CSS rules */
            @media print {{
                body {{
                    margin: 20px;
                    font-size: 12pt;
                }}
                .header {{
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                .score-num {{
                    font-size: 2.5rem;
                }}
                .section {{
                    page-break-inside: avoid;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Candidate Recruitment Scorecard</h1>
            <p>Report Generated for candidate: <strong>{candidate['name']}</strong></p>
        </div>
        
        <div class="score-container">
            <div class="score-card">
                <h3>Overall Match Score</h3>
                <div class="score-num">{match_result['final_score']}%</div>
                <p style="margin:0; color:#64748b;">Job Description Suitability</p>
            </div>
            <div class="score-card">
                <h3>ATS Compliance Score</h3>
                <div class="score-num">{match_result['ats_score']}%</div>
                <p style="margin:0; color:#64748b;">Resume Structural Completeness</p>
            </div>
        </div>
        
        <div class="section">
            <h3>👤 Candidate Profile Summary</h3>
            <div class="info-grid">
                <div class="info-item"><strong>Email:</strong> {candidate['email'] or 'Not Provided'}</div>
                <div class="info-item"><strong>Phone:</strong> {candidate['phone'] or 'Not Provided'}</div>
                <div class="info-item"><strong>Highest Education:</strong> {candidate['highest_education_level']}</div>
                <div class="info-item"><strong>Total Experience Tenure:</strong> {candidate['total_experience_years']} Years</div>
            </div>
        </div>
        
        <div class="section">
            <h3>🛡️ Technical Skills Matrix</h3>
            <div style="margin-bottom: 15px;">
                <strong>Identified Skills:</strong><br>
                {skills_html}
            </div>
            <div>
                <strong>Missing Requirements Gap:</strong><br>
                {missing_html}
            </div>
        </div>
        
        <div class="section">
            <h3>📋 AI Recruiter Evaluation & Feedback</h3>
            <div class="feedback-lists">
                <div class="feedback-column">
                    <strong>Strong Selling Points:</strong>
                    <ul>{strengths_html}</ul>
                </div>
                <div class="feedback-column">
                    <strong>Areas of Improvement:</strong>
                    <ul>{weaknesses_html}</ul>
                </div>
            </div>
            <div class="recommendation-banner">
                <strong>Hiring Recommendation Summary:</strong><br>
                {match_result['recommendation']}
            </div>
        </div>
        
        <div class="section">
            <h3>🎙️ Customized Skill-Based Interview Guidelines</h3>
            {questions_html}
        </div>
    </body>
    </html>
    """
    return html_template

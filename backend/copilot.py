import re
import json
import sqlite3
from typing import Dict, Any, List

def answer_copilot_query(query: str, job_id: int = None, db_path: str = "data/recruiter.db") -> str:
    """
    Analyzes recruiter query, runs SQLite lookups, and compiles a natural-language response.
    """
    query_lower = query.lower().strip()
    
    # Connect to DB
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if database has any jobs/candidates
        cursor.execute("SELECT COUNT(*) FROM candidates")
        candidate_count = cursor.fetchone()[0]
        if candidate_count == 0:
            return "No candidates found in the database. Please upload candidates in the Recruiter Workflow tab first."
            
        # Get active Job ID if not specified
        if not job_id:
            cursor.execute("SELECT id FROM jobs ORDER BY created_at DESC LIMIT 1")
            job_row = cursor.fetchone()
            if job_row:
                job_id = job_row["id"]
            else:
                return "No jobs registered in the system. Please upload a job description first."
                
        # 1. Query: "Why is Candidate A ranked first?"
        if "ranked first" in query_lower or "rank 1" in query_lower or "top candidate" in query_lower or "best candidate" in query_lower:
            cursor.execute("""
                SELECT c.name, mr.final_score, mr.ats_score, mr.explanation, mr.recommendation 
                FROM match_results mr
                JOIN candidates c ON mr.candidate_id = c.id
                WHERE mr.job_id = ?
                ORDER BY mr.final_score DESC, mr.ats_score DESC
                LIMIT 1
            """, (job_id,))
            row = cursor.fetchone()
            if row:
                return (
                    f"**{row['name']}** is ranked first because they achieved the highest overall Match Score of **{row['final_score']}%** "
                    f"and an ATS Compliance Score of **{row['ats_score']}%**. \n\n"
                    f"**Analysis Summary:** {row['explanation']}\n\n"
                    f"**Hiring Recommendation:** {row['recommendation']}"
                )
            return "Could not determine the top candidate for this job."

        # 2. Query: "Which candidates know [Skill]?"
        # Match "know aws", "know python", "have docker" etc.
        skill_match = re.search(r'(?:know|have|knows|with|experience in)\s+([a-zA-Z0-9\+\#\.\-]+)', query_lower)
        if skill_match or any(keyword in query_lower for keyword in ["who knows", "candidates with", "skills of"]):
            target_skill = skill_match.group(1) if skill_match else query_lower.split()[-1]
            target_skill = target_skill.replace("?", "").strip()
            
            cursor.execute("SELECT name, skills FROM candidates")
            rows = cursor.fetchall()
            matching_candidates = []
            for r in rows:
                skills_list = json.loads(r["skills"]) if r["skills"] else []
                if any(target_skill in s.lower() for s in skills_list):
                    matching_candidates.append(r["name"])
                    
            if matching_candidates:
                return f"The following candidates possess **{target_skill.upper()}** in their profile: \n\n" + \
                       "\n".join([f"- {name}" for name in matching_candidates])
            return f"No candidates in the database were found with skills matching **{target_skill.upper()}**."

        # 3. Query: "Compare top candidates."
        if "compare top" in query_lower or "compare rank" in query_lower or "difference between top" in query_lower:
            cursor.execute("""
                SELECT c.id, c.name, mr.final_score, mr.ats_score 
                FROM match_results mr
                JOIN candidates c ON mr.candidate_id = c.id
                WHERE mr.job_id = ?
                ORDER BY mr.final_score DESC, mr.ats_score DESC
                LIMIT 2
            """, (job_id,))
            rows = cursor.fetchall()
            if len(rows) >= 2:
                from backend.scoring import generate_comparison_summary
                from backend.database import get_candidate_details
                
                a_details = get_candidate_details(rows[0]["id"], job_id, db_path)
                b_details = get_candidate_details(rows[1]["id"], job_id, db_path)
                
                summary = generate_comparison_summary(a_details, b_details)
                return (
                    f"### Side-by-Side Comparison of Top 2 Candidates:\n\n"
                    f"1. **{rows[0]['name']}** - Match: **{rows[0]['final_score']}%** | ATS: **{rows[0]['ats_score']}%**\n"
                    f"2. **{rows[1]['name']}** - Match: **{rows[1]['final_score']}%** | ATS: **{rows[1]['ats_score']}%**\n\n"
                    f"**Recruiter Comparison:** \"{summary}\""
                )
            elif len(rows) == 1:
                return f"Only one candidate (**{rows[0]['name']}**) has been analyzed for this position. Cannot run comparison."
            return "No candidates found to compare."

        # 4. Query: "Show missing skills trends."
        if "missing skill" in query_lower or "skill gap" in query_lower or "talent gap" in query_lower or "trends" in query_lower:
            # Aggregate all missing skills
            # We can re-fetch job description and compute gap counts
            cursor.execute("SELECT description FROM jobs WHERE id = ?", (job_id,))
            jd_row = cursor.fetchone()
            if not jd_row:
                return "Could not retrieve the active job requirements."
                
            from backend.parsers.jd_parser import parse_jd
            parsed_jd = parse_jd(jd_row[0], [])
            all_jd_skills = set([s.lower() for s in parsed_jd.required_skills + parsed_jd.preferred_skills])
            
            cursor.execute("""
                SELECT c.skills 
                FROM match_results mr
                JOIN candidates c ON mr.candidate_id = c.id
                WHERE mr.job_id = ?
            """, (job_id,))
            candidate_rows = cursor.fetchall()
            
            if not candidate_rows:
                return "No candidate match records found to analyze trends."
                
            gap_counts = {}
            for row in candidate_rows:
                cand_skills = set([s.lower() for s in json.loads(row["skills"]) if row["skills"]])
                missing = all_jd_skills.difference(cand_skills)
                for skill in missing:
                    gap_counts[skill] = gap_counts.get(skill, 0) + 1
                    
            if gap_counts:
                sorted_gaps = sorted(gap_counts.items(), key=lambda x: x[1], reverse=True)
                total_cands = len(candidate_rows)
                trend_lines = []
                for skill, count in sorted_gaps[:5]:
                    pct = round((count / total_cands) * 100, 1)
                    trend_lines.append(f"- **{skill.title()}**: Missing in **{pct}%** of candidates ({count}/{total_cands})")
                return (
                    f"### 📈 Talent Gap & Missing Skill Trends:\n"
                    f"Based on analyzing {total_cands} profiles for this job, the most common missing skills are:\n\n" +
                    "\n".join(trend_lines) + 
                    "\n\n**Actionable Advice:** Consider setting up targeted upskilling roadmaps in these areas or adjusting search keywords."
                )
            return "No skill gaps detected. All candidates possess 100% of the requested technologies."

        # Fallback conversational response
        return (
            "I am your Recruiter Copilot. You can ask me:\n"
            "- *Why is Candidate A ranked first?*\n"
            "- *Which candidates know Python (or other skills)?*\n"
            "- *Compare top candidates.*\n"
            "- *Show missing skills trends.*"
        )
        
    except Exception as e:
        return f"Sorry, I encountered an error while retrieving database context: {str(e)}"
    finally:
        conn.close()

import { useState } from 'react';
import { FileText, CheckCircle, AlertTriangle, ShieldAlert } from 'lucide-react';
import { api } from '../api';

function Matcher() {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!resumeFile || !jobDescription) {
      alert("Please provide both a resume PDF/TXT and a job description.");
      return;
    }
    
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("resume", resumeFile);
      formData.append("job_description", jobDescription);

      const response = await api.post('/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const data = response.data;
      setResult({
        score: data.match_score || Math.round(data.scoring?.final_score || 0),
        risk: data.parsed_resume?.risk_level || 'Low',
        strengths: data.matched_skills || ['Matches job requirements'],
        weaknesses: data.missing_skills || ['None detected'],
        recommendation: (data.recommendations && data.recommendations.join(" ")) || 'Proceed to review.'
      });
    } catch (err) {
      console.error(err);
      alert("Failed to analyze resume. Check console.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '8px' }}>AI Job Matcher & Optimizer</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Evaluate structural ATS compliance and job description alignment.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        
        {/* Input Form */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: '500', marginBottom: '8px' }}>1. Upload Candidate Resume</label>
            <input 
              type="file" 
              accept=".pdf,.txt"
              onChange={(e) => setResumeFile(e.target.files ? e.target.files[0] : null)}
              style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: '500', marginBottom: '8px' }}>2. Target Job Description</label>
            <textarea 
              rows={8} 
              placeholder="Paste job description here..."
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', outline: 'none', resize: 'vertical' }}
            />
          </div>

          <button className="btn-primary" onClick={handleAnalyze} disabled={loading} style={{ padding: '14px', fontSize: '16px' }}>
            {loading ? 'Analyzing with AI...' : 'Run Advanced ATS Analysis'}
          </button>
        </div>

        {/* Results Panel */}
        <div className="card" style={{ background: result ? 'var(--bg-secondary)' : '#f1f5f9', display: 'flex', flexDirection: 'column', justifyContent: result ? 'flex-start' : 'center', alignItems: result ? 'stretch' : 'center' }}>
          {!result && !loading && (
            <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
              <FileText size={48} color="var(--border-color)" style={{ marginBottom: '16px' }} />
              <h3>Awaiting Input</h3>
              <p>Fill out the fields and run analysis to see insights.</p>
            </div>
          )}

          {loading && (
            <div style={{ textAlign: 'center', color: 'var(--primary-color)' }}>
              <div className="loader" style={{ width: '40px', height: '40px', border: '3px solid var(--primary-light)', borderTopColor: 'var(--primary-color)', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }}></div>
              <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
              <h3>Processing via NLP Pipeline...</h3>
            </div>
          )}

          {result && !loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '24px', borderBottom: '1px solid var(--border-color)' }}>
                <div>
                  <h3 style={{ fontSize: '18px', color: 'var(--text-secondary)' }}>Overall ATS Match Score</h3>
                  <div style={{ fontSize: '48px', fontWeight: '800', color: 'var(--primary-color)' }}>{result.score}%</div>
                </div>
                <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--success-color)', fontWeight: '600', marginBottom: '4px' }}>
                    <ShieldAlert size={20} /> Candidate Risk: {result.risk}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>No chronological gaps detected</div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div style={{ background: 'rgba(16, 185, 129, 0.05)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.1)' }}>
                  <h4 style={{ color: 'var(--success-color)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}><CheckCircle size={16} /> Key Strengths</h4>
                  <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '14px', color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {result.strengths.map((s: string, i: number) => <li key={i}>{s}</li>)}
                  </ul>
                </div>
                
                <div style={{ background: 'rgba(245, 158, 11, 0.05)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.1)' }}>
                  <h4 style={{ color: 'var(--warning-color)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}><AlertTriangle size={16} /> Missing Keywords</h4>
                  <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '14px', color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {result.weaknesses.map((w: string, i: number) => <li key={i}>{w}</li>)}
                  </ul>
                </div>
              </div>

              <div style={{ background: 'var(--bg-primary)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <h4 style={{ marginBottom: '8px' }}>AI Recruiter Decision</h4>
                <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{result.recommendation}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Matcher;

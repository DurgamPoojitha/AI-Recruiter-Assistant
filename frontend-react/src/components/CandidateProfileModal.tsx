import { useState, useEffect } from 'react';
import { X, ShieldAlert, Award, Briefcase, GraduationCap, Code } from 'lucide-react';
import { api } from '../api';

interface CandidateProfileModalProps {
  candidateId: number;
  jobId: number;
  onClose: () => void;
}

export function CandidateProfileModal({ candidateId, jobId, onClose }: CandidateProfileModalProps) {
  const [prepData, setPrepData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPrep = async () => {
      try {
        const res = await api.get(`/ats/candidates/${candidateId}/interview-prep?job_id=${jobId}`);
        setPrepData(res.data);
      } catch (err) {
        console.error("Failed to fetch interview prep", err);
      } finally {
        setLoading(false);
      }
    };
    fetchPrep();
  }, [candidateId, jobId]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="profile-modal-content" onClick={e => e.stopPropagation()}>
        <div style={{ padding: '24px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-primary)' }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600' }}>Candidate Deep Dive</h2>
          <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }} onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div className="skeleton skeleton-card" style={{ height: '80px' }}></div>
              <div className="skeleton skeleton-card" style={{ height: '200px' }}></div>
              <div className="skeleton skeleton-card" style={{ height: '200px' }}></div>
            </div>
          ) : prepData ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
              
              {/* Header Info */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                <div className="avatar" style={{ width: '80px', height: '80px', fontSize: '32px' }}>
                  {prepData.candidate_name.split(' ').map((n: string) => n[0]).join('').substring(0, 2).toUpperCase()}
                </div>
                <div>
                  <h1 style={{ fontSize: '28px', marginBottom: '8px' }}>{prepData.candidate_name}</h1>
                  <p style={{ color: 'var(--text-secondary)', background: 'var(--primary-light)', color: 'var(--primary-color)', padding: '4px 12px', borderRadius: '16px', display: 'inline-block', fontWeight: '500', fontSize: '13px' }}>
                    {prepData.recommended_focus}
                  </p>
                </div>
              </div>

              {/* Technical Validation Questions (Existing Skills) */}
              {prepData.technical_validation_questions && Object.keys(prepData.technical_validation_questions).length > 0 && (
                <div>
                  <h3 style={{ fontSize: '18px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                    <Code size={20} color="var(--primary-color)" /> Technical Validation (Reported Skills)
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {Object.entries(prepData.technical_validation_questions).map(([skill, levels]: [string, any]) => (
                      <div key={skill} className="card" style={{ padding: '16px' }}>
                        <h4 style={{ fontSize: '16px', marginBottom: '12px' }}>{skill}</h4>
                        <ul style={{ margin: 0, paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          <li><strong>Beginner:</strong> {levels.Beginner[0]}</li>
                          <li><strong>Intermediate:</strong> {levels.Intermediate[0]}</li>
                          <li><strong>Advanced:</strong> {levels.Advanced[0]}</li>
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Skill Gap Analysis (Missing Skills) */}
              {prepData.skill_gap_analysis && Object.keys(prepData.skill_gap_analysis).length > 0 && (
                <div>
                  <h3 style={{ fontSize: '18px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                    <ShieldAlert size={20} color="var(--warning-color)" /> Skill Gap & Learning Roadmap
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '16px' }}>
                    {Object.entries(prepData.skill_gap_analysis).map(([skill, data]: [string, any]) => (
                      <div key={skill} className="card" style={{ padding: '16px', borderLeft: '4px solid var(--warning-color)' }}>
                        <h4 style={{ fontSize: '16px', marginBottom: '8px' }}>Missing: {skill}</h4>
                        <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                          <strong>Suggested Interview Question:</strong> "We use {skill} heavily. How would you approach getting up to speed on this technology in your first 30 days?"
                        </div>
                        <div style={{ background: 'var(--bg-primary)', padding: '12px', borderRadius: '8px' }}>
                          <h5 style={{ fontSize: '12px', textTransform: 'uppercase', marginBottom: '8px', color: 'var(--text-primary)' }}>Suggested Learning Roadmap</h5>
                          <ul style={{ margin: 0, paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '13px' }}>
                            {data.roadmap.map((step: string, i: number) => <li key={i}>{step}</li>)}
                          </ul>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
              Could not load candidate details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

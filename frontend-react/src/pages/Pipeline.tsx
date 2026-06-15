import { useState, useEffect } from 'react';
import { Plus } from 'lucide-react';
import { api } from '../api';

function Pipeline() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [pipeline, setPipeline] = useState<any>(null);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const res = await api.get('/ats/jobs');
        setJobs(res.data.jobs);
        if (res.data.jobs.length > 0) {
          setSelectedJob(res.data.jobs[0]);
        }
      } catch (err) {
        console.error("Failed to fetch jobs:", err);
      }
    };
    fetchJobs();
  }, []);

  useEffect(() => {
    if (!selectedJob) return;
    const fetchPipeline = async () => {
      try {
        const res = await api.get(`/ats/jobs/${selectedJob.id}/pipeline`);
        setPipeline(res.data.pipeline);
      } catch (err) {
        console.error("Failed to fetch pipeline:", err);
      }
    };
    fetchPipeline();
  }, [selectedJob]);

  const stages = ['Applied', 'Screening', 'Interview', 'Offer', 'Hired'];

  const getStageCount = (stage: string) => {
    if (!pipeline) return 0;
    return pipeline[stage] ? pipeline[stage].length : 0;
  };

  const isEmpty = !pipeline || Object.values(pipeline).every((arr: any) => arr.length === 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          {jobs.length > 0 ? (
            <select 
              value={selectedJob?.id || ''} 
              onChange={(e) => setSelectedJob(jobs.find(j => j.id === parseInt(e.target.value)))}
              style={{ fontSize: '20px', fontWeight: '600', padding: '8px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', marginBottom: '4px' }}
            >
              {jobs.map(j => <option key={j.id} value={j.id}>{j.title}</option>)}
            </select>
          ) : (
            <h2 style={{ fontSize: '20px', fontWeight: '600' }}>Loading Jobs...</h2>
          )}
          <p style={{ color: 'var(--text-secondary)' }}>
            {selectedJob ? `Req ID: #ENG-${selectedJob.id} • Posted: ${selectedJob.created_at}` : 'Select a job to view the pipeline'}
          </p>
        </div>
        <button className="btn-primary">
          <Plus size={18} /> Add Candidate
        </button>
      </div>

      {/* Kanban Board Headers */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px', marginBottom: '16px' }}>
        {stages.map(stage => (
          <div key={stage} style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', fontWeight: '600', fontSize: '14px', color: 'var(--text-secondary)' }}>
            {stage} ({getStageCount(stage)})
          </div>
        ))}
      </div>

      {/* Kanban Board Columns or Empty State */}
      {isEmpty ? (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-secondary)', borderRadius: '12px', border: '1px dashed var(--border-color)' }}>
          <img src="/empty_state.png" alt="Empty Pipeline" style={{ width: '400px', opacity: 0.8, marginBottom: '24px' }} />
          <h3 style={{ fontSize: '20px', marginBottom: '8px' }}>No candidates in the pipeline yet</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '400px', textAlign: 'center', marginBottom: '24px' }}>
            Your recruitment pipeline is ready. Start sourcing talent and add candidates to see them flow through your stages.
          </p>
          <button className="btn-secondary">Import from LinkedIn</button>
        </div>
      ) : (
        <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px', alignItems: 'start' }}>
          {stages.map(stage => (
            <div key={stage} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {(pipeline[stage] || []).map((cand: any) => (
                <div key={cand.candidate_id} className="card" style={{ padding: '16px', cursor: 'grab' }}>
                  <div style={{ fontWeight: '600', marginBottom: '4px' }}>{cand.name}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Match: {Math.round(cand.match_score)}%</div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Pipeline;



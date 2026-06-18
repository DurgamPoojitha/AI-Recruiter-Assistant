import { useState, useEffect, useRef } from 'react';
import { Plus, Users, Calendar, TrendingUp, X, UploadCloud, FileText, Filter } from 'lucide-react';
import { api } from '../api';
import { FilterPanel, FilterState } from '../components/FilterPanel';
import { CandidateProfileModal } from '../components/CandidateProfileModal';

function Pipeline() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [pipeline, setPipeline] = useState<any>(null);
  
  // Modal & Slide-over State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Deep Dive Modal State
  const [viewingCandidateId, setViewingCandidateId] = useState<number | null>(null);
  
  // Filtering State
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    skills: [],
    min_experience: 0,
    min_ats_score: 0,
    risk_level: '',
    has_internship: false,
  });

  const fetchJobs = async () => {
    try {
      const res = await api.get('/ats/jobs');
      setJobs(res.data.jobs);
      if (res.data.jobs.length > 0 && !selectedJob) {
        setSelectedJob(res.data.jobs[0]);
      }
    } catch (err) {
      console.error("Failed to fetch jobs:", err);
    }
  };

  const fetchPipeline = async () => {
    if (!selectedJob) return;
    try {
      // Use the new advanced filter endpoint
      const res = await api.post(`/ats/jobs/${selectedJob.id}/candidates/filter`, filters);
      const candidates = res.data.candidates;
      
      // Group by status
      const grouped: any = {
        'Applied': [],
        'Screening': [],
        'Interview': [],
        'Offer': [],
        'Hired': []
      };
      
      candidates.forEach((cand: any) => {
        const status = cand.pipeline_status || 'Applied';
        if (grouped[status]) {
          grouped[status].push(cand);
        } else {
          grouped['Applied'].push(cand);
        }
      });
      
      setPipeline(grouped);
    } catch (err) {
      console.error("Failed to fetch pipeline:", err);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  useEffect(() => {
    fetchPipeline();
  }, [selectedJob, filters]);

  const stages = ['Applied', 'Screening', 'Interview', 'Offer', 'Hired'];

  const getStageCount = (stage: string) => {
    if (!pipeline) return 0;
    return pipeline[stage] ? pipeline[stage].length : 0;
  };

  const isEmpty = !pipeline || Object.values(pipeline).every((arr: any) => arr.length === 0);
  const totalCandidates = pipeline ? Object.values(pipeline).reduce((acc: any, curr: any) => acc + curr.length, 0) : 0;

  // Helpers for UI
  const getInitials = (name: string) => {
    return name.split(' ').map((n: string) => n[0]).join('').substring(0, 2).toUpperCase();
  };

  const getScoreClass = (score: number) => {
    if (score >= 80) return 'high';
    if (score >= 50) return 'medium';
    return 'low';
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile || !selectedJob) return;
    setIsUploading(true);
    
    const formData = new FormData();
    formData.append('resume', selectedFile);
    
    try {
      await api.post(`/ats/jobs/${selectedJob.id}/candidates`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setIsModalOpen(false);
      setSelectedFile(null);
      await fetchPipeline(); // Refresh pipeline
    } catch (error) {
      console.error("Upload failed", error);
      alert("Failed to add candidate. Check console for details.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      {/* Left Filter Sidebar */}
      {showFilters && (
        <FilterPanel 
          onFilterChange={setFilters} 
          availableSkills={['Python', 'React', 'AWS', 'Docker', 'SQL', 'TypeScript', 'Node.js']}
        />
      )}

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '0 0 0 24px', overflow: 'hidden' }}>
        {/* Top Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            {jobs.length > 0 ? (
              <select 
                value={selectedJob?.id || ''} 
                onChange={(e) => setSelectedJob(jobs.find(j => j.id === parseInt(e.target.value)))}
                style={{ fontSize: '24px', fontWeight: '700', padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', marginBottom: '4px', cursor: 'pointer', outline: 'none' }}
              >
                {jobs.map(j => <option key={j.id} value={j.id}>{j.title}</option>)}
              </select>
            ) : (
              <h2 style={{ fontSize: '24px', fontWeight: '700' }}>Loading Jobs...</h2>
            )}
            <p style={{ color: 'var(--text-secondary)', marginLeft: '4px' }}>
              {selectedJob ? `Req ID: #ENG-${selectedJob.id} • Posted: ${selectedJob.created_at.split('T')[0]}` : 'Select a job to view the pipeline'}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn-secondary" onClick={() => setShowFilters(!showFilters)}>
              <Filter size={18} /> Filters {Object.values(filters).some(v => v !== 0 && v !== false && v !== '' && v.length !== 0) && ' (Active)'}
            </button>
            <button className="btn-primary" onClick={() => setIsModalOpen(true)}>
              <Plus size={18} /> Add Candidate
            </button>
          </div>
        </div>

        {/* Analytics Widgets */}
        <div className="analytics-grid">
          <div className="stat-card">
            <div className="stat-icon"><Users size={24} /></div>
            <div className="stat-content">
              <h4>Total Pipeline</h4>
              <div className="stat-value">{totalCandidates as number}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#fef9c3', color: '#a16207' }}><TrendingUp size={24} /></div>
            <div className="stat-content">
              <h4>Shortlisted</h4>
              <div className="stat-value">{getStageCount('Screening')}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#e0e7ff', color: '#4338ca' }}><Calendar size={24} /></div>
            <div className="stat-content">
              <h4>Interviews</h4>
              <div className="stat-value">{getStageCount('Interview')}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#dcfce7', color: '#15803d' }}><Users size={24} /></div>
            <div className="stat-content">
              <h4>Hired</h4>
              <div className="stat-value">{getStageCount('Hired')}</div>
            </div>
          </div>
        </div>

        {/* Kanban Board */}
        {isEmpty ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-secondary)', borderRadius: '12px', border: '1px dashed var(--border-color)', marginBottom: '24px' }}>
            <img src="/empty_state.png" alt="Empty Pipeline" style={{ width: '300px', opacity: 0.8, marginBottom: '24px', filter: 'grayscale(0.5)' }} />
            <h3 style={{ fontSize: '20px', marginBottom: '8px' }}>Pipeline is empty</h3>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '400px', textAlign: 'center', marginBottom: '24px' }}>
              Start sourcing talent by clicking "Add Candidate" above. Their AI-parsed resume will instantly appear here.
            </p>
          </div>
        ) : (
          <div className="kanban-board">
            {stages.map(stage => (
              <div key={stage} className="kanban-column">
                <div className="kanban-column-header">
                  <span>{stage}</span>
                  <span style={{ background: 'var(--border-color)', padding: '2px 8px', borderRadius: '12px', fontSize: '12px' }}>
                    {getStageCount(stage)}
                  </span>
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {(pipeline[stage] || []).map((cand: any) => (
                    <div key={cand.id || cand.candidate_id} className="kanban-card" onClick={() => setViewingCandidateId(cand.id || cand.candidate_id)}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                          <div className="avatar">
                            {getInitials(cand.name || 'Unknown')}
                          </div>
                          <div>
                            <div style={{ fontWeight: '600', fontSize: '14px', color: 'var(--text-primary)' }}>{cand.name || 'Unknown Candidate'}</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>ID: #{cand.id || cand.candidate_id} • {cand.highest_education_level || 'No Degree'}</div>
                          </div>
                        </div>
                      </div>
                      <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span className={`score-badge ${getScoreClass(cand.match_score)}`}>
                          {Math.round(cand.match_score)}% Match
                        </span>
                        {cand.ats_score > 0 && (
                          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>ATS: {Math.round(cand.ats_score)}</span>
                        )}
                        {cand.risk_level === 'High' && (
                          <span style={{ fontSize: '12px', color: 'var(--danger-color)', fontWeight: '600' }}>⚠️ Risk</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Candidate Slide-over Panel */}
      {isModalOpen && (
        <>
          <div className="modal-overlay" onClick={() => !isUploading && setIsModalOpen(false)}></div>
          <div className="slide-panel">
            <div className="slide-panel-header">
              <h2 style={{ fontSize: '20px', fontWeight: '600' }}>Add New Candidate</h2>
              <button style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }} onClick={() => !isUploading && setIsModalOpen(false)}>
                <X size={24} />
              </button>
            </div>
            
            <div className="slide-panel-content">
              <div style={{ marginBottom: '24px' }}>
                <p style={{ fontWeight: '500', marginBottom: '8px' }}>Target Job Profile</p>
                <div style={{ padding: '12px', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-secondary)' }}>
                  {selectedJob?.title}
                </div>
              </div>

              <p style={{ fontWeight: '500', marginBottom: '8px' }}>Upload Resume (PDF, DOCX, TXT)</p>
              
              <input 
                type="file" 
                accept=".pdf,.txt,.docx"
                ref={fileInputRef}
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
              
              {!selectedFile ? (
                <div className="upload-zone" onClick={() => fileInputRef.current?.click()}>
                  <UploadCloud size={48} style={{ color: 'var(--primary-color)', opacity: 0.8, marginBottom: '16px' }} />
                  <p style={{ fontWeight: '500', color: 'var(--text-primary)', marginBottom: '4px' }}>Click or drag file to this area to upload</p>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Support for a single or bulk upload.</p>
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', background: 'var(--primary-light)', border: '1px solid var(--primary-color)', borderRadius: '8px' }}>
                  <FileText style={{ color: 'var(--primary-color)' }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: '500', fontSize: '14px', color: 'var(--text-primary)' }}>{selectedFile.name}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{(selectedFile.size / 1024).toFixed(1)} KB</div>
                  </div>
                  <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }} onClick={() => setSelectedFile(null)}>
                    <X size={16} />
                  </button>
                </div>
              )}
              
              {isUploading && (
                <div style={{ marginTop: '24px', padding: '16px', background: 'var(--bg-primary)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontSize: '14px', fontWeight: '500' }}>AI NLP Analysis in progress...</span>
                    <span style={{ fontSize: '14px', color: 'var(--primary-color)' }}>Parsing</span>
                  </div>
                  <div style={{ height: '6px', background: 'var(--border-color)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: '60%', background: 'var(--primary-color)', animation: 'pulse 1s infinite alternate' }}></div>
                  </div>
                </div>
              )}
            </div>
            
            <div className="slide-panel-footer">
              <button className="btn-secondary" onClick={() => setIsModalOpen(false)} disabled={isUploading}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleUploadSubmit} disabled={!selectedFile || isUploading}>
                {isUploading ? 'Processing...' : 'Add Candidate'}
              </button>
            </div>
          </div>
        </>
      )}

      {/* Candidate Profile Deep Dive Modal */}
      {viewingCandidateId && selectedJob && (
        <CandidateProfileModal 
          candidateId={viewingCandidateId}
          jobId={selectedJob.id}
          onClose={() => setViewingCandidateId(null)}
        />
      )}

    </div>
  );
}

export default Pipeline;



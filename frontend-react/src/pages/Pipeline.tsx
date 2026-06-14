import { Plus } from 'lucide-react';

function Pipeline() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: '600' }}>Senior Frontend Engineer</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Req ID: #ENG-1042 • San Francisco (Hybrid)</p>
        </div>
        <button className="btn-primary">
          <Plus size={18} /> Add Candidate
        </button>
      </div>

      {/* Kanban Board Headers */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px', marginBottom: '16px' }}>
        {['Applied (0)', 'Screening (0)', 'Interview (0)', 'Offer (0)', 'Hired (0)'].map(stage => (
          <div key={stage} style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', fontWeight: '600', fontSize: '14px', color: 'var(--text-secondary)' }}>
            {stage}
          </div>
        ))}
      </div>

      {/* Empty State */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-secondary)', borderRadius: '12px', border: '1px dashed var(--border-color)' }}>
        <img src="/empty_state.png" alt="Empty Pipeline" style={{ width: '400px', opacity: 0.8, marginBottom: '24px' }} />
        <h3 style={{ fontSize: '20px', marginBottom: '8px' }}>No candidates in the pipeline yet</h3>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '400px', textAlign: 'center', marginBottom: '24px' }}>
          Your recruitment pipeline is ready. Start sourcing talent and add candidates to see them flow through your stages.
        </p>
        <button className="btn-secondary">Import from LinkedIn</button>
      </div>
    </div>
  );
}

export default Pipeline;

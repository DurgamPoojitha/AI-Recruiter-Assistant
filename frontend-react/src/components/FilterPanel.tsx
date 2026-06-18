import { useState, useEffect } from 'react';

export interface FilterState {
  skills: string[];
  min_experience: number;
  min_ats_score: number;
  risk_level: string;
  has_internship: boolean;
}

interface FilterPanelProps {
  onFilterChange: (filters: FilterState) => void;
  availableSkills: string[];
}

export function FilterPanel({ onFilterChange, availableSkills }: FilterPanelProps) {
  const [filters, setFilters] = useState<FilterState>({
    skills: [],
    min_experience: 0,
    min_ats_score: 0,
    risk_level: '',
    has_internship: false,
  });

  const handleFilterChange = (key: keyof FilterState, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
  };

  const toggleSkill = (skill: string) => {
    const newSkills = filters.skills.includes(skill)
      ? filters.skills.filter(s => s !== skill)
      : [...filters.skills, skill];
    handleFilterChange('skills', newSkills);
  };

  // Debounce API calls or apply immediately
  useEffect(() => {
    onFilterChange(filters);
  }, [filters]);

  return (
    <div className="filter-sidebar">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '16px', fontWeight: '600' }}>Advanced Filters</h3>
        <button 
          style={{ background: 'none', border: 'none', color: 'var(--primary-color)', fontSize: '12px', cursor: 'pointer', fontWeight: '500' }}
          onClick={() => setFilters({ skills: [], min_experience: 0, min_ats_score: 0, risk_level: '', has_internship: false })}
        >
          Reset
        </button>
      </div>

      <div className="filter-group">
        <label className="filter-label">Target Skills</label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '150px', overflowY: 'auto' }}>
          {availableSkills.map(skill => (
            <label key={skill} className="filter-checkbox">
              <input 
                type="checkbox" 
                checked={filters.skills.includes(skill)}
                onChange={() => toggleSkill(skill)}
              />
              {skill}
            </label>
          ))}
        </div>
      </div>

      <div className="filter-group">
        <label className="filter-label">Min Experience (Years): {filters.min_experience}</label>
        <input 
          type="range" 
          min="0" 
          max="20" 
          step="1"
          value={filters.min_experience}
          onChange={(e) => handleFilterChange('min_experience', Number(e.target.value))}
          style={{ width: '100%' }}
        />
      </div>

      <div className="filter-group">
        <label className="filter-label">Min ATS Score: {filters.min_ats_score}%</label>
        <input 
          type="range" 
          min="0" 
          max="100" 
          step="5"
          value={filters.min_ats_score}
          onChange={(e) => handleFilterChange('min_ats_score', Number(e.target.value))}
          style={{ width: '100%' }}
        />
      </div>

      <div className="filter-group">
        <label className="filter-label">Risk Level</label>
        <select 
          className="filter-input"
          value={filters.risk_level}
          onChange={(e) => handleFilterChange('risk_level', e.target.value)}
        >
          <option value="">Any Risk Level</option>
          <option value="Low">Low Risk Only</option>
          <option value="Medium">Up to Medium Risk</option>
        </select>
      </div>

      <div className="filter-group">
        <label className="filter-checkbox">
          <input 
            type="checkbox" 
            checked={filters.has_internship}
            onChange={(e) => handleFilterChange('has_internship', e.target.checked)}
          />
          Must have Internship Exp
        </label>
      </div>
      
    </div>
  );
}

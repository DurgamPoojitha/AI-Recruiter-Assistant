import { Bell, Search, User } from 'lucide-react';
import { useAuth0 } from '@auth0/auth0-react';
import { useLocation } from 'react-router-dom';

function Header() {
  const { user } = useAuth0();
  const location = useLocation();
  
  const getPageTitle = () => {
    switch(location.pathname) {
      case '/dashboard': return 'Analytics Dashboard';
      case '/pipeline': return 'Candidate Pipeline';
      case '/matcher': return 'AI Job Matcher';
      default: return 'Recruiter Pro';
    }
  };

  return (
    <div className="header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: '600', margin: 0 }}>{getPageTitle()}</h2>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <div style={{ position: 'relative' }}>
          <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
          <input 
            type="text" 
            placeholder="Search candidates or jobs..." 
            style={{ 
              padding: '10px 16px 10px 40px', borderRadius: '24px', border: '1px solid var(--border-color)', 
              background: 'var(--bg-primary)', width: '300px', fontSize: '14px', outline: 'none',
              transition: 'all 0.2s'
            }}
            onFocus={(e) => e.target.style.borderColor = 'var(--primary-color)'}
            onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
          />
        </div>
        
        <button style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', position: 'relative' }}>
          <Bell size={20} />
          <span style={{ position: 'absolute', top: '-2px', right: '-2px', width: '8px', height: '8px', background: 'var(--danger-color)', borderRadius: '50%' }}></span>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', paddingLeft: '24px', borderLeft: '1px solid var(--border-color)' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)' }}>{user?.name || 'Recruiter'}</div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{user?.email || 'admin@airecruiter.local'}</div>
          </div>
          <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--primary-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
            {user?.picture ? (
              <img src={user.picture} alt="Profile" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <User size={20} color="var(--primary-color)" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Header;

import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, FileSearch, LogOut } from 'lucide-react';
import { useAuth0 } from '@auth0/auth0-react';
import '../index.css';

function Sidebar() {
  const { logout } = useAuth0();

  return (
    <div className="sidebar">
      <div style={{ padding: '24px 32px', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ background: 'var(--primary-color)', width: '32px', height: '32px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>AI</div>
        <h2 style={{ fontSize: '18px', color: 'white', margin: 0 }}>Recruiter Pro</h2>
      </div>

      <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px', padding: '16px' }}>
        <NavLink to="/dashboard" style={({ isActive }) => ({
          display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', borderRadius: '8px',
          background: isActive ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
          color: isActive ? 'white' : 'var(--text-muted-on-dark)',
          fontWeight: isActive ? '600' : '400',
          transition: 'all 0.2s'
        })}>
          <LayoutDashboard size={20} /> Dashboard
        </NavLink>
        
        <NavLink to="/pipeline" style={({ isActive }) => ({
          display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', borderRadius: '8px',
          background: isActive ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
          color: isActive ? 'white' : 'var(--text-muted-on-dark)',
          fontWeight: isActive ? '600' : '400',
          transition: 'all 0.2s'
        })}>
          <Users size={20} /> Candidate Pipeline
        </NavLink>

        <NavLink to="/matcher" style={({ isActive }) => ({
          display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', borderRadius: '8px',
          background: isActive ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
          color: isActive ? 'white' : 'var(--text-muted-on-dark)',
          fontWeight: isActive ? '600' : '400',
          transition: 'all 0.2s'
        })}>
          <FileSearch size={20} /> AI Job Matcher
        </NavLink>
      </nav>

      <div style={{ padding: '16px' }}>
        <button 
          onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
          style={{ 
            display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', width: '100%',
            background: 'transparent', color: 'var(--text-muted-on-dark)', border: 'none',
            borderRadius: '8px', cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s'
          }}
          onMouseOver={(e) => { e.currentTarget.style.color = 'white'; e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'; }}
          onMouseOut={(e) => { e.currentTarget.style.color = 'var(--text-muted-on-dark)'; e.currentTarget.style.background = 'transparent'; }}
        >
          <LogOut size={20} /> Sign Out
        </button>
      </div>
    </div>
  );
}

export default Sidebar;

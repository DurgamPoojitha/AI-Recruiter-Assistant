import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import Pipeline from './pages/Pipeline';
import Matcher from './pages/Matcher';
import { setAuthTokenGetter } from './api';
import './App.css';

function App() {
  const { isAuthenticated, loginWithRedirect, isLoading, getAccessTokenSilently } = useAuth0();

  useEffect(() => {
    setAuthTokenGetter(getAccessTokenSilently);
  }, [getAccessTokenSilently]);

  if (isLoading) {
    return <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center' }}>Loading Enterprise Recruiter...</div>;
  }

  if (!isAuthenticated) {
    return (
      <div className="login-container">
        <div className="login-left">
          <h1 style={{ fontSize: '3rem', marginBottom: '16px' }}>AI Recruiter Assistant</h1>
          <p style={{ fontSize: '1.2rem', color: 'var(--text-muted-on-dark)', marginBottom: '32px' }}>
            The enterprise-grade talent acquisition platform powered by advanced NLP.
          </p>
          <button 
            className="btn-primary" 
            style={{ padding: '16px 32px', fontSize: '1.1rem', alignSelf: 'flex-start' }}
            onClick={() => loginWithRedirect()}
          >
            Sign In with SSO
          </button>
        </div>
        <div className="login-right"></div>
      </div>
    );
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-content">
        <Header />
        <div className="page-container">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/pipeline" element={<Pipeline />} />
            <Route path="/matcher" element={<Matcher />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

export default App;

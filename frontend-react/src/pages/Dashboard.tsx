import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Users, FileText, CheckCircle, TrendingUp } from 'lucide-react';
import { api } from '../api';

const data = [
  { name: 'Jan', applicants: 4000, hired: 240 },
  { name: 'Feb', applicants: 3000, hired: 139 },
  { name: 'Mar', applicants: 2000, hired: 980 },
  { name: 'Apr', applicants: 2780, hired: 390 },
  { name: 'May', applicants: 1890, hired: 480 },
  { name: 'Jun', applicants: 2390, hired: 380 },
  { name: 'Jul', applicants: 3490, hired: 430 },
];

const skillsData = [
  { name: 'React', demand: 85 },
  { name: 'Python', demand: 92 },
  { name: 'Node.js', demand: 78 },
  { name: 'AWS', demand: 88 },
  { name: 'TypeScript', demand: 95 },
];

function Dashboard() {
  const [metrics, setMetrics] = useState({
    total_candidates: 0,
    open_roles: 0,
    avg_match_score: 0,
    time_to_hire_days: 0
  });

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await api.get('/ats/dashboard/metrics');
        setMetrics(response.data);
      } catch (err) {
        console.error("Failed to fetch dashboard metrics:", err);
      }
    };
    fetchMetrics();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* Top Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px' }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ color: 'var(--text-secondary)' }}>Total Candidates</h3>
            <div style={{ background: 'var(--primary-light)', padding: '8px', borderRadius: '8px' }}>
              <Users size={20} color="var(--primary-color)" />
            </div>
          </div>
          <div style={{ fontSize: '32px', fontWeight: '700' }}>{metrics.total_candidates}</div>
          <div style={{ fontSize: '14px', color: 'var(--success-color)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <TrendingUp size={16} /> +14% this month
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ color: 'var(--text-secondary)' }}>Open Roles</h3>
            <div style={{ background: 'rgba(245, 158, 11, 0.1)', padding: '8px', borderRadius: '8px' }}>
              <FileText size={20} color="var(--warning-color)" />
            </div>
          </div>
          <div style={{ fontSize: '32px', fontWeight: '700' }}>{metrics.open_roles}</div>
          <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Active requisitions</div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ color: 'var(--text-secondary)' }}>Avg Match Score</h3>
            <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '8px', borderRadius: '8px' }}>
              <CheckCircle size={20} color="var(--success-color)" />
            </div>
          </div>
          <div style={{ fontSize: '32px', fontWeight: '700' }}>{metrics.avg_match_score}%</div>
          <div style={{ fontSize: '14px', color: 'var(--success-color)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <TrendingUp size={16} /> +2.5% vs last month
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ color: 'var(--text-secondary)' }}>Time to Hire</h3>
            <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '8px', borderRadius: '8px' }}>
              <Users size={20} color="var(--danger-color)" />
            </div>
          </div>
          <div style={{ fontSize: '32px', fontWeight: '700' }}>{metrics.time_to_hire_days} Days</div>
          <div style={{ fontSize: '14px', color: 'var(--success-color)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <TrendingUp size={16} style={{ transform: 'rotate(180deg)' }} /> -3 days vs average
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        <div className="card" style={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '18px' }}>Applicant Volume Overview</h2>
            <p style={{ color: 'var(--text-secondary)' }}>Monthly inbound applications vs hires</p>
          </div>
          <div style={{ flex: 1 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorApps" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--primary-color)" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="var(--primary-color)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: 'var(--text-secondary)'}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: 'var(--text-secondary)'}} />
                <Tooltip 
                  contentStyle={{ borderRadius: '8px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-md)' }}
                />
                <Area type="monotone" dataKey="applicants" stroke="var(--primary-color)" strokeWidth={3} fillOpacity={1} fill="url(#colorApps)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card" style={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '18px' }}>Top Required Skills</h2>
            <p style={{ color: 'var(--text-secondary)' }}>Most demanded skills across open roles</p>
          </div>
          <div style={{ flex: 1 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={skillsData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="var(--border-color)" />
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{fill: 'var(--text-secondary)'}} width={80} />
                <Tooltip cursor={{fill: 'var(--bg-primary)'}} contentStyle={{ borderRadius: '8px', border: '1px solid var(--border-color)' }} />
                <Bar dataKey="demand" fill="var(--primary-color)" radius={[0, 4, 4, 0]} barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      
    </div>
  );
}

export default Dashboard;

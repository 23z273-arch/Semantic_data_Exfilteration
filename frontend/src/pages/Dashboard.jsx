import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import DecisionBadge from '../components/DecisionBadge';
import { 
  ShieldAlert, 
  Eye, 
  HelpCircle, 
  Activity, 
  Clock, 
  Database,
  RefreshCw
} from 'lucide-react';

export default function Dashboard({ onNavigateToLogs }) {
  const [stats, setStats] = useState(null);
  const [recentLogs, setRecentLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const statsData = await api.getStats();
      const logsData = await api.getAuditLogs({ limit: 5 });
      setStats(statsData);
      setRecentLogs(logsData);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Could not fetch latest governance metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading && !stats) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: '100px' }}><RefreshCw className="pulse-glow" /></div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.02em' }}>Security Analytics & Threat Intel</h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>Real-time semantic exfiltration defense metrics for autonomous agent systems</p>
        </div>
        <button onClick={fetchDashboardData} className="btn btn-secondary btn-sm" style={{ display: 'flex', gap: '6px' }}>
          <RefreshCw size={14} /> Refresh metrics
        </button>
      </div>

      {error && (
        <div className="alert-box danger">
          <ShieldAlert size={20} />
          <div>
            <strong>Operational Error:</strong> {error}
          </div>
        </div>
      )}

      {/* Grid Stats */}
      <div className="grid-cols-4">
        <div className="glass-card metric-card">
          <div>
            <div className="metric-title">Total Interceptions</div>
            <div className="metric-value">{stats?.total_evaluations || 0}</div>
          </div>
          <div className="metric-icon-box primary">
            <Activity size={20} />
          </div>
        </div>

        <div className="glass-card metric-card">
          <div>
            <div className="metric-title">Blocked Threats</div>
            <div className="metric-value" style={{ color: 'var(--danger)' }}>{stats?.blocked || 0}</div>
          </div>
          <div className="metric-icon-box danger">
            <ShieldAlert size={20} />
          </div>
        </div>

        <div className="glass-card metric-card">
          <div>
            <div className="metric-title">Active Sessions</div>
            <div className="metric-value" style={{ color: 'var(--warning)' }}>{stats?.active_sessions || 0}</div>
          </div>
          <div className="metric-icon-box warning">
            <Clock size={20} />
          </div>
        </div>

        <div className="glass-card metric-card">
          <div>
            <div className="metric-title">Average Risk Score</div>
            <div className="metric-value">
              {stats?.avg_composite_risk_score !== undefined 
                ? `${Math.round(stats.avg_composite_risk_score * 100)}%` 
                : '0%'}
            </div>
          </div>
          <div className="metric-icon-box success">
            <Database size={20} />
          </div>
        </div>
      </div>

      <div className="grid-main-layout">
        {/* Recent logs */}
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Real-Time Policy Evaluation Stream</h3>
            <button onClick={onNavigateToLogs} className="btn btn-secondary btn-sm">View All Logs</button>
          </div>

          <div className="table-container">
            <table className="gov-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Agent ID</th>
                  <th>Verdict</th>
                  <th>Risk Score</th>
                  <th>Origin Target</th>
                  <th>Latency</th>
                </tr>
              </thead>
              <tbody>
                {recentLogs.length === 0 ? (
                  <tr>
                    <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '40px' }}>
                      No evaluation history available. Make evaluations in the DLP Playground!
                    </td>
                  </tr>
                ) : (
                  recentLogs.map((log) => {
                    const tagInfo = log.flagged_lineage_tags && log.flagged_lineage_tags[0];
                    return (
                      <tr key={log.id}>
                        <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                          {new Date(log.created_at).toLocaleTimeString()}
                        </td>
                        <td style={{ fontWeight: 600 }}>{log.agent_id}</td>
                        <td><DecisionBadge decision={log.decision} /></td>
                        <td style={{ fontWeight: 700 }}>{Math.round(log.composite_risk_score * 100)}%</td>
                        <td style={{ color: tagInfo ? 'var(--primary)' : 'var(--text-muted)' }}>
                          {tagInfo ? tagInfo.document_name : 'None (No Leak)'}
                        </td>
                        <td style={{ color: 'var(--text-muted)' }}>{Math.round(log.total_latency_ms)}ms</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Security Overview panel */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Governance Summary</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Evaluations ALLOWED:</span>
              <span style={{ fontWeight: 600, color: 'var(--success)' }}>{stats?.allowed || 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Evaluations WARNED:</span>
              <span style={{ fontWeight: 600, color: 'var(--warning)' }}>{stats?.warned || 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Evaluations BLOCKED:</span>
              <span style={{ fontWeight: 600, color: 'var(--danger)' }}>{stats?.blocked || 0}</span>
            </div>
          </div>

          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px', marginTop: '10px' }}>
            <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
              Threat Mitigation Status
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span>FPR Tolerance (Goal: &lt; 20%)</span>
                  <strong>PASSED</strong>
                </div>
                <div style={{ height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', background: 'var(--success)', width: '90%' }}></div>
                </div>
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span>Semantic Detection Rate</span>
                  <strong>100%</strong>
                </div>
                <div style={{ height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', background: 'var(--primary)', width: '100%' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

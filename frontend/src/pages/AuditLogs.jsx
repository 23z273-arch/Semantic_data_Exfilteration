import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import DecisionBadge from '../components/DecisionBadge';
import { 
  FileJson, 
  Search, 
  Sliders, 
  X, 
  ChevronRight, 
  Terminal, 
  RefreshCw,
  Clock
} from 'lucide-react';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [selectedLog, setSelectedLog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterDecision, setFilterDecision] = useState('');
  const [filterAgent, setFilterAgent] = useState('');
  const [error, setError] = useState(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditLogs({
        decision: filterDecision || undefined,
        agent_id: filterAgent || undefined,
        limit: 100
      });
      setLogs(data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Could not fetch audit logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [filterDecision]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchLogs();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.02em' }}>Governance Ledger & Auditing</h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>Immutable session records, policy decisions, and lineage mappings for regulatory compliance auditing.</p>
        </div>
        <button onClick={fetchLogs} className="btn btn-secondary btn-sm" style={{ display: 'flex', gap: '6px' }}>
          <RefreshCw size={14} /> Reload logs
        </button>
      </div>

      {error && (
        <div className="alert-box danger">
          <strong>Auditor Connection Error:</strong> {error}
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="glass-card" style={{ padding: '16px 24px' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '16px', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sliders size={16} style={{ color: 'var(--text-muted)' }} />
              <select 
                value={filterDecision} 
                onChange={(e) => setFilterDecision(e.target.value)} 
                className="form-control"
                style={{ padding: '8px 12px', fontSize: '0.85rem' }}
              >
                <option value="">All Decisions</option>
                <option value="ALLOW">Allow</option>
                <option value="WARN">Warn</option>
                <option value="BLOCK">Block</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', position: 'relative' }}>
              <input 
                type="text" 
                value={filterAgent} 
                onChange={(e) => setFilterAgent(e.target.value)} 
                placeholder="Filter by Agent ID…" 
                className="form-control"
                style={{ padding: '8px 12px 8px 36px', fontSize: '0.85rem', width: '200px' }}
              />
              <Search size={14} style={{ position: 'absolute', left: '12px', color: 'var(--text-muted)' }} />
            </div>

            <button type="submit" className="btn btn-secondary btn-sm" style={{ padding: '8px 16px' }}>Filter</button>
          </div>
        </form>
      </div>

      <div className="grid-main-layout">
        {/* Logs Table */}
        <div className="glass-card">
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '20px' }}>Audit Ledger Feed</h3>

          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '60px' }}><RefreshCw className="pulse-glow" /></div>
          ) : logs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
              <FileJson size={40} style={{ marginBottom: '12px', opacity: 0.3 }} />
              <p>No audit records matching your criteria were found.</p>
            </div>
          ) : (
            <div className="table-container">
              <table className="gov-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Agent ID</th>
                    <th>Session ID</th>
                    <th>Verdict</th>
                    <th>Risk</th>
                    <th>Latency</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr 
                      key={log.id} 
                      onClick={() => setSelectedLog(log)}
                      style={{ 
                        cursor: 'pointer',
                        background: selectedLog?.id === log.id ? 'rgba(255,255,255,0.015)' : ''
                      }}
                    >
                      <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td style={{ fontWeight: 600 }}>{log.agent_id}</td>
                      <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{log.session_id}</td>
                      <td><DecisionBadge decision={log.decision} /></td>
                      <td style={{ fontWeight: 700 }}>{Math.round(log.composite_risk_score * 100)}%</td>
                      <td style={{ color: 'var(--text-muted)' }}>{Math.round(log.total_latency_ms)}ms</td>
                      <td><ChevronRight size={16} style={{ color: 'var(--text-muted)' }} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Selected Log Drawer */}
        <div className="glass-card" style={{ minHeight: '400px' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '20px' }}>Security Trace details</h3>

          {!selectedLog ? (
            <div style={{ height: '80%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>
              <Clock size={40} style={{ marginBottom: '16px', opacity: 0.3 }} />
              <p>Select any audit record on the left to examine the complete security trace.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Log Reference ID</h4>
                  <strong style={{ fontSize: '0.9rem', color: 'var(--primary)' }}>{selectedLog.request_id}</strong>
                </div>
                <button onClick={() => setSelectedLog(null)} className="btn btn-secondary btn-icon btn-sm"><X size={14} /></button>
              </div>

              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
                <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Original Completion Text</h4>
                <div style={{ 
                  fontSize: '0.85rem', 
                  lineHeight: '1.5', 
                  padding: '12px', 
                  borderRadius: 'var(--radius-sm)', 
                  background: 'rgba(0,0,0,0.2)', 
                  maxHeight: '150px', 
                  overflowY: 'auto' 
                }}>
                  {selectedLog.output_preview}...
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Stage 1 Similarity:</span>
                  <strong>{selectedLog.stage1_max_similarity !== null ? `${Math.round(selectedLog.stage1_max_similarity * 100)}%` : 'N/A'}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Stage 2 Factual Overlap:</span>
                  <strong>{selectedLog.stage2_factual_score !== null ? `${Math.round(selectedLog.stage2_factual_score * 100)}%` : 'N/A'}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Multi-Turn Aggregation:</span>
                  <strong>{selectedLog.session_escalated ? 'ESCALATED' : 'Stable'}</strong>
                </div>
              </div>

              {selectedLog.flagged_lineage_tags && selectedLog.flagged_lineage_tags.length > 0 && (
                <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
                  <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Lineage Trace Tags</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {selectedLog.flagged_lineage_tags.map((tag, idx) => (
                      <div key={idx} style={{ padding: '8px 12px', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '4px', background: 'rgba(255,255,255,0.01)', fontSize: '0.8rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <strong>{tag.tag}</strong>
                          <span style={{ color: 'var(--text-muted)' }}>Match: {Math.round(tag.match_score * 100)}%</span>
                        </div>
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '2px' }}>Doc: {tag.document_name}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

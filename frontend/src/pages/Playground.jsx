import React, { useState } from 'react';
import { api } from '../api/client';
import RiskGauge from '../components/RiskGauge';
import DecisionBadge from '../components/DecisionBadge';
import { 
  Send, 
  HelpCircle, 
  Layers, 
  FileText, 
  Terminal, 
  AlertOctagon, 
  RefreshCw,
  Fingerprint
} from 'lucide-react';

export default function Playground() {
  const [agentId, setAgentId] = useState('agent-alpha');
  const [sessionId, setSessionId] = useState('sess-interactive');
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  const handleEvaluate = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.evaluate({
        agent_id: agentId,
        session_id: sessionId,
        output_text: inputText
      });
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Error occurred during semantic check.');
    } finally {
      setLoading(false);
    }
  };

  const loadExample = (text, aid = 'agent-alpha', sid = 'sess-interactive') => {
    setInputText(text);
    setAgentId(aid);
    setSessionId(sid);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <h2 style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.02em' }}>Semantic DLP Interceptor Playground</h2>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>Submit agent completions to evaluate exfiltration risk and view the multi-stage decision trace.</p>
      </div>

      <div className="grid-main-layout">
        {/* Input Panel */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Agent Completion Form</h3>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button 
                type="button" 
                onClick={() => loadExample("Hello there! I'm your virtual assistant. How can I help you manage your calendar or coordinate meetings today?", 'agent-safe-bot', 'sess-safe-1')} 
                className="btn btn-secondary btn-sm"
                style={{ fontSize: '0.8rem' }}
              >
                Safe Output
              </button>
              <button 
                type="button" 
                onClick={() => loadExample("Priya Mehta in engineering has a base salary of 295,000 dollars with a 20 percent bonus target, reporting directly to Alan Forsythe.", 'agent-leaker', 'sess-leak-1')} 
                className="btn btn-danger btn-sm"
                style={{ fontSize: '0.8rem' }}
              >
                Paraphrased HR Leak
              </button>
              <button 
                type="button" 
                onClick={() => loadExample("The trial participant is a male in his mid-forties diagnosed with a pancreatic stage 2 neuroendocrine tumor showing an MEN1 positive mutation.", 'agent-leaker', 'sess-leak-2')} 
                className="btn btn-danger btn-sm"
                style={{ fontSize: '0.8rem' }}
              >
                Paraphrased Clinical Trial
              </button>
            </div>
          </div>

          <form onSubmit={handleEvaluate} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Agent Identifier</label>
                <input 
                  type="text" 
                  value={agentId} 
                  onChange={(e) => setAgentId(e.target.value)} 
                  className="form-control"
                  placeholder="agent-id"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Session ID (For Multi-Turn Tracking)</label>
                <input 
                  type="text" 
                  value={sessionId} 
                  onChange={(e) => setSessionId(e.target.value)} 
                  className="form-control"
                  placeholder="session-id"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Agent Output Content</label>
              <textarea 
                value={inputText} 
                onChange={(e) => setInputText(e.target.value)} 
                className="form-control"
                placeholder="Type or paste the text content generated by the AI agent to run semantic exfiltration detection..."
                required
                style={{ minHeight: '180px' }}
              />
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary" style={{ alignSelf: 'flex-end', minWidth: '160px' }}>
              {loading ? (
                <>
                  <RefreshCw className="pulse-glow" size={18} /> Evaluating…
                </>
              ) : (
                <>
                  <Send size={18} /> Run Governance Check
                </>
              )}
            </button>
          </form>
        </div>

        {/* Results Panel */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '20px', minHeight: '400px' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Evaluation Results</h3>

          {error && (
            <div className="alert-box danger">
              <AlertOctagon size={20} />
              <div>{error}</div>
            </div>
          )}

          {!result && !loading && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>
              <Terminal size={48} style={{ marginBottom: '16px', opacity: 0.3 }} />
              <p>Submit an agent completion to view real-time vector matches, LLM factual overlap score, and policy action.</p>
            </div>
          )}

          {loading && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px' }}>
              <RefreshCw className="pulse-glow" size={48} style={{ color: 'var(--primary)', marginBottom: '16px' }} />
              <p style={{ color: 'var(--text-secondary)' }}>Processing dual-stage semantic filters…</p>
            </div>
          )}

          {result && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {/* Verdict header card */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', background: 'rgba(255,255,255,0.01)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                  <RiskGauge score={result.composite_risk_score} />
                  <div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Security Policy Action
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                      <DecisionBadge decision={result.decision} />
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                        ({Math.round(result.total_latency_ms)}ms Latency)
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="tab-container">
                <button onClick={() => setActiveTab('overview')} className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}>Overview</button>
                <button onClick={() => setActiveTab('vector')} className={`tab-btn ${activeTab === 'vector' ? 'active' : ''}`}>Vector Matches (S1)</button>
                <button onClick={() => setActiveTab('factual')} className={`tab-btn ${activeTab === 'factual' ? 'active' : ''}`}>Factual Claims (S2)</button>
                <button onClick={() => setActiveTab('session')} className={`tab-btn ${activeTab === 'session' ? 'active' : ''}`}>Session State (S3)</button>
                <button onClick={() => setActiveTab('json')} className={`tab-btn ${activeTab === 'json' ? 'active' : ''}`}>JSON Response</button>
              </div>

              {/* Tab Contents */}
              {activeTab === 'overview' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div>
                    <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>Decision Rationale</h4>
                    <p style={{ fontSize: '0.9rem', lineHeight: '1.4', padding: '12px', borderRadius: 'var(--radius-sm)', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)' }}>
                      {result.decision_rationale}
                    </p>
                  </div>
                  {result.lineage_tags && result.lineage_tags.length > 0 && (
                    <div>
                      <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Lineage Trace Metadata</h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {result.lineage_tags.map((tag, idx) => (
                          <div key={idx} style={{ padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.01)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <strong style={{ fontSize: '0.85rem' }}>{tag.tag}</strong>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{tag.document_name}</div>
                            </div>
                            <span className="badge badge-sec-topsecret" style={{ fontSize: '0.7rem' }}>{tag.classification}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'vector' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Max Cosine Similarity:</span>
                    <strong style={{ color: result.stage1?.max_similarity >= 0.55 ? 'var(--warning)' : 'var(--success)' }}>
                      {result.stage1 ? `${Math.round(result.stage1.max_similarity * 100)}%` : '0%'}
                    </strong>
                  </div>

                  {result.stage1?.all_matches.length === 0 ? (
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No database vector overlap matches found.</p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {result.stage1?.all_matches.map((match, idx) => (
                        <div key={idx} style={{ padding: '12px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', background: 'rgba(255,255,255,0.01)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '0.8rem' }}>
                            <span style={{ fontWeight: 600, color: 'var(--primary)' }}>{match.document_name}</span>
                            <span style={{ fontWeight: 700 }}>Similarity: {Math.round(match.similarity * 100)}%</span>
                          </div>
                          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontStyle: 'italic', lineHeight: '1.4' }}>
                            "...{match.chunk_preview}..."
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'factual' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {result.stage_executed === 1 ? (
                    <div className="alert-box success" style={{ fontSize: '0.85rem' }}>
                      Stage 2 Factual Claim Check was skipped because Stage 1 similarity remained below the trigger threshold (0.55).
                    </div>
                  ) : (
                    <>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Factual Overlap Ratio:</span>
                        <strong style={{ color: result.stage2?.factual_overlap_score >= 0.60 ? 'var(--danger)' : 'var(--success)' }}>
                          {result.stage2 ? `${Math.round(result.stage2.factual_overlap_score * 100)}%` : '0%'}
                        </strong>
                      </div>

                      {result.stage2?.reasoning && (
                        <div>
                          <h4 style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Judge Reasoning</h4>
                          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '4px' }}>
                            {result.stage2.reasoning}
                          </p>
                        </div>
                      )}

                      <div>
                        <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Extracted Contaminated Claims</h4>
                        {result.stage2?.contaminated_claims.length === 0 ? (
                          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No private, non-public factual claims detected.</p>
                        ) : (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {result.stage2?.contaminated_claims.map((claim, idx) => (
                              <div key={idx} style={{ padding: '12px', borderLeft: '3px solid var(--danger)', background: 'rgba(239, 68, 68, 0.02)', borderRadius: '0 var(--radius-sm) var(--radius-sm) 0', fontSize: '0.85rem' }}>
                                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{claim.claim}</div>
                                <div style={{ color: 'var(--text-secondary)', marginTop: '4px', fontSize: '0.8rem' }}>
                                  <strong>Vault Correlative:</strong> {claim.source_reference}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}

              {activeTab === 'session' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Turn Number:</span>
                    <strong>{result.session.turn_number}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Cumulative Risk Score:</span>
                    <strong>{Math.round(result.session.cumulative_score * 100)}%</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Cumulative Escalation Status:</span>
                    <strong style={{ color: result.session.escalated ? 'var(--danger)' : 'var(--text-muted)' }}>
                      {result.session.escalated ? 'ESCALATED (Reconstruction Attack Alert)' : 'Stable'}
                    </strong>
                  </div>
                  {result.session.risk_window.length > 0 && (
                    <div>
                      <h4 style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>Turn Risk Timeline (Last 10 turns)</h4>
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'flex-end', height: '60px', padding: '10px', background: 'rgba(0,0,0,0.2)', borderRadius: '4px' }}>
                        {result.session.risk_window.map((val, idx) => (
                          <div 
                            key={idx} 
                            style={{ 
                              flex: 1, 
                              background: val >= 0.75 ? 'var(--danger)' : val >= 0.50 ? 'var(--warning)' : 'var(--success)', 
                              height: `${val * 100}%`,
                              borderRadius: '2px',
                              minWidth: '10px'
                            }} 
                            title={`Turn ${idx+1}: ${Math.round(val*100)}%`}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'json' && (
                <pre style={{ background: '#020306', color: '#10b981', padding: '16px', borderRadius: 'var(--radius-md)', overflowX: 'auto', fontSize: '0.8rem', maxHeight: '350px' }}>
                  {JSON.stringify(result, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

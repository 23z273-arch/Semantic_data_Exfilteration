import React, { useState } from 'react';
import { api } from '../api/client';
import { 
  ActivitySquare, 
  CheckCircle2, 
  XCircle, 
  ShieldAlert, 
  RefreshCw, 
  Sliders,
  AlertTriangle
} from 'lucide-react';

export default function TestSuite() {
  const [loading, setLoading] = useState(false);
  const [benchmarkResult, setBenchmarkResult] = useState(null);
  const [filterCategory, setFilterCategory] = useState('ALL');
  const [error, setError] = useState(null);

  const handleRunBenchmark = async () => {
    setLoading(true);
    setError(null);
    setBenchmarkResult(null);

    try {
      const data = await api.runBenchmark({
        include_per_case_details: true
      });
      setBenchmarkResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to complete benchmark run.');
    } finally {
      setLoading(false);
    }
  };

  const getFilteredResults = () => {
    if (!benchmarkResult?.per_case_results) return [];
    if (filterCategory === 'ALL') return benchmarkResult.per_case_results;
    return benchmarkResult.per_case_results.filter(r => r.category === filterCategory);
  };

  // Helper values for confusion matrix calculation from statistics
  const getMatrixStats = () => {
    if (!benchmarkResult?.metrics) return { tp: 0, fp: 0, tn: 0, fn: 0 };
    const byCat = benchmarkResult.metrics.by_category || {};
    
    // TN = Correct normal cases
    const tn = byCat.NORMAL?.correct || 0;
    // FP = False positive normal cases
    const fp = byCat.NORMAL?.fp || 0;
    
    // TP = Correct paraphrase + adversarial cases
    const tp_para = byCat.PARAPHRASED?.correct || 0;
    const tp_adv = byCat.ADVERSARIAL?.correct || 0;
    const tp = tp_para + tp_adv;

    // FN = Missed paraphrase + adversarial cases
    const fn_para = byCat.PARAPHRASED?.fn || 0;
    const fn_adv = byCat.ADVERSARIAL?.fn || 0;
    const fn = fn_para + fn_adv;

    return { tp, fp, tn, fn };
  };

  const { tp, fp, tn, fn } = getMatrixStats();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.02em' }}>Governance Test Suite Runner</h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>Execute standardized evaluations against 30 adversarial, paraphrased, and borderline test scenarios to measure detection accuracy.</p>
        </div>
        <button 
          onClick={handleRunBenchmark} 
          disabled={loading} 
          className="btn btn-primary"
          style={{ display: 'flex', gap: '8px', minWidth: '180px' }}
        >
          {loading ? (
            <><RefreshCw className="pulse-glow" size={18} /> Running Suite…</>
          ) : (
            <><ActivitySquare size={18} /> Execute Test Suite</>
          )}
        </button>
      </div>

      {error && (
        <div className="alert-box danger">
          <ShieldAlert size={20} />
          <div>{error}</div>
        </div>
      )}

      {/* Intro Box */}
      {!benchmarkResult && !loading && (
        <div className="glass-card" style={{ textAlign: 'center', padding: '60px 40px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          <ActivitySquare size={48} style={{ color: 'var(--primary)', opacity: 0.8 }} />
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Model Alignment Verification Matrix</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', lineHeight: '1.6' }}>
            Running the suite will test the semantic similarity filters, LLM factual overlap detectors, and multi-turn session tracking against 10 safe normal controls, 5 paraphrased leaks, 5 borderline domain queries, and 10 multi-lingual, code-form, or numeric obfuscated attacks.
          </p>
          <button onClick={handleRunBenchmark} className="btn btn-primary" style={{ marginTop: '8px' }}>
            Execute Suite (30 Cases)
          </button>
        </div>
      )}

      {loading && (
        <div className="glass-card" style={{ textAlign: 'center', padding: '80px 40px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' }}>
          <RefreshCw className="pulse-glow" size={48} style={{ color: 'var(--primary)' }} />
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Processing Adversarial Test Vectors...</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '400px' }}>
            Evaluating exact hashes, sentence tokenizers, Cosine similarity checks, and LLM-as-a-Judge factual mappings. This takes around 5-10 seconds.
          </p>
        </div>
      )}

      {benchmarkResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          
          {/* Main metrics overview */}
          <div className="grid-cols-4">
            <div className="glass-card" style={{ borderLeft: '4px solid var(--primary)' }}>
              <div className="metric-title">Accuracy</div>
              <div className="metric-value" style={{ color: 'var(--primary)' }}>
                {Math.round(benchmarkResult.metrics.overall.accuracy * 100)}%
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Overall Suite Score</span>
            </div>
            
            <div className="glass-card" style={{ borderLeft: '4px solid var(--danger)' }}>
              <div className="metric-title">False Positive Rate</div>
              <div className="metric-value" style={{ color: benchmarkResult.metrics.overall.false_positive_rate >= 0.20 ? 'var(--danger)' : 'var(--text-primary)' }}>
                {Math.round(benchmarkResult.metrics.overall.false_positive_rate * 100)}%
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Target: &lt; 20% FPR</span>
            </div>

            <div className="glass-card" style={{ borderLeft: '4px solid var(--success)' }}>
              <div className="metric-title">Recall Rate (TPR)</div>
              <div className="metric-value" style={{ color: 'var(--success)' }}>
                {Math.round(benchmarkResult.metrics.overall.true_positive_rate * 100)}%
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Semantic Attack Capture</span>
            </div>

            <div className="glass-card" style={{ borderLeft: '4px solid var(--purple)' }}>
              <div className="metric-title">Verification status</div>
              <div className="metric-value" style={{ color: benchmarkResult.passed ? 'var(--success)' : 'var(--danger)' }}>
                {benchmarkResult.passed ? 'PASSED' : 'FAILED'}
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>DLP Governance Criteria</span>
            </div>
          </div>

          <div className="grid-main-layout">
            {/* Left side: test cases details list */}
            <div className="glass-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Test Matrix Evaluations</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sliders size={16} style={{ color: 'var(--text-muted)' }} />
                  <select 
                    value={filterCategory} 
                    onChange={(e) => setFilterCategory(e.target.value)} 
                    className="form-control"
                    style={{ padding: '4px 8px', fontSize: '0.8rem', borderRadius: '4px' }}
                  >
                    <option value="ALL">All Test Cases</option>
                    <option value="NORMAL">Normal Controls</option>
                    <option value="PARAPHRASED">Paraphrased Content</option>
                    <option value="BORDERLINE">Borderline Queries</option>
                    <option value="ADVERSARIAL">Adversarial Attacks</option>
                  </select>
                </div>
              </div>

              <div className="table-container">
                <table className="gov-table">
                  <thead>
                    <tr>
                      <th>Case ID</th>
                      <th>Category</th>
                      <th>Expected</th>
                      <th>Actual</th>
                      <th>Risk Score</th>
                      <th>Outcome</th>
                    </tr>
                  </thead>
                  <tbody>
                    {getFilteredResults().map((res) => (
                      <tr key={res.case_id}>
                        <td style={{ fontWeight: 600 }}>{res.case_id}</td>
                        <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{res.category}</td>
                        <td><span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>{res.expected}</span></td>
                        <td><span style={{ fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 600 }}>{res.actual}</span></td>
                        <td style={{ fontWeight: 700 }}>{Math.round(res.composite_risk_score * 100)}%</td>
                        <td>
                          {res.passed ? (
                            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--success)', fontSize: '0.85rem', fontWeight: 600 }}>
                              <CheckCircle2 size={16} /> PASS
                            </span>
                          ) : (
                            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--danger)', fontSize: '0.85rem', fontWeight: 600 }}>
                              <XCircle size={16} /> FAIL
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Right side: Confusion Matrix visualization */}
            <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Confusion Matrix</h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  {/* True Positive */}
                  <div className="matrix-cell" style={{ borderLeft: '3px solid var(--success)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>True Positives</div>
                    <div className="matrix-count success">{tp}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Leaks Blocked</div>
                  </div>
                  {/* False Positive */}
                  <div className="matrix-cell" style={{ borderLeft: '3px solid var(--danger)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>False Positives</div>
                    <div className="matrix-count danger">{fp}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Safe Blocked</div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  {/* False Negative */}
                  <div className="matrix-cell" style={{ borderLeft: '3px solid var(--danger)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>False Negatives</div>
                    <div className="matrix-count danger">{fn}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Leaks Allowed</div>
                  </div>
                  {/* True Negative */}
                  <div className="matrix-cell" style={{ borderLeft: '3px solid var(--success)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>True Negatives</div>
                    <div className="matrix-count success">{tn}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Safe Allowed</div>
                  </div>
                </div>
              </div>

              {/* Status checklist */}
              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px', marginTop: '10px' }}>
                <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
                  Compliance Check list
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.85rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <CheckCircle2 size={16} style={{ color: benchmarkResult.metrics.success_criteria.normal_fpr_below_20pct.passed ? 'var(--success)' : 'var(--danger)' }} />
                    <span>FPR under 20% ({Math.round(benchmarkResult.metrics.overall.false_positive_rate * 100)}% actual)</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <CheckCircle2 size={16} style={{ color: benchmarkResult.metrics.success_criteria.paraphrased_detection_4_of_5.passed ? 'var(--success)' : 'var(--danger)' }} />
                    <span>Paraphrase Recall &gt; 80% ({Math.round(benchmarkResult.metrics.overall.true_positive_rate * 100)}% actual)</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <CheckCircle2 size={16} style={{ color: benchmarkResult.metrics.success_criteria.similarity_ranking_correct.passed ? 'var(--success)' : 'var(--danger)' }} />
                    <span>Similarity Scorer correctly ranks content</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}

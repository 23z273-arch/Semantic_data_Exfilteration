import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { 
  FolderLock, 
  Trash2, 
  Plus, 
  FileText, 
  Tag, 
  Building, 
  User, 
  ChevronRight, 
  X,
  RefreshCw,
  Upload
} from 'lucide-react';

export default function VaultManager() {
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form states
  const [showAddForm, setShowAddForm] = useState(false);
  const [formName, setFormName] = useState('');
  const [formCategory, setFormCategory] = useState('HR_RECORD');
  const [formClassification, setFormClassification] = useState('TOP_SECRET');
  const [formLineageTag, setFormLineageTag] = useState('');
  const [formDepartment, setFormDepartment] = useState('');
  const [formDataOwner, setFormDataOwner] = useState('');
  const [formContent, setFormContent] = useState('');

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const data = await api.getDocuments();
      setDocuments(data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Could not load protected documents.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleDocClick = async (doc) => {
    try {
      const details = await api.getDocumentDetails(doc.id);
      setSelectedDoc(details);
    } catch (err) {
      alert('Failed to fetch document chunks.');
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this document from the vault? Its embeddings will be permanently removed from FAISS.')) return;
    
    setActionLoading(true);
    try {
      await api.deleteDocument(id);
      setSelectedDoc(null);
      await fetchDocuments();
    } catch (err) {
      alert(err.message || 'Failed to delete document.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleIngest = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    setError(null);

    try {
      await api.ingestDocument({
        name: formName,
        category: formCategory,
        classification: formClassification,
        lineage_tag: formLineageTag,
        department: formDepartment,
        data_owner: formDataOwner,
        content: formContent
      });
      
      // Reset form
      setFormName('');
      setFormLineageTag('');
      setFormDepartment('');
      setFormDataOwner('');
      setFormContent('');
      setShowAddForm(false);
      
      await fetchDocuments();
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to ingest document.');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.02em' }}>Reference Data Vault</h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>Manage protected datasets, configure dynamic lineage tags, and explore semantic chunk partitions.</p>
        </div>
        <button 
          onClick={() => setShowAddForm(!showAddForm)} 
          className="btn btn-primary"
          style={{ display: 'flex', gap: '8px' }}
        >
          <Plus size={18} /> Ingest Document
        </button>
      </div>

      {showAddForm && (
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Document Ingestion Pipeline</h3>
            <button onClick={() => setShowAddForm(false)} className="btn btn-secondary btn-icon"><X size={16} /></button>
          </div>

          <form onSubmit={handleIngest} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Document Name</label>
                <input 
                  type="text" 
                  value={formName} 
                  onChange={(e) => setFormName(e.target.value)} 
                  className="form-control" 
                  placeholder="e.g. Strategic_Plan_2026.txt"
                  required 
                />
              </div>
              <div className="form-group">
                <label className="form-label">Category</label>
                <select value={formCategory} onChange={(e) => setFormCategory(e.target.value)} className="form-control">
                  <option value="HR_RECORD">HR Records</option>
                  <option value="MEDICAL">Medical Records</option>
                  <option value="FINANCIAL">Financial/M&A Data</option>
                  <option value="INFRASTRUCTURE">IT Infrastructure</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Classification</label>
                <select value={formClassification} onChange={(e) => setFormClassification(e.target.value)} className="form-control">
                  <option value="TOP_SECRET">Top Secret</option>
                  <option value="CONFIDENTIAL">Confidential</option>
                  <option value="RESTRICTED">Restricted</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Lineage Tag (Dynamic Linkage)</label>
                <input 
                  type="text" 
                  value={formLineageTag} 
                  onChange={(e) => setFormLineageTag(e.target.value)} 
                  className="form-control" 
                  placeholder="e.g. VAULT-IT-IP-029"
                  required 
                />
              </div>
              <div className="form-group">
                <label className="form-label">Department Owner</label>
                <input 
                  type="text" 
                  value={formDepartment} 
                  onChange={(e) => setFormDepartment(e.target.value)} 
                  className="form-control" 
                  placeholder="e.g. Engineering"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Data Custodian</label>
                <input 
                  type="text" 
                  value={formDataOwner} 
                  onChange={(e) => setFormDataOwner(e.target.value)} 
                  className="form-control" 
                  placeholder="e.g. Alan Forsythe"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Document Content (Plain Text)</label>
              <textarea 
                value={formContent} 
                onChange={(e) => setFormContent(e.target.value)} 
                className="form-control" 
                placeholder="Paste the full, raw text content of the document. The system will automatically execute recursive sentence-boundary token chunking and index vectors..."
                required 
                style={{ minHeight: '150px' }}
              />
            </div>

            <button type="submit" disabled={actionLoading} className="btn btn-primary" style={{ alignSelf: 'flex-end', minWidth: '150px' }}>
              {actionLoading ? <RefreshCw className="pulse-glow" size={16} /> : <><Upload size={16} /> Ingest & Embed</>}
            </button>
          </form>
        </div>
      )}

      {error && (
        <div className="alert-box danger">
          <strong>Vault Operations Alert:</strong> {error}
        </div>
      )}

      <div className="grid-main-layout">
        {/* Document list */}
        <div className="glass-card">
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '20px' }}>Ingested Datasets</h3>

          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '60px' }}><RefreshCw className="pulse-glow" /></div>
          ) : documents.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
              <FolderLock size={40} style={{ marginBottom: '12px', opacity: 0.3 }} />
              <p>No documents are currently ingested in the reference vault.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {documents.map((doc) => (
                <div 
                  key={doc.id} 
                  onClick={() => handleDocClick(doc)}
                  className={`glass-card`} 
                  style={{ 
                    padding: '16px 20px', 
                    cursor: 'pointer', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    borderLeft: selectedDoc?.id === doc.id ? '4px solid var(--primary)' : '1px solid var(--border-color)',
                    background: selectedDoc?.id === doc.id ? 'rgba(59, 130, 246, 0.02)' : ''
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <FileText size={24} style={{ color: 'var(--primary)' }} />
                    <div>
                      <h4 style={{ fontSize: '0.95rem', fontWeight: 700 }}>{doc.name}</h4>
                      <div style={{ display: 'flex', gap: '12px', marginTop: '4px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Tag size={12} /> {doc.lineage_tag}</span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Building size={12} /> {doc.department || 'N/A'}</span>
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <span className={`badge ${doc.classification === 'TOP_SECRET' ? 'badge-sec-topsecret' : doc.classification === 'CONFIDENTIAL' ? 'badge-sec-confidential' : 'badge-sec-restricted'}`}>
                      {doc.classification.replace('_', ' ')}
                    </span>
                    <button onClick={(e) => handleDelete(doc.id, e)} className="btn btn-secondary btn-icon btn-sm" style={{ color: 'var(--danger)' }}>
                      <Trash2 size={16} />
                    </button>
                    <ChevronRight size={16} style={{ color: 'var(--text-muted)' }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selected Document Details / Chunks Explorer */}
        <div className="glass-card" style={{ minHeight: '300px' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '20px' }}>Chunk Inspector</h3>

          {!selectedDoc ? (
            <div style={{ height: '80%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>
              <FolderLock size={40} style={{ marginBottom: '16px', opacity: 0.3 }} />
              <p>Select a document on the left to inspect its recursive vector chunk partitions.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div>
                <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>{selectedDoc.name}</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '12px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Dynamic Lineage:</span>
                    <strong style={{ color: 'var(--text-primary)' }}>{selectedDoc.lineage_tag}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Custodian:</span>
                    <span style={{ color: 'var(--text-primary)' }}>{selectedDoc.data_owner || 'N/A'}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Partition Chunks:</span>
                    <span style={{ color: 'var(--text-primary)' }}>{selectedDoc.chunk_count}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Embedding Dimension:</span>
                    <span style={{ color: 'var(--text-primary)' }}>{selectedDoc.embedding_model}</span>
                  </div>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '12px' }}>Vector Chunks ({selectedDoc.chunks?.length})</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '400px', overflowY: 'auto', paddingRight: '4px' }}>
                  {selectedDoc.chunks?.map((chunk) => (
                    <div key={chunk.id} style={{ padding: '12px', background: 'rgba(0, 0, 0, 0.2)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                        <span>Chunk #{chunk.chunk_index + 1}</span>
                        <span>{chunk.token_count} tokens</span>
                      </div>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                        {chunk.chunk_text}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

import React from 'react';
import { 
  ShieldCheck, 
  LayoutDashboard, 
  Terminal, 
  FolderLock, 
  ActivitySquare, 
  FileJson,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

export default function Sidebar({ activePage, setActivePage, isHealthy }) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'playground', label: 'DLP Playground', icon: Terminal },
    { id: 'vault', label: 'Protected Vault', icon: FolderLock },
    { id: 'benchmark', label: 'Test Suite Runner', icon: ActivitySquare },
    { id: 'logs', label: 'Audit Logs', icon: FileJson },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <ShieldCheck className="sidebar-logo-icon" size={32} />
        <div>
          <h2 className="sidebar-title">Aivar DLP</h2>
          <div className="sidebar-subtitle">Semantic Firewall</div>
        </div>
      </div>
      
      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              className={`sidebar-nav-item ${activePage === item.id ? 'active' : ''}`}
              style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left' }}
            >
              <Icon size={18} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isHealthy ? (
            <>
              <CheckCircle size={14} style={{ color: 'var(--success)' }} />
              <span style={{ color: 'var(--text-primary)' }}>System Online</span>
            </>
          ) : (
            <>
              <AlertTriangle size={14} style={{ color: 'var(--danger)' }} />
              <span style={{ color: 'var(--text-secondary)' }}>System Degraded</span>
            </>
          )}
        </div>
        <div style={{ fontSize: '0.75rem', opacity: 0.6 }}>v1.0.0 — Q2 2026</div>
      </div>
    </aside>
  );
}

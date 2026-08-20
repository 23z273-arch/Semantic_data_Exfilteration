import React, { useEffect, useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Playground from './pages/Playground';
import VaultManager from './pages/VaultManager';
import TestSuite from './pages/TestSuite';
import AuditLogs from './pages/AuditLogs';
import { api } from './api/client';

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [isHealthy, setIsHealthy] = useState(false);

  // Poll system health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await api.getHealth();
        setIsHealthy(health.status === 'healthy');
      } catch (err) {
        setIsHealthy(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      {/* Navigation Sidebar */}
      <Sidebar 
        activePage={activePage} 
        setActivePage={setActivePage} 
        isHealthy={isHealthy} 
      />

      <div className="main-wrapper">
        {/* Sticky Header */}
        <header className="main-header">
          <div className="header-title-container">
            <h1 style={{ textTransform: 'capitalize' }}>
              {activePage === 'benchmark' ? 'Test Suite Matrix' : activePage.replace('-', ' ')}
            </h1>
          </div>
          <div className="header-stats">
            <div className="header-stat-item">
              <span className="header-stat-dot" style={{ backgroundColor: isHealthy ? 'var(--success)' : 'var(--danger)' }} />
              <span>DLP Engine Status: {isHealthy ? 'Operational' : 'Disconnected'}</span>
            </div>
          </div>
        </header>

        {/* Content Body */}
        <main className="main-content">
          {activePage === 'dashboard' && (
            <Dashboard onNavigateToLogs={() => setActivePage('logs')} />
          )}
          {activePage === 'playground' && <Playground />}
          {activePage === 'vault' && <VaultManager />}
          {activePage === 'benchmark' && <TestSuite />}
          {activePage === 'logs' && <AuditLogs />}
        </main>
      </div>
    </div>
  );
}

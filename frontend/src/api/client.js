const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/v1';

async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    if (response.status === 204) {
      return null;
    }

    // Safely attempt JSON parsing — non-JSON bodies (e.g. 500 HTML pages) must not throw.
    let data;
    try {
      data = await response.json();
    } catch {
      if (!response.ok) {
        throw new Error(response.statusText || `HTTP ${response.status}`);
      }
      return null;
    }

    if (!response.ok) {
      throw new Error(data.detail || response.statusText || 'API error');
    }
    return data;
  } catch (error) {
    console.error(`API Request to ${path} failed:`, error);
    throw error;
  }
}

export const api = {
  // Health
  getHealth: () => request('/health'),

  // Stats
  getStats: () => request('/governance/stats'),

  // Vault Documents
  getDocuments: () => request('/vault/documents'),
  getDocumentDetails: (id) => request(`/vault/documents/${id}`),
  ingestDocument: (data) => request('/vault/documents', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  deleteDocument: (id) => request(`/vault/documents/${id}`, {
    method: 'DELETE',
  }),

  // Governance Evaluate
  evaluate: (data) => request('/governance/evaluate', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // Audit Logs
  getAuditLogs: (params = {}) => {
    const query = new URLSearchParams();
    if (params.agent_id) query.append('agent_id', params.agent_id);
    if (params.decision) query.append('decision', params.decision);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);
    const queryString = query.toString();
    return request(`/governance/audit-logs${queryString ? `?${queryString}` : ''}`);
  },

  // Benchmark Run
  runBenchmark: (data = {}) => request('/governance/benchmark/run', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
};

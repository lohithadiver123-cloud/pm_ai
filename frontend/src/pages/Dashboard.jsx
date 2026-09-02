/**
 * Dashboard page.
 * Shows welcome message, workspace info, and feedback statistics.
 * Provides navigation to import and feedback pages.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

function Dashboard() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('pm_copilot_user') || 'null');

  const [workspaces, setWorkspaces] = useState([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState('');
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Workspace creation state
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [creating, setCreating] = useState(false);

  // Fetch workspaces on mount
  useEffect(() => {
    fetchWorkspaces();
  }, []);

  // Fetch stats when workspace selection changes
  useEffect(() => {
    if (selectedWorkspace) {
      fetchStats(selectedWorkspace);
    }
  }, [selectedWorkspace]);

  const fetchWorkspaces = async () => {
    try {
      const response = await api.get('/workspaces');
      setWorkspaces(response.data);
      if (response.data.length > 0) {
        setSelectedWorkspace(response.data[0]._id);
      } else {
        setLoading(false);
      }
    } catch (err) {
      setError('Failed to load workspaces.');
      setLoading(false);
    }
  };

  const fetchStats = async (workspaceId) => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get(`/workspaces/${workspaceId}/stats`);
      setStats(response.data);
    } catch (err) {
      setError('Failed to load workspace statistics.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkspace = async () => {
    if (!newWorkspaceName.trim()) return;
    setCreating(true);
    try {
      await api.post('/workspaces', { name: newWorkspaceName.trim() });
      setNewWorkspaceName('');
      setShowCreateForm(false);
      await fetchWorkspaces();
    } catch (err) {
      setError('Failed to create workspace.');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Welcome back, {user?.name || 'Product Manager'} 👋</h1>
          <p className="page-subtitle">Here's an overview of your feedback workspace.</p>
        </div>
        <div className="page-actions">
          <button className="btn btn-primary" onClick={() => navigate('/import')}>
            📥 Import Data
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/feedback')}>
            💬 View Feedback
          </button>
        </div>
      </div>

      {/* Workspace Selector */}
      <div className="card">
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 className="card-title">📁 Workspace</h2>
          <button
            className="btn btn-sm btn-primary"
            onClick={() => setShowCreateForm((v) => !v)}
          >
            {showCreateForm ? 'Cancel' : '+ New Workspace'}
          </button>
        </div>
        <div className="card-body">
          {showCreateForm && (
            <div className="create-workspace-form">
              <input
                type="text"
                placeholder="e.g. Product Q4 2025"
                value={newWorkspaceName}
                onChange={(e) => setNewWorkspaceName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateWorkspace()}
                autoFocus
              />
              <button
                className="btn btn-primary btn-sm"
                onClick={handleCreateWorkspace}
                disabled={creating || !newWorkspaceName.trim()}
              >
                {creating ? 'Creating...' : 'Create'}
              </button>
            </div>
          )}

          {workspaces.length === 0 && !showCreateForm ? (
            <div className="empty-state">
              <p>No workspaces yet. Click <strong>+ New Workspace</strong> to create one.</p>
            </div>
          ) : workspaces.length > 0 ? (
            <select
              value={selectedWorkspace}
              onChange={(e) => setSelectedWorkspace(e.target.value)}
              className="select-input"
            >
              {workspaces.map((ws) => (
                <option key={ws._id} value={ws._id}>
                  {ws.name}
                </option>
              ))}
            </select>
          ) : null}
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading && selectedWorkspace && (
        <div className="loading-state">Loading workspace data...</div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card stat-card-primary">
            <div className="stat-icon">📊</div>
            <div className="stat-value">{stats.total_feedback}</div>
            <div className="stat-label">Total Feedback</div>
          </div>
          <div className="stat-card stat-card-info">
            <div className="stat-icon">🎫</div>
            <div className="stat-value">{stats.total_tickets}</div>
            <div className="stat-label">Support Tickets</div>
          </div>
          <div className="stat-card stat-card-success">
            <div className="stat-icon">✨</div>
            <div className="stat-value">{stats.cleaned_count}</div>
            <div className="stat-label">Cleaned</div>
          </div>
          <div className="stat-card stat-card-warning">
            <div className="stat-icon">🏷️</div>
            <div className="stat-value">{stats.categorized_count}</div>
            <div className="stat-label">Categorized</div>
          </div>
        </div>
      )}

      {/* Category Breakdown */}
      {stats && stats.by_category && Object.keys(stats.by_category).length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">📊 Category Breakdown</h2>
          </div>
          <div className="card-body">
            <div className="breakdown-grid">
              {Object.entries(stats.by_category).map(([category, count]) => (
                <div key={category} className="breakdown-item">
                  <span className="breakdown-label">{category.replace(/_/g, ' ')}</span>
                  <span className="breakdown-bar-container">
                    <span
                      className="breakdown-bar"
                      style={{ width: `${(count / (stats.total_feedback || 1)) * 100}%` }}
                    />
                  </span>
                  <span className="breakdown-count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Source Breakdown */}
      {stats && stats.by_source && Object.keys(stats.by_source).length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">🌐 Feedback Sources</h2>
          </div>
          <div className="card-body">
            <div className="source-list">
              {Object.entries(stats.by_source).map(([source, count]) => (
                <div key={source} className="source-item">
                  <span className="source-name">{source.replace(/_/g, ' ')}</span>
                  <span className="source-count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Sentiment Breakdown */}
      {stats && stats.by_sentiment && Object.keys(stats.by_sentiment).length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">😊 Sentiment Overview</h2>
          </div>
          <div className="card-body">
            <div className="sentiment-row">
              <div className="sentiment-chip positive">
                🟢 Positive: {stats.by_sentiment.positive || 0}
              </div>
              <div className="sentiment-chip neutral">
                🟡 Neutral: {stats.by_sentiment.neutral || 0}
              </div>
              <div className="sentiment-chip negative">
                🔴 Negative: {stats.by_sentiment.negative || 0}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;

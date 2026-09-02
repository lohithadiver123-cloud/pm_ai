/**
 * FeedbackList page.
 * Table showing feedback with filters, pagination, clean, and categorize actions.
 */
import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const CATEGORIES = [
  { value: '', label: 'All Categories' },
  { value: 'bug_report', label: 'Bug Report' },
  { value: 'feature_request', label: 'Feature Request' },
  { value: 'performance_issue', label: 'Performance Issue' },
  { value: 'general_feedback', label: 'General Feedback' },
];

const SENTIMENTS = [
  { value: '', label: 'All Sentiments' },
  { value: 'positive', label: 'Positive' },
  { value: 'neutral', label: 'Neutral' },
  { value: 'negative', label: 'Negative' },
];

const SOURCES = [
  { value: '', label: 'All Sources' },
  { value: 'app_review', label: 'App Review' },
  { value: 'support_ticket', label: 'Support Ticket' },
  { value: 'survey', label: 'Survey' },
  { value: 'social_media', label: 'Social Media' },
  { value: 'email', label: 'Email' },
];

function FeedbackList() {
  const [workspaces, setWorkspaces] = useState([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState('');
  const [feedback, setFeedback] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [category, setCategory] = useState('');
  const [sentiment, setSentiment] = useState('');
  const [source, setSource] = useState('');
  const [cleaning, setCleaning] = useState(false);
  const [categorizing, setCategorizing] = useState(false);
  const [actionMessage, setActionMessage] = useState('');

  // Define fetchWorkspaces
  const fetchWorkspaces = async () => {
    try {
      const response = await api.get('/workspaces');
      setWorkspaces(response.data);
      if (response.data.length > 0) {
        setSelectedWorkspace(response.data[0]._id);
      }
    } catch (err) {
      setError('Failed to load workspaces.');
    }
  };

  // Define fetchFeedback with proper dependencies
  const fetchFeedback = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = {
        workspace_id: selectedWorkspace,
        page,
        limit,
      };
      if (category) params.category = category;
      if (sentiment) params.sentiment = sentiment;
      if (source) params.source = source;

      const response = await api.get('/feedback', { params });
      setFeedback(response.data.items);
      setTotal(response.data.total);
      setTotalPages(response.data.total_pages);
    } catch (err) {
      setError('Failed to load feedback.');
    } finally {
      setLoading(false);
    }
  }, [selectedWorkspace, page, limit, category, sentiment, source]);

  // Fetch workspaces on mount
  useEffect(() => {
    fetchWorkspaces();
  }, []);

  // Fetch feedback when workspace, page, or filters change
  useEffect(() => {
    if (selectedWorkspace) {
      fetchFeedback();
    }
  }, [selectedWorkspace, page, category, sentiment, source, fetchFeedback]);

  const handleClean = async () => {
    setCleaning(true);
    setActionMessage('');
    try {
      const formData = new FormData();
      formData.append('workspace_id', selectedWorkspace);
      const response = await api.post('/feedback/clean', formData);
      setActionMessage(response.data.message);
      fetchFeedback(); // Refresh data
    } catch (err) {
      setActionMessage('Cleaning failed: ' + (err.response?.data?.detail || 'Unknown error'));
    } finally {
      setCleaning(false);
    }
  };

  const handleCategorize = async () => {
    setCategorizing(true);
    setActionMessage('');
    try {
      const formData = new FormData();
      formData.append('workspace_id', selectedWorkspace);
      const response = await api.post('/feedback/categorize', formData);
      setActionMessage(response.data.message);
      fetchFeedback(); // Refresh data
    } catch (err) {
      setActionMessage('Categorization failed: ' + (err.response?.data?.detail || 'Unknown error'));
    } finally {
      setCategorizing(false);
    }
  };

  // Reset page when filters change
  const handleCategoryChange = (e) => { setCategory(e.target.value); setPage(1); };
  const handleSentimentChange = (e) => { setSentiment(e.target.value); setPage(1); };
  const handleSourceChange = (e) => { setSource(e.target.value); setPage(1); };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Feedback</h1>
          <p className="page-subtitle">
            {total > 0 ? `Showing ${feedback.length} of ${total} feedback entries` : 'No feedback yet'}
          </p>
        </div>
        <div className="page-actions">
          <button
            className="btn btn-secondary"
            onClick={handleClean}
            disabled={cleaning || !selectedWorkspace}
          >
            {cleaning ? 'Cleaning...' : 'Clean Data'}
          </button>
          <button
            className="btn btn-primary"
            onClick={handleCategorize}
            disabled={categorizing || !selectedWorkspace}
          >
            {categorizing ? 'Categorizing...' : 'Categorize'}
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="alert alert-success">{actionMessage}</div>
      )}
      {error && <div className="alert alert-error">{error}</div>}

      {/* Filters */}
      <div className="card">
        <div className="card-body">
          <div className="filters-row">
            <div className="form-group">
              <label>Workspace</label>
              <select
                value={selectedWorkspace}
                onChange={(e) => { setSelectedWorkspace(e.target.value); setPage(1); }}
                className="select-input"
              >
                {workspaces.length === 0 && <option value="">No workspaces</option>}
                {workspaces.map((ws) => (
                  <option key={ws._id} value={ws._id}>{ws.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Category</label>
              <select value={category} onChange={handleCategoryChange} className="select-input">
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Sentiment</label>
              <select value={sentiment} onChange={handleSentimentChange} className="select-input">
                {SENTIMENTS.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Source</label>
              <select value={source} onChange={handleSourceChange} className="select-input">
                {SOURCES.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Feedback Table */}
      <div className="card">
        <div className="card-body" style={{ padding: 0 }}>
          {loading ? (
            <div className="loading-state">Loading feedback...</div>
          ) : feedback.length === 0 ? (
            <div className="empty-state">
              <p>No feedback found. Try adjusting your filters or import some data.</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Source</th>
                    <th>Category</th>
                    <th>Sentiment</th>
                    <th>Rating</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {feedback.map((item) => (
                    <tr key={item._id}>
                      <td>
                        <div className="feedback-title-cell">
                          <strong>{item.title || 'Untitled'}</strong>
                          <span className="feedback-preview">{item.content?.substring(0, 80)}...</span>
                        </div>
                      </td>
                      <td>
                        <span className="source-badge">{item.source?.replace(/_/g, ' ')}</span>
                      </td>
                      <td>
                        {item.category ? (
                          <span className="category-badge">{item.category.replace(/_/g, ' ')}</span>
                        ) : (
                          <span className="text-muted">Uncategorized</span>
                        )}
                      </td>
                      <td>
                        {item.sentiment ? (
                          <span className={`sentiment-badge ${item.sentiment}`}>
                            {item.sentiment}
                          </span>
                        ) : (
                          <span className="text-muted">-</span>
                        )}
                      </td>
                      <td>
                        {item.rating ? (
                          <span className="rating">{'★'.repeat(item.rating)}{'☆'.repeat(5 - item.rating)}</span>
                        ) : (
                          <span className="text-muted">-</span>
                        )}
                      </td>
                      <td className="text-muted">
                        {item.created_at ? new Date(item.created_at).toLocaleDateString() : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="btn btn-sm btn-secondary"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
          >
            Previous
          </button>
          <span className="pagination-info">
            Page {page} of {totalPages}
          </span>
          <button
            className="btn btn-sm btn-secondary"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default FeedbackList;

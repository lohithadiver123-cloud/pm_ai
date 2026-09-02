/**
 * Import Data page.
 * File upload (CSV/JSON) with source type dropdown.
 * Shows import history table. Calls /api/feedback/import.
 */
import { useState, useEffect, useRef } from 'react';
import api from '../services/api';

const SOURCE_OPTIONS = [
  { value: 'app_review', label: 'App Review' },
  { value: 'support_ticket', label: 'Support Ticket' },
  { value: 'survey', label: 'Survey' },
  { value: 'social_media', label: 'Social Media' },
  { value: 'email', label: 'Email' },
  { value: 'other', label: 'Other' },
];

function ImportData() {
  const fileInputRef = useRef(null);

  const [workspaces, setWorkspaces] = useState([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState('');
  const [source, setSource] = useState('app_review');
  const [file, setFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [error, setError] = useState('');
  const [importLogs, setImportLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(false);

  // Fetch workspaces on mount
  useEffect(() => {
    fetchWorkspaces();
  }, []);

  // Fetch import logs when workspace changes
  useEffect(() => {
    if (selectedWorkspace) {
      fetchImportLogs(selectedWorkspace);
    }
  }, [selectedWorkspace]);

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

  const fetchImportLogs = async (workspaceId) => {
    setLoadingLogs(true);
    try {
      const response = await api.get('/feedback/import-logs', {
        params: { workspace_id: workspaceId },
      });
      setImportLogs(response.data);
    } catch (err) {
      setImportLogs([]);
    } finally {
      setLoadingLogs(false);
    }
  };

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      const ext = selected.name.split('.').pop().toLowerCase();
      if (ext !== 'csv' && ext !== 'json') {
        setError('Please upload a CSV or JSON file.');
        setFile(null);
        return;
      }
      setFile(selected);
      setError('');
    }
  };

  const handleImport = async () => {
    if (!file) {
      setError('Please select a file to import.');
      return;
    }
    if (!selectedWorkspace) {
      setError('Please select a workspace.');
      return;
    }

    setImporting(true);
    setError('');
    setImportResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('workspace_id', selectedWorkspace);
      formData.append('source', source);

      const response = await api.post('/feedback/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setImportResult(response.data);
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      // Refresh import logs
      fetchImportLogs(selectedWorkspace);
    } catch (err) {
      const message = err.response?.data?.detail || 'Import failed. Please try again.';
      setError(message);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Import Feedback</h1>
          <p className="page-subtitle">Upload CSV or JSON files to import customer feedback.</p>
        </div>
      </div>

      {/* Import Form */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Upload File</h2>
        </div>
        <div className="card-body">
          {error && <div className="alert alert-error">{error}</div>}

          <div className="import-form">
            <div className="form-row">
              <div className="form-group form-group-half">
                <label>Workspace</label>
                <select
                  value={selectedWorkspace}
                  onChange={(e) => setSelectedWorkspace(e.target.value)}
                  className="select-input"
                  disabled={importing}
                >
                  {workspaces.length === 0 && (
                    <option value="">No workspaces available</option>
                  )}
                  {workspaces.map((ws) => (
                    <option key={ws._id} value={ws._id}>
                      {ws.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group form-group-half">
                <label>Source Type</label>
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  className="select-input"
                  disabled={importing}
                >
                  {SOURCE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>File (CSV or JSON)</label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.json"
                onChange={handleFileChange}
                disabled={importing}
                className="file-input"
              />
              {file && (
                <span className="file-name">Selected: {file.name}</span>
              )}
            </div>

            <button
              className="btn btn-primary"
              onClick={handleImport}
              disabled={importing || !file}
            >
              {importing ? 'Importing...' : 'Import File'}
            </button>
          </div>

          {/* Import Result */}
          {importResult && (
            <div className="import-result">
              <div className="import-result-header">Import Complete</div>
              <div className="import-result-stats">
                <span>File: {importResult.filename}</span>
                <span>Total: {importResult.record_count}</span>
                <span className="text-success">Success: {importResult.successful}</span>
                {importResult.failed > 0 && (
                  <span className="text-danger">Failed: {importResult.failed}</span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Import History */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Import History</h2>
        </div>
        <div className="card-body">
          {loadingLogs ? (
            <p className="text-muted">Loading...</p>
          ) : importLogs.length === 0 ? (
            <div className="empty-state">
              <p>No imports yet. Upload a file above to get started.</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Filename</th>
                    <th>Records</th>
                    <th>Success</th>
                    <th>Failed</th>
                    <th>Status</th>
                    <th>Imported At</th>
                  </tr>
                </thead>
                <tbody>
                  {importLogs.map((log) => (
                    <tr key={log._id}>
                      <td>{log.filename}</td>
                      <td>{log.record_count}</td>
                      <td className="text-success">{log.successful}</td>
                      <td className={log.failed > 0 ? 'text-danger' : ''}>
                        {log.failed}
                      </td>
                      <td>
                        <span
                          className={`status-badge status-${log.status === 'completed' ? 'success' : log.status === 'failed' ? 'error' : 'warning'}`}
                        >
                          {log.status}
                        </span>
                      </td>
                      <td className="text-muted">
                        {log.imported_at
                          ? new Date(log.imported_at).toLocaleString()
                          : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ImportData;

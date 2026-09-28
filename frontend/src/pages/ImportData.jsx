import { useCallback, useEffect, useRef, useState } from 'react';
import api from '../services/api';
import { useBusy } from '../context/BusyContext';
import {
  Alert,
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  EmptyState,
  PageHeader,
  Select,
  SkeletonTable,
} from '../components/ui';

const SOURCE_OPTIONS = [
  { value: 'app_review', label: 'App review' },
  { value: 'support_ticket', label: 'Support ticket' },
  { value: 'survey', label: 'Survey' },
  { value: 'social_media', label: 'Social media' },
  { value: 'email', label: 'Email' },
  { value: 'other', label: 'Other' },
];

const STATUS_TONE = { completed: 'success', failed: 'danger', pending: 'warning' };

/**
 * Import — get raw feedback in.
 *
 * The file is the one required input, so it owns the dropzone at the top; the
 * destination workspace and source label sit underneath it as settings. Import
 * runs are tracked in the global busy bar, and the history table below makes
 * past runs auditable.
 */
export default function ImportData() {
  const { begin } = useBusy();
  const fileInputRef = useRef(null);

  const [workspaces, setWorkspaces] = useState([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState('');
  const [source, setSource] = useState('app_review');
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const [logs, setLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(true);

  const fetchWorkspaces = useCallback(async () => {
    try {
      const { data } = await api.get('/workspaces');
      setWorkspaces(data);
      if (data.length > 0) setSelectedWorkspace(data[0]._id);
      else setLoadingLogs(false);
    } catch {
      setError('Could not load your workspaces.');
      setLoadingLogs(false);
    }
  }, []);

  const fetchLogs = useCallback(async (workspaceId) => {
    if (!workspaceId) return;
    setLoadingLogs(true);
    try {
      const { data } = await api.get('/feedback/import-logs', { params: { workspace_id: workspaceId } });
      setLogs(data);
    } catch {
      setLogs([]);
    } finally {
      setLoadingLogs(false);
    }
  }, []);

  useEffect(() => {
    fetchWorkspaces();
  }, [fetchWorkspaces]);

  useEffect(() => {
    fetchLogs(selectedWorkspace);
  }, [selectedWorkspace, fetchLogs]);

  const acceptFile = (candidate) => {
    if (!candidate) return;
    const ext = candidate.name.split('.').pop().toLowerCase();
    if (ext !== 'csv' && ext !== 'json') {
      setError('That file type is not supported. Upload a .csv or .json export.');
      setFile(null);
      return;
    }
    setFile(candidate);
    setError('');
  };

  const handleImport = async () => {
    if (!file) {
      setError('Choose a file to import first.');
      return;
    }
    if (!selectedWorkspace) {
      setError('Choose a destination workspace first.');
      return;
    }

    const done = begin('Importing feedback');
    setImporting(true);
    setError('');
    setResult(null);

    try {
      const body = new FormData();
      body.append('file', file);
      body.append('workspace_id', selectedWorkspace);
      body.append('source', source);

      const { data } = await api.post('/feedback/import', body, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setResult(data);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      await fetchLogs(selectedWorkspace);
    } catch (err) {
      setError(err.response?.data?.detail || 'The import failed. Nothing was written — try again.');
    } finally {
      setImporting(false);
      done();
    }
  };

  return (
    <div className="page-container">
      <PageHeader
        icon="download"
        title="Import feedback"
        description="Bring in CSV or JSON exports from reviews, support tickets and surveys. Each row becomes one feedback record."
      />

      <Card>
        <CardHeader title="Choose a file" hint="Up to 10 MB. CSV and JSON are both accepted." />
        <CardBody className="stack stack-md">
          {error && <Alert variant="error">{error}</Alert>}

          <label
            className={['dropzone', dragging && 'is-active'].filter(Boolean).join(' ')}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              acceptFile(e.dataTransfer.files?.[0]);
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.json"
              onChange={(e) => acceptFile(e.target.files?.[0])}
              disabled={importing}
            />
            <span className="dropzone-title">
              {file ? file.name : 'Drop a file here, or click to browse'}
            </span>
            <span className="dropzone-hint">
              {file
                ? `${(file.size / 1024).toFixed(1)} KB · ready to import`
                : 'CSV or JSON · one feedback item per row'}
            </span>
          </label>

          <div className="form-row">
            <div className="form-group form-group-half">
              <Select
                label="Destination workspace"
                value={selectedWorkspace}
                onChange={(e) => setSelectedWorkspace(e.target.value)}
                disabled={importing || workspaces.length === 0}
              >
                {workspaces.length === 0 && <option value="">No workspaces available</option>}
                {workspaces.map((ws) => (
                  <option key={ws._id} value={ws._id}>
                    {ws.name}
                  </option>
                ))}
              </Select>
            </div>

            <div className="form-group form-group-half">
              <Select
                label="Where it came from"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                disabled={importing}
                hint="Applied to every row in this file."
              >
                {SOURCE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </Select>
            </div>
          </div>

          <div className="row justify-end">
            <Button
              variant="primary"
              icon="download"
              loading={importing}
              disabled={!file || !selectedWorkspace}
              onClick={handleImport}
            >
              {importing ? 'Importing…' : 'Import file'}
            </Button>
          </div>

          {result && (
            <Alert variant={result.failed > 0 ? 'warning' : 'success'} title="Import complete">
              <div className="row row-wrap" style={{ gap: 'var(--sp-4)' }}>
                <span>{result.filename}</span>
                <span>{result.record_count} rows read</span>
                <span>{result.successful} imported</span>
                {result.failed > 0 && <span>{result.failed} rejected</span>}
              </div>
            </Alert>
          )}
        </CardBody>
      </Card>

      <Card flush>
        <CardHeader
          title="Import history"
          hint="Every run against the selected workspace, newest first."
        />
        {loadingLogs ? (
          <SkeletonTable rows={4} columns={6} />
        ) : logs.length === 0 ? (
          <EmptyState icon="clock" title="No imports yet">
            Once you upload a file, the run is recorded here with its row counts and status.
          </EmptyState>
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">File</th>
                  <th scope="col">Rows</th>
                  <th scope="col">Imported</th>
                  <th scope="col">Rejected</th>
                  <th scope="col">Status</th>
                  <th scope="col">When</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log._id}>
                    <td className="text-semibold">{log.filename}</td>
                    <td>{log.record_count}</td>
                    <td>{log.successful}</td>
                    <td className={log.failed > 0 ? 'text-danger' : ''}>{log.failed}</td>
                    <td>
                      <Badge tone={STATUS_TONE[log.status] || 'neutral'}>{log.status}</Badge>
                    </td>
                    <td className="text-muted tight">
                      {log.imported_at ? new Date(log.imported_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

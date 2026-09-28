import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { CategoryPieChart, SentimentDonutChart } from '../components/Charts';
import { sentiment, getCategoryColor, tint } from '../theme';
import {
  Alert,
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  EmptyState,
  PageHeader,
  ProgressBar,
  SkeletonChart,
  SkeletonStatGrid,
  Stat,
  StatGrid,
} from '../components/ui';

const SENTIMENT_TONE = { positive: 'success', neutral: 'warning', negative: 'danger' };

function stars(rating) {
  const n = Math.min(5, Math.max(1, Math.round(rating)));
  return '★'.repeat(n) + '☆'.repeat(5 - n);
}

/**
 * Dashboard — the "where do we stand" screen.
 *
 * Reads top to bottom as one argument: how much feedback (stats), what it is
 * about (category mix), how people feel (sentiment), how processed it is, and
 * the newest raw items. One primary action: go to Insights.
 */
export default function Dashboard() {
  const navigate = useNavigate();

  const [workspaces, setWorkspaces] = useState([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState('');
  const [stats, setStats] = useState(null);
  const [recentFeedback, setRecentFeedback] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [creating, setCreating] = useState(false);

  const fetchWorkspaces = useCallback(async () => {
    try {
      const { data } = await api.get('/workspaces');
      setWorkspaces(data);
      if (data.length > 0) {
        setSelectedWorkspace((current) => current || data[0]._id);
      } else {
        setLoading(false);
      }
    } catch {
      setError('Could not load your workspaces.');
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWorkspaces();
  }, [fetchWorkspaces]);

  useEffect(() => {
    if (!selectedWorkspace) return undefined;
    let cancelled = false;

    (async () => {
      setLoading(true);
      setError('');
      try {
        const [statsRes, feedbackRes] = await Promise.all([
          api.get(`/workspaces/${selectedWorkspace}/stats`),
          api.get('/feedback', { params: { workspace_id: selectedWorkspace, limit: 6, page: 1 } }),
        ]);
        if (cancelled) return;
        setStats(statsRes.data);
        setRecentFeedback(feedbackRes.data?.items || []);
      } catch {
        if (!cancelled) setError('Could not load this workspace’s data.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [selectedWorkspace]);

  const handleCreateWorkspace = async () => {
    if (!newWorkspaceName.trim()) return;
    setCreating(true);
    try {
      const { data } = await api.post('/workspaces', { name: newWorkspaceName.trim() });
      setNewWorkspaceName('');
      setShowCreateForm(false);
      await fetchWorkspaces();
      if (data?._id) setSelectedWorkspace(data._id);
    } catch {
      setError('Could not create that workspace.');
    } finally {
      setCreating(false);
    }
  };

  const total = stats?.total_feedback || 0;
  const cleaned = stats?.cleaned_count || 0;
  const categorized = stats?.categorized_count || 0;
  const positive = stats?.by_sentiment?.positive || 0;
  const positivePercent = total > 0 ? Math.round((positive / total) * 1000) / 10 : 0;
  const pct = (value) => (total > 0 ? Math.round((value / total) * 100) : 0);

  return (
    <div className="page-container">
      <PageHeader
        icon="layout"
        title="Dashboard"
        description="Feedback volume, what it is about, and how the pipeline is tracking for the selected workspace."
        actions={
          <>
            <div className="workspace-selector-box">
              <label className="ws-label" htmlFor="workspace-select">
                Workspace
              </label>
              {workspaces.length > 0 ? (
                <select
                  id="workspace-select"
                  className="ws-dropdown"
                  value={selectedWorkspace}
                  onChange={(e) => setSelectedWorkspace(e.target.value)}
                >
                  {workspaces.map((ws) => (
                    <option key={ws._id} value={ws._id}>
                      {ws.name}
                    </option>
                  ))}
                </select>
              ) : (
                <span className="text-muted text-sm">None yet</span>
              )}
            </div>

            <Button
              size="sm"
              variant={showCreateForm ? 'ghost' : 'outline'}
              icon={showCreateForm ? 'x' : 'plus'}
              aria-expanded={showCreateForm}
              onClick={() => setShowCreateForm((v) => !v)}
            >
              {showCreateForm ? 'Cancel' : 'New workspace'}
            </Button>

            <Button variant="outline" icon="download" onClick={() => navigate('/import')}>
              Import
            </Button>

            <Button variant="primary" onClick={() => navigate('/insights')}>
              Review insights
            </Button>
          </>
        }
      />

      {showCreateForm && (
        <Card>
          <CardBody>
            <div className="row">
              <label className="field-label sr-only" htmlFor="new-workspace">
                New workspace name
              </label>
              <input
                id="new-workspace"
                className="input flex-1"
                placeholder="Workspace name, e.g. Q4 Store Feedback"
                value={newWorkspaceName}
                onChange={(e) => setNewWorkspaceName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateWorkspace()}
                autoFocus
              />
              <Button
                variant="primary"
                loading={creating}
                disabled={!newWorkspaceName.trim()}
                onClick={handleCreateWorkspace}
              >
                Create
              </Button>
            </div>
          </CardBody>
        </Card>
      )}

      {error && <Alert variant="error">{error}</Alert>}

      {loading ? (
        <>
          <SkeletonStatGrid count={3} />
          <SkeletonChart label="Loading category mix" />
        </>
      ) : total === 0 ? (
        <Card>
          <EmptyState
            icon="inbox"
            title="No feedback in this workspace yet"
            actions={
              <Button variant="primary" icon="download" onClick={() => navigate('/import')}>
                Import feedback
              </Button>
            }
          >
            Import a CSV or JSON export of customer reviews, tickets or survey answers and this page
            fills in automatically.
          </EmptyState>
        </Card>
      ) : (
        <>
          <StatGrid>
            <Stat label="Feedback items" value={total} icon="inbox" featured />
            <Stat label="Categorised" value={`${pct(categorized)}%`} hint={`${categorized} of ${total}`} />
            <Stat label="Positive sentiment" value={`${positivePercent}%`} hint={`${positive} of ${total}`} />
          </StatGrid>

          <div className="grid grid-2">
            <Card>
              <CardHeader
                title="What the feedback is about"
                hint="Every item, grouped by the category the classifier assigned."
              />
              <CardBody>
                <CategoryPieChart categoryDistribution={stats?.by_category || {}} totalFeedback={total} />
              </CardBody>
            </Card>

            <Card>
              <CardHeader
                title="How customers feel"
                actions={
                  <Badge tone={SENTIMENT_TONE.positive}>{positivePercent}% positive</Badge>
                }
                hint="Sentiment across every item that carried a tone."
              />
              <CardBody className="stack stack-md">
                <SentimentDonutChart
                  positive={positive}
                  neutral={stats?.by_sentiment?.neutral || 0}
                  negative={stats?.by_sentiment?.negative || 0}
                  healthScore={positivePercent}
                />
                <div className="stack stack-sm">
                  {['positive', 'neutral', 'negative'].map((key) => {
                    const count = stats?.by_sentiment?.[key] || 0;
                    return (
                      <div key={key} className="row" style={{ gap: 'var(--sp-2)' }}>
                        <span
                          className="dot"
                          style={{ color: sentiment[key].line }}
                          aria-hidden="true"
                        />
                        <span className="text-sm" style={{ textTransform: 'capitalize', width: 72 }}>
                          {key}
                        </span>
                        <span className="text-sm text-muted flex-1">{count} items</span>
                        <span className="text-sm text-semibold">{pct(count)}%</span>
                      </div>
                    );
                  })}
                </div>
              </CardBody>
            </Card>
          </div>

          <Card>
            <CardHeader
              title="Pipeline progress"
              hint="Cleaning normalises the text; categorising assigns a category and sentiment."
              actions={
                cleaned === total && categorized === total ? (
                  <Badge tone="success" icon="checkCircle">
                    Up to date
                  </Badge>
                ) : (
                  <Button variant="outline" size="sm" icon="zap" onClick={() => navigate('/insights')}>
                    Finish processing
                  </Button>
                )
              }
            />
            <CardBody className="stack stack-md">
              <div className="stack stack-sm">
                <div className="row row-between">
                  <span className="text-sm">Cleaned</span>
                  <span className="text-sm text-muted">
                    {cleaned} of {total}
                  </span>
                </div>
                <ProgressBar value={pct(cleaned)} label="Cleaning progress" />
              </div>
              <div className="stack stack-sm">
                <div className="row row-between">
                  <span className="text-sm">Categorised</span>
                  <span className="text-sm text-muted">
                    {categorized} of {total}
                  </span>
                </div>
                <ProgressBar value={pct(categorized)} label="Categorisation progress" />
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title="Newest feedback"
              hint={`The ${recentFeedback.length} most recent items in this workspace.`}
              actions={
                recentFeedback.length > 0 && (
                  <Button variant="ghost" size="sm" iconRight="arrowRight" onClick={() => navigate('/feedback')}>
                    View all {total}
                  </Button>
                )
              }
            />

            {recentFeedback.length === 0 ? (
              <EmptyState icon="inbox" title="Nothing here yet">
                Once feedback is imported, the latest items appear in this list.
              </EmptyState>
            ) : (
              <div className="table-responsive">
                <table className="table">
                  <thead>
                    <tr>
                      <th scope="col">Item</th>
                      <th scope="col">Category</th>
                      <th scope="col">Sentiment</th>
                      <th scope="col">Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentFeedback.map((item) => (
                      <tr key={item._id || item.title}>
                        <td>
                          <div className="table-primary">
                            <strong className="clamp-2">
                              {item.title || item.content?.slice(0, 90) || 'Untitled feedback'}
                            </strong>
                            {item.title && item.content && (
                              <span className="table-secondary">{item.content}</span>
                            )}
                          </div>
                        </td>
                        <td>
                          {item.category ? (
                            <span
                              className="badge"
                              style={{
                                background: tint(getCategoryColor(item.category)),
                                color: getCategoryColor(item.category),
                                borderColor: tint(getCategoryColor(item.category), 0.22),
                              }}
                            >
                              {item.category.replace(/_/g, ' ')}
                            </span>
                          ) : (
                            <span className="text-light">—</span>
                          )}
                        </td>
                        <td>
                          {item.sentiment ? (
                            <Badge tone={SENTIMENT_TONE[item.sentiment] || 'neutral'}>{item.sentiment}</Badge>
                          ) : (
                            <span className="text-light">—</span>
                          )}
                        </td>
                        <td>
                          <div className="stack stack-sm">
                            <span className="text-sm">{(item.source || 'review').replace(/_/g, ' ')}</span>
                            <span className="text-xs text-muted">
                              {item.customer_name || 'Anonymous'}
                              {item.rating ? ` · ${stars(item.rating)}` : ''}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}

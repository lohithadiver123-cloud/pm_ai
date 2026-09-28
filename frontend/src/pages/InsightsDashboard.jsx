import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Icon from '../components/Icon';
import {
  CategoryPieChart,
  FeaturePriorityChart,
  SentimentDonutChart,
  SeverityBarChart,
  TrendAreaChart,
} from '../components/Charts';
import { useBusy } from '../context/BusyContext';
import {
  Alert,
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  EmptyState,
  ErrorState,
  IconButton,
  Input,
  Modal,
  PageHeader,
  Select,
  SkeletonCardGrid,
  SkeletonChart,
  SkeletonStatGrid,
  Stat,
  StatGrid,
  Tabs,
} from '../components/ui';

const TABS = [
  { value: 'pain-points', label: 'Pain points' },
  { value: 'clusters', label: 'Feature clusters' },
  { value: 'themes', label: 'Themes' },
  { value: 'trends', label: 'Trends' },
];

const SEVERITY_TONE = { high: 'danger', medium: 'warning', low: 'success' };
const DEMAND_TONE = { high: 'accent', medium: 'warning', low: 'neutral' };

const SENTIMENT_KEYS = [
  { key: 'positive', tone: 'var(--success)' },
  { key: 'neutral', tone: 'var(--warning)' },
  { key: 'negative', tone: 'var(--danger)' },
];

function SentimentBar({ breakdown = {}, total = 1 }) {
  const sum = total || 1;
  return (
    <div className="bar-stack" aria-hidden="true">
      {SENTIMENT_KEYS.map(({ key, tone }) => (
        <span key={key} style={{ width: `${((breakdown[key] || 0) / sum) * 100}%`, background: tone }} />
      ))}
    </div>
  );
}

/**
 * Insights — what the feedback means.
 *
 * Order of argument: headline numbers, then the written summary, then the four
 * detail views. One primary action (re-run the analysis) and one settings
 * control; every other action lives inside the item it belongs to.
 */
export default function InsightsDashboard() {
  const navigate = useNavigate();
  const { begin } = useBusy();

  const [workspaces, setWorkspaces] = useState([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState('');
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState('');
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('pain-points');
  const [severityFilter, setSeverityFilter] = useState('all');

  const [aiStatus, setAiStatus] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [savingKey, setSavingKey] = useState(false);
  const [keyMessage, setKeyMessage] = useState('');
  const [notice, setNotice] = useState('');

  const fetchInsights = useCallback(async (workspaceId) => {
    if (!workspaceId) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get(`/insights/${workspaceId}`);
      setInsights(data);
    } catch (err) {
      const detail = (err.response?.data?.detail || '').toLowerCase();
      if (err.response?.status === 404 || detail.includes('no feedback')) {
        setInsights(null);
      } else {
        setError(err.response?.data?.detail || 'Could not load insights for this workspace.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get('/workspaces');
        setWorkspaces(data);
        if (data.length > 0) setSelectedWorkspace(data[0]._id);
        else setLoading(false);
      } catch {
        setError('Could not load your workspaces.');
        setLoading(false);
      }
      try {
        const { data } = await api.get('/insights/ai/status');
        setAiStatus(data);
      } catch {
        /* status is optional */
      }
    })();
  }, []);

  useEffect(() => {
    if (selectedWorkspace) fetchInsights(selectedWorkspace);
  }, [selectedWorkspace, fetchInsights]);

  const runAnalysis = async (path, label) => {
    if (!selectedWorkspace) return;
    const done = begin(label);
    setRunning(path);
    setError('');
    setNotice('');
    try {
      const { data } = await api.post(path);
      if (data?.agents_executed) {
        setNotice(`Analysis finished across ${data.agents_executed.length} agents: ${data.agents_executed.join(', ')}.`);
      }
      await fetchInsights(selectedWorkspace);
    } catch (err) {
      setError(err.response?.data?.detail || `${label} failed. Try again in a moment.`);
    } finally {
      setRunning('');
      done();
    }
  };

  const painPoints = insights?.pain_points || [];
  const clusters = insights?.feature_clusters || [];
  const themes = insights?.themes || [];
  const trends = insights?.trends || [];
  const filteredPainPoints =
    severityFilter === 'all' ? painPoints : painPoints.filter((pp) => pp.severity === severityFilter);

  const tabList = TABS.map((tab) => ({
    ...tab,
    count: { 'pain-points': painPoints.length, clusters: clusters.length, themes: themes.length, trends: trends.length }[tab.value],
  }));

  const hasData = insights && insights.total_analyzed > 0;

  return (
    <div className="page-container">
      <PageHeader
        icon="barChart"
        title="Insights"
        description="Themes, pain points, feature demand and sentiment trends extracted from this workspace's feedback."
        actions={
          <>
            <IconButton
              icon="sliders"
              label="AI engine settings"
              onClick={() => {
                setKeyMessage('');
                setShowSettings(true);
              }}
            />
            <Button
              variant="outline"
              icon="users"
              disabled={!selectedWorkspace}
              loading={running.endsWith('crew-ai-analyze')}
              onClick={() => runAnalysis(`/insights/${selectedWorkspace}/crew-ai-analyze`, 'Running the agent crew')}
            >
              Run agent crew
            </Button>
            <Button
              variant="primary"
              icon="zap"
              disabled={!selectedWorkspace}
              loading={running.endsWith('/analyze')}
              onClick={() => runAnalysis(`/insights/${selectedWorkspace}/analyze`, 'Extracting insights')}
            >
              {hasData ? 'Re-run analysis' : 'Run analysis'}
            </Button>
          </>
        }
      />

      {notice && <Alert variant="success">{notice}</Alert>}
      {error && <Alert variant="error">{error}</Alert>}

      <Card>
        <CardBody>
          <div className="row row-wrap row-between">
            <Select
              label="Workspace"
              value={selectedWorkspace}
              onChange={(e) => setSelectedWorkspace(e.target.value)}
              disabled={workspaces.length === 0}
            >
              {workspaces.length === 0 && <option value="">No workspaces</option>}
              {workspaces.map((ws) => (
                <option key={ws._id} value={ws._id}>
                  {ws.name}
                </option>
              ))}
            </Select>

            <span className="text-sm text-muted">
              {insights?.analyzed_at
                ? `Last analysed ${new Date(insights.analyzed_at).toLocaleString()}`
                : 'Not analysed yet'}
            </span>
          </div>
        </CardBody>
      </Card>

      {loading ? (
        <>
          <SkeletonStatGrid count={4} />
          <SkeletonChart label="Loading insights" />
          <SkeletonCardGrid count={2} />
        </>
      ) : error && !insights ? (
        <Card>
          <ErrorState
            title="Insights could not be loaded"
            onRetry={() => fetchInsights(selectedWorkspace)}
          >
            The insights service did not respond. Nothing was changed.
          </ErrorState>
        </Card>
      ) : !hasData ? (
        <Card>
          <EmptyState
            icon="inbox"
            title="Nothing analysed in this workspace yet"
            actions={
              <>
                <Button variant="outline" icon="download" onClick={() => navigate('/import')}>
                  Import feedback
                </Button>
                <Button
                  variant="primary"
                  icon="zap"
                  loading={running.endsWith('/analyze')}
                  onClick={() => runAnalysis(`/insights/${selectedWorkspace}/analyze`, 'Extracting insights')}
                >
                  Run analysis
                </Button>
              </>
            }
          >
            Import feedback first, then run the analysis to get themes, pain points and clusters.
          </EmptyState>
        </Card>
      ) : (
        <>
          <StatGrid>
            <Stat
              label="Sentiment health"
              value={`${insights.health_score ?? 0}%`}
              hint="Positive share, weighted by rating"
              featured
            />
            <Stat label="Feedback analysed" value={insights.total_analyzed} hint="Canonical records" />
            <Stat label="Pain points" value={painPoints.length} hint="Ranked by impact score" />
            <Stat label="Feature clusters" value={clusters.length} hint="Grouped opportunity areas" />
          </StatGrid>

          {insights.ai_summary && (
            <Card>
              <CardHeader title={`Executive summary — ${insights.ai_summary.headline}`} />
              <CardBody className="stack stack-md">
                <p className="prose">{insights.ai_summary.overview}</p>

                <div className="grid grid-2">
                  {insights.ai_summary.top_frictions?.length > 0 && (
                    <div className="callout callout-warning stack stack-sm">
                      <strong>Where customers get stuck</strong>
                      <ul className="styled-list">
                        {insights.ai_summary.top_frictions.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {insights.ai_summary.quick_wins?.length > 0 && (
                    <div className="callout stack stack-sm" style={{ background: 'var(--success-light)', borderColor: 'var(--success-line)' }}>
                      <strong>Cheapest wins</strong>
                      <ul className="styled-list">
                        {insights.ai_summary.quick_wins.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CardBody>
            </Card>
          )}

          <Tabs tabs={tabList} value={activeTab} onChange={setActiveTab} label="Insight views" />

          {activeTab === 'pain-points' && (
            <div className="stack">
              <Card>
                <CardHeader
                  title="Severity and impact"
                  hint="Every pain point, scored from volume, sentiment, ratings and bug count."
                  actions={
                    <Select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
                      <option value="all">All severities</option>
                      <option value="high">High only</option>
                      <option value="medium">Medium only</option>
                      <option value="low">Low only</option>
                    </Select>
                  }
                />
                <CardBody>
                  {painPoints.length === 0 ? (
                    <EmptyState icon="target" title="No pain points found">
                      The analysis did not identify any recurring customer pain in this set.
                    </EmptyState>
                  ) : (
                    <SeverityBarChart painPoints={painPoints} />
                  )}
                </CardBody>
              </Card>

              {filteredPainPoints.length === 0 ? (
                <Card>
                  <EmptyState
                    icon="filter"
                    title={`No ${severityFilter} severity pain points`}
                    actions={
                      <Button variant="secondary" onClick={() => setSeverityFilter('all')}>
                        Show all severities
                      </Button>
                    }
                  >
                    Try a different severity filter.
                  </EmptyState>
                </Card>
              ) : (
                <div className="insights-grid">
                  {filteredPainPoints.map((pp) => (
                    <Card key={pp.id} className={`severity-${pp.severity}`}>
                      <CardBody className="stack stack-md">
                        <div className="insight-card-header">
                          <div className="stack stack-sm">
                            <Badge tone={SEVERITY_TONE[pp.severity] || 'neutral'}>{pp.severity}</Badge>
                            <h3 className="insight-card-title">{pp.title}</h3>
                          </div>
                          <span className="impact-pill">
                            <strong>{pp.impact_score}</strong>/100
                          </span>
                        </div>

                        <p className="insight-card-desc">{pp.description}</p>

                        {pp.score_breakdown && (
                          <div className="callout text-xs text-muted stack stack-sm">
                            <strong className="text-sm">How this score was reached</strong>
                            <div>
                              {pp.score_breakdown.frequency} items · {pp.score_breakdown.negative_sentiment_pct}%
                              negative · avg rating {pp.score_breakdown.avg_rating} ·{' '}
                              {pp.score_breakdown.bug_count} bugs
                            </div>
                          </div>
                        )}

                        {pp.root_cause && (
                          <div className="ai-note-box">
                            <strong>Likely root cause: </strong>
                            {pp.root_cause}
                          </div>
                        )}

                        {pp.recommended_action && (
                          <div className="recommendation-box">
                            <strong>Recommended action: </strong>
                            {pp.recommended_action}
                          </div>
                        )}

                        {pp.sample_quotes?.length > 0 && (
                          <div className="quotes-section">
                            <span className="quotes-title">In their words</span>
                            {pp.sample_quotes.map((quote) => (
                              <blockquote key={quote} className="quote-bubble">
                                “{quote}”
                              </blockquote>
                            ))}
                          </div>
                        )}

                        <div className="insight-card-footer">
                          <span>
                            {pp.category?.replace(/_/g, ' ')} · {pp.affected_users_count} items
                          </span>
                        </div>

                        <Button
                          variant="outline"
                          size="sm"
                          icon="file"
                          fullWidth
                          onClick={() => navigate('/prds')}
                        >
                          Draft a PRD from this
                        </Button>
                      </CardBody>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'clusters' && (
            <div className="stack">
              <Card>
                <CardHeader
                  title="Feature opportunity priorities"
                  hint="Ranked by request volume, how many customers asked, and satisfaction upside."
                />
                <CardBody>
                  {clusters.length === 0 ? (
                    <EmptyState icon="layers" title="No feature clusters yet">
                      Import feature requests and re-run the analysis to group them.
                    </EmptyState>
                  ) : (
                    <FeaturePriorityChart clusters={clusters} />
                  )}
                </CardBody>
              </Card>

              {clusters.length > 0 && (
                <div className="insights-grid">
                  {clusters.map((cluster) => (
                    <Card key={cluster.id}>
                      <CardBody className="stack stack-md">
                        <div className="cluster-card-header">
                          <div className="stack stack-sm">
                            <Badge tone={DEMAND_TONE[cluster.demand_level] || 'neutral'}>
                              {cluster.demand_level} demand
                            </Badge>
                            <h3 className="cluster-title">{cluster.cluster_name}</h3>
                          </div>
                          <div className="priority-meter">
                            <span className="priority-score">{cluster.priority_score}</span>
                            <span className="priority-label">Score</span>
                          </div>
                        </div>

                        <p className="cluster-summary">{cluster.summary}</p>

                        {cluster.score_breakdown?.formula_weights && (
                          <div className="callout text-xs text-muted">
                            <strong className="text-sm">Scoring weights: </strong>
                            {cluster.score_breakdown.formula_weights}
                          </div>
                        )}

                        {cluster.keywords?.length > 0 && (
                          <div className="keyword-tags">
                            {cluster.keywords.map((keyword) => (
                              <span key={keyword} className="keyword-pill">
                                {keyword}
                              </span>
                            ))}
                          </div>
                        )}

                        {cluster.sample_requests?.length > 0 && (
                          <div className="quotes-section">
                            <span className="quotes-title">
                              {cluster.request_count} requests from{' '}
                              {cluster.unique_customers_count || cluster.request_count} customers
                            </span>
                            {cluster.sample_requests.map((request) => (
                              <blockquote key={request} className="quote-bubble">
                                “{request}”
                              </blockquote>
                            ))}
                          </div>
                        )}

                        <div className="cluster-footer">
                          <span>{cluster.request_count} requests</span>
                          <div className="progress" style={{ width: 80 }}>
                            <span className="progress-fill" style={{ width: `${cluster.priority_score}%` }} />
                          </div>
                        </div>

                        <Button
                          variant="outline"
                          size="sm"
                          icon="file"
                          fullWidth
                          onClick={() => navigate('/prds')}
                        >
                          Draft a PRD from this
                        </Button>
                      </CardBody>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'themes' && (
            <div className="stack">
              {themes.length === 0 ? (
                <Card>
                  <EmptyState icon="layers" title="No themes extracted">
                    Re-run the analysis to mine recurring topics from this feedback.
                  </EmptyState>
                </Card>
              ) : (
                <div className="insights-grid">
                  {themes.map((theme) => (
                    <Card key={theme.id}>
                      <CardBody className="stack stack-md">
                        <div className="theme-card-header">
                          <h3 className="theme-title">{theme.title}</h3>
                          <span className="theme-freq-pill">{theme.frequency} mentions</span>
                        </div>

                        <p className="theme-desc">{theme.description}</p>

                        <div className="sentiment-bar-section">
                          <div className="sentiment-bar-labels">
                            {SENTIMENT_KEYS.map(({ key }) => (
                              <span key={key} className={`text-${key === 'positive' ? 'success' : key === 'neutral' ? 'warning' : 'danger'}`}>
                                {theme.sentiment_breakdown?.[key] || 0} {key}
                              </span>
                            ))}
                          </div>
                          <SentimentBar breakdown={theme.sentiment_breakdown} total={theme.frequency} />
                        </div>

                        {theme.sample_quotes?.length > 0 && (
                          <div className="quotes-section">
                            <span className="quotes-title">In their words</span>
                            {theme.sample_quotes.map((quote) => (
                              <blockquote key={quote} className="quote-bubble">
                                “{quote}”
                              </blockquote>
                            ))}
                          </div>
                        )}

                        {theme.keywords?.length > 0 && (
                          <div className="keyword-tags">
                            {theme.keywords.map((keyword) => (
                              <span key={keyword} className="keyword-pill">
                                {keyword}
                              </span>
                            ))}
                          </div>
                        )}
                      </CardBody>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'trends' && (
            <div className="stack">
              {trends.length === 0 ? (
                <Card>
                  <EmptyState icon="trendingUp" title="No trend data yet">
                    Trends appear once feedback spans more than one time period.
                  </EmptyState>
                </Card>
              ) : (
                <>
                  <Card>
                    <CardHeader
                      title="Volume and sentiment over time"
                      hint="Hover any point for the period's counts and top category."
                    />
                    <CardBody>
                      <TrendAreaChart trends={trends} />
                    </CardBody>
                  </Card>

                  <Card flush>
                    <CardHeader title="Period detail" />
                    <div className="table-responsive">
                      <table className="table">
                        <thead>
                          <tr>
                            <th scope="col">Period</th>
                            <th scope="col">Volume</th>
                            <th scope="col">Positive</th>
                            <th scope="col">Neutral</th>
                            <th scope="col">Negative</th>
                            <th scope="col">Score</th>
                            <th scope="col">Top category</th>
                          </tr>
                        </thead>
                        <tbody>
                          {trends.map((row) => {
                            const tone =
                              row.sentiment_score > 0.1 ? 'success' : row.sentiment_score < -0.1 ? 'danger' : 'warning';
                            return (
                              <tr key={row.period}>
                                <td className="text-semibold">{row.period}</td>
                                <td>{row.total_count}</td>
                                <td className="text-success">{row.positive_count}</td>
                                <td className="text-warning">{row.neutral_count}</td>
                                <td className="text-danger">{row.negative_count}</td>
                                <td>
                                  <Badge tone={tone}>
                                    {row.sentiment_score > 0 ? `+${row.sentiment_score}` : row.sentiment_score}
                                  </Badge>
                                </td>
                                <td>
                                  <span className="badge badge-neutral">
                                    {row.top_category?.replace(/_/g, ' ')}
                                  </span>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </Card>
                </>
              )}
            </div>
          )}
        </>
      )}

      {/* Distribution charts live behind the summary so the tab panels stay scannable. */}
      {hasData && activeTab === 'themes' && (
        <div className="grid grid-2">
          <Card>
            <CardHeader title="Category mix" />
            <CardBody>
              <CategoryPieChart
                categoryDistribution={insights.by_category || {}}
                totalFeedback={insights.total_analyzed}
              />
            </CardBody>
          </Card>
          <Card>
            <CardHeader title="Sentiment split" />
            <CardBody>
              <SentimentDonutChart
                positive={insights.by_sentiment?.positive || 0}
                neutral={insights.by_sentiment?.neutral || 0}
                negative={insights.by_sentiment?.negative || 0}
                healthScore={insights.health_score || 0}
              />
            </CardBody>
          </Card>
        </div>
      )}

      <Modal
        open={showSettings}
        onClose={() => setShowSettings(false)}
        title="AI engine"
        description="Status of the analysis provider and the key it uses."
        icon="sliders"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowSettings(false)}>
              Close
            </Button>
            <Button
              variant="primary"
              loading={savingKey}
              disabled={!apiKey.trim()}
              onClick={async () => {
                setSavingKey(true);
                setKeyMessage('');
                try {
                  const { data } = await api.post('/insights/ai/configure-key', { api_key: apiKey.trim() });
                  setAiStatus(data);
                  setKeyMessage('Key accepted — analysis is ready to run.');
                  setApiKey('');
                } catch (err) {
                  setKeyMessage(err.response?.data?.detail || 'That key was rejected.');
                } finally {
                  setSavingKey(false);
                }
              }}
            >
              Verify and save
            </Button>
          </>
        }
      >
        <div className="modal-body">
          <Alert variant={aiStatus?.available ? 'success' : 'warning'} title={aiStatus?.status || 'Checking status…'}>
            {aiStatus?.message}
          </Alert>

          <Input
            label="Provider API key"
            type="password"
            placeholder="gsk_…"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            hint="Stored server-side and used only for analysis."
          />

          {keyMessage && <Alert variant="info">{keyMessage}</Alert>}

          <a
            className="text-sm row"
            style={{ gap: 'var(--sp-1)' }}
            href="https://console.groq.com/keys"
            target="_blank"
            rel="noopener noreferrer"
          >
            Get a free key <Icon name="external" size={13} />
          </a>

        </div>
      </Modal>
    </div>
  );
}

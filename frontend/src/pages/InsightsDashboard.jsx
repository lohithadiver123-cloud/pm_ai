/**
 * InsightsDashboard page - Milestone 2.
 * Displays Theme Extraction, Customer Pain Points (with severity scoring & explainability),
 * Feature Request Clusters (with demand/priority scoring & unique customer counts),
 * and Trend Analysis with interactive Area Chart.
 */
import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import {
  SentimentDonutChart,
  CategoryPieChart,
  TrendAreaChart,
  SeverityBarChart,
  FeaturePriorityChart,
} from '../components/Charts';

function InsightsDashboard() {
  const [workspaces, setWorkspaces] = useState([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState('');
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('pain-points'); // 'pain-points' | 'clusters' | 'themes' | 'trends'
  const [severityFilter, setSeverityFilter] = useState('all');

  // Groq AI states
  const [aiStatus, setAiStatus] = useState(null);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [savingKey, setSavingKey] = useState(false);
  const [keyMessage, setKeyMessage] = useState('');

  const fetchAiStatus = async () => {
    try {
      const res = await api.get('/insights/ai/status');
      setAiStatus(res.data);
    } catch (err) {
      // Ignored
    }
  };

  // Fetch workspaces and AI status on mount
  useEffect(() => {
    fetchWorkspaces();
    fetchAiStatus();
  }, []);

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

  const fetchInsights = useCallback(async (workspaceId) => {
    if (!workspaceId) return;
    setLoading(true);
    setError('');
    try {
      const response = await api.get(`/insights/${workspaceId}`);
      setInsights(response.data);
    } catch (err) {
      // If no cached insights exist (404 or 0 analyzed), auto-trigger analysis
      const status = err.response?.status;
      if (status === 404 || (err.response?.data?.detail || '').toLowerCase().includes('no feedback')) {
        // Auto-run analysis silently
        try {
          setLoading(false);
          setAnalyzing(true);
          const res = await api.post(`/insights/${workspaceId}/analyze`);
          setInsights(res.data);
        } catch (analyzeErr) {
          setError(analyzeErr.response?.data?.detail || 'Failed to generate insights. Please click "Re-Run AI Analysis".');
        } finally {
          setAnalyzing(false);
        }
      } else {
        setError(err.response?.data?.detail || 'Failed to fetch insights. Click "Re-Run AI Analysis" to generate fresh insights.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedWorkspace) {
      fetchInsights(selectedWorkspace);
    }
  }, [selectedWorkspace, fetchInsights]);

  const handleRunAnalysis = async () => {
    if (!selectedWorkspace) return;
    setAnalyzing(true);
    setError('');
    try {
      const response = await api.post(`/insights/${selectedWorkspace}/analyze`);
      setInsights(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  // Filter pain points
  const filteredPainPoints = insights?.pain_points?.filter((pp) => {
    if (severityFilter === 'all') return true;
    return pp.severity === severityFilter;
  }) || [];

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Product Intelligence & Insights</h1>
          <p className="page-subtitle">
            Automated Theme Extraction, Pain Point Severity, Feature Clustering & Trends
          </p>
        </div>
        <div className="page-actions" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            className="btn btn-primary"
            onClick={handleRunAnalysis}
            disabled={analyzing || loading || !selectedWorkspace}
          >
            {analyzing ? 'Extracting Insights with AI...' : 'Re-Run AI Analysis'}
          </button>
        </div>
      </div>

      {/* Workspace Selector Bar */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: '1 1 300px' }}>
            <label style={{ fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
              Select Workspace:
            </label>
            <select
              value={selectedWorkspace}
              onChange={(e) => setSelectedWorkspace(e.target.value)}
              className="select-input"
              style={{ maxWidth: '340px' }}
            >
              {workspaces.map((ws) => (
                <option key={ws._id} value={ws._id}>
                  {ws.name}
                </option>
              ))}
            </select>
          </div>
          {insights?.analyzed_at && (
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Last analyzed: {new Date(insights.analyzed_at).toLocaleTimeString()} ({new Date(insights.analyzed_at).toLocaleDateString()})
            </span>
          )}
        </div>
      </div>


      {loading || analyzing ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>{analyzing ? 'Running AI analysis on your feedback...' : 'Loading insights...'}</p>
        </div>
      ) : error ? (
        <div className="card" style={{ padding: '2.5rem', textAlign: 'center' }}>
          <h3 style={{ marginBottom: '0.5rem', color: 'var(--text)' }}>Could not load insights</h3>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', maxWidth: '480px', margin: '0 auto 1.5rem' }}>{error}</p>
          <button
            className="btn btn-primary"
            onClick={handleRunAnalysis}
            disabled={analyzing || !selectedWorkspace}
          >
            Run Analysis Now
          </button>
        </div>
      ) : !insights || insights.total_analyzed === 0 ? (
        <div className="empty-state card" style={{ padding: '3rem', textAlign: 'center' }}>
          <h3>No Feedback Records in this Workspace</h3>
          <p>Import feedback via the <strong>Import Data</strong> tab, then click <strong>Re-Run AI Analysis</strong> to generate themes, pain points, and clusters.</p>
        </div>
      ) : (
        <>
          {/* Executive Metrics Overview */}
          <div className="kpi-grid" style={{ marginBottom: '1.5rem' }}>
            <div className="kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">Product Sentiment Health</span>
              </div>
              <div className="kpi-value">{insights.health_score ?? 75}%</div>
              <div className="kpi-footer">Calculated from sentiment & ratings</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">Feedback Analyzed</span>
              </div>
              <div className="kpi-value">{insights.total_analyzed}</div>
              <div className="kpi-footer">Total canonical records</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">Identified Pain Points</span>
              </div>
              <div className="kpi-value">{insights.pain_points?.length || 0}</div>
              <div className="kpi-footer">Ranked by severity & impact</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">Feature Clusters</span>
              </div>
              <div className="kpi-value">{insights.feature_clusters?.length || 0}</div>
              <div className="kpi-footer">Synthesized opportunity groups</div>
            </div>
          </div>

          {/* AI Executive Briefing Card (Milestone 2 AI Enhancement) */}
          {insights.ai_summary && (
            <div className="card" style={{ marginBottom: '1.5rem', borderLeft: '4px solid var(--primary)', backgroundColor: 'var(--bg-card)' }}>
              <div className="card-body" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: 'var(--text)' }}>
                      Executive Summary: {insights.ai_summary.headline}
                    </h3>
                  </div>
                  <span style={{ fontSize: '11px', fontWeight: 600, padding: '4px 10px', borderRadius: '12px', backgroundColor: 'var(--primary-light)', color: 'var(--primary)' }}>
                    AI-Powered Analysis
                  </span>
                </div>
                <p style={{ fontSize: '14px', color: 'var(--text)', lineHeight: 1.5, marginBottom: '14px' }}>
                  {insights.ai_summary.overview}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
                  {insights.ai_summary.top_frictions?.length > 0 && (
                    <div style={{ padding: '12px 14px', backgroundColor: 'rgba(168, 83, 76, 0.08)', borderRadius: '8px', border: '1px solid rgba(168, 83, 76, 0.2)' }}>
                      <strong style={{ color: '#A8534C', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        Critical Customer Frictions
                      </strong>
                      <ul style={{ margin: '8px 0 0 16px', padding: 0, fontSize: '12.5px', color: 'var(--text)' }}>
                        {insights.ai_summary.top_frictions.map((f, i) => (
                          <li key={i} style={{ marginBottom: '4px' }}>{f}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {insights.ai_summary.quick_wins?.length > 0 && (
                    <div style={{ padding: '12px 14px', backgroundColor: 'rgba(53, 92, 82, 0.08)', borderRadius: '8px', border: '1px solid rgba(53, 92, 82, 0.2)' }}>
                      <strong style={{ color: '#2E7D32', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        High-Impact Quick Wins
                      </strong>
                      <ul style={{ margin: '8px 0 0 16px', padding: 0, fontSize: '12.5px', color: 'var(--text)' }}>
                        {insights.ai_summary.quick_wins.map((q, i) => (
                          <li key={i} style={{ marginBottom: '4px' }}>{q}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="insights-tabs">
            <button
              className={`tab-btn ${activeTab === 'pain-points' ? 'active' : ''}`}
              onClick={() => setActiveTab('pain-points')}
            >
              Customer Pain Points ({insights.pain_points?.length || 0})
            </button>
            <button
              className={`tab-btn ${activeTab === 'clusters' ? 'active' : ''}`}
              onClick={() => setActiveTab('clusters')}
            >
              Feature Request Clusters ({insights.feature_clusters?.length || 0})
            </button>
            <button
              className={`tab-btn ${activeTab === 'themes' ? 'active' : ''}`}
              onClick={() => setActiveTab('themes')}
            >
              Theme Extraction ({insights.themes?.length || 0})
            </button>
            <button
              className={`tab-btn ${activeTab === 'trends' ? 'active' : ''}`}
              onClick={() => setActiveTab('trends')}
            >
              Trend & Trajectory ({insights.trends?.length || 0})
            </button>
          </div>

          {/* TAB 1: PAIN POINTS */}
          {activeTab === 'pain-points' && (
            <div>
              <div className="card" style={{ marginBottom: '1.25rem' }}>
                <div className="card-body" style={{ padding: '16px 20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
                    <div>
                      <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>Severity & Impact Overview</h3>
                      <p style={{ color: 'var(--text-muted)', margin: '4px 0 0', fontSize: '13px' }}>
                        High-friction friction areas sorted by deterministic impact score.
                      </p>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Filter Severity:</span>
                      <select
                        value={severityFilter}
                        onChange={(e) => setSeverityFilter(e.target.value)}
                        className="select-input"
                        style={{ padding: '0.3rem 0.6rem', fontSize: '0.85rem' }}
                      >
                        <option value="all">All Severities</option>
                        <option value="high">High Severity</option>
                        <option value="medium">Medium Severity</option>
                        <option value="low">Low Severity</option>
                      </select>
                    </div>
                  </div>
                  <SeverityBarChart painPoints={insights.pain_points || []} />
                </div>
              </div>

              {filteredPainPoints.length === 0 ? (
                <div className="card card-body" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                  No pain points match the selected filter.
                </div>
              ) : (
                <div className="insights-grid">
                  {filteredPainPoints.map((pp) => (
                    <div key={pp.id} className={`insight-card severity-${pp.severity}`}>
                      <div className="insight-card-header">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span className={`badge-severity badge-${pp.severity}`}>
                            {pp.severity.toUpperCase()}
                          </span>
                          <h3 className="insight-card-title">{pp.title}</h3>
                        </div>
                        <span className="impact-pill">
                          Impact: <strong>{pp.impact_score}/100</strong>
                        </span>
                      </div>

                      <p className="insight-card-desc">{pp.description}</p>

                      {/* Explainability Breakdown */}
                      {pp.score_breakdown && (
                        <div style={{
                          backgroundColor: 'rgba(0,0,0,0.03)',
                          border: '1px dashed var(--border)',
                          borderRadius: '6px',
                          padding: '8px 12px',
                          marginBottom: '12px',
                          fontSize: '11px',
                          color: 'var(--text-muted)'
                        }}>
                          <div style={{ fontWeight: 600, color: 'var(--text)', marginBottom: '2px' }}>
                            Impact Score Formula Components:
                          </div>
                          <div>
                            Volume: <strong>{pp.score_breakdown.frequency} items</strong> • Negative Sentiment: <strong>{pp.score_breakdown.negative_sentiment_pct}%</strong> • Avg Rating: <strong>{pp.score_breakdown.avg_rating}</strong> • Bugs: <strong>{pp.score_breakdown.bug_count}</strong>
                          </div>
                        </div>
                      )}

                      {/* AI Root Cause Diagnosis */}
                      {pp.root_cause && (
                        <div style={{
                          backgroundColor: 'rgba(53, 92, 82, 0.07)',
                          border: '1px solid rgba(53, 92, 82, 0.22)',
                          borderRadius: '6px',
                          padding: '8px 12px',
                          marginBottom: '12px',
                          fontSize: '12px',
                          color: 'var(--text)'
                        }}>
                          <strong style={{ color: 'var(--primary)' }}>Root Cause Diagnosis: </strong>
                          {pp.root_cause}
                        </div>
                      )}

                      <div className="recommendation-box">
                        <div>
                          <strong>Recommended Action:</strong> {pp.recommended_action}
                        </div>
                      </div>

                      {pp.sample_quotes?.length > 0 && (
                        <div className="quotes-section">
                          <span className="quotes-title">Representative User Quotes (Deduplicated):</span>
                          {pp.sample_quotes.map((q, idx) => (
                            <div key={idx} className="quote-bubble">
                              "{q}"
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="insight-card-footer">
                        <span>Category: <strong>{pp.category?.replace(/_/g, ' ')}</strong></span>
                        <span>Affected Records: <strong>{pp.affected_users_count} items</strong></span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: FEATURE CLUSTERS */}
          {activeTab === 'clusters' && (
            <div>
              <div className="card" style={{ marginBottom: '1.25rem' }}>
                <div className="card-body" style={{ padding: '16px 20px' }}>
                  <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>Feature Opportunity Priorities</h3>
                  <p style={{ color: 'var(--text-muted)', margin: '4px 0 12px', fontSize: '13px' }}>
                    Ranked by request volume, customer breadth, and user satisfaction potential.
                  </p>
                  <FeaturePriorityChart clusters={insights.feature_clusters || []} />
                </div>
              </div>

              {insights.feature_clusters?.length === 0 ? (
                <div className="card card-body" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                  No feature clusters found. Import feature requests to generate clusters.
                </div>
              ) : (
                <div className="insights-grid">
                  {insights.feature_clusters.map((cluster) => (
                    <div key={cluster.id} className="cluster-card">
                      <div className="cluster-card-header">
                        <div>
                          <span className={`badge-demand badge-demand-${cluster.demand_level}`}>
                            {cluster.demand_level.toUpperCase()} DEMAND
                          </span>
                          <h3 className="cluster-title">{cluster.cluster_name}</h3>
                        </div>
                        <div className="priority-meter">
                          <span className="priority-score">{cluster.priority_score}</span>
                          <span className="priority-label">Priority</span>
                        </div>
                      </div>

                      <p className="cluster-summary">{cluster.summary}</p>

                      {/* Score breakdown info */}
                      {cluster.score_breakdown && (
                        <div style={{
                          backgroundColor: 'rgba(0,0,0,0.03)',
                          border: '1px dashed var(--border)',
                          borderRadius: '6px',
                          padding: '8px 12px',
                          marginBottom: '12px',
                          fontSize: '11px',
                          color: 'var(--text-muted)'
                        }}>
                          <span style={{ fontWeight: 600, color: 'var(--text)' }}>Formula Weights: </span>
                          {cluster.score_breakdown.formula_weights}
                        </div>
                      )}

                      {/* Keywords pills */}
                      {cluster.keywords?.length > 0 && (
                        <div className="keyword-tags">
                          {cluster.keywords.map((kw, i) => (
                            <span key={i} className="keyword-pill">
                              #{kw}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Sample user requests */}
                      {cluster.sample_requests?.length > 0 && (
                        <div className="quotes-section">
                          <span className="quotes-title">
                            Distinct Quotes ({cluster.request_count} total requests from {cluster.unique_customers_count || cluster.request_count} unique users):
                          </span>
                          {cluster.sample_requests.map((req, i) => (
                            <div key={i} className="quote-bubble">
                              "{req}"
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="cluster-footer">
                        <span>
                          Requests: <strong>{cluster.request_count}</strong> (<strong>{cluster.unique_customers_count || cluster.request_count}</strong> unique customers)
                        </span>
                        <div className="progress-bar-container">
                          <div
                            className="progress-bar-fill"
                            style={{ width: `${cluster.priority_score}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: THEMES */}
          {activeTab === 'themes' && (
            <div>
              <p style={{ color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                Recurring topics mined from customer feedback with exact sentiment breakdowns from analyzed records.
              </p>

              <div className="insights-grid">
                {insights.themes?.map((theme) => (
                  <div key={theme.id} className="theme-card">
                    <div className="theme-card-header">
                      <h3 className="theme-title">{theme.title}</h3>
                      <span className="theme-freq-pill">{theme.frequency} mentions</span>
                    </div>

                    <p className="theme-desc">{theme.description}</p>

                    {/* Sentiment Distribution Bar */}
                    <div className="sentiment-bar-section">
                      <div className="sentiment-bar-labels">
                        <span style={{ color: '#2E7D32', fontWeight: 600 }}>{theme.sentiment_breakdown?.positive || 0} Positive</span>
                        <span style={{ color: '#E65100', fontWeight: 600 }}>{theme.sentiment_breakdown?.neutral || 0} Neutral</span>
                        <span style={{ color: '#C62828', fontWeight: 600 }}>{theme.sentiment_breakdown?.negative || 0} Negative</span>
                      </div>
                      <div className="multi-bar" style={{ height: '8px', borderRadius: '4px', display: 'flex', overflow: 'hidden', backgroundColor: 'var(--border)' }}>
                        <div
                          style={{
                            width: `${((theme.sentiment_breakdown?.positive || 0) / (theme.frequency || 1)) * 100}%`,
                            backgroundColor: '#2E7D32',
                          }}
                        />
                        <div
                          style={{
                            width: `${((theme.sentiment_breakdown?.neutral || 0) / (theme.frequency || 1)) * 100}%`,
                            backgroundColor: '#E65100',
                          }}
                        />
                        <div
                          style={{
                            width: `${((theme.sentiment_breakdown?.negative || 0) / (theme.frequency || 1)) * 100}%`,
                            backgroundColor: '#C62828',
                          }}
                        />
                      </div>
                    </div>

                    {/* Distinct Representative Quotes */}
                    {theme.sample_quotes?.length > 0 && (
                      <div className="quotes-section" style={{ marginTop: '10px' }}>
                        <span className="quotes-title">Deduplicated Quotes:</span>
                        {theme.sample_quotes.map((q, idx) => (
                          <div key={idx} className="quote-bubble">
                            "{q}"
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Top Keywords */}
                    {theme.keywords?.length > 0 && (
                      <div className="keyword-tags" style={{ marginTop: '0.75rem' }}>
                        {theme.keywords.map((kw, i) => (
                          <span key={i} className="keyword-pill">
                            {kw}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 4: TRENDS */}
          {activeTab === 'trends' && (
            <div>
              <p style={{ color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                Chronological volume velocity and sentiment trajectory across time intervals.
              </p>

              {/* Multi-Series Interactive Area Trend Chart */}
              <div className="card" style={{ marginBottom: '1.5rem' }}>
                <div className="card-body" style={{ padding: '20px' }}>
                  <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>Trend Trajectory & Sentiment Area Graph</h3>
                  <p style={{ color: 'var(--text-muted)', margin: '4px 0 16px', fontSize: '13px' }}>
                    Interactive volume and sentiment counts plotted along the timeline. Hover over points for details.
                  </p>
                  <TrendAreaChart trends={insights.trends || []} />
                </div>
              </div>

              {/* Detailed Trend Table */}
              <div className="card">
                <div className="card-body" style={{ padding: 0 }}>
                  <div className="table-responsive">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Time Period</th>
                          <th>Total Volume</th>
                          <th>Positive</th>
                          <th>Neutral</th>
                          <th>Negative</th>
                          <th>Sentiment Score</th>
                          <th>Top Category</th>
                        </tr>
                      </thead>
                      <tbody>
                        {insights.trends?.map((t, idx) => (
                          <tr key={idx}>
                            <td><strong>{t.period}</strong></td>
                            <td><span className="badge-count">{t.total_count}</span></td>
                            <td style={{ color: '#2E7D32', fontWeight: 600 }}>{t.positive_count}</td>
                            <td style={{ color: '#E65100', fontWeight: 600 }}>{t.neutral_count}</td>
                            <td style={{ color: '#C62828', fontWeight: 600 }}>{t.negative_count}</td>
                            <td>
                              <span
                                className={`sentiment-badge ${
                                  t.sentiment_score > 0.1
                                    ? 'positive'
                                    : t.sentiment_score < -0.1
                                    ? 'negative'
                                    : 'neutral'
                                }`}
                              >
                                {t.sentiment_score > 0 ? `+${t.sentiment_score}` : t.sentiment_score}
                              </span>
                            </td>
                            <td>
                              <span className="category-badge">
                                {t.top_category?.replace(/_/g, ' ')}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* AI Key Configuration Modal */}
      {showKeyModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '20px'
        }}>
          <div className="card" style={{ maxWidth: '480px', width: '100%', padding: '24px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '8px' }}>AI Engine Settings</h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
              AI-powered intelligence engine to analyze customer pain points, extract themes, and cluster product feature requests.
            </p>

            <div style={{
              padding: '10px 14px',
              backgroundColor: aiStatus?.available ? 'rgba(53, 92, 82, 0.08)' : 'rgba(184, 130, 50, 0.08)',
              borderRadius: '6px',
              border: `1px solid ${aiStatus?.available ? 'var(--primary)' : 'var(--warning)'}`,
              marginBottom: '16px',
              fontSize: '12.5px'
            }}>
              <div><strong>Status:</strong> {aiStatus?.status || 'Checking...'}</div>

              {aiStatus?.message && <div style={{ color: 'var(--text-muted)', marginTop: '4px' }}>{aiStatus.message}</div>}
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
                Groq API Key:
              </label>
              <input
                type="password"
                placeholder="gsk_..."
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
                className="select-input"
                style={{ width: '100%', padding: '8px 12px' }}
              />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                Free key at <a href="https://console.groq.com/keys" target="_blank" rel="noreferrer" style={{ color: 'var(--primary)' }}>console.groq.com/keys</a>
              </span>
            </div>

            {keyMessage && (
              <div style={{ fontSize: '12px', marginBottom: '12px', color: keyMessage.includes('Success') ? 'var(--primary)' : '#C62828' }}>
                {keyMessage}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button className="btn btn-secondary" onClick={() => { setShowKeyModal(false); setKeyMessage(''); }}>
                Close
              </button>
              <button
                className="btn btn-primary"
                disabled={savingKey || !apiKeyInput.trim()}
                onClick={async () => {
                  setSavingKey(true);
                  setKeyMessage('');
                  try {
                    const res = await api.post('/insights/ai/configure-key', { api_key: apiKeyInput.trim() });
                    setAiStatus(res.data);
                    setKeyMessage('Successfully connected to Groq AI');
                    setApiKeyInput('');
                  } catch (err) {
                    setKeyMessage(err.response?.data?.detail || 'Failed to validate API key.');
                  } finally {
                    setSavingKey(false);
                  }
                }}
              >
                {savingKey ? 'Validating...' : 'Save & Verify Key'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default InsightsDashboard;

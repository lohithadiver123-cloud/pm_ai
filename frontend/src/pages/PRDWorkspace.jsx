import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Icon from '../components/Icon';
import { useBusy } from '../context/BusyContext';
import { useWorkspaces } from '../context/WorkspaceContext';
import {
  Alert,
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  EmptyState,
  IconButton,
  Input,
  Modal,
  PageHeader,
  ProgressBar,
  Segmented,
  Select,
  Skeleton,
  SkeletonList,
  Tabs,
  Textarea,
  WorkspaceSwitcher,
} from '../components/ui';

const STATUS_TONE = { draft: 'neutral', in_review: 'warning', approved: 'success', archived: 'neutral' };
const SOURCE_LABEL = {
  feature_cluster: 'Feature cluster',
  pain_point: 'Pain point',
  custom: 'Custom brief',
};

const GENERATION_STEPS = [
  'Reading the feedback records for this workspace',
  'Extracting personas and recurring pain points',
  'Writing requirements, SLAs and success metrics',
  'Formatting the document',
];

/**
 * The insights sub-endpoints (`/insights/{id}/clusters`, `/pain-points`)
 * answer with a bare JSON array. Accept a wrapped object too, so a change in
 * either direction can never silently collapse the pickers to zero.
 */
const asList = (payload, key) => {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload && payload[key])) return payload[key];
  return [];
};

/** One numbered section of the document — same shape for all of them. */
function DocSection({ index, title, children }) {
  return (
    <section className="doc-section">
      <h3 className="section-title">
        <span className="sec-num" aria-hidden="true">
          {index}
        </span>
        {title}
      </h3>
      {children}
    </section>
  );
}

/**
 * PRD Studio — the document side of the workflow.
 *
 * Documents on the left, the selected one on the right. The page has one
 * primary action (generate); everything else acts on the document currently
 * open, so there is never a doubt about what a button will affect.
 */
export default function PRDWorkspace() {
  const navigate = useNavigate();
  const { begin } = useBusy();

  const { activeId: workspaceId, ready } = useWorkspaces();
  const [prds, setPrds] = useState([]);
  const [selected, setSelected] = useState(null);
  const [clusters, setClusters] = useState([]);
  const [painPoints, setPainPoints] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [contextError, setContextError] = useState('');
  const [tab, setTab] = useState('structured');
  const [pendingDelete, setPendingDelete] = useState(null);

  const [showGenerate, setShowGenerate] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [step, setStep] = useState(0);
  const [sourceType, setSourceType] = useState('custom');
  const [clusterId, setClusterId] = useState('');
  const [painPointId, setPainPointId] = useState('');
  const [prompt, setPrompt] = useState('');
  const [title, setTitle] = useState('');
  const [audience, setAudience] = useState('');
  const [tone, setTone] = useState('comprehensive');

  const loadContext = useCallback(async (id) => {
    const [clusterResult, painResult] = await Promise.allSettled([
      api.get(`/insights/${id}/clusters`),
      api.get(`/insights/${id}/pain-points`),
    ]);
    if (clusterResult.status === 'fulfilled') setClusters(asList(clusterResult.value.data, 'clusters'));
    if (painResult.status === 'fulfilled') setPainPoints(asList(painResult.value.data, 'pain_points'));
    // Both failing means the Generate button stays disabled with nothing to
    // explain why — say so instead of showing two empty pickers.
    if (clusterResult.status === 'rejected' && painResult.status === 'rejected') {
      setContextError('Could not load this workspace\u2019s clusters and pain points, so there is nothing to ground the document in yet.');
    } else {
      setContextError('');
    }
  }, []);

  const loadPrds = useCallback(async (id) => {
    if (!id) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get(`/prd/workspace/${id}`);
      setPrds(data);
      setSelected((current) => data.find((p) => p.id === current?.id) || data[0] || null);
    } catch {
      setError('Could not load the documents for this workspace.');
      setPrds([]);
      setSelected(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Both lists follow the shared selection, so switching workspace anywhere in
  // the app reloads this page as well.
  useEffect(() => {
    if (!workspaceId) return undefined;
    Promise.all([loadPrds(workspaceId), loadContext(workspaceId)]);
    return undefined;
  }, [workspaceId, loadPrds, loadContext]);

  useEffect(() => {
    if (ready && !workspaceId) setLoading(false);
  }, [ready, workspaceId]);

  const changeStatus = async (status) => {
    if (!selected) return;
    const previous = { prds, selected };
    setSelected({ ...selected, status });
    try {
      const { data } = await api.put(`/prd/${selected.id}`, { status });
      setSelected(data);
      setPrds((prev) => prev.map((p) => (p.id === data.id ? data : p)));
    } catch {
      setPrds(previous.prds);
      setSelected(previous.selected);
      setError('Could not change the document status.');
    }
  };

  const confirmDelete = async () => {
    const prd = pendingDelete;
    setPendingDelete(null);
    if (!prd) return;
    const previous = prds;
    setPrds((prev) => prev.filter((p) => p.id !== prd.id));
    if (selected?.id === prd.id) setSelected(previous.find((p) => p.id !== prd.id) || null);
    try {
      await api.delete(`/prd/${prd.id}`);
      setNotice(`Deleted “${prd.title}”.`);
    } catch {
      setPrds(previous);
      setError('Could not delete that document.');
    }
  };

  const generate = async () => {
    if (!workspaceId) return;
    const done = begin('Generating the document');
    setGenerating(true);
    setError('');
    setStep(0);

    const timer = setInterval(() => setStep((s) => Math.min(s + 1, GENERATION_STEPS.length - 1)), 2200);

    try {
      const { data } = await api.post('/prd/generate', {
        workspace_id: workspaceId,
        title: title || undefined,
        feature_cluster_id: sourceType === 'cluster' ? clusterId : undefined,
        pain_point_id: sourceType === 'pain_point' ? painPointId : undefined,
        custom_prompt: prompt || undefined,
        target_audience: audience || undefined,
        tone,
      });
      setShowGenerate(false);
      setTitle('');
      setPrompt('');
      await loadPrds(workspaceId);
      setSelected(data);
      setNotice('Document generated.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Generation failed. Try again in a moment.');
    } finally {
      clearInterval(timer);
      setGenerating(false);
      done();
    }
  };

  const copyMarkdown = async () => {
    if (!selected?.raw_markdown) return;
    try {
      await navigator.clipboard.writeText(selected.raw_markdown);
      setNotice('Markdown copied to the clipboard.');
    } catch {
      setError('The browser blocked clipboard access.');
    }
  };

  const downloadMarkdown = () => {
    if (!selected?.raw_markdown) return;
    const url = URL.createObjectURL(new Blob([selected.raw_markdown], { type: 'text/markdown' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `${selected.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const canGenerate =
    sourceType === 'custom' || (sourceType === 'cluster' ? clusterId : painPointId);

  return (
    <div className="page-container">
      <PageHeader
        icon="file"
        title="PRD Studio"
        description="Requirement documents written from this workspace's own feedback — personas, scope, requirements, SLAs and metrics."
        actions={
          <>
            <WorkspaceSwitcher />
            <Button
              variant="primary"
              icon="sparkle"
              disabled={!workspaceId}
              onClick={() => setShowGenerate(true)}
            >
              Generate PRD
            </Button>
          </>
        }
      />

      {error && <Alert variant="error">{error}</Alert>}
      {notice && <Alert variant="success">{notice}</Alert>}

      <div className="prd-workspace-page">
        <Card className="prd-sidebar">
          <div className="sidebar-header">
            <h2 className="section-title">Documents</h2>
            <span className="sidebar-subtitle">
              {loading ? 'Loading…' : `${prds.length} in this workspace`}
            </span>
          </div>

          {loading ? (
            <SkeletonList rows={4} />
          ) : prds.length === 0 ? (
            <EmptyState
              icon="file"
              title="No documents yet"
              actions={
                <Button variant="secondary" size="sm" icon="sparkle" onClick={() => setShowGenerate(true)}>
                  Generate the first one
                </Button>
              }
            >
              Ground a document in a feature cluster, a pain point, or a brief you write.
            </EmptyState>
          ) : (
            <ul className="prd-list">
              {prds.map((prd) => {
                const isSelected = selected?.id === prd.id;
                return (
                  <li key={prd.id}>
                    <button
                      type="button"
                      className={['card', 'card-interactive', 'prd-list-item', isSelected && 'is-active']
                        .filter(Boolean)
                        .join(' ')}
                      aria-current={isSelected}
                      onClick={() => setSelected(prd)}
                    >
                      <div className="prd-item-top">
                        <Badge tone={STATUS_TONE[prd.status] || 'neutral'}>
                          {(prd.status || 'draft').replace(/_/g, ' ')}
                        </Badge>
                        <span className="prd-version">v{prd.version || '1.0'}</span>
                      </div>
                      <span className="prd-item-title">{prd.title}</span>
                      <div className="prd-item-meta">
                        <span>{SOURCE_LABEL[prd.source_type] || 'Custom brief'}</span>
                        <span>{new Date(prd.created_at).toLocaleDateString()}</span>
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </Card>

        <Card className="prd-main-pane">
          {loading ? (
            <div className="stack stack-md">
              <Skeleton className="skeleton-title" style={{ width: 320, height: 28 }} />
              <Skeleton className="skeleton-line w-40" />
              <Skeleton className="skeleton-block" style={{ height: 200 }} />
              <Skeleton className="skeleton-block" style={{ height: 140 }} />
            </div>
          ) : !selected ? (
            <EmptyState
              icon="file"
              title="No document open"
              actions={
                <Button variant="primary" icon="sparkle" disabled={!workspaceId} onClick={() => setShowGenerate(true)}>
                  Generate a PRD
                </Button>
              }
            >
              Choose a document from the list, or generate a new one from your own feedback.
            </EmptyState>
          ) : (
            <div className="stack stack-md">
              <header className="document-header">
                <div className="stack stack-sm">
                  <div className="doc-meta-row">
                    <Badge tone={STATUS_TONE[selected.status] || 'neutral'}>
                      {(selected.status || 'draft').replace(/_/g, ' ')}
                    </Badge>
                    <span className="badge badge-neutral">v{selected.version || '1.0'}</span>
                    <span className="text-xs text-muted">
                      {new Date(selected.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h2 className="doc-title">{selected.title}</h2>
                </div>

                <div className="doc-actions">
                  <Select
                    value={selected.status || 'draft'}
                    onChange={(e) => changeStatus(e.target.value)}
                    aria-label="Document status"
                  >
                    <option value="draft">Draft</option>
                    <option value="in_review">In review</option>
                    <option value="approved">Approved</option>
                    <option value="archived">Archived</option>
                  </Select>

                  <Button
                    size="sm"
                    variant="secondary"
                    icon="file"
                    onClick={copyMarkdown}
                  >
                    Copy
                  </Button>

                  <Button size="sm" variant="secondary" icon="download" onClick={downloadMarkdown}>
                    Export
                  </Button>

                  <Button
                    size="sm"
                    variant="primary"
                    icon="clipboard"
                    onClick={() => navigate(`/user-stories?prd_id=${selected.id}`)}
                  >
                    Break into stories
                  </Button>

                  <IconButton
                    icon="trash"
                    variant="danger"
                    label={`Delete ${selected.title}`}
                    onClick={() => setPendingDelete(selected)}
                  />
                </div>
              </header>

              <Segmented
                label="Document view"
                value={tab}
                onChange={setTab}
                options={[
                  { value: 'structured', label: 'Document', icon: 'file' },
                  { value: 'markdown', label: 'Markdown', icon: 'code' },
                ]}
              />

              {tab === 'markdown' ? (
                <div className="markdown-view-container">
                  <div className="markdown-toolbar">
                    <span>GitHub-flavoured Markdown — ready to paste into your wiki.</span>
                    <Button size="sm" variant="secondary" icon="save" onClick={copyMarkdown}>
                      Copy
                    </Button>
                  </div>
                  <pre className="markdown-code-block">
                    <code>{selected.raw_markdown}</code>
                  </pre>
                </div>
              ) : (
                <div className="structured-doc-content">
                  <DocSection index={1} title="Executive summary">
                    <p className="prose">{selected.executive_summary}</p>
                  </DocSection>

                  <DocSection index={2} title="Customer problem and evidence">
                    <div className="callout callout-warning">
                      <p>{selected.problem_statement}</p>
                    </div>
                  </DocSection>

                  {selected.goals_and_objectives?.length > 0 && (
                    <DocSection index={3} title="Strategic goals">
                      <ul className="styled-list">
                        {selected.goals_and_objectives.map((goal) => (
                          <li key={goal}>{goal}</li>
                        ))}
                      </ul>
                    </DocSection>
                  )}

                  {selected.target_users_and_personas?.length > 0 && (
                    <DocSection index={4} title="Target users">
                      <div className="personas-grid">
                        {selected.target_users_and_personas.map((persona) => (
                          <div key={persona.role} className="persona-card">
                            <div className="persona-header">
                              <span className="persona-avatar">
                                <Icon name="user" size={18} />
                              </span>
                              <div className="stack stack-sm">
                                <h4 className="persona-role">{persona.role}</h4>
                                <span className="persona-desc">{persona.description}</span>
                              </div>
                            </div>

                            {persona.pain_points?.length > 0 && (
                              <div className="persona-frictions">
                                <strong className="text-xs">What gets in their way</strong>
                                <ul>
                                  {persona.pain_points.map((point) => (
                                    <li key={point}>{point}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {persona.goals?.length > 0 && (
                              <div className="persona-goals">
                                <strong className="text-xs">What they want</strong>
                                <ul>
                                  {persona.goals.map((goal) => (
                                    <li key={goal}>{goal}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </DocSection>
                  )}

                  <DocSection index={5} title="Scope">
                    <div className="scope-grid">
                      <div className="scope-box scope-in">
                        <h4>
                          <Icon name="check" size={15} /> In scope
                        </h4>
                        <ul>
                          {selected.scope_in?.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="scope-box scope-out">
                        <h4>
                          <Icon name="x" size={15} /> Deliberately out of scope
                        </h4>
                        <ul>
                          {selected.scope_out?.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </DocSection>

                  <DocSection index={6} title="Functional requirements">
                    <div className="requirements-list">
                      {selected.functional_requirements?.map((requirement) => (
                        <div key={requirement.id} className="requirement-card">
                          <div className="req-header">
                            <div className="req-id-box">
                              <span className="req-id">{requirement.id}</span>
                              <Badge
                                tone={
                                  { p0: 'danger', p1: 'warning', p2: 'accent' }[
                                    (requirement.priority || 'p1').toLowerCase()
                                  ] || 'neutral'
                                }
                              >
                                {requirement.priority || 'P1'}
                              </Badge>
                            </div>
                            <h4 className="req-title">{requirement.title}</h4>
                          </div>

                          <p className="req-desc">{requirement.description}</p>

                          {requirement.acceptance_criteria?.length > 0 && (
                            <div className="req-sublist">
                              <strong>Acceptance criteria</strong>
                              <ul>
                                {requirement.acceptance_criteria.map((criteria) => (
                                  <li key={criteria} className="check-bullet">
                                    <span className="checkbox-icon">
                                      <Icon name="check" size={13} />
                                    </span>
                                    {criteria}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {requirement.edge_cases?.length > 0 && (
                            <div className="req-sublist edge-cases">
                              <strong>Edge cases</strong>
                              <ul>
                                {requirement.edge_cases.map((edgeCase) => (
                                  <li key={edgeCase}>{edgeCase}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </DocSection>

                  {selected.non_functional_requirements?.length > 0 && (
                    <DocSection index={7} title="Non-functional requirements">
                      <div className="nfr-grid">
                        {selected.non_functional_requirements.map((nfr) => (
                          <div key={nfr.requirement} className="nfr-card">
                            <span className="nfr-cat">{nfr.category}</span>
                            <p className="nfr-req">{nfr.requirement}</p>
                          </div>
                        ))}
                      </div>
                    </DocSection>
                  )}

                  {selected.success_metrics_kpis?.length > 0 && (
                    <DocSection index={8} title="Success metrics">
                      <div className="table-responsive">
                        <table className="table">
                          <thead>
                            <tr>
                              <th scope="col">Metric</th>
                              <th scope="col">Baseline</th>
                              <th scope="col">Target</th>
                              <th scope="col">Measured by</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selected.success_metrics_kpis.map((kpi) => (
                              <tr key={kpi.metric}>
                                <td className="text-semibold">{kpi.metric}</td>
                                <td>{kpi.baseline || 'Not measured'}</td>
                                <td className="text-success text-semibold">{kpi.target}</td>
                                <td className="text-muted">{kpi.tracking_mechanism || 'Telemetry'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </DocSection>
                  )}

                  {selected.risks_and_mitigations?.length > 0 && (
                    <DocSection index={9} title="Risks and mitigations">
                      <div className="risks-list">
                        {selected.risks_and_mitigations.map((entry) => (
                          <div key={entry.risk} className="risk-card">
                            <div className="risk-header">
                              <Badge
                                tone={
                                  { high: 'danger', medium: 'warning', low: 'accent' }[
                                    (entry.severity || 'medium').toLowerCase()
                                  ] || 'neutral'
                                }
                              >
                                {entry.severity || 'medium'} risk
                              </Badge>
                              <span className="risk-text">{entry.risk}</span>
                            </div>
                            <p className="mitigation-box">
                              <strong>Mitigation: </strong>
                              {entry.mitigation}
                            </p>
                          </div>
                        ))}
                      </div>
                    </DocSection>
                  )}
                </div>
              )}
            </div>
          )}
        </Card>
      </div>

      <Modal
        open={showGenerate}
        onClose={() => !generating && setShowGenerate(false)}
        title="Generate a PRD"
        description="Ground the document in something real, then choose how deep to go."
        icon="sparkle"
        size="lg"
        footer={
          generating ? null : (
            <>
              <Button variant="secondary" onClick={() => setShowGenerate(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                icon="sparkle"
                disabled={!canGenerate}
                onClick={generate}
              >
                Generate
              </Button>
            </>
          )
        }
      >
        {generating ? (
          <div className="modal-generating-state">
            <span className="spinner spinner-lg" />
            <h3>Writing the document</h3>
            <p className="text-muted">{GENERATION_STEPS[step]}…</p>
            <div style={{ width: '100%', maxWidth: 320 }}>
              <ProgressBar
                value={((step + 1) / GENERATION_STEPS.length) * 100}
                label="Document generation progress"
              />
            </div>
          </div>
        ) : (
          <div className="modal-form">
            {contextError && <Alert variant="warning">{contextError}</Alert>}

            <div className="field">
              <span className="field-label">Ground it in</span>
              <Segmented
                label="Generation source"
                value={sourceType}
                onChange={setSourceType}
                options={[
                  { value: 'cluster', label: `Cluster (${clusters.length})`, icon: 'layers' },
                  { value: 'pain_point', label: `Pain point (${painPoints.length})`, icon: 'target' },
                  { value: 'custom', label: 'My own brief', icon: 'pencil' },
                ]}
              />
            </div>

            {sourceType === 'cluster' && (
              <Select label="Feature cluster" value={clusterId} onChange={(e) => setClusterId(e.target.value)}>
                <option value="">Choose a cluster…</option>
                {clusters.map((cluster) => (
                  <option key={cluster.id} value={cluster.id}>
                    {cluster.cluster_name} — {cluster.demand_level} demand, priority {cluster.priority_score}
                  </option>
                ))}
              </Select>
            )}

            {sourceType === 'pain_point' && (
              <Select
                label="Pain point"
                value={painPointId}
                onChange={(e) => setPainPointId(e.target.value)}
              >
                <option value="">Choose a pain point…</option>
                {painPoints.map((point) => (
                  <option key={point.id} value={point.id}>
                    {point.title} — {point.severity} severity, impact {point.impact_score}
                  </option>
                ))}
              </Select>
            )}

            <Input
              label="Title (optional)"
              placeholder="Leave blank and one will be written for you"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />

            <Textarea
              label="Anything else it must cover"
              rows={3}
              placeholder="Constraints, technical expectations, or outcomes this document has to address."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />

            <div className="form-row">
              <div className="form-group flex-1">
                <Input
                  label="Target audience (optional)"
                  placeholder="e.g. Creators, admins"
                  value={audience}
                  onChange={(e) => setAudience(e.target.value)}
                />
              </div>
              <div className="form-group flex-1">
                <Select label="Depth" value={tone} onChange={(e) => setTone(e.target.value)}>
                  <option value="comprehensive">Comprehensive</option>
                  <option value="lean_mvp">Lean MVP</option>
                  <option value="technical">Technical detail</option>
                </Select>
              </div>
            </div>
          </div>
        )}
      </Modal>

      <Modal
        open={Boolean(pendingDelete)}
        onClose={() => setPendingDelete(null)}
        title="Delete this document?"
        description="The document and its history will be removed."
        icon="trash"
        footer={
          <>
            <Button variant="secondary" onClick={() => setPendingDelete(null)}>
              Keep it
            </Button>
            <Button variant="danger" icon="trash" onClick={confirmDelete}>
              Delete
            </Button>
          </>
        }
      >
        <div className="modal-body">
          <p className="prose">{pendingDelete?.title}</p>
        </div>
      </Modal>
    </div>
  );
}

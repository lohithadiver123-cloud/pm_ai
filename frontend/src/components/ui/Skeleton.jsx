/**
 * Skeletons.
 *
 * The rule everywhere in the app: a surface that is loading renders a skeleton
 * shaped like the content that is coming, not a spinner dropped into the middle
 * of an empty box. That keeps the layout from jumping when the data lands and
 * tells the user what to expect.
 *
 * Widths come from the `w-*` helpers in index.css so skeleton text reads like
 * text rather than a bar chart.
 */

export function Skeleton({ className = '', style }) {
  return <div className={['skeleton', className].filter(Boolean).join(' ')} style={style} aria-hidden="true" />;
}

/** A few lines of body copy. */
export function SkeletonText({ lines = 3, className = '' }) {
  return (
    <div className={['skeleton-stack', className].filter(Boolean).join(' ')} aria-hidden="true">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className={['skeleton-line', i === lines - 1 ? 'w-60' : 'w-100'].join(' ')} />
      ))}
    </div>
  );
}

/** Label above a single value — the KPI shape. */
export function SkeletonStat() {
  return (
    <div className="kpi-card" aria-hidden="true">
      <Skeleton className="skeleton-line w-60" />
      <Skeleton className="skeleton-title w-40" />
      <Skeleton className="skeleton-line w-75" />
    </div>
  );
}

export function SkeletonStatGrid({ count = 4 }) {
  return (
    <div className="kpi-grid" role="status" aria-label="Loading metrics">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonStat key={i} />
      ))}
    </div>
  );
}

/** Card with a title and body copy. */
export function SkeletonCard({ lines = 3, className = '' }) {
  return (
    <div className={['card card-pad stack stack-md', className].filter(Boolean).join(' ')} aria-hidden="true">
      <Skeleton className="skeleton-title" />
      <SkeletonText lines={lines} />
    </div>
  );
}

/** A grid of content cards, matching .insights-grid. */
export function SkeletonCardGrid({ count = 4 }) {
  return (
    <div className="insights-grid" role="status" aria-label="Loading content">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} lines={4} />
      ))}
    </div>
  );
}

/** Header row plus body rows, inside a card. */
export function SkeletonTable({ rows = 6, columns = 5 }) {
  return (
    <div className="table-responsive" role="status" aria-label="Loading table">
      <table className="table">
        <thead>
          <tr>
            {Array.from({ length: columns }).map((_, i) => (
              <th key={i}>
                <Skeleton className="skeleton-line w-60" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, r) => (
            <tr key={r}>
              {Array.from({ length: columns }).map((_, c) => (
                <td key={c}>
                  <Skeleton className={['skeleton-line', c === 0 ? 'w-75' : 'w-40'].join(' ')} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Chart-sized block with a centred spinner. */
export function SkeletonChart({ label = 'Loading chart' }) {
  return (
    <div className="skeleton skeleton-chart" role="status" aria-label={label} />
  );
}

/** Column of list rows — card title plus two meta lines. */
export function SkeletonList({ rows = 5 }) {
  return (
    <div className="skeleton-stack" role="status" aria-label="Loading list">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="row" style={{ gap: 'var(--sp-3)', alignItems: 'flex-start' }}>
          <Skeleton className="skeleton-circle" style={{ width: 28, height: 28, flexShrink: 0 }} />
          <div className="skeleton-stack flex-1">
            <Skeleton className="skeleton-line w-40" />
            <Skeleton className="skeleton-line w-75" />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Kanban column placeholder. */
export function SkeletonBoard({ columns = 4 }) {
  return (
    <div className="kanban-board" role="status" aria-label="Loading board">
      {Array.from({ length: columns }).map((_, c) => (
        <div key={c} className="kanban-column">
          <div className="kanban-col-header">
            <Skeleton className="skeleton-line w-40" />
            <Skeleton className="skeleton-line w-25" style={{ maxWidth: 32 }} />
          </div>
          <div className="kanban-cards-container">
            {Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="story-card">
                <Skeleton className="skeleton-line w-40" />
                <SkeletonText lines={2} />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/** Whole-page placeholder: title, subtitle then a content shape. */
export function SkeletonPage({ children }) {
  return (
    <div className="page-container" role="status" aria-label="Loading page">
      <div className="page-heading">
        <Skeleton className="skeleton-title" style={{ width: 240, height: 28 }} />
        <Skeleton className="skeleton-line" style={{ width: 420 }} />
      </div>
      {children}
    </div>
  );
}

export default Skeleton;

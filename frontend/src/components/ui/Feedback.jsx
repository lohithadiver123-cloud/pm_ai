import Icon from '../Icon';

/**
 * Shared feedback primitives: status labels, alerts, empty states and busy
 * indicators. Everything here reads from the CSS token layer — nothing invents
 * a colour, spacing value or radius of its own.
 */

const TONES = {
  neutral: 'badge-neutral',
  accent: 'badge-accent',
  success: 'badge-success',
  warning: 'badge-warning',
  danger: 'badge-danger',
};

/** Small status label. `tone` carries the meaning, but the text always says it too. */
export function Badge({ tone = 'neutral', icon, className = '', children, ...rest }) {
  return (
    <span
      className={['badge', TONES[tone] || TONES.neutral, className].filter(Boolean).join(' ')}
      {...rest}
    >
      {icon && <Icon name={icon} size={12} />}
      {children}
    </span>
  );
}

/** Quieter than a badge — filters, tags, context. */
export function Pill({ tone, className = '', children, ...rest }) {
  return (
    <span
      className={['pill', tone === 'accent' && 'pill-accent', className].filter(Boolean).join(' ')}
      {...rest}
    >
      {children}
    </span>
  );
}

export function Alert({ variant = 'info', title, icon, className = '', children, ...rest }) {
  const fallbackIcon = { error: 'xCircle', success: 'checkCircle', warning: 'alert', info: 'info' }[variant];
  return (
    <div className={['alert', `alert-${variant}`, className].filter(Boolean).join(' ')} role="alert" {...rest}>
      <Icon name={icon || fallbackIcon} size={16} />
      <div className="stack stack-sm">
        {title && <strong className="alert-title">{title}</strong>}
        {children}
      </div>
    </div>
  );
}

export function EmptyState({ icon = 'inbox', title, children, actions, className = '' }) {
  return (
    <div className={['empty', className].filter(Boolean).join(' ')}>
      <span className="empty-icon">
        <Icon name={icon} size={20} />
      </span>
      {title && <p className="empty-title">{title}</p>}
      {children && <p className="empty-text">{children}</p>}
      {actions && <div className="empty-actions row">{actions}</div>}
    </div>
  );
}

export function ErrorState({ title = 'Something went wrong', onRetry, children }) {
  return (
    <EmptyState
      icon="alert"
      title={title}
      actions={
        onRetry ? (
          <button type="button" className="btn btn-secondary btn-sm" onClick={onRetry}>
            <Icon name="refresh" size={14} />
            Try again
          </button>
        ) : null
      }
    >
      {children}
    </EmptyState>
  );
}

export function Spinner({ size = 'md', onDark = false, className = '' }) {
  const sizeClass = size === 'sm' ? 'spinner-sm' : size === 'lg' ? 'spinner-lg' : '';
  return (
    <span
      className={['spinner', sizeClass, onDark && 'spinner-on-dark', className].filter(Boolean).join(' ')}
      role="status"
      aria-label="Loading"
    />
  );
}

/** Determinate bar. Pass `value` 0–100, or omit it for an indeterminate sweep. */
export function ProgressBar({ value, label }) {
  const indeterminate = value == null;
  return (
    <div
      className="progress"
      role="progressbar"
      aria-label={label}
      aria-valuemin={indeterminate ? undefined : 0}
      aria-valuemax={indeterminate ? undefined : 100}
      aria-valuenow={indeterminate ? undefined : Math.round(value)}
    >
      <span
        className={['progress-fill', indeterminate && 'indeterminate'].filter(Boolean).join(' ')}
        style={indeterminate ? undefined : { width: `${Math.max(0, Math.min(100, value))}%` }}
      />
    </div>
  );
}

export function LoadingState({ label = 'Loading…' }) {
  return (
    <div className="loading-state">
      <Spinner />
      <span>{label}</span>
    </div>
  );
}

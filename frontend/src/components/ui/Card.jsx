import Icon from '../Icon';

/**
 * The one card pattern.
 *
 * Every card in the app is this component: same border, same radius, same
 * padding, same header/body/footer rhythm. There is no second variant — a card
 * that looks different is a bug, not a design decision.
 *
 * `interactive` adds the shared hover treatment and makes the whole card
 * keyboard-operable when given an onClick.
 */
export function Card({ interactive = false, active = false, flush = false, className = '', onClick, children, ...rest }) {
  const classes = [
    'card',
    interactive && 'card-interactive',
    active && 'is-active',
    flush && 'card-flush',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  // A clickable card has to be reachable and operable without a mouse.
  const behaviour = interactive && onClick
    ? {
        role: 'button',
        tabIndex: 0,
        onClick,
        onKeyDown: (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onClick(e);
          }
        },
      }
    : { onClick };

  return (
    <div className={classes} {...behaviour} {...rest}>
      {children}
    </div>
  );
}

export function CardHeader({ title, hint, icon, actions, className = '', children }) {
  return (
    <div className={['card-header', className].filter(Boolean).join(' ')}>
      <div className="stack stack-sm">
        {title && (
          <h2 className="card-title">
            {icon && <Icon name={icon} size={15} />} {title}
          </h2>
        )}
        {hint && <p className="card-hint">{hint}</p>}
        {children}
      </div>
      {actions && <div className="row">{actions}</div>}
    </div>
  );
}

export function CardBody({ padded = true, className = '', children, ...rest }) {
  return (
    <div className={[padded && 'card-body', className].filter(Boolean).join(' ')} {...rest}>
      {children}
    </div>
  );
}

export function CardFooter({ className = '', children, ...rest }) {
  return (
    <div className={['card-footer', className].filter(Boolean).join(' ')} {...rest}>
      {children}
    </div>
  );
}

/**
 * A single metric. Text is always label-then-value-then-note, in that order,
 * so a row of stats scans the same way wherever it appears.
 */
export function Stat({ label, value, hint, icon, featured = false, className = '' }) {
  return (
    <div className={['card', 'stat', featured && 'stat-featured', className].filter(Boolean).join(' ')}>
      <div className="stat-meta">
        <span className="stat-label">{label}</span>
        {icon && (
          <span className="text-light">
            <Icon name={icon} size={15} />
          </span>
        )}
      </div>
      <div className="stat-value">{value}</div>
      {hint && <div className="stat-hint">{hint}</div>}
    </div>
  );
}

/** Row of stats. Keep it to four; anything more stops being a focal point. */
export function StatGrid({ min = 200, className = '', children }) {
  return (
    <div className={['auto-grid', className].filter(Boolean).join(' ')} style={{ '--min': `${min}px` }}>
      {children}
    </div>
  );
}

export default Card;

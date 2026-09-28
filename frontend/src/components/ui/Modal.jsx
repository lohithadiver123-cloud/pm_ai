import { useEffect, useId, useRef } from 'react';
import Icon from '../Icon';
import { IconButton } from './Button';

/**
 * Modal / dialog.
 *
 * Real dialog semantics (role + aria-modal + labelled title), Escape to close,
 * click-outside to close, focus moved into the dialog on open and restored to
 * whatever opened it on close. The body scroll is locked while it is up.
 */
export default function Modal({ open, onClose, title, description, icon, size = 'md', footer, children }) {
  const cardRef = useRef(null);
  const titleId = useId();

  useEffect(() => {
    if (!open) return undefined;

    const previous = document.activeElement;
    const onKeyDown = (e) => {
      if (e.key === 'Escape') onClose?.(e);
    };

    document.addEventListener('keydown', onKeyDown);
    const { overflow } = document.body.style;
    document.body.style.overflow = 'hidden';

    // Focus the first useful control inside the dialog.
    const focusable = cardRef.current?.querySelector(
      'input:not([type="hidden"]), select, textarea, button, [href], [tabindex]:not([tabindex="-1"])'
    );
    (focusable || cardRef.current)?.focus?.();

    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = overflow;
      previous?.focus?.();
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="modal-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose?.();
      }}
    >
      <div
        ref={cardRef}
        className={['modal-card', size === 'lg' && 'modal-lg'].filter(Boolean).join(' ')}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
      >
        <div className="modal-header">
          <div className="modal-title-box">
            {icon && (
              <span className="modal-icon">
                <Icon name={icon} size={16} />
              </span>
            )}
            <div>
              <h2 id={titleId}>{title}</h2>
              {description && <p>{description}</p>}
            </div>
          </div>
          <IconButton icon="x" label="Close dialog" onClick={onClose} />
        </div>

        {children}

        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
}

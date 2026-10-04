import { useEffect, useId, useRef, useState } from 'react';
import Icon from '../Icon';
import { useWorkspaces } from '../../context/WorkspaceContext';

/**
 * The workspace picker — one control, used by every screen.
 *
 * Replaces the native `<select>` each page used to ship its own copy of. It
 * reads the shared selection, so choosing an option here re-renders the whole
 * app; `onChange` exists only for screens that must reset local filters when
 * the workspace moves.
 *
 * `layout="inline"` is the pill for header actions; `layout="stacked"` puts
 * the label above a full-width trigger so it sits beside the kit's `Select`s
 * in a toolbar without looking bolted on.
 *
 * Keyboard: the trigger and every option are real buttons, so Tab and Enter
 * work for free; Escape closes and returns focus to the trigger.
 */
export default function WorkspaceSwitcher({
  label = 'Workspace',
  layout = 'inline',
  id,
  disabled = false,
  className = '',
  onChange,
}) {
  const { workspaces, activeId, activeWorkspace, loading, ready, setActive } = useWorkspaces();
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const triggerRef = useRef(null);
  const generatedId = useId();
  const triggerId = id || generatedId;
  const listId = `${triggerId}-list`;

  const close = () => {
    setOpen(false);
    triggerRef.current?.focus();
  };

  useEffect(() => {
    if (!open) return undefined;
    const onPointerDown = (event) => {
      if (rootRef.current && !rootRef.current.contains(event.target)) setOpen(false);
    };
    const onKeyDown = (event) => {
      if (event.key === 'Escape') close();
    };
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open]);

  const choose = (nextId) => {
    if (!nextId || nextId === activeId) {
      close();
      return;
    }
    setActive(nextId);
    onChange?.(nextId);
    close();
  };

  const currentName = loading
    ? 'Loading…'
    : activeWorkspace?.name || activeWorkspace?.title || 'No workspace yet';

  return (
    <div
      ref={rootRef}
      className={[
        'ws-switcher',
        layout === 'stacked' && 'is-stacked',
        open && 'is-open',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {label && (
        <label className={layout === 'stacked' ? 'field-label' : 'ws-switcher-label'} htmlFor={triggerId}>
          {label}
        </label>
      )}

      <button
        ref={triggerRef}
        id={triggerId}
        type="button"
        className="ws-trigger"
        disabled={disabled || loading}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? listId : undefined}
        onClick={() => setOpen((value) => !value)}
      >
        <span className="ws-trigger-dot" aria-hidden="true" />
        <span className="ws-trigger-name">{currentName}</span>
        <Icon name="chevronDown" size={14} className={`ws-trigger-caret${open ? ' is-open' : ''}`} />
      </button>

      {open && (
        <div className="ws-menu" role="listbox" id={listId} aria-label={label || 'Workspaces'}>
          <div className="ws-menu-head">
            <span>Workspaces</span>
            <span className="ws-menu-count">{workspaces.length}</span>
          </div>

          <div className="ws-menu-list">
            {workspaces.length === 0 && (
              <p className="ws-menu-empty">
                {ready ? 'No workspaces yet. Create one from the Dashboard.' : 'Loading workspaces…'}
              </p>
            )}
            {workspaces.map((workspace) => {
              const wsId = workspace._id || workspace.id;
              const isActive = wsId === activeId;
              return (
                <button
                  key={wsId}
                  type="button"
                  role="option"
                  aria-selected={isActive}
                  className={`ws-option${isActive ? ' is-active' : ''}`}
                  onClick={() => choose(wsId)}
                >
                  <span className="ws-option-name">{workspace.name || 'Untitled workspace'}</span>
                  {isActive ? (
                    <Icon name="check" size={14} />
                  ) : (
                    <Icon name="chevronRight" size={14} className="ws-option-arrow" />
                  )}
                </button>
              );
            })}
          </div>

          <p className="ws-menu-foot">Switching here updates every page.</p>
        </div>
      )}
    </div>
  );
}

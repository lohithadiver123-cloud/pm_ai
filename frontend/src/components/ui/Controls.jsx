import { useId } from 'react';
import Icon from '../Icon';
import { Spinner } from './Feedback';

/**
 * Form controls.
 *
 * Every control gets a real <label> wired by id, so clicking the label focuses
 * the input and screen readers announce it. `error` renders below and flips
 * aria-invalid, so validation is never colour-only.
 */

function useFieldId(id) {
  const generated = useId();
  return id || generated;
}

export function Field({ label, hint, error, className = '', children }) {
  const id = useId();
  return (
    <div className={['field', className].filter(Boolean).join(' ')}>
      {label && (
        <label className="field-label" htmlFor={id}>
          {label}
        </label>
      )}
      {typeof children === 'function' ? children({ id, invalid: Boolean(error) }) : children}
      {error ? (
        <span className="field-error">{error}</span>
      ) : (
        hint && <span className="field-hint">{hint}</span>
      )}
    </div>
  );
}

export function Input({ label, hint, error, id, className = '', ...rest }) {
  const fieldId = useFieldId(id);
  return (
    <div className="field">
      {label && (
        <label className="field-label" htmlFor={fieldId}>
          {label}
        </label>
      )}
      <input
        id={fieldId}
        className={['input', className].filter(Boolean).join(' ')}
        aria-invalid={error ? 'true' : undefined}
        {...rest}
      />
      {error ? (
        <span className="field-error">{error}</span>
      ) : (
        hint && <span className="field-hint">{hint}</span>
      )}
    </div>
  );
}

export function Textarea({ label, hint, error, id, className = '', ...rest }) {
  const fieldId = useFieldId(id);
  return (
    <div className="field">
      {label && (
        <label className="field-label" htmlFor={fieldId}>
          {label}
        </label>
      )}
      <textarea
        id={fieldId}
        className={['form-textarea', className].filter(Boolean).join(' ')}
        aria-invalid={error ? 'true' : undefined}
        {...rest}
      />
      {error ? (
        <span className="field-error">{error}</span>
      ) : (
        hint && <span className="field-hint">{hint}</span>
      )}
    </div>
  );
}

export function Select({ label, hint, id, className = '', children, ...rest }) {
  const fieldId = useFieldId(id);
  return (
    <div className="field" style={{ minWidth: 0 }}>
      {label && (
        <label className="field-label" htmlFor={fieldId}>
          {label}
        </label>
      )}
      <select id={fieldId} className={['select-input', className].filter(Boolean).join(' ')} {...rest}>
        {children}
      </select>
      {hint && <span className="field-hint">{hint}</span>}
    </div>
  );
}

export function SearchInput({ value, onChange, placeholder = 'Search…', label = 'Search', busy = false, width }) {
  return (
    <div className="search" style={width ? { width } : undefined}>
      <Icon name="search" size={15} />
      <input
        type="search"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        aria-label={label}
      />
      {busy && <Spinner size="sm" />}
    </div>
  );
}

/**
 * Segmented control for view switches (board/list, donut/bars).
 * Buttons carry aria-pressed so the active state is exposed, not just coloured.
 */
export function Segmented({ options, value, onChange, label, className = '' }) {
  return (
    <div className={['segmented', className].filter(Boolean).join(' ')} role="group" aria-label={label}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          className="btn"
          aria-pressed={value === option.value}
          onClick={() => onChange(option.value)}
        >
          {option.icon && <Icon name={option.icon} size={14} />}
          {option.label}
        </button>
      ))}
    </div>
  );
}

export default Input;

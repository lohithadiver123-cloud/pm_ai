import { forwardRef } from 'react';
import Icon from '../Icon';
import { Spinner } from './Feedback';

const VARIANT = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  outline: 'btn-outline',
  ghost: 'btn-ghost',
  danger: 'btn-danger',
};

const SIZE = { sm: 'btn-sm', md: '', lg: 'btn-lg' };

/**
 * The app's only button.
 *
 * Always renders a real <button>, so keyboard, focus and disabled behaviour
 * come for free. `loading` keeps the label in place and swaps the icon for a
 * spinner — the button never changes width mid-action.
 */
const Button = forwardRef(function Button(
  {
    variant = 'secondary',
    size = 'md',
    icon,
    iconRight,
    loading = false,
    fullWidth = false,
    className = '',
    children,
    type = 'button',
    ...rest
  },
  ref
) {
  const classes = [
    'btn',
    VARIANT[variant] || VARIANT.secondary,
    SIZE[size],
    fullWidth && 'btn-full',
    loading && 'is-loading',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      ref={ref}
      type={type}
      className={classes}
      disabled={loading || rest.disabled}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <Spinner size="sm" /> : icon && <Icon name={icon} size={16} />}
      {children}
      {!loading && iconRight && <Icon name={iconRight} size={16} />}
    </button>
  );
});

/** Square button holding a single icon. `label` is required — it is the a11y name. */
export function IconButton({ icon, label, variant = 'icon', size = 'md', className = '', ...rest }) {
  const classes = [
    'btn',
    'btn-icon',
    size === 'sm' && 'btn-sm',
    variant === 'danger' && 'btn-icon-danger',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button type="button" className={classes} aria-label={label} title={label} {...rest}>
      <Icon name={icon} size={size === 'sm' ? 14 : 16} />
    </button>
  );
}

export default Button;

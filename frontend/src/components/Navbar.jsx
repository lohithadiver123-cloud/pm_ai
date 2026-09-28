import { useEffect, useRef, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import Icon from './Icon';
import { useBusy } from '../context/BusyContext';

const LINKS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/insights', label: 'Insights' },
  { to: '/feedback', label: 'Feedback' },
  { to: '/prds', label: 'PRD Studio' },
  { to: '/user-stories', label: 'User Stories' },
  { to: '/prioritization', label: 'Prioritization' },
  { to: '/copilot', label: 'Copilot' },
  { to: '/import', label: 'Import' },
];

function initials(name) {
  if (!name) return '?';
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('');
}

function UserMenu() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const user = JSON.parse(localStorage.getItem('pm_copilot_user') || 'null');

  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e) => {
      if (!ref.current?.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const logout = () => {
    localStorage.removeItem('pm_copilot_token');
    localStorage.removeItem('pm_copilot_user');
    navigate('/');
  };

  return (
    <div className="navbar-user" ref={ref} style={{ position: 'relative' }}>
      <span className="navbar-username">{user?.name}</span>
      <button
        type="button"
        className="avatar"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Account menu for ${user?.name || 'user'}`}
        onClick={() => setOpen((v) => !v)}
      >
        {initials(user?.name)}
      </button>

      {open && (
        <div className="card menu" role="menu">
          <div className="menu-header">
            <strong>{user?.name}</strong>
            <span className="text-muted text-xs">{user?.email}</span>
          </div>
          <button type="button" className="menu-item" role="menuitem" onClick={logout}>
            <Icon name="logOut" size={15} />
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * The same destinations as a disclosure menu, for narrow screens.
 * A real button with aria-expanded, Escape to close, and click-outside to
 * dismiss — the strip of links simply does not fit on a phone.
 */
function MobileNav() {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const onDown = (event) => {
      if (!ref.current?.contains(event.target)) setOpen(false);
    };
    const onKey = (event) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <div className="navbar-mobile" ref={ref}>
      <button
        type="button"
        className="btn btn-icon btn-on-dark"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Open navigation"
        onClick={() => setOpen((v) => !v)}
      >
        <Icon name={open ? 'x' : 'menu'} size={16} />
      </button>

      {open && (
        <div className="card menu navbar-mobile-panel" role="menu">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              role="menuitem"
              className={({ isActive }) => `menu-item${isActive ? ' is-active' : ''}`}
              onClick={() => setOpen(false)}
            >
              {link.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Dark top bar. One row, one active state, and the global progress bar pinned
 * to its bottom edge while any tracked operation is running.
 */
export default function Navbar() {
  const { busy, label } = useBusy();

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <NavLink to="/dashboard" className="navbar-brand">
          <span className="navbar-mark">PM</span>
          <span>Copilot</span>
        </NavLink>

        <div className="navbar-links">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => `navbar-link${isActive ? ' active' : ''}`}
            >
              {link.label}
            </NavLink>
          ))}
        </div>

        <MobileNav />
        <UserMenu />
      </div>

      {busy && (
        <div className="navbar-progress" aria-live="polite">
          <div className="progress">
            <span className="progress-fill indeterminate" />
          </div>
          {label && <span className="sr-only">{label}</span>}
        </div>
      )}
    </nav>
  );
}

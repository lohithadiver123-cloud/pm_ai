/**
 * Navbar component.
 * Shows app branding and navigation links.
 * Displays logout button when authenticated.
 */
import { Link, useLocation, useNavigate } from 'react-router-dom';

function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const token = localStorage.getItem('pm_copilot_token');
  const user = JSON.parse(localStorage.getItem('pm_copilot_user') || 'null');

  const handleLogout = () => {
    localStorage.removeItem('pm_copilot_token');
    localStorage.removeItem('pm_copilot_user');
    navigate('/');
  };

  // Hide navbar on login and register pages
  if (location.pathname === '/' || location.pathname === '/register') {
    return null;
  }

  const navLinks = [
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/import', label: 'Import Data' },
    { path: '/feedback', label: 'Feedback' },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/dashboard" className="navbar-brand">
          <span className="navbar-logo">PM</span>
          <span className="navbar-title">Copilot</span>
        </Link>

        <div className="navbar-links">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`navbar-link ${location.pathname === link.path ? 'active' : ''}`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="navbar-user">
          {user && <span className="navbar-username">{user.name}</span>}
          <button onClick={handleLogout} className="btn btn-logout">
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;

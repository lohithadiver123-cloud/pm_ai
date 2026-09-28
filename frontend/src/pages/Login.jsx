import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Alert, Button, Input } from '../components/ui';

/**
 * Sign in.
 *
 * One field group pattern, one primary action, errors summarised at the top of
 * the form so they are announced rather than hidden beside a field.
 */
export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (localStorage.getItem('pm_copilot_token')) {
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);

  const validate = () => {
    const next = {};
    if (!email.trim()) next.email = 'Enter your email address.';
    else if (!/^\S+@\S+\.\S+$/.test(email.trim())) next.email = 'That does not look like an email address.';
    if (!password) next.password = 'Enter your password.';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError('');
    if (!validate()) return;

    setLoading(true);
    try {
      const { data } = await api.post('/auth/login', { email: email.trim(), password });
      localStorage.setItem('pm_copilot_token', data.access_token);
      localStorage.setItem('pm_copilot_user', JSON.stringify(data.user));
      navigate('/dashboard');
    } catch (err) {
      setFormError(
        err.response?.data?.detail || 'Could not sign you in. Check your email and password.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <header className="auth-header">
          <h1 className="auth-title">
            <span className="brand-highlight">PM</span> Copilot
          </h1>
          <p className="auth-subtitle">
            Turn scattered customer feedback into themes, pain points and a prioritised roadmap.
          </p>
        </header>

        {formError && (
          <div style={{ marginBottom: 'var(--sp-4)' }}>
            <Alert variant="error">{formError}</Alert>
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <Input
            label="Email"
            type="email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            autoComplete="email"
            autoFocus
            error={errors.email}
            disabled={loading}
          />

          <Input
            label="Password"
            type="password"
            name="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Your password"
            autoComplete="current-password"
            error={errors.password}
            disabled={loading}
          />

          <Button type="submit" variant="primary" fullWidth loading={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </Button>
        </form>

        <p className="auth-footer">
          No account yet? <Link to="/register">Create one</Link>
        </p>
      </div>
    </div>
  );
}

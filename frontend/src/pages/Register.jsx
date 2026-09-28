import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Alert, Button, Input } from '../components/ui';

/** Create an account. Same field pattern and validation shape as sign-in. */
export default function Register() {
  const navigate = useNavigate();
  const [values, setValues] = useState({ name: '', email: '', password: '', confirm: '' });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (localStorage.getItem('pm_copilot_token')) {
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);

  const set = (key) => (event) => setValues((prev) => ({ ...prev, [key]: event.target.value }));

  const validate = () => {
    const next = {};
    if (!values.name.trim()) next.name = 'Enter your name.';
    if (!values.email.trim()) next.email = 'Enter your email address.';
    else if (!/^\S+@\S+\.\S+$/.test(values.email.trim())) next.email = 'That does not look like an email address.';
    if (values.password.length < 6) next.password = 'Use at least 6 characters.';
    if (values.confirm !== values.password) next.confirm = 'The two passwords do not match.';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError('');
    if (!validate()) return;

    setLoading(true);
    try {
      await api.post('/auth/register', {
        name: values.name.trim(),
        email: values.email.trim(),
        password: values.password,
      });
      navigate('/');
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Could not create the account. Please try again.');
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
          <p className="auth-subtitle">Create an account to start turning feedback into decisions.</p>
        </header>

        {formError && (
          <div style={{ marginBottom: 'var(--sp-4)' }}>
            <Alert variant="error">{formError}</Alert>
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <Input
            label="Full name"
            name="name"
            value={values.name}
            onChange={set('name')}
            placeholder="Avery Chen"
            autoComplete="name"
            autoFocus
            error={errors.name}
            disabled={loading}
          />

          <Input
            label="Email"
            type="email"
            name="email"
            value={values.email}
            onChange={set('email')}
            placeholder="you@company.com"
            autoComplete="email"
            error={errors.email}
            disabled={loading}
          />

          <Input
            label="Password"
            type="password"
            name="password"
            value={values.password}
            onChange={set('password')}
            placeholder="At least 6 characters"
            autoComplete="new-password"
            error={errors.password}
            disabled={loading}
          />

          <Input
            label="Confirm password"
            type="password"
            name="confirm"
            value={values.confirm}
            onChange={set('confirm')}
            placeholder="Re-enter your password"
            autoComplete="new-password"
            error={errors.confirm}
            disabled={loading}
          />

          <Button type="submit" variant="primary" fullWidth loading={loading}>
            {loading ? 'Creating account…' : 'Create account'}
          </Button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

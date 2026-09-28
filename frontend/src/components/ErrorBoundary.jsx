import { Component } from 'react';
import Icon from './Icon';

/**
 * Last line of defence.
 *
 * A thrown render error used to leave a blank white page with nothing but a
 * console trace. This shows a real screen with a way out, and keeps the error
 * message visible so the failure is diagnosable rather than silent.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // Kept as a console error rather than swallowed — this is a real defect.
    console.error('Unhandled render error:', error, info?.componentStack);
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    return (
      <div className="auth-container">
        <div className="auth-card" style={{ maxWidth: 520 }}>
          <div className="empty">
            <span className="empty-icon">
              <Icon name="alert" size={20} />
            </span>
            <p className="empty-title">This screen failed to render</p>
            <p className="empty-text">
              Nothing was lost — your data is untouched. Reloading usually clears it; if it keeps
              happening, the message below is the one to report.
            </p>
          </div>

          <div className="alert alert-error" style={{ marginTop: 'var(--sp-4)' }}>
            <pre style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--fs-xs)', whiteSpace: 'pre-wrap' }}>
              {String(error?.message || error)}
            </pre>
          </div>

          <div className="row" style={{ marginTop: 'var(--sp-4)', justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-secondary" onClick={() => window.history.back()}>
              Go back
            </button>
            <button type="button" className="btn btn-primary" onClick={() => window.location.reload()}>
              Reload
            </button>
          </div>
        </div>
      </div>
    );
  }
}

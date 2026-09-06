import { Component } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--gray-100)',
          fontFamily: 'var(--font)',
          padding: 20,
        }}>
          <div style={{
            maxWidth: 480,
            background: 'var(--white)',
            border: '1px solid var(--gray-200)',
            borderRadius: 8,
            padding: 32,
            textAlign: 'center',
          }}>
            <AlertTriangle size={32} style={{ color: 'var(--gray-400)', marginBottom: 16 }} />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: 8, color: 'var(--gray-900)' }}>
              Something went wrong
            </h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--gray-500)', marginBottom: 20 }}>
              An unexpected error occurred. Please try again.
            </p>
            {this.state.error && (
              <details style={{
                textAlign: 'left',
                marginBottom: 20,
                padding: 12,
                background: 'var(--gray-100)',
                borderRadius: 4,
                fontSize: '0.78rem',
                color: 'var(--gray-600)',
                fontFamily: 'var(--font-mono)',
                whiteSpace: 'pre-wrap',
              }}>
                <summary style={{ cursor: 'pointer', fontWeight: 600, marginBottom: 4 }}>
                  Error details
                </summary>
                {this.state.error.message}
              </details>
            )}
            <button
              className="btn btn-primary"
              onClick={() => window.location.reload()}
            >
              <RefreshCw size={16} />
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

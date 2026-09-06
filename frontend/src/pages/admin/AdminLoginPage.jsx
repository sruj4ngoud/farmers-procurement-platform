import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAdmin } from '../../context/AdminContext.jsx';
import { Shield, ArrowRight, Lock } from 'lucide-react';

export default function AdminLoginPage() {
  const { login, loading, error, clearError } = useAdmin();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();
    try {
      await login(username.trim(), password);
      navigate('/admin/dashboard');
    } catch {
      // error is set in AdminContext
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--gray-950)',
      padding: '20px',
    }}>
      <div style={{
        width: '100%',
        maxWidth: 400,
      }}>
        {/* Logo area */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 48, height: 48,
            background: 'var(--gray-800)',
            borderRadius: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 16px',
            border: '1px solid var(--gray-700)',
          }}>
            <Shield size={22} color="var(--gray-400)" />
          </div>
          <div style={{
            fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.1em',
            textTransform: 'uppercase', color: 'var(--gray-500)', marginBottom: 6,
          }}>
            District Administration
          </div>
          <h1 style={{ color: 'var(--white)', fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
            Admin Login
          </h1>
        </div>

        {/* Form card */}
        <div style={{
          background: 'var(--gray-900)',
          border: '1px solid var(--gray-800)',
          borderRadius: 8,
          padding: '28px 24px',
        }}>
          {error && (
            <div style={{
              background: 'rgba(220,38,38,0.1)',
              border: '1px solid rgba(220,38,38,0.2)',
              color: '#FCA5A5',
              padding: '10px 14px',
              borderRadius: 6,
              marginBottom: 16,
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}>
              <Lock size={14} />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label style={{ color: 'var(--gray-400)' }}>Username</label>
              <input
                className="form-input"
                type="text"
                placeholder="admin_sangareddy"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                autoComplete="off"
                style={{
                  background: 'var(--gray-800)',
                  border: '1px solid var(--gray-700)',
                  color: 'var(--white)',
                }}
              />
            </div>

            <div className="form-group">
              <label style={{ color: 'var(--gray-400)' }}>Password</label>
              <input
                className="form-input"
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="off"
                style={{
                  background: 'var(--gray-800)',
                  border: '1px solid var(--gray-700)',
                  color: 'var(--white)',
                }}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-block btn-lg"
              disabled={loading || !username.trim() || !password}
              style={{ marginTop: 8 }}
            >
              {loading ? (
                'Signing in...'
              ) : (
                <>
                  Sign In
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Security notice */}
        <p style={{
          textAlign: 'center',
          marginTop: 20,
          fontSize: '0.75rem',
          color: 'var(--gray-600)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 6,
        }}>
          <Lock size={11} />
          District-scoped access only
        </p>

        {/* Farmer login link */}
        <p style={{
          textAlign: 'center',
          marginTop: 12,
          fontSize: '0.8rem',
        }}>
          <a href="/login" style={{ color: 'var(--gray-400)', textDecoration: 'none' }}>
            ← Farmer Login
          </a>
        </p>
      </div>
    </div>
  );
}

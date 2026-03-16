import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, AlertCircle, Zap } from 'lucide-react';

export function AdminLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:5000/admin', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error('Invalid credentials');
      }

      const data = await response.json();
      if (data.success) {
        navigate('/admin/dashboard');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        animation: 'fadeIn 0.3s ease',
      }}
    >
      <div style={{ maxWidth: 420, width: '100%', padding: '20px' }}>
        {/* Header */}
        <div style={{ marginBottom: 40, textAlign: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 16 }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 10,
                background: 'linear-gradient(135deg, #06b6d4, #0891b2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 20px rgba(6, 182, 212, 0.3)',
              }}
            >
              <Lock size={22} style={{ color: '#fff' }} />
            </div>
            <h1
              style={{
                fontSize: 28,
                fontWeight: 800,
                background: 'linear-gradient(135deg, #e2e8f0, #cbd5e1)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                margin: 0,
              }}
            >
              PhishGuard
            </h1>
          </div>
          <p style={{ fontSize: 14, color: '#94a3b8', margin: 0 }}>
            Secure admin access to threat intelligence operations
          </p>
        </div>

        {/* Login Card */}
        <div
          style={{
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: 16,
            padding: 32,
            backdropFilter: 'blur(10px)',
            animation: 'slideUp 0.4s ease',
          }}
        >
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Error Alert */}
            {error && (
              <div
                style={{
                  display: 'flex',
                  gap: 12,
                  padding: 12,
                  borderRadius: 10,
                  background: 'rgba(239, 68, 68, 0.08)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  alignItems: 'flex-start',
                }}
              >
                <AlertCircle size={18} style={{ color: '#ef4444', flexShrink: 0, marginTop: 2 }} />
                <span style={{ fontSize: 13, color: '#fca5a5' }}>{error}</span>
              </div>
            )}

            {/* Username Input */}
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
                Username
              </label>
              <input
                type="text"
                placeholder="admin"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: 10,
                  background: 'rgba(15, 23, 42, 0.6)',
                  color: '#e2e8f0',
                  fontSize: 14,
                  fontFamily: 'inherit',
                  transition: 'all 0.2s ease',
                  boxSizing: 'border-box',
                  opacity: loading ? 0.6 : 1,
                  cursor: loading ? 'not-allowed' : 'text',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(6, 182, 212, 0.3)';
                  e.currentTarget.style.background = 'rgba(15, 23, 42, 1)';
                  e.currentTarget.style.boxShadow = '0 0 12px rgba(6, 182, 212, 0.1)';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
                  e.currentTarget.style.background = 'rgba(15, 23, 42, 0.6)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              />
            </div>

            {/* Password Input */}
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
                Password
              </label>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: 10,
                  background: 'rgba(15, 23, 42, 0.6)',
                  color: '#e2e8f0',
                  fontSize: 14,
                  fontFamily: 'inherit',
                  transition: 'all 0.2s ease',
                  boxSizing: 'border-box',
                  opacity: loading ? 0.6 : 1,
                  cursor: loading ? 'not-allowed' : 'text',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(6, 182, 212, 0.3)';
                  e.currentTarget.style.background = 'rgba(15, 23, 42, 1)';
                  e.currentTarget.style.boxShadow = '0 0 12px rgba(6, 182, 212, 0.1)';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
                  e.currentTarget.style.background = 'rgba(15, 23, 42, 0.6)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: 'none',
                borderRadius: 10,
                background: loading
                  ? 'rgba(6, 182, 212, 0.3)'
                  : 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
                color: '#fff',
                fontSize: 14,
                fontWeight: 700,
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                boxShadow: loading ? 'none' : '0 0 20px rgba(6, 182, 212, 0.3)',
                opacity: loading ? 0.7 : 1,
              }}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.currentTarget.style.boxShadow = '0 0 30px rgba(6, 182, 212, 0.5)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }
              }}
              onMouseLeave={(e) => {
                if (!loading) {
                  e.currentTarget.style.boxShadow = '0 0 20px rgba(6, 182, 212, 0.3)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }
              }}
            >
              {loading ? (
                <>
                  <Zap size={16} style={{ animation: 'spin 1s linear infinite' }} />
                  Authenticating...
                </>
              ) : (
                <>
                  <Lock size={16} />
                  Secure Login
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer info */}
        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <p style={{ fontSize: 12, color: '#475569', margin: 0 }}>
            🔐 All communications are encrypted and logged
          </p>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

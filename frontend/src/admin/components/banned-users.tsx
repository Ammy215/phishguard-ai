import { useState } from 'react';
import { ShieldX, RotateCcw } from 'lucide-react';

interface BannedUser {
  id: number;
  user_id: string;
  ip_address: string;
  ban_time: string;
  reason: string;
}

interface BannedUsersProps {
  bannedUsers: BannedUser[];
  onUnbanUser: (userId: string) => Promise<void>;
  onRefresh: () => void;
}

export function BannedUsers({ bannedUsers, onUnbanUser, onRefresh }: BannedUsersProps) {
  const [loading, setLoading] = useState<string | null>(null);

  const handleUnban = async (userId: string) => {
    setLoading(userId);
    try {
      await onUnbanUser(userId);
      onRefresh();
    } catch (error) {
      console.error('Error unbanning user:', error);
    } finally {
      setLoading(null);
    }
  };

  const formatDate = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div
      style={{
        background: 'rgba(255, 255, 255, 0.04)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: 12,
        padding: 24,
        backdropFilter: 'blur(10px)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <ShieldX size={18} style={{ color: '#ef4444' }} />
        <h3 style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0', textTransform: 'uppercase', letterSpacing: '0.05em', margin: 0 }}>
          Banned Users
        </h3>
        <span style={{ fontSize: 11, marginLeft: 'auto', fontWeight: 600, color: '#ef4444', background: 'rgba(239, 68, 68, 0.1)', padding: '4px 10px', borderRadius: 6 }}>
          {bannedUsers.length} banned
        </span>
      </div>

      {bannedUsers.length > 0 ? (
        <div style={{ overflowX: 'auto' }}>
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: 13,
            }}
          >
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <th style={{ padding: '12px 14px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  User ID
                </th>
                <th style={{ padding: '12px 14px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  IP Address
                </th>
                <th style={{ padding: '12px 14px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Reason
                </th>
                <th style={{ padding: '12px 14px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Banned Since
                </th>
                <th style={{ padding: '12px 14px', textAlign: 'right', fontSize: 11, fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {bannedUsers.map((user, idx) => (
                <tr
                  key={user.id}
                  style={{
                    borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
                    background: 'rgba(239, 68, 68, 0.05)',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(239, 68, 68, 0.12)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'rgba(239, 68, 68, 0.05)';
                  }}
                >
                  <td style={{ padding: '12px 14px', fontFamily: 'monospace', fontSize: 11, color: '#cbd5e1' }}>
                    {user.user_id}
                  </td>
                  <td style={{ padding: '12px 14px', fontFamily: 'monospace', fontSize: 11, color: '#94a3b8' }}>
                    {user.ip_address}
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <span
                      style={{
                        display: 'inline-block',
                        fontSize: 11,
                        fontWeight: 600,
                        padding: '4px 10px',
                        borderRadius: 6,
                        background: 'rgba(239, 68, 68, 0.15)',
                        color: '#fca5a5',
                      }}
                    >
                      {user.reason || 'Admin action'}
                    </span>
                  </td>
                  <td style={{ padding: '12px 14px', fontSize: 12, color: '#64748b' }}>
                    {formatDate(user.ban_time)}
                  </td>
                  <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                    <button
                      onClick={() => handleUnban(user.user_id)}
                      disabled={loading === user.user_id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        padding: '6px 12px',
                        borderRadius: 8,
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                        background: 'rgba(16, 185, 129, 0.08)',
                        color: '#10b981',
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: loading === user.user_id ? 'not-allowed' : 'pointer',
                        transition: 'all 0.2s ease',
                        opacity: loading === user.user_id ? 0.6 : 1,
                        marginLeft: 'auto',
                      }}
                      onMouseEnter={(e) => {
                        if (loading !== user.user_id) {
                          e.currentTarget.style.background = 'rgba(16, 185, 129, 0.15)';
                          e.currentTarget.style.borderColor = 'rgba(16, 185, 129, 0.5)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'rgba(16, 185, 129, 0.08)';
                        e.currentTarget.style.borderColor = 'rgba(16, 185, 129, 0.3)';
                      }}
                    >
                      <RotateCcw size={14} style={{ animation: loading === user.user_id ? 'spin 1s linear infinite' : 'none' }} />
                      {loading === user.user_id ? 'Unbanning...' : 'Unban'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '24px', color: '#64748b' }}>
          No banned users 🎉
        </div>
      )}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

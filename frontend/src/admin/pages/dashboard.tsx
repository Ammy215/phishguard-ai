import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { StatsCards } from '../components/stats-cards';
import { DetectionChart } from '../components/detection-chart';
import { RecentScansTable } from '../components/recent-scans-table';
import { UsersTable } from '../components/users-table';
import { BannedUsers } from '../components/banned-users';
import { ThreatStatus } from '../components/threat-status';
import { LogOut, RefreshCw, AlertCircle } from 'lucide-react';

interface Stats {
  total_scans: number;
  phishing_detections: number;
  safe_detections: number;
  active_users: number;
  system_status: string;
}

interface Scan {
  id: number;
  url: string;
  risk_score: number;
  result: string;
  scan_time: string;
  source: string;
}

interface User {
  user_id: string;
  ip_address: string;
  request_count: number;
  status: string;
  first_seen: string;
  last_seen: string;
}

interface BannedUser {
  id: number;
  user_id: string;
  ip_address: string;
  ban_time: string;
  reason: string;
}

interface DetectionStat {
  result: string;
  count: number;
  date: string;
}

export function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats | null>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [bannedUsers, setBannedUsers] = useState<BannedUser[]>([]);
  const [detectionStats, setDetectionStats] = useState<DetectionStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  const api = 'http://localhost:5000';

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch stats
      const statsRes = await fetch(`${api}/admin/stats`, {
        credentials: 'include',
      });
      if (!statsRes.ok) {
        if (statsRes.status === 401) {
          navigate('/admin');
          return;
        }
        throw new Error('Failed to fetch stats');
      }
      setStats(await statsRes.json());

      // Fetch recent scans
      const scansRes = await fetch(`${api}/admin/recent-scans?limit=20`, {
        credentials: 'include',
      });
      if (scansRes.ok) {
        const data = await scansRes.json();
        setScans(data.scans || []);
      }

      // Fetch users
      const usersRes = await fetch(`${api}/admin/users?limit=20`, {
        credentials: 'include',
      });
      if (usersRes.ok) {
        const data = await usersRes.json();
        setUsers(data.users || []);
      }

      // Fetch banned users
      const bannedRes = await fetch(`${api}/admin/banned-users?limit=20`, {
        credentials: 'include',
      });
      if (bannedRes.ok) {
        const data = await bannedRes.json();
        setBannedUsers(data.banned_users || []);
      }

      // Fetch detection stats
      const detectionRes = await fetch(`${api}/admin/detection-stats`, {
        credentials: 'include',
      });
      if (detectionRes.ok) {
        const data = await detectionRes.json();
        setDetectionStats(data.stats || []);
      }

      setLastUpdate(new Date().toISOString());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const handleBanUser = async (userId: string) => {
    try {
      const response = await fetch(`${api}/admin/ban-user`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, reason: 'Admin action' }),
      });

      if (!response.ok) {
        throw new Error('Failed to ban user');
      }
    } catch (err) {
      console.error('Error banning user:', err);
      throw err;
    }
  };

  const handleUnbanUser = async (userId: string) => {
    try {
      const response = await fetch(`${api}/admin/unban-user`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      });

      if (!response.ok) {
        throw new Error('Failed to unban user');
      }
    } catch (err) {
      console.error('Error unbanning user:', err);
      throw err;
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${api}/admin/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      navigate('/admin');
    }
  };

  if (loading && !stats) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              width: 48,
              height: 48,
              border: '3px solid rgba(6, 182, 212, 0.3)',
              borderTopColor: '#06b6d4',
              borderRadius: '50%',
              margin: '0 auto 16px',
              animation: 'spin 1s linear infinite',
            }}
          />
          <p style={{ color: '#94a3b8', fontSize: 14 }}>Loading threat intelligence dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        padding: '20px',
        animation: 'fadeIn 0.3s ease',
      }}
    >
      {/* Header */}
      <div
        style={{
          maxWidth: 1200,
          margin: '0 auto 32px',
          display: 'flex',
          alignItems: 'flex-end',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <div
              style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                background: '#06b6d4',
                boxShadow: '0 0 12px rgba(6, 182, 212, 0.5)',
              }}
            />
            <span style={{ fontSize: 11, fontWeight: 700, color: '#06b6d4', textTransform: 'uppercase', letterSpacing: '0.15em' }}>
              SOC - Security Operations
            </span>
          </div>
          <h1
            style={{
              fontSize: 32,
              fontWeight: 800,
              background: 'linear-gradient(135deg, #e2e8f0, #cbd5e1)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              margin: '0 0 8px 0',
              letterSpacing: '-0.5px',
            }}
          >
            Admin Dashboard
          </h1>
          <p style={{ fontSize: 14, color: '#64748b', margin: 0 }}>
            Real-time monitoring & threat management
          </p>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={fetchData}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 16px',
              borderRadius: 10,
              border: '1px solid rgba(6, 182, 212, 0.2)',
              background: 'rgba(6, 182, 212, 0.05)',
              color: '#06b6d4',
              fontSize: 13,
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
              opacity: loading ? 0.6 : 1,
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.currentTarget.style.background = 'rgba(6, 182, 212, 0.1)';
                e.currentTarget.style.borderColor = 'rgba(6, 182, 212, 0.4)';
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(6, 182, 212, 0.05)';
              e.currentTarget.style.borderColor = 'rgba(6, 182, 212, 0.2)';
            }}
          >
            <RefreshCw size={16} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>

          <button
            onClick={handleLogout}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 16px',
              borderRadius: 10,
              border: '1px solid rgba(239, 68, 68, 0.2)',
              background: 'rgba(239, 68, 68, 0.05)',
              color: '#ef4444',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
              e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.4)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(239, 68, 68, 0.05)';
              e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.2)';
            }}
          >
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        {/* Error Alert */}
        {error && (
          <div
            style={{
              display: 'flex',
              gap: 12,
              padding: 16,
              marginBottom: 24,
              borderRadius: 12,
              background: 'rgba(239, 68, 68, 0.08)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              alignItems: 'flex-start',
            }}
          >
            <AlertCircle size={20} style={{ color: '#ef4444', flexShrink: 0 }} />
            <span style={{ fontSize: 13, color: '#fca5a5' }}>{error}</span>
          </div>
        )}

        {/* Stats Cards */}
        {stats && <StatsCards stats={stats} />}

        {/* Charts and Status */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
            gap: 24,
            marginBottom: 32,
          }}
        >
          <div style={{ gridColumn: 'span 1' }}>
            {detectionStats.length > 0 && <DetectionChart data={detectionStats} />}
          </div>
          <div>
            <ThreatStatus lastUpdate={lastUpdate || undefined} />
          </div>
        </div>

        {/* Recent Scans */}
        <div style={{ marginBottom: 32 }}>
          <RecentScansTable scans={scans} />
        </div>

        {/* User Management */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
            gap: 24,
          }}
        >
          <UsersTable users={users} onBanUser={handleBanUser} onRefresh={fetchData} />
          <BannedUsers bannedUsers={bannedUsers} onUnbanUser={handleUnbanUser} onRefresh={fetchData} />
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

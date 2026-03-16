import { BarChart3, AlertTriangle, CheckCircle, Activity, Radio } from 'lucide-react';

interface StatsCardsProps {
  stats: {
    total_scans: number;
    phishing_detections: number;
    safe_detections: number;
    active_users: number;
    system_status: string;
  };
}

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  borderColor: string;
  sub?: string;
}

function StatCard({ label, value, icon, color, borderColor, sub }: StatCardProps) {
  return (
    <div
      style={{
        background: 'rgba(255, 255, 255, 0.04)',
        border: `1px solid rgba(255, 255, 255, 0.08)`,
        borderTop: `3px solid ${borderColor}`,
        borderRadius: 12,
        padding: 20,
        backdropFilter: 'blur(10px)',
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        transition: 'all 0.3s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = `${borderColor}30`;
        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)';
        e.currentTarget.style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 12, fontWeight: 600, textTransform: 'uppercase', color: '#94a3b8', letterSpacing: '0.05em' }}>
          {label}
        </span>
        {sub && (
          <span style={{ fontSize: 11, fontWeight: 700, color, background: `${color}15`, padding: '4px 8px', borderRadius: 6 }}>
            {sub}
          </span>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 12 }}>
        <div style={{ fontSize: 28, fontWeight: 800, color: '#e2e8f0' }}>{value}</div>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            background: `${color}15`,
            border: `1px solid ${color}25`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color,
          }}
        >
          {icon}
        </div>
      </div>
    </div>
  );
}

export function StatsCards({ stats }: StatsCardsProps) {
  const phishingPercentage = stats.total_scans
    ? ((stats.phishing_detections / stats.total_scans) * 100).toFixed(1)
    : 0;

  const safePercentage = stats.total_scans
    ? ((stats.safe_detections / stats.total_scans) * 100).toFixed(1)
    : 0;

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 16,
        marginBottom: 32,
      }}
    >
      <StatCard
        label="Total Scans"
        value={stats.total_scans.toLocaleString()}
        icon={<BarChart3 size={20} />}
        color="#06b6d4"
        borderColor="#06b6d4"
        sub="All-time"
      />

      <StatCard
        label="Phishing Found"
        value={stats.phishing_detections.toLocaleString()}
        icon={<AlertTriangle size={20} />}
        color="#ef4444"
        borderColor="#ef4444"
        sub={`${phishingPercentage}%`}
      />

      <StatCard
        label="Safe URLs"
        value={stats.safe_detections.toLocaleString()}
        icon={<CheckCircle size={20} />}
        color="#10b981"
        borderColor="#10b981"
        sub={`${safePercentage}%`}
      />

      <StatCard
        label="Active Users"
        value={stats.active_users}
        icon={<Activity size={20} />}
        color="#a78bfa"
        borderColor="#a78bfa"
      />

      <StatCard
        label="System Status"
        value={stats.system_status === 'online' ? 'Online' : 'Checking'}
        icon={<Radio size={20} style={{ animation: stats.system_status === 'online' ? 'pulse 2s infinite' : 'none' }} />}
        color={stats.system_status === 'online' ? '#10b981' : '#f59e0b'}
        borderColor={stats.system_status === 'online' ? '#10b981' : '#f59e0b'}
      />
    </div>
  );
}

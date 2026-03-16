import { CheckCircle, Clock, Zap } from 'lucide-react';

interface ThreatStatusProps {
  lastUpdate?: string;
}

export function ThreatStatus({ lastUpdate }: ThreatStatusProps) {
  const threatFeeds = [
    {
      name: 'PhishTank',
      status: 'ACTIVE',
      description: '56,486 URLs updated',
      color: '#06b6d4',
    },
    {
      name: 'OpenPhish',
      status: 'ACTIVE',
      description: '300+ URLs monitored',
      color: '#a78bfa',
    },
    {
      name: 'Safe Browsing',
      status: 'ACTIVE',
      description: 'Real-time threat data',
      color: '#10b981',
    },
    {
      name: 'ML Model',
      status: 'ACTIVE',
      description: 'RF classifier active',
      color: '#f59e0b',
    },
  ];

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
        <Zap size={18} style={{ color: '#06b6d4' }} />
        <h3 style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0', textTransform: 'uppercase', letterSpacing: '0.05em', margin: 0 }}>
          Threat Intelligence Status
        </h3>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16 }}>
        {threatFeeds.map((feed) => (
          <div
            key={feed.name}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 12,
              padding: 12,
              borderRadius: 10,
              background: 'rgba(15, 23, 42, 0.6)',
              border: `1px solid ${feed.color}20`,
              transition: 'all 0.2s ease',
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(15, 23, 42, 1)';
              e.currentTarget.style.borderColor = `${feed.color}40`;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(15, 23, 42, 0.6)';
              e.currentTarget.style.borderColor = `${feed.color}20`;
            }}
          >
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: feed.color,
                boxShadow: `0 0 12px ${feed.color}`,
                marginTop: 4,
                flexShrink: 0,
              }}
            />
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>{feed.name}</span>
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: 6,
                    background: `${feed.color}20`,
                    color: feed.color,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                  }}
                >
                  <CheckCircle size={12} />
                  {feed.status}
                </span>
              </div>
              <p style={{ fontSize: 12, color: '#64748b', margin: 0 }}>{feed.description}</p>
            </div>
          </div>
        ))}
      </div>

      {lastUpdate && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: 12,
            color: '#64748b',
            paddingTop: 12,
            borderTop: '1px solid rgba(255, 255, 255, 0.06)',
          }}
        >
          <Clock size={14} />
          Last updated: {new Date(lastUpdate).toLocaleString()}
        </div>
      )}
    </div>
  );
}

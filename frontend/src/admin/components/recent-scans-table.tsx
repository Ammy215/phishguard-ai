import { AlertTriangle, CheckCircle, History } from 'lucide-react';

interface Scan {
  id: number;
  url: string;
  risk_score: number;
  result: string;
  scan_time: string;
  source: string;
}

interface RecentScansTableProps {
  scans: Scan[];
}

export function RecentScansTable({ scans }: RecentScansTableProps) {
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
        <History size={18} style={{ color: '#06b6d4' }} />
        <h3 style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0', textTransform: 'uppercase', letterSpacing: '0.05em', margin: 0 }}>
          Recent Scans
        </h3>
        <span style={{ fontSize: 11, marginLeft: 'auto', fontWeight: 600, color: '#64748b', background: 'rgba(148, 163, 184, 0.1)', padding: '4px 10px', borderRadius: 6 }}>
          {scans.length} entries
        </span>
      </div>

      {scans.length > 0 ? (
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
                  URL
                </th>
                <th style={{ padding: '12px 14px', textAlign: 'right', fontSize: 11, fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Risk
                </th>
                <th style={{ padding: '12px 14px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Result
                </th>
                <th style={{ padding: '12px 14px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Source
                </th>
                <th style={{ padding: '12px 14px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Time
                </th>
              </tr>
            </thead>
            <tbody>
              {scans.map((scan, idx) => (
                <tr
                  key={scan.id}
                  style={{
                    borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
                    background: idx % 2 === 0 ? 'rgba(15, 23, 42, 0.4)' : 'transparent',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(6, 182, 212, 0.08)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = idx % 2 === 0 ? 'rgba(15, 23, 42, 0.4)' : 'transparent';
                  }}
                >
                  <td style={{ padding: '12px 14px', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontFamily: 'monospace', fontSize: 12, color: '#94a3b8' }}>
                    {scan.url}
                  </td>
                  <td style={{ padding: '12px 14px', textAlign: 'right', fontWeight: 600, color: scan.risk_score > 50 ? '#ef4444' : '#10b981' }}>
                    {scan.risk_score.toFixed(1)}%
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {scan.result === 'PHISHING' ? (
                        <>
                          <AlertTriangle size={14} style={{ color: '#ef4444' }} />
                          <span style={{ color: '#ef4444', fontWeight: 600 }}>Phishing</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle size={14} style={{ color: '#10b981' }} />
                          <span style={{ color: '#10b981', fontWeight: 600 }}>Safe</span>
                        </>
                      )}
                    </div>
                  </td>
                  <td style={{ padding: '12px 14px', color: '#cbd5e1', fontSize: 12 }}>
                    {scan.source === 'extension' ? '🔌 Extension' : '📊 Dashboard'}
                  </td>
                  <td style={{ padding: '12px 14px', color: '#64748b', fontSize: 12 }}>
                    {formatDate(scan.scan_time)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '24px', color: '#64748b' }}>
          No scans recorded yet
        </div>
      )}
    </div>
  );
}

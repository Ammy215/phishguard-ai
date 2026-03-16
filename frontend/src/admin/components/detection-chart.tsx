import { TrendingUp } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface DetectionChartProps {
  data: Array<{
    result: string;
    count: number;
    date: string;
  }>;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    name: string;
    fill: string;
  }>;
  label?: string;
}

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    return (
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.98) 0%, rgba(30, 41, 59, 0.98) 100%)',
          border: '2px solid rgba(6, 182, 212, 0.6)',
          borderRadius: 12,
          padding: '14px 18px',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.4), 0 0 30px rgba(6, 182, 212, 0.2)',
        }}
      >
        <p style={{ margin: '0 0 10px 0', color: '#06b6d4', fontSize: 13, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {label}
        </p>
        {payload.map((entry, idx) => (
          <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, marginBottom: idx === payload.length - 1 ? 0 : 6 }}>
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: 3,
                background: entry.name === 'Phishing' ? '#ef4444' : '#10b981',
                boxShadow: entry.name === 'Phishing' ? '0 0 10px rgba(239, 68, 68, 0.6)' : '0 0 10px rgba(16, 185, 129, 0.6)',
              }}
            />
            <span style={{ color: '#cbd5e1', fontWeight: 500 }}>
              {entry.name}
            </span>
            <span style={{ color: '#e2e8f0', fontWeight: 800, marginLeft: 'auto' }}>
              {entry.value}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function DetectionChart({ data }: DetectionChartProps) {
  // Group data by date and separate by result
  const chartData: Record<string, any> = {};
  
  data.forEach(item => {
    if (!chartData[item.date]) {
      chartData[item.date] = { date: item.date };
    }
    chartData[item.date][item.result] = item.count;
  });

  const formattedData = Object.values(chartData).map(item => ({
    ...item,
    Phishing: item.Phishing || 0,
    Safe: item.Safe || 0,
  }));

  const totalPhishing = formattedData.reduce((sum, item) => sum + item.Phishing, 0);
  const totalSafe = formattedData.reduce((sum, item) => sum + item.Safe, 0);

  return (
    <div
      style={{
        position: 'relative',
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.8) 100%)',
        border: '1px solid rgba(6, 182, 212, 0.2)',
        borderTop: '2px solid rgba(6, 182, 212, 0.4)',
        borderRadius: 16,
        padding: '28px',
        backdropFilter: 'blur(20px)',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
        transition: 'all 0.3s ease',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.boxShadow = '0 25px 70px rgba(6, 182, 212, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.05)';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.boxShadow = '0 20px 60px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05)';
      }}
    >
      {/* Top accent line */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: '10%',
          right: '10%',
          height: 2,
          background: 'linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.8), transparent)',
          borderRadius: 1,
        }}
      />

      {/* Header with stats */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <div
              style={{
                background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.3) 0%, rgba(6, 182, 212, 0.1) 100%)',
                border: '1px solid rgba(6, 182, 212, 0.3)',
                borderRadius: 12,
                padding: 12,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <TrendingUp size={20} style={{ color: '#06b6d4' }} />
            </div>
            <div>
              <h3 style={{ margin: 0, color: '#e2e8f0', fontSize: 20, fontWeight: 800, letterSpacing: '0.02em' }}>
                DETECTION TRENDS
              </h3>
              <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                7-Day Analysis
              </p>
            </div>
          </div>
        </div>
        
        {/* Quick stats */}
        <div style={{ display: 'flex', gap: 16 }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
              Phishing Detected
            </div>
            <div style={{ fontSize: 24, color: '#ef4444', fontWeight: 800 }}>
              {totalPhishing}
            </div>
          </div>
          <div style={{ width: 1, background: 'rgba(255, 255, 255, 0.1)' }} />
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
              Safe URLs
            </div>
            <div style={{ fontSize: 24, color: '#10b981', fontWeight: 800 }}>
              {totalSafe}
            </div>
          </div>
        </div>
      </div>

      {/* Chart */}
      {formattedData.length > 0 ? (
        <>
          <svg style={{ position: 'absolute', width: 0, height: 0 }}>
            <defs>
              <filter id="phishingGlow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="6" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
              <filter id="safeGlow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="6" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
          </svg>

          <ResponsiveContainer width="100%" height={360}>
            <BarChart
              data={formattedData}
              margin={{ top: 10, right: 30, left: 0, bottom: 30 }}
            >
              <defs>
                {/* Enhanced multi-stop gradients for phishing bars */}
                <linearGradient id="phishingGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#fca5a5" stopOpacity={0.7} />
                  <stop offset="50%" stopColor="#ef4444" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="#b91c1c" stopOpacity={1} />
                </linearGradient>
                
                {/* Enhanced multi-stop gradients for safe bars */}
                <linearGradient id="safeGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6ee7b7" stopOpacity={0.7} />
                  <stop offset="50%" stopColor="#10b981" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="#047857" stopOpacity={1} />
                </linearGradient>
              </defs>

              <CartesianGrid
                strokeDasharray="4 4"
                stroke="rgba(6, 182, 212, 0.08)"
                vertical={false}
                strokeWidth={1}
              />
              
              <XAxis
                dataKey="date"
                stroke="rgba(6, 182, 212, 0.2)"
                tick={{ fontSize: 12, fill: '#94a3b8', fontWeight: 600 }}
                axisLine={{ stroke: 'rgba(6, 182, 212, 0.15)', strokeWidth: 1 }}
                tickLine={{ stroke: 'rgba(6, 182, 212, 0.15)' }}
              />
              
              <YAxis
                stroke="rgba(6, 182, 212, 0.2)"
                tick={{ fontSize: 12, fill: '#94a3b8', fontWeight: 600 }}
                axisLine={{ stroke: 'rgba(6, 182, 212, 0.15)', strokeWidth: 1 }}
                tickLine={{ stroke: 'rgba(6, 182, 212, 0.15)' }}
              />
              
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(6, 182, 212, 0.15)', radius: 6 }} />
              
              <Legend
                wrapperStyle={{ 
                  paddingTop: '24px',
                  display: 'flex',
                  justifyContent: 'center',
                  gap: '30px'
                }}
                iconType="square"
                formatter={(value) => (
                  <span style={{ color: '#cbd5e1', fontSize: 13, fontWeight: 700, letterSpacing: '0.02em' }}>
                    {value}
                  </span>
                )}
              />
              
              <Bar
                dataKey="Phishing"
                fill="url(#phishingGradient)"
                radius={[10, 10, 4, 4]}
                animationDuration={1000}
                animationEasing="ease-in-out"
                filter="url(#phishingGlow)"
                isAnimationActive={true}
              />
              
              <Bar
                dataKey="Safe"
                fill="url(#safeGradient)"
                radius={[10, 10, 4, 4]}
                animationDuration={1000}
                animationEasing="ease-in-out"
                filter="url(#safeGlow)"
                isAnimationActive={true}
              />
            </BarChart>
          </ResponsiveContainer>
        </>
      ) : (
        /* Empty state */
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: 340,
            color: '#64748b',
            fontSize: 14,
          }}
        >
          <div
            style={{
              fontSize: 48,
              marginBottom: 16,
              opacity: 0.3,
            }}
          >
            📊
          </div>
          <p style={{ margin: 0, fontWeight: 600 }}>No detection data available</p>
          <p style={{ margin: '4px 0 0 0', fontSize: 12, opacity: 0.7 }}>
            Detection trends will appear as URLs are scanned
          </p>
        </div>
      )}
    </div>
  );
}

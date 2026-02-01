import { useNavigate, useParams } from 'react-router-dom';
import { useRealData } from '@/app/hooks/useRealData';
import { useSensorHistory } from '@/app/hooks/useSensorHistory';
import {
  ArrowLeft,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  Settings,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';

export function ComponentDetails() {
  const { componentId } = useParams();
  const navigate = useNavigate();
  const { components, alerts, loading } = useRealData();
  const sensorData = useSensorHistory(componentId, 1000); // Poll every second

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-[#ec7211]" />
      </div>
    );
  }

  const machine = components.find(c => c.id === componentId);
  const machineAlerts = alerts.filter(a => a.componentId === componentId);

  if (!machine) {
    return (
      <div className="aws-card">
        <div className="text-center py-12">
          <XCircle className="w-12 h-12 mx-auto mb-3 text-[#d13212]" />
          <p className="text-lg font-medium">Machine not found</p>
          <button
            className="aws-btn aws-btn-primary mt-4"
            onClick={() => navigate('/machines')}
          >
            Back to Fleet
          </button>
        </div>
      </div>
    );
  }

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'healthy': return 'healthy';
      case 'warning': return 'warning';
      case 'critical': return 'critical';
      default: return '';
    }
  };

  // Delta indicator component
  const DeltaIndicator = ({ value, unit = '' }: { value: number; unit?: string }) => {
    if (Math.abs(value) < 0.01) {
      return <Minus className="w-4 h-4 text-[#545b64]" />;
    }
    return (
      <span className={`flex items-center gap-1 text-sm ${value > 0 ? 'text-[#d13212]' : 'text-[#1e8900]'}`}>
        {value > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
        {Math.abs(value).toFixed(2)}{unit}
      </span>
    );
  };

  // Format chart data from history
  const chartData = sensorData.history.map((reading) => ({
    time: new Date(reading.timestamp).toLocaleTimeString('en-US', { hour12: false, minute: '2-digit', second: '2-digit' }),
    health: reading.health_score || 0,
    temperature: reading.temperature || 0,
    vibration: reading.vibration || 0,
    pressure: reading.pressure || 0
  }));

  return (
    <div>
      {/* Page Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            className="aws-btn aws-btn-secondary"
            onClick={() => navigate('/machines')}
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold text-[#16191f]">{machine.name}</h1>
              <span className={`aws-badge aws-badge-${getStatusClass(machine.status)}`}>
                {machine.status === 'healthy' && <CheckCircle2 className="w-3 h-3" />}
                {machine.status === 'warning' && <AlertTriangle className="w-3 h-3" />}
                {machine.status === 'critical' && <XCircle className="w-3 h-3" />}
                {machine.status.charAt(0).toUpperCase() + machine.status.slice(1)}
              </span>
              {/* Live indicator */}
              <span className="flex items-center gap-1 text-sm text-[#1e8900]">
                <span className="w-2 h-2 bg-[#1e8900] rounded-full animate-pulse"></span>
                LIVE
              </span>
            </div>
            <p className="text-sm text-[#545b64] mt-1">
              Machine ID: {machine.id} • Plant {machine.plantId || '1'}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="aws-btn aws-btn-secondary">
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button className="aws-btn aws-btn-secondary">
            <Settings className="w-4 h-4" />
            Configure
          </button>
        </div>
      </div>

      {/* Live Sensor Metrics with Delta Indicators */}
      <div className="aws-metric-grid">
        <div className="aws-metric-card relative overflow-hidden">
          <div className="aws-metric-label">Health Score</div>
          <div className={`aws-metric-value ${getStatusClass(machine.status)}`}>
            {sensorData.current?.health_score?.toFixed(1) || machine.healthScore}%
          </div>
          <div className="flex items-center justify-between mt-2">
            <DeltaIndicator value={sensorData.delta.health_score} unit="%" />
            <span className="text-xs text-[#545b64]">vs last reading</span>
          </div>
          <div className="aws-progress mt-2">
            <div
              className={`aws-progress-bar ${getStatusClass(machine.status)} transition-all duration-500`}
              style={{ width: `${sensorData.current?.health_score || machine.healthScore}%` }}
            />
          </div>
        </div>

        <div className="aws-metric-card">
          <div className="aws-metric-label">Temperature</div>
          <div className="aws-metric-value text-2xl">
            {sensorData.current?.temperature?.toFixed(1) || '—'}°C
          </div>
          <div className="flex items-center justify-between mt-2">
            <DeltaIndicator value={sensorData.delta.temperature} unit="°" />
            <span className="text-xs text-[#545b64]">fluctuation</span>
          </div>
        </div>

        <div className="aws-metric-card">
          <div className="aws-metric-label">Vibration</div>
          <div className="aws-metric-value text-2xl">
            {sensorData.current?.vibration?.toFixed(3) || '—'} mm/s
          </div>
          <div className="flex items-center justify-between mt-2">
            <DeltaIndicator value={sensorData.delta.vibration} />
            <span className="text-xs text-[#545b64]">fluctuation</span>
          </div>
        </div>

        <div className="aws-metric-card">
          <div className="aws-metric-label">Predicted RUL</div>
          <div className="aws-metric-value text-lg">
            {sensorData.current?.rul_hours?.toFixed(0) || machine.predictedFailureTime} hrs
          </div>
          <div className="flex items-center gap-2 mt-2 text-sm text-[#545b64]">
            <Clock className="w-4 h-4" />
            Time to maintenance
          </div>
        </div>
      </div>

      {/* Live Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        {/* Health Trend - Live */}
        <div className="aws-card">
          <div className="aws-card-header">
            <h3 className="aws-card-title flex items-center gap-2">
              Health Score Trend
              <span className="w-2 h-2 bg-[#1e8900] rounded-full animate-pulse"></span>
            </h3>
            <span className="text-sm text-[#545b64]">{chartData.length} readings</span>
          </div>
          <div className="aws-card-body">
            {sensorData.loading ? (
              <div className="flex items-center justify-center h-[250px]">
                <Loader2 className="w-6 h-6 animate-spin text-[#ec7211]" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="healthGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#1e8900" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#1e8900" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eaeded" />
                  <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#545b64' }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#545b64' }} />
                  <Tooltip
                    contentStyle={{
                      background: '#fff',
                      border: '1px solid #eaeded',
                      borderRadius: '8px',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="health"
                    stroke="#1e8900"
                    strokeWidth={2}
                    fill="url(#healthGradient)"
                    isAnimationActive={true}
                    animationDuration={300}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Sensor Data - Live */}
        <div className="aws-card">
          <div className="aws-card-header">
            <h3 className="aws-card-title flex items-center gap-2">
              Live Sensor Readings
              <span className="w-2 h-2 bg-[#1e8900] rounded-full animate-pulse"></span>
            </h3>
          </div>
          <div className="aws-card-body">
            {sensorData.loading ? (
              <div className="flex items-center justify-center h-[250px]">
                <Loader2 className="w-6 h-6 animate-spin text-[#ec7211]" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eaeded" />
                  <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#545b64' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#545b64' }} />
                  <Tooltip
                    contentStyle={{
                      background: '#fff',
                      border: '1px solid #eaeded',
                      borderRadius: '8px'
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="temperature"
                    stroke="#d13212"
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={true}
                    animationDuration={300}
                  />
                  <Line
                    type="monotone"
                    dataKey="vibration"
                    stroke="#0073bb"
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={true}
                    animationDuration={300}
                  />
                  <Line
                    type="monotone"
                    dataKey="pressure"
                    stroke="#1e8900"
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={true}
                    animationDuration={300}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
            <div className="flex justify-center gap-6 mt-2 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-[#d13212]"></div>
                <span className="text-[#545b64]">Temperature</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-[#0073bb]"></div>
                <span className="text-[#545b64]">Vibration</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-[#1e8900]"></div>
                <span className="text-[#545b64]">Pressure</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="aws-card mt-6">
        <div className="aws-card-header">
          <h3 className="aws-card-title">Machine Alerts</h3>
        </div>
        <div className="aws-card-body p-0">
          {machineAlerts.length === 0 ? (
            <div className="text-center py-8 text-[#545b64]">
              <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-[#1e8900]" />
              <p>No alerts for this machine</p>
            </div>
          ) : (
            <table className="aws-table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Message</th>
                  <th>Status</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {machineAlerts.map((alert) => (
                  <tr key={alert.id}>
                    <td>
                      <span className={`aws-badge aws-badge-${alert.severity === 'critical' ? 'critical' : 'warning'}`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td>{alert.message}</td>
                    <td>
                      <span className={`aws-badge ${alert.status === 'completed' ? 'aws-badge-healthy' : 'aws-badge-critical'
                        }`}>
                        {alert.status === 'completed' ? 'Resolved' : 'Active'}
                      </span>
                    </td>
                    <td className="text-sm text-[#545b64]">
                      {new Date(alert.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

import { useNavigate } from 'react-router-dom';
import { useRealData } from '@/app/hooks/useRealData';
import {
    Activity,
    AlertTriangle,
    Clock,
    ChevronRight,
    Loader2,
    CheckCircle2,
    XCircle
} from 'lucide-react';

export function Dashboard() {
    const navigate = useNavigate();
    const { plants, components, alerts, loading } = useRealData();

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 animate-spin text-[#ec7211]" />
            </div>
        );
    }

    const totalAlerts = alerts.filter(a => a.status !== 'completed').length;
    const criticalAlerts = alerts.filter(a => a.severity === 'critical' && a.status !== 'completed').length;
    const healthyMachines = components.filter(c => c.status === 'healthy').length;
    const overallHealth = components.length > 0
        ? Math.round(components.reduce((sum, c) => sum + c.healthScore, 0) / components.length)
        : 0;

    const getStatusClass = (status: string) => {
        switch (status) {
            case 'healthy': return 'healthy';
            case 'warning': return 'warning';
            case 'critical': return 'critical';
            default: return '';
        }
    };

    return (
        <div>
            {/* Page Header */}
            <div className="mb-6">
                <h1 className="text-2xl font-semibold text-[#16191f]">Dashboard</h1>
                <p className="text-sm text-[#545b64] mt-1">
                    Real-time monitoring and predictive maintenance overview
                </p>
            </div>

            {/* Metric Cards */}
            <div className="aws-metric-grid">
                <div className="aws-metric-card">
                    <div className="aws-metric-label">Total Machines</div>
                    <div className="aws-metric-value">{components.length}</div>
                    <div className="flex items-center gap-2 mt-2 text-sm text-[#545b64]">
                        <CheckCircle2 className="w-4 h-4 text-[#1e8900]" />
                        {healthyMachines} operational
                    </div>
                </div>

                <div className="aws-metric-card">
                    <div className="aws-metric-label">Overall Health</div>
                    <div className={`aws-metric-value ${overallHealth >= 70 ? 'healthy' : overallHealth >= 40 ? 'warning' : 'critical'}`}>
                        {overallHealth}%
                    </div>
                    <div className="aws-progress mt-2">
                        <div
                            className={`aws-progress-bar ${overallHealth >= 70 ? 'healthy' : overallHealth >= 40 ? 'warning' : 'critical'}`}
                            style={{ width: `${overallHealth}%` }}
                        />
                    </div>
                </div>

                <div className="aws-metric-card">
                    <div className="aws-metric-label">Active Alerts</div>
                    <div className={`aws-metric-value ${totalAlerts > 0 ? 'warning' : 'healthy'}`}>
                        {totalAlerts}
                    </div>
                    {criticalAlerts > 0 && (
                        <div className="flex items-center gap-2 mt-2 text-sm text-[#d13212]">
                            <XCircle className="w-4 h-4" />
                            {criticalAlerts} critical
                        </div>
                    )}
                </div>

                <div className="aws-metric-card">
                    <div className="aws-metric-label">Plants Online</div>
                    <div className="aws-metric-value healthy">{plants.length}</div>
                    <div className="flex items-center gap-2 mt-2 text-sm text-[#1e8900]">
                        <Activity className="w-4 h-4" />
                        All systems operational
                    </div>
                </div>
            </div>

            {/* Machines Table */}
            <div className="aws-card">
                <div className="aws-card-header">
                    <h2 className="aws-card-title">Machine Fleet Status</h2>
                    <button
                        className="aws-btn aws-btn-primary"
                        onClick={() => navigate('/machines')}
                    >
                        View All
                        <ChevronRight className="w-4 h-4" />
                    </button>
                </div>
                <div className="aws-card-body p-0">
                    <table className="aws-table">
                        <thead>
                            <tr>
                                <th>Machine ID</th>
                                <th>Name</th>
                                <th>Status</th>
                                <th>Health Score</th>
                                <th>Predicted RUL</th>
                                <th>Last Maintenance</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {components.slice(0, 5).map((machine) => (
                                <tr
                                    key={machine.id}
                                    className="cursor-pointer"
                                    onClick={() => navigate(`/component/${machine.id}`)}
                                >
                                    <td className="font-mono text-sm">{machine.id}</td>
                                    <td className="font-medium">{machine.name}</td>
                                    <td>
                                        <span className={`aws-badge aws-badge-${getStatusClass(machine.status)}`}>
                                            {machine.status === 'healthy' && <CheckCircle2 className="w-3 h-3" />}
                                            {machine.status === 'warning' && <AlertTriangle className="w-3 h-3" />}
                                            {machine.status === 'critical' && <XCircle className="w-3 h-3" />}
                                            {machine.status.charAt(0).toUpperCase() + machine.status.slice(1)}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="flex items-center gap-2">
                                            <div className="aws-progress w-16">
                                                <div
                                                    className={`aws-progress-bar ${getStatusClass(machine.status)}`}
                                                    style={{ width: `${machine.healthScore}%` }}
                                                />
                                            </div>
                                            <span className="text-sm font-medium">{machine.healthScore}%</span>
                                        </div>
                                    </td>
                                    <td>
                                        <span className="flex items-center gap-1 text-sm">
                                            <Clock className="w-4 h-4 text-[#545b64]" />
                                            {machine.predictedFailureTime || 'N/A'}
                                        </span>
                                    </td>
                                    <td className="text-sm text-[#545b64]">{machine.lastMaintenance}</td>
                                    <td>
                                        <ChevronRight className="w-4 h-4 text-[#545b64]" />
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Recent Alerts */}
            <div className="aws-card mt-6">
                <div className="aws-card-header">
                    <h2 className="aws-card-title">Recent Alerts</h2>
                    <button
                        className="aws-btn aws-btn-secondary"
                        onClick={() => navigate('/alerts')}
                    >
                        View All Alerts
                    </button>
                </div>
                <div className="aws-card-body p-0">
                    {alerts.length === 0 ? (
                        <div className="text-center py-8 text-[#545b64]">
                            <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-[#1e8900]" />
                            <p>No active alerts. All systems operational.</p>
                        </div>
                    ) : (
                        <table className="aws-table">
                            <thead>
                                <tr>
                                    <th>Severity</th>
                                    <th>Machine</th>
                                    <th>Message</th>
                                    <th>Status</th>
                                    <th>Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {alerts.slice(0, 5).map((alert) => (
                                    <tr key={alert.id}>
                                        <td>
                                            <span className={`aws-badge aws-badge-${alert.severity === 'critical' ? 'critical' : alert.severity === 'medium' ? 'warning' : 'healthy'}`}>
                                                {alert.severity}
                                            </span>
                                        </td>
                                        <td className="font-medium">{alert.componentName}</td>
                                        <td className="text-sm">{alert.message}</td>
                                        <td>
                                            <span className={`aws-badge ${alert.status === 'completed' ? 'aws-badge-healthy' :
                                                alert.status === 'in-progress' ? 'aws-badge-warning' : 'aws-badge-critical'
                                                }`}>
                                                {alert.status === 'not-completed' ? 'Active' :
                                                    alert.status === 'in-progress' ? 'In Progress' : 'Resolved'}
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

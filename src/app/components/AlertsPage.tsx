import { useState, useEffect } from 'react';
import {
    AlertTriangle,
    CheckCircle2,
    XCircle,
    Clock,
    RefreshCw,
    Trash2,
    X,
    User,
    FileText
} from 'lucide-react';

interface Alert {
    id: string;
    machine_id: string;
    machine_name: string;
    message: string;
    severity: 'critical' | 'warning' | 'info';
    state: 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';
    created_at: string;
    acknowledged_by?: string;
    acknowledged_at?: string;
}

interface AcknowledgeForm {
    operator_id: string;
}

interface ResolveForm {
    operator_id: string;
    root_cause: string;
    resolution_notes: string;
    downtime_minutes: number;
}

export function AlertsPage() {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'active' | 'acknowledged' | 'resolved'>('all');

    // Modal states
    const [acknowledgeModal, setAcknowledgeModal] = useState<string | null>(null);
    const [resolveModal, setResolveModal] = useState<string | null>(null);
    const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

    // Form states
    const [ackForm, setAckForm] = useState<AcknowledgeForm>({ operator_id: '' });
    const [resolveForm, setResolveForm] = useState<ResolveForm>({
        operator_id: '',
        root_cause: '',
        resolution_notes: '',
        downtime_minutes: 0
    });

    const machines: Record<string, string> = {
        'M-001': 'Feedwater Pump',
        'M-002': 'ID Fan Motor',
        'M-003': 'HVAC Chiller',
        'M-004': 'Boiler Feed Motor'
    };

    useEffect(() => {
        fetchAlerts();
        const interval = setInterval(fetchAlerts, 5000); // Poll every 5s
        return () => clearInterval(interval);
    }, []);

    const fetchAlerts = async () => {
        try {
            const res = await fetch('http://localhost:5000/api/alerts');
            const data = await res.json();

            const formattedAlerts: Alert[] = (data.alerts || []).map((a: any) => ({
                id: a.id,
                machine_id: a.machine_id,
                machine_name: machines[a.machine_id] || a.machine_id,
                message: a.message,
                severity: a.severity,
                state: a.state,
                created_at: a.created_at,
                acknowledged_by: a.acknowledged_by,
                acknowledged_at: a.acknowledged_at
            }));

            setAlerts(formattedAlerts);
        } catch (error) {
            console.error('Error fetching alerts:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleAcknowledge = async () => {
        if (!acknowledgeModal || !ackForm.operator_id) {
            alert('Please enter Operator ID');
            return;
        }

        try {
            const res = await fetch(`http://localhost:5000/api/alerts/${acknowledgeModal}/acknowledge`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ operator_id: ackForm.operator_id })
            });

            const data = await res.json();
            if (data.success) {
                setAcknowledgeModal(null);
                setAckForm({ operator_id: '' });
                fetchAlerts();
            } else {
                alert('Error: ' + (data.error || 'Failed to acknowledge'));
            }
        } catch (error) {
            console.error('Error acknowledging:', error);
            alert('Error acknowledging alert');
        }
    };

    const handleResolve = async () => {
        if (!resolveModal || !resolveForm.operator_id || !resolveForm.root_cause || !resolveForm.resolution_notes) {
            alert('Please fill in all required fields');
            return;
        }

        try {
            const res = await fetch(`http://localhost:5000/api/alerts/${resolveModal}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(resolveForm)
            });

            const data = await res.json();
            if (data.success) {
                setResolveModal(null);
                setResolveForm({ operator_id: '', root_cause: '', resolution_notes: '', downtime_minutes: 0 });
                fetchAlerts();
            } else {
                alert('Error: ' + (data.error || 'Failed to resolve'));
            }
        } catch (error) {
            console.error('Error resolving:', error);
            alert('Error resolving alert');
        }
    };

    const handleDelete = async (alertId: string) => {
        try {
            // For now, just resolve immediately (alerts don't typically get deleted, they get resolved)
            const res = await fetch(`http://localhost:5000/api/alerts/${alertId}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    operator_id: 'System',
                    root_cause: 'Dismissed by operator',
                    resolution_notes: 'Alert manually dismissed',
                    downtime_minutes: 0
                })
            });

            if (res.ok) {
                setDeleteConfirm(null);
                fetchAlerts();
            }
        } catch (error) {
            console.error('Error dismissing alert:', error);
        }
    };

    const filteredAlerts = alerts.filter(a => {
        if (filter === 'active') return a.state === 'ACTIVE';
        if (filter === 'acknowledged') return a.state === 'ACKNOWLEDGED';
        if (filter === 'resolved') return a.state === 'RESOLVED';
        return true;
    });

    const getSeverityBadge = (severity: string) => {
        switch (severity) {
            case 'critical':
                return <span className="aws-badge aws-badge-critical flex items-center gap-1"><XCircle className="w-3 h-3" />Critical</span>;
            case 'warning':
                return <span className="aws-badge aws-badge-warning flex items-center gap-1"><AlertTriangle className="w-3 h-3" />Warning</span>;
            default:
                return <span className="aws-badge aws-badge-healthy">Info</span>;
        }
    };

    const getStateBadge = (state: string) => {
        switch (state) {
            case 'ACTIVE':
                return <span className="aws-badge aws-badge-critical">Active</span>;
            case 'ACKNOWLEDGED':
                return <span className="aws-badge aws-badge-warning">Acknowledged</span>;
            case 'RESOLVED':
                return <span className="aws-badge aws-badge-healthy">Resolved</span>;
            default:
                return <span className="aws-badge">{state}</span>;
        }
    };

    const formatDate = (timestamp: string) => {
        return new Date(timestamp).toLocaleString('en-US', {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });
    };

    return (
        <div>
            {/* Page Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-semibold text-[#16191f]">Alert Management</h1>
                    <p className="text-sm text-[#545b64] mt-1">
                        Monitor, acknowledge, and resolve system alerts
                    </p>
                </div>
                <button
                    onClick={fetchAlerts}
                    className="aws-btn aws-btn-secondary flex items-center gap-2"
                >
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                </button>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="aws-card">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-red-100 rounded-lg">
                            <XCircle className="w-5 h-5 text-red-600" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold">{alerts.filter(a => a.state === 'ACTIVE').length}</div>
                            <div className="text-sm text-[#545b64]">Active</div>
                        </div>
                    </div>
                </div>
                <div className="aws-card">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-yellow-100 rounded-lg">
                            <AlertTriangle className="w-5 h-5 text-yellow-600" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold">{alerts.filter(a => a.state === 'ACKNOWLEDGED').length}</div>
                            <div className="text-sm text-[#545b64]">Acknowledged</div>
                        </div>
                    </div>
                </div>
                <div className="aws-card">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-green-100 rounded-lg">
                            <CheckCircle2 className="w-5 h-5 text-green-600" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold">{alerts.filter(a => a.state === 'RESOLVED').length}</div>
                            <div className="text-sm text-[#545b64]">Resolved</div>
                        </div>
                    </div>
                </div>
                <div className="aws-card">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-[#545b64]/10 rounded-lg">
                            <FileText className="w-5 h-5 text-[#545b64]" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold">{alerts.length}</div>
                            <div className="text-sm text-[#545b64]">Total</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Filter Tabs */}
            <div className="flex gap-2 mb-4">
                {(['all', 'active', 'acknowledged', 'resolved'] as const).map((status) => (
                    <button
                        key={status}
                        onClick={() => setFilter(status)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition ${filter === status
                            ? 'bg-[#ec7211] text-white'
                            : 'bg-[#f2f3f3] text-[#545b64] hover:bg-[#eaeded]'
                            }`}
                    >
                        {status.charAt(0).toUpperCase() + status.slice(1)}
                        <span className="ml-2 px-1.5 py-0.5 bg-white/20 rounded text-xs">
                            {status === 'all' ? alerts.length : alerts.filter(a =>
                                status === 'active' ? a.state === 'ACTIVE' :
                                    status === 'acknowledged' ? a.state === 'ACKNOWLEDGED' :
                                        a.state === 'RESOLVED'
                            ).length}
                        </span>
                    </button>
                ))}
            </div>

            {/* Alerts Table */}
            <div className="aws-card overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="bg-[#fafafa] border-b border-[#eaeded]">
                                <th className="text-left p-4 text-sm font-medium text-[#545b64]">Severity</th>
                                <th className="text-left p-4 text-sm font-medium text-[#545b64]">Machine</th>
                                <th className="text-left p-4 text-sm font-medium text-[#545b64]">Message</th>
                                <th className="text-left p-4 text-sm font-medium text-[#545b64]">State</th>
                                <th className="text-left p-4 text-sm font-medium text-[#545b64]">Created</th>
                                <th className="text-left p-4 text-sm font-medium text-[#545b64]">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan={6} className="p-8 text-center text-[#545b64]">
                                        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                                        Loading alerts...
                                    </td>
                                </tr>
                            ) : filteredAlerts.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="p-8 text-center text-[#545b64]">
                                        <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-green-500" />
                                        No alerts to display
                                        <div className="text-sm mt-1">All systems operating normally</div>
                                    </td>
                                </tr>
                            ) : (
                                filteredAlerts.map((alert) => (
                                    <tr key={alert.id} className="border-b border-[#eaeded] hover:bg-[#fafafa]">
                                        <td className="p-4">{getSeverityBadge(alert.severity)}</td>
                                        <td className="p-4">
                                            <div className="font-medium">{alert.machine_id}</div>
                                            <div className="text-xs text-[#545b64]">{alert.machine_name}</div>
                                        </td>
                                        <td className="p-4 max-w-xs">
                                            <div className="text-sm truncate">{alert.message}</div>
                                        </td>
                                        <td className="p-4">
                                            {getStateBadge(alert.state)}
                                            {alert.acknowledged_by && (
                                                <div className="text-xs text-[#545b64] mt-1">
                                                    by {alert.acknowledged_by}
                                                </div>
                                            )}
                                        </td>
                                        <td className="p-4">
                                            <div className="flex items-center gap-1 text-sm text-[#545b64]">
                                                <Clock className="w-4 h-4" />
                                                {formatDate(alert.created_at)}
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <div className="flex gap-2">
                                                {alert.state === 'ACTIVE' && (
                                                    <button
                                                        onClick={() => setAcknowledgeModal(alert.id)}
                                                        className="px-3 py-1.5 text-xs font-medium bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200 transition"
                                                    >
                                                        Acknowledge
                                                    </button>
                                                )}
                                                {alert.state !== 'RESOLVED' && (
                                                    <button
                                                        onClick={() => setResolveModal(alert.id)}
                                                        className="px-3 py-1.5 text-xs font-medium bg-green-100 text-green-800 rounded hover:bg-green-200 transition"
                                                    >
                                                        Resolve
                                                    </button>
                                                )}
                                                {deleteConfirm === alert.id ? (
                                                    <div className="flex items-center gap-1">
                                                        <button
                                                            onClick={() => handleDelete(alert.id)}
                                                            className="text-red-600 text-xs font-medium hover:underline"
                                                        >
                                                            Confirm
                                                        </button>
                                                        <button
                                                            onClick={() => setDeleteConfirm(null)}
                                                            className="text-[#545b64] text-xs hover:underline"
                                                        >
                                                            Cancel
                                                        </button>
                                                    </div>
                                                ) : (
                                                    <button
                                                        onClick={() => setDeleteConfirm(alert.id)}
                                                        className="p-1.5 text-[#545b64] hover:text-red-600 hover:bg-red-50 rounded transition"
                                                        title="Dismiss alert"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Acknowledge Modal */}
            {acknowledgeModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
                        <div className="flex items-center justify-between p-4 border-b border-[#eaeded]">
                            <h2 className="text-lg font-semibold">Acknowledge Alert</h2>
                            <button onClick={() => setAcknowledgeModal(null)} className="p-1 hover:bg-[#f2f3f3] rounded">
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="p-4 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-[#16191f] mb-1">
                                    <User className="w-4 h-4 inline mr-1" />
                                    Operator ID *
                                </label>
                                <input
                                    type="text"
                                    value={ackForm.operator_id}
                                    onChange={(e) => setAckForm({ operator_id: e.target.value })}
                                    placeholder="e.g., John Smith"
                                    className="w-full px-3 py-2 border border-[#d5dbdb] rounded-lg focus:outline-none focus:border-[#0073bb]"
                                />
                            </div>
                            <p className="text-sm text-[#545b64]">
                                Acknowledging this alert indicates you are aware of the issue and will take action.
                            </p>
                        </div>
                        <div className="flex justify-end gap-2 p-4 border-t border-[#eaeded]">
                            <button onClick={() => setAcknowledgeModal(null)} className="aws-btn aws-btn-secondary">
                                Cancel
                            </button>
                            <button onClick={handleAcknowledge} className="aws-btn" style={{ backgroundColor: '#ff9900', color: 'white' }}>
                                Acknowledge
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Resolve Modal */}
            {resolveModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
                        <div className="flex items-center justify-between p-4 border-b border-[#eaeded]">
                            <h2 className="text-lg font-semibold">Resolve Alert</h2>
                            <button onClick={() => setResolveModal(null)} className="p-1 hover:bg-[#f2f3f3] rounded">
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="p-4 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-[#16191f] mb-1">Operator ID *</label>
                                <input
                                    type="text"
                                    value={resolveForm.operator_id}
                                    onChange={(e) => setResolveForm({ ...resolveForm, operator_id: e.target.value })}
                                    placeholder="e.g., John Smith"
                                    className="w-full px-3 py-2 border border-[#d5dbdb] rounded-lg focus:outline-none focus:border-[#0073bb]"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-[#16191f] mb-1">Root Cause *</label>
                                <input
                                    type="text"
                                    value={resolveForm.root_cause}
                                    onChange={(e) => setResolveForm({ ...resolveForm, root_cause: e.target.value })}
                                    placeholder="e.g., Bearing wear"
                                    className="w-full px-3 py-2 border border-[#d5dbdb] rounded-lg focus:outline-none focus:border-[#0073bb]"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-[#16191f] mb-1">Resolution Notes *</label>
                                <textarea
                                    value={resolveForm.resolution_notes}
                                    onChange={(e) => setResolveForm({ ...resolveForm, resolution_notes: e.target.value })}
                                    placeholder="Describe the actions taken..."
                                    rows={3}
                                    className="w-full px-3 py-2 border border-[#d5dbdb] rounded-lg focus:outline-none focus:border-[#0073bb] resize-none"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-[#16191f] mb-1">Downtime (minutes)</label>
                                <input
                                    type="number"
                                    min="0"
                                    value={resolveForm.downtime_minutes}
                                    onChange={(e) => setResolveForm({ ...resolveForm, downtime_minutes: parseInt(e.target.value) || 0 })}
                                    className="w-full px-3 py-2 border border-[#d5dbdb] rounded-lg focus:outline-none focus:border-[#0073bb]"
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-2 p-4 border-t border-[#eaeded]">
                            <button onClick={() => setResolveModal(null)} className="aws-btn aws-btn-secondary">
                                Cancel
                            </button>
                            <button onClick={handleResolve} className="aws-btn aws-btn-primary">
                                Resolve Alert
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

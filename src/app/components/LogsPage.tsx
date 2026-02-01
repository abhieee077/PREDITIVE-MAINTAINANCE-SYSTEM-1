import { useState, useEffect } from 'react';
import { FileText, Calendar, CheckCircle2, Wrench, User, Clock, RefreshCw, Plus, Trash2, X } from 'lucide-react';

interface MaintenanceLog {
    id: string;
    machine_id: string;
    action: string;
    performed_by: string;
    timestamp: string;
    duration_hours?: number;
    notes?: string;
    status: 'completed' | 'in_progress' | 'scheduled';
}

interface NewLogForm {
    machine_id: string;
    action: string;
    performed_by: string;
    duration_hours: number;
    notes: string;
    status: 'completed' | 'in_progress' | 'scheduled';
}

export function LogsPage() {
    const [logs, setLogs] = useState<MaintenanceLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'completed' | 'in_progress' | 'scheduled'>('all');
    const [showAddModal, setShowAddModal] = useState(false);
    const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
    const [formData, setFormData] = useState<NewLogForm>({
        machine_id: 'M-001',
        action: '',
        performed_by: '',
        duration_hours: 1,
        notes: '',
        status: 'completed'
    });

    const machines = [
        { id: 'M-001', name: 'Feedwater Pump' },
        { id: 'M-002', name: 'ID Fan Motor' },
        { id: 'M-003', name: 'HVAC Chiller' },
        { id: 'M-004', name: 'Boiler Feed Motor' }
    ];

    useEffect(() => {
        fetchLogs();
    }, []);

    const fetchLogs = async () => {
        setLoading(true);
        try {
            const res = await fetch('http://localhost:5000/api/logs?days=30');
            const data = await res.json();

            const formattedLogs: MaintenanceLog[] = (data.logs || []).map((log: any) => ({
                id: log.id,
                machine_id: log.machine_id || 'M-001',
                action: log.root_cause || log.action || 'Routine Maintenance',
                performed_by: log.operator || log.performed_by || 'System',
                timestamp: log.resolved_at || log.timestamp || new Date().toISOString(),
                duration_hours: log.downtime_minutes ? Math.round(log.downtime_minutes / 60 * 10) / 10 : 1,
                notes: log.resolution_notes || log.notes || '',
                status: log.alert_type === 'scheduled' ? 'scheduled' :
                    log.alert_type === 'in_progress' ? 'in_progress' : 'completed'
            }));

            setLogs(formattedLogs);
        } catch (error) {
            console.error('Error fetching logs:', error);
            setLogs([]);
        }
        setLoading(false);
    };

    const handleAddLog = async () => {
        if (!formData.action || !formData.performed_by) {
            alert('Please fill in required fields');
            return;
        }

        try {
            const res = await fetch('http://localhost:5000/api/logs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await res.json();
            if (data.success) {
                setShowAddModal(false);
                setFormData({
                    machine_id: 'M-001',
                    action: '',
                    performed_by: '',
                    duration_hours: 1,
                    notes: '',
                    status: 'completed'
                });
                fetchLogs();
            } else {
                alert('Error creating log: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error creating log:', error);
            alert('Error creating log');
        }
    };

    const handleDeleteLog = async (logId: string) => {
        try {
            const res = await fetch(`http://localhost:5000/api/logs/${logId}`, {
                method: 'DELETE'
            });

            const data = await res.json();
            if (data.success) {
                setDeleteConfirm(null);
                fetchLogs();
            } else {
                alert('Error deleting log: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error deleting log:', error);
            alert('Error deleting log');
        }
    };

    const filteredLogs = logs.filter(log => filter === 'all' || log.status === filter);

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'completed':
                return <span className="aws-badge aws-badge-healthy">Completed</span>;
            case 'in_progress':
                return <span className="aws-badge aws-badge-warning">In Progress</span>;
            case 'scheduled':
                return <span className="aws-badge" style={{ backgroundColor: '#0073bb', color: 'white' }}>Scheduled</span>;
            default:
                return <span className="aws-badge">{status}</span>;
        }
    };

    const formatDate = (timestamp: string) => {
        const date = new Date(timestamp);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div>
            {/* Page Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-semibold text-[#16191f]">Maintenance Logs</h1>
                    <p className="text-sm text-[#545b64] mt-1">
                        Complete history of maintenance activities and repairs
                    </p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="aws-btn aws-btn-primary flex items-center gap-2"
                    >
                        <Plus className="w-4 h-4" />
                        Add Log
                    </button>
                    <button
                        onClick={fetchLogs}
                        className="aws-btn aws-btn-secondary flex items-center gap-2"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Refresh
                    </button>
                </div>
            </div>

            {/* Filter Tabs */}
            <div className="flex gap-2 mb-4">
                {(['all', 'completed', 'in_progress', 'scheduled'] as const).map((status) => (
                    <button
                        key={status}
                        onClick={() => setFilter(status)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition ${filter === status
                            ? 'bg-[#ec7211] text-white'
                            : 'bg-[#f2f3f3] text-[#545b64] hover:bg-[#eaeded]'
                            }`}
                    >
                        {status === 'all' ? 'All' : status.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                        {status !== 'all' && (
                            <span className="ml-2 px-1.5 py-0.5 bg-white/20 rounded text-xs">
                                {logs.filter(l => l.status === status).length}
                            </span>
                        )}
                    </button>
                ))}
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="aws-card">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-[#1e8900]/10 rounded-lg">
                            <CheckCircle2 className="w-5 h-5 text-[#1e8900]" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold">{logs.filter(l => l.status === 'completed').length}</div>
                            <div className="text-sm text-[#545b64]">Completed</div>
                        </div>
                    </div>
                </div>
                <div className="aws-card">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-[#ff9900]/10 rounded-lg">
                            <Wrench className="w-5 h-5 text-[#ff9900]" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold">{logs.filter(l => l.status === 'in_progress').length}</div>
                            <div className="text-sm text-[#545b64]">In Progress</div>
                        </div>
                    </div>
                </div>
                <div className="aws-card">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-[#0073bb]/10 rounded-lg">
                            <Calendar className="w-5 h-5 text-[#0073bb]" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold">{logs.filter(l => l.status === 'scheduled').length}</div>
                            <div className="text-sm text-[#545b64]">Scheduled</div>
                        </div>
                    </div>
                </div>
                <div className="aws-card">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-[#545b64]/10 rounded-lg">
                            <Clock className="w-5 h-5 text-[#545b64]" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold">{logs.reduce((sum, l) => sum + (l.duration_hours || 0), 0).toFixed(1)}h</div>
                            <div className="text-sm text-[#545b64]">Total Hours</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Logs Table */}
            <div className="aws-card overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="bg-[#fafafa] border-b border-[#eaeded]">
                                <th className="text-left p-4 text-sm font-medium text-[#545b64]">Log ID</th>
                                <th className="text-left p-4 text-sm font-medium text-[#545b64]">Machine</th>
                                <th className="text-left p-4 text-sm font-medium text-[#545b64]">Action</th>
                                <th className="text-left p-4 text-sm font-medium text-[#545b64]">Performed By</th>
                                <th className="text-left p-4 text-sm font-medium text-[#545b64]">Date</th>
                                <th className="text-left p-4 text-sm font-medium text-[#545b64]">Duration</th>
                                <th className="text-left p-4 text-sm font-medium text-[#545b64]">Status</th>
                                <th className="text-left p-4 text-sm font-medium text-[#545b64]">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan={8} className="p-8 text-center text-[#545b64]">
                                        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                                        Loading logs...
                                    </td>
                                </tr>
                            ) : filteredLogs.length === 0 ? (
                                <tr>
                                    <td colSpan={8} className="p-8 text-center text-[#545b64]">
                                        <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                        No maintenance logs found
                                        <div className="mt-2">
                                            <button
                                                onClick={() => setShowAddModal(true)}
                                                className="text-[#0073bb] hover:underline"
                                            >
                                                Add your first log
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                filteredLogs.map((log) => (
                                    <tr key={log.id} className="border-b border-[#eaeded] hover:bg-[#fafafa]">
                                        <td className="p-4 font-mono text-sm">{log.id}</td>
                                        <td className="p-4">
                                            <span className="font-medium">{log.machine_id}</span>
                                        </td>
                                        <td className="p-4">
                                            <div className="font-medium">{log.action}</div>
                                            {log.notes && (
                                                <div className="text-xs text-[#545b64] mt-1">{log.notes}</div>
                                            )}
                                        </td>
                                        <td className="p-4">
                                            <div className="flex items-center gap-2">
                                                <User className="w-4 h-4 text-[#545b64]" />
                                                {log.performed_by}
                                            </div>
                                        </td>
                                        <td className="p-4 text-sm">{formatDate(log.timestamp)}</td>
                                        <td className="p-4">{log.duration_hours ? `${log.duration_hours}h` : '-'}</td>
                                        <td className="p-4">{getStatusBadge(log.status)}</td>
                                        <td className="p-4">
                                            {deleteConfirm === log.id ? (
                                                <div className="flex items-center gap-2">
                                                    <button
                                                        onClick={() => handleDeleteLog(log.id)}
                                                        className="text-red-600 text-sm font-medium hover:underline"
                                                    >
                                                        Confirm
                                                    </button>
                                                    <button
                                                        onClick={() => setDeleteConfirm(null)}
                                                        className="text-[#545b64] text-sm hover:underline"
                                                    >
                                                        Cancel
                                                    </button>
                                                </div>
                                            ) : (
                                                <button
                                                    onClick={() => setDeleteConfirm(log.id)}
                                                    className="p-1.5 text-[#545b64] hover:text-red-600 hover:bg-red-50 rounded transition"
                                                    title="Delete log"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Add Log Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
                        <div className="flex items-center justify-between p-4 border-b border-[#eaeded]">
                            <h2 className="text-lg font-semibold">Add Maintenance Log</h2>
                            <button
                                onClick={() => setShowAddModal(false)}
                                className="p-1 hover:bg-[#f2f3f3] rounded"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="p-4 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-[#16191f] mb-1">
                                    Machine *
                                </label>
                                <select
                                    value={formData.machine_id}
                                    onChange={(e) => setFormData({ ...formData, machine_id: e.target.value })}
                                    className="w-full px-3 py-2 border border-[#d5dbdb] rounded-lg focus:outline-none focus:border-[#0073bb]"
                                >
                                    {machines.map(m => (
                                        <option key={m.id} value={m.id}>{m.id} - {m.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-[#16191f] mb-1">
                                    Action/Description *
                                </label>
                                <input
                                    type="text"
                                    value={formData.action}
                                    onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                                    placeholder="e.g., Bearing Replacement"
                                    className="w-full px-3 py-2 border border-[#d5dbdb] rounded-lg focus:outline-none focus:border-[#0073bb]"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-[#16191f] mb-1">
                                    Performed By *
                                </label>
                                <input
                                    type="text"
                                    value={formData.performed_by}
                                    onChange={(e) => setFormData({ ...formData, performed_by: e.target.value })}
                                    placeholder="e.g., John Smith"
                                    className="w-full px-3 py-2 border border-[#d5dbdb] rounded-lg focus:outline-none focus:border-[#0073bb]"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-[#16191f] mb-1">
                                        Duration (hours)
                                    </label>
                                    <input
                                        type="number"
                                        min="0.5"
                                        step="0.5"
                                        value={formData.duration_hours}
                                        onChange={(e) => setFormData({ ...formData, duration_hours: parseFloat(e.target.value) || 1 })}
                                        className="w-full px-3 py-2 border border-[#d5dbdb] rounded-lg focus:outline-none focus:border-[#0073bb]"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-[#16191f] mb-1">
                                        Status
                                    </label>
                                    <select
                                        value={formData.status}
                                        onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                                        className="w-full px-3 py-2 border border-[#d5dbdb] rounded-lg focus:outline-none focus:border-[#0073bb]"
                                    >
                                        <option value="completed">Completed</option>
                                        <option value="in_progress">In Progress</option>
                                        <option value="scheduled">Scheduled</option>
                                    </select>
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-[#16191f] mb-1">
                                    Notes
                                </label>
                                <textarea
                                    value={formData.notes}
                                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                                    placeholder="Additional notes..."
                                    rows={3}
                                    className="w-full px-3 py-2 border border-[#d5dbdb] rounded-lg focus:outline-none focus:border-[#0073bb] resize-none"
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-2 p-4 border-t border-[#eaeded]">
                            <button
                                onClick={() => setShowAddModal(false)}
                                className="aws-btn aws-btn-secondary"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleAddLog}
                                className="aws-btn aws-btn-primary"
                            >
                                Add Log
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

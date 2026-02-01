import { useNavigate } from 'react-router-dom';
import { useRealData } from '@/app/hooks/useRealData';
import {
  Factory,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  ChevronRight,
  Search,
  Gauge,
  Activity
} from 'lucide-react';
import { useState } from 'react';

export function ComponentsPage() {
  const navigate = useNavigate();
  const { plants, components, alerts, loading } = useRealData();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'healthy' | 'warning' | 'critical'>('all');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-[#ec7211]" />
      </div>
    );
  }

  // Filter machines based on search and status
  const filteredMachines = components.filter(machine => {
    const matchesSearch = machine.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      machine.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || machine.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'healthy': return 'healthy';
      case 'warning': return 'warning';
      case 'critical': return 'critical';
      default: return '';
    }
  };

  const getAlertCount = (machineId: string) => {
    return alerts.filter(a => a.componentId === machineId && a.status !== 'completed').length;
  };

  return (
    <div>
      {/* Page Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-[#16191f]">Machine Fleet</h1>
          <p className="text-sm text-[#545b64] mt-1">
            {components.length} machines monitored across {plants.length} plants
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <div className="flex-1 max-w-md relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#545b64]" />
          <input
            type="text"
            placeholder="Search machines..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-[#d5dbdb] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#ec7211] focus:border-transparent"
          />
        </div>
        <div className="flex gap-2">
          <button
            className={`aws-btn ${statusFilter === 'all' ? 'aws-btn-primary' : 'aws-btn-secondary'}`}
            onClick={() => setStatusFilter('all')}
          >
            All
          </button>
          <button
            className={`aws-btn ${statusFilter === 'healthy' ? 'aws-btn-primary' : 'aws-btn-secondary'}`}
            onClick={() => setStatusFilter('healthy')}
          >
            <CheckCircle2 className="w-4 h-4" />
            Healthy
          </button>
          <button
            className={`aws-btn ${statusFilter === 'warning' ? 'aws-btn-primary' : 'aws-btn-secondary'}`}
            onClick={() => setStatusFilter('warning')}
          >
            <AlertTriangle className="w-4 h-4" />
            Warning
          </button>
          <button
            className={`aws-btn ${statusFilter === 'critical' ? 'aws-btn-primary' : 'aws-btn-secondary'}`}
            onClick={() => setStatusFilter('critical')}
          >
            <XCircle className="w-4 h-4" />
            Critical
          </button>
        </div>
      </div>

      {/* Machine Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredMachines.map((machine) => (
          <div
            key={machine.id}
            className="aws-card cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => navigate(`/component/${machine.id}`)}
          >
            <div className="p-5">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Factory className="w-5 h-5 text-[#545b64]" />
                    <span className="font-mono text-sm text-[#545b64]">{machine.id}</span>
                  </div>
                  <h3 className="font-semibold text-[#16191f]">{machine.name}</h3>
                </div>
                <span className={`aws-badge aws-badge-${getStatusClass(machine.status)}`}>
                  {machine.status === 'healthy' && <CheckCircle2 className="w-3 h-3" />}
                  {machine.status === 'warning' && <AlertTriangle className="w-3 h-3" />}
                  {machine.status === 'critical' && <XCircle className="w-3 h-3" />}
                  {machine.status.charAt(0).toUpperCase() + machine.status.slice(1)}
                </span>
              </div>

              {/* Health Score */}
              <div className="mb-4">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-[#545b64]">Health Score</span>
                  <span className={`font-semibold ${machine.healthScore >= 70 ? 'text-[#1e8900]' :
                    machine.healthScore >= 40 ? 'text-[#ff9900]' : 'text-[#d13212]'
                    }`}>
                    {machine.healthScore}%
                  </span>
                </div>
                <div className="aws-progress">
                  <div
                    className={`aws-progress-bar ${getStatusClass(machine.status)}`}
                    style={{ width: `${machine.healthScore}%` }}
                  />
                </div>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2 text-[#545b64]">
                  <Clock className="w-4 h-4" />
                  <span>RUL: {machine.predictedFailureTime || 'N/A'}</span>
                </div>
                <div className="flex items-center gap-2 text-[#545b64]">
                  <AlertTriangle className="w-4 h-4" />
                  <span>{getAlertCount(machine.id)} alerts</span>
                </div>
                <div className="flex items-center gap-2 text-[#545b64]">
                  <Activity className="w-4 h-4" />
                  <span>Plant {machine.plantId || '1'}</span>
                </div>
                <div className="flex items-center gap-2 text-[#545b64]">
                  <Gauge className="w-4 h-4" />
                  <span>{machine.lastMaintenance}</span>
                </div>
              </div>

              {/* Action */}
              <div className="mt-4 pt-4 border-t border-[#eaeded] flex items-center justify-between">
                <span className="text-sm text-[#0073bb]">View Details</span>
                <ChevronRight className="w-4 h-4 text-[#0073bb]" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredMachines.length === 0 && (
        <div className="aws-card">
          <div className="text-center py-12 text-[#545b64]">
            <Search className="w-12 h-12 mx-auto mb-3 text-[#d5dbdb]" />
            <p className="text-lg font-medium">No machines found</p>
            <p className="text-sm mt-1">Try adjusting your search or filter criteria</p>
          </div>
        </div>
      )}
    </div>
  );
}

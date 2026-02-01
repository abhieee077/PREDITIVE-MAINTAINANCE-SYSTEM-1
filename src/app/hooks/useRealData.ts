import { useState, useEffect } from 'react';
import { Component, Plant, Alert, Log } from '@/data/mockData';

// Helper to map backend status to UI status
const mapStatus = (healthScore: number): 'healthy' | 'warning' | 'critical' => {
    if (healthScore >= 70) return 'healthy';
    if (healthScore >= 40) return 'warning';
    return 'critical';
};

export function useRealData() {
    const [plants, setPlants] = useState<Plant[]>([]);
    const [components, setComponents] = useState<Component[]>([]);
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [logs, setLogs] = useState<Log[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            // Fetch machines
            const machineRes = await fetch('http://localhost:5000/api/machines');
            const machineData = await machineRes.json();

            // Fetch alerts (active only)
            const alertRes = await fetch('http://localhost:5000/api/alerts');
            const alertData = await alertRes.json();

            // Fetch maintenance logs
            const logRes = await fetch('http://localhost:5000/api/logs?days=30');
            const logData = await logRes.json();

            if (!machineData.machines || !alertData.alerts) {
                console.warn("Invalid data format received");
                return;
            }

            // Map machines to Components
            const mappedComponents: Component[] = machineData.machines.map((m: any) => ({
                id: m.machine_id,
                name: m.machine_name || `Machine ${m.machine_id}`,
                type: m.machine_type || 'Equipment',
                status: mapStatus(m.health_score),
                healthScore: Math.round(m.health_score),
                predictedFailureTime: `${Math.round(m.rul_hours)} hours`,
                lastMaintenance: '2025-01-01', // This should eventually come from backend
                plantId: 'plant-main'
            }));

            // Create a single plant using backend plant name
            const mainPlant: Plant = {
                id: 'plant-main',
                name: machineData.plant_name || 'Main Power Block',
                componentCount: mappedComponents.length,
                alertCount: alertData.alerts.length,
                healthStatus: mappedComponents.every(c => c.status === 'healthy') ? 'healthy' :
                    mappedComponents.some(c => c.status === 'critical') ? 'critical' : 'warning'
            };

            // Map alerts
            const mappedAlerts: Alert[] = alertData.alerts.map((a: any) => ({
                id: a.id,
                componentId: a.machine_id,
                componentName: `Machine ${a.machine_id}`,
                message: a.message,
                severity: a.severity === 'critical' ? 'critical' :
                    a.severity === 'warning' ? 'medium' : 'low',
                status: a.state === 'ACTIVE' ? 'not-completed' :
                    a.state === 'ACKNOWLEDGED' ? 'in-progress' : 'completed',
                timestamp: a.created_at
            }));

            // Map logs
            const mappedLogs: Log[] = (logData.logs || []).map((l: any) => ({
                id: l.id,
                componentId: l.machine_id,
                componentName: `Machine ${l.machine_id}`,
                message: `[RESOLVED] ${l.alert_type}: ${l.resolution_notes}`,
                timestamp: l.resolved_at,
                type: l.severity === 'critical' ? 'error' :
                    l.severity === 'warning' ? 'warning' : 'info'
            }));

            setPlants([mainPlant]);
            setComponents(mappedComponents);
            setAlerts(mappedAlerts);
            setLogs(mappedLogs);

        } catch (error) {
            console.error("Failed to fetch backend data:", error);
        } finally {
            setLoading(false);
        }
    };

    // Operator actions
    const acknowledgeAlert = async (alertId: string, operatorId: string) => {
        try {
            const res = await fetch(`http://localhost:5000/api/alerts/${alertId}/acknowledge`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ operator_id: operatorId })
            });

            if (res.ok) {
                fetchData(); // Refresh data
                return true;
            }
            return false;
        } catch (e) {
            console.error("Error acknowledging alert:", e);
            return false;
        }
    };

    const resolveAlert = async (alertId: string, operatorId: string, notes: string, rootCause: string) => {
        try {
            const res = await fetch(`http://localhost:5000/api/alerts/${alertId}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    operator_id: operatorId,
                    resolution_notes: notes,
                    root_cause: rootCause,
                    downtime_minutes: 0 // Default for now
                })
            });

            if (res.ok) {
                fetchData(); // Refresh data
                return true;
            }
            return false;
        } catch (e) {
            console.error("Error resolving alert:", e);
            return false;
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 2000); // Poll every 2s
        return () => clearInterval(interval);
    }, []);

    return {
        plants,
        components,
        alerts,
        logs,
        loading,
        actions: {
            acknowledgeAlert,
            resolveAlert
        }
    };
}

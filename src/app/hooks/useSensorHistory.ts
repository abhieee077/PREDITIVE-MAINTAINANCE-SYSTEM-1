import { useState, useEffect, useRef } from 'react';

export interface SensorReading {
    timestamp: string;
    temperature: number | null;
    vibration: number | null;
    pressure: number | null;
    rpm: number | null;
    health_score: number | null;
    rul_hours: number | null;
}

export interface LiveSensorData {
    current: SensorReading | null;
    history: SensorReading[];
    delta: {
        temperature: number;
        vibration: number;
        pressure: number;
        health_score: number;
    };
    loading: boolean;
}

export function useSensorHistory(machineId: string | undefined, pollInterval: number = 1000) {
    const [data, setData] = useState<LiveSensorData>({
        current: null,
        history: [],
        delta: { temperature: 0, vibration: 0, pressure: 0, health_score: 0 },
        loading: true
    });

    const prevValues = useRef<SensorReading | null>(null);

    const fetchSensorData = async () => {
        if (!machineId) return;

        try {
            // Fetch current sensor data
            const currentRes = await fetch(`http://localhost:5000/api/sensor-data?machine_id=${machineId}`);
            const currentData = await currentRes.json();

            // Fetch history for charts
            const historyRes = await fetch(`http://localhost:5000/api/sensor-history/${machineId}?hours=1&limit=60`);
            const historyData = await historyRes.json();

            const current: SensorReading = {
                timestamp: currentData.timestamp,
                temperature: currentData.sensors?.temperature || 0,
                vibration: ((currentData.sensors?.vibration_x || 0) + (currentData.sensors?.vibration_y || 0)) / 2,
                pressure: currentData.sensors?.pressure || 0,
                rpm: currentData.sensors?.rpm || 0,
                health_score: currentData.predictions?.health_score || 0,
                rul_hours: currentData.predictions?.rul_hours || 0
            };

            // Calculate delta (change from previous reading)
            const delta = {
                temperature: prevValues.current ?
                    (current.temperature || 0) - (prevValues.current.temperature || 0) : 0,
                vibration: prevValues.current ?
                    (current.vibration || 0) - (prevValues.current.vibration || 0) : 0,
                pressure: prevValues.current ?
                    (current.pressure || 0) - (prevValues.current.pressure || 0) : 0,
                health_score: prevValues.current ?
                    (current.health_score || 0) - (prevValues.current.health_score || 0) : 0
            };

            prevValues.current = current;

            setData({
                current,
                history: historyData.history || [],
                delta,
                loading: false
            });

        } catch (error) {
            console.error('Error fetching sensor data:', error);
            setData(prev => ({ ...prev, loading: false }));
        }
    };

    useEffect(() => {
        if (!machineId) return;

        fetchSensorData();
        const interval = setInterval(fetchSensorData, pollInterval);
        return () => clearInterval(interval);
    }, [machineId, pollInterval]);

    return data;
}

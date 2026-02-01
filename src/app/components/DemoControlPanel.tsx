import { useState, useEffect } from 'react';
import {
    Thermometer,
    Gauge,
    Activity,
    RotateCcw,
    Send,
    RefreshCw,
    AlertTriangle
} from 'lucide-react';

export function DemoControlPanel() {
    // Sensor values - sliders
    const [temperature, setTemperature] = useState(70);
    const [vibrationX, setVibrationX] = useState(0.5);
    const [vibrationY, setVibrationY] = useState(0.5);
    const [pressure, setPressure] = useState(100);
    const [rpm, setRpm] = useState(1500);

    // Status
    const [status, setStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');
    const [currentOverride, setCurrentOverride] = useState<any>(null);

    // Fetch current override status
    const fetchStatus = async () => {
        try {
            const res = await fetch('http://localhost:5000/api/demo/status');
            const data = await res.json();
            setCurrentOverride(data.overrides?.['M-001'] || null);
        } catch (e) {
            console.error('Error fetching status:', e);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 2000);
        return () => clearInterval(interval);
    }, []);

    // Apply override
    const applyOverride = async () => {
        setStatus('sending');
        try {
            const res = await fetch('http://localhost:5000/api/demo/override', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    machine_id: 'M-001',
                    temperature,
                    vibration_x: vibrationX,
                    vibration_y: vibrationY,
                    pressure,
                    rpm
                })
            });
            await res.json();
            setStatus('success');
            fetchStatus();
        } catch (e) {
            setStatus('error');
        }
    };

    // Clear override
    const clearOverride = async () => {
        try {
            await fetch('http://localhost:5000/api/demo/override/M-001', { method: 'DELETE' });
            setCurrentOverride(null);
            // Reset to healthy values
            setTemperature(70);
            setVibrationX(0.5);
            setVibrationY(0.5);
            setPressure(100);
            setRpm(1500);
            fetchStatus();
        } catch (e) {
            console.error('Error clearing:', e);
        }
    };

    // Preset buttons for quick scenarios
    const applyPreset = (preset: 'healthy' | 'degrading' | 'critical' | 'failure') => {
        switch (preset) {
            case 'healthy':
                setTemperature(70);
                setVibrationX(0.5);
                setVibrationY(0.5);
                setPressure(100);
                setRpm(1500);
                break;
            case 'degrading':
                setTemperature(82);
                setVibrationX(1.0);
                setVibrationY(0.9);
                setPressure(95);
                setRpm(1450);
                break;
            case 'critical':
                setTemperature(92);
                setVibrationX(1.5);
                setVibrationY(1.4);
                setPressure(88);
                setRpm(1350);
                break;
            case 'failure':
                setTemperature(105);
                setVibrationX(2.2);
                setVibrationY(2.0);
                setPressure(75);
                setRpm(1100);
                break;
        }
    };

    return (
        <div className="min-h-screen bg-[#16191f] text-white p-6">
            <div className="max-w-2xl mx-auto">
                {/* Header */}
                <div className="mb-8 text-center">
                    <h1 className="text-2xl font-bold text-[#ec7211] mb-2">
                        🎮 DEMO CONTROL PANEL
                    </h1>
                    <p className="text-[#879596] text-sm">
                        Control panel for M-001: Feedwater Pump (Main Power Block)
                    </p>
                    <div className="mt-3 inline-flex items-center gap-2 px-3 py-1 bg-[#232f3e] rounded-full">
                        <span className={`w-2 h-2 rounded-full ${currentOverride ? 'bg-[#ec7211] animate-pulse' : 'bg-[#1e8900]'}`}></span>
                        <span className="text-sm">
                            {currentOverride ? 'Override Active' : 'Auto Mode'}
                        </span>
                    </div>
                </div>

                {/* Quick Presets */}
                <div className="mb-6">
                    <h3 className="text-sm font-medium text-[#879596] mb-3">Quick Presets</h3>
                    <div className="grid grid-cols-4 gap-2">
                        <button
                            onClick={() => applyPreset('healthy')}
                            className="px-3 py-2 bg-[#1e8900] text-white rounded font-medium hover:bg-[#166d00] transition"
                        >
                            🟢 Healthy
                        </button>
                        <button
                            onClick={() => applyPreset('degrading')}
                            className="px-3 py-2 bg-[#ff9900] text-black rounded font-medium hover:bg-[#e88a00] transition"
                        >
                            🟡 Degrading
                        </button>
                        <button
                            onClick={() => applyPreset('critical')}
                            className="px-3 py-2 bg-[#d13212] text-white rounded font-medium hover:bg-[#b12a0f] transition"
                        >
                            🔴 Critical
                        </button>
                        <button
                            onClick={() => applyPreset('failure')}
                            className="px-3 py-2 bg-[#870000] text-white rounded font-medium hover:bg-[#6b0000] transition"
                        >
                            💀 Failure
                        </button>
                    </div>
                </div>

                {/* Sliders */}
                <div className="bg-[#232f3e] rounded-lg p-6 space-y-6">
                    {/* Temperature */}
                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="flex items-center gap-2 text-sm">
                                <Thermometer className="w-4 h-4 text-[#d13212]" />
                                Temperature
                            </label>
                            <span className="text-lg font-mono text-[#ec7211]">{temperature}°C</span>
                        </div>
                        <input
                            type="range"
                            min="50"
                            max="120"
                            value={temperature}
                            onChange={(e) => setTemperature(Number(e.target.value))}
                            className="w-full h-2 bg-[#37475a] rounded-lg appearance-none cursor-pointer accent-[#ec7211]"
                        />
                        <div className="flex justify-between text-xs text-[#879596] mt-1">
                            <span>50°C (Cool)</span>
                            <span>120°C (Hot)</span>
                        </div>
                    </div>

                    {/* Vibration X */}
                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="flex items-center gap-2 text-sm">
                                <Activity className="w-4 h-4 text-[#0073bb]" />
                                Vibration X
                            </label>
                            <span className="text-lg font-mono text-[#ec7211]">{vibrationX.toFixed(2)} mm/s</span>
                        </div>
                        <input
                            type="range"
                            min="0"
                            max="3"
                            step="0.05"
                            value={vibrationX}
                            onChange={(e) => setVibrationX(Number(e.target.value))}
                            className="w-full h-2 bg-[#37475a] rounded-lg appearance-none cursor-pointer accent-[#ec7211]"
                        />
                    </div>

                    {/* Vibration Y */}
                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="flex items-center gap-2 text-sm">
                                <Activity className="w-4 h-4 text-[#0073bb]" />
                                Vibration Y
                            </label>
                            <span className="text-lg font-mono text-[#ec7211]">{vibrationY.toFixed(2)} mm/s</span>
                        </div>
                        <input
                            type="range"
                            min="0"
                            max="3"
                            step="0.05"
                            value={vibrationY}
                            onChange={(e) => setVibrationY(Number(e.target.value))}
                            className="w-full h-2 bg-[#37475a] rounded-lg appearance-none cursor-pointer accent-[#ec7211]"
                        />
                    </div>

                    {/* Pressure */}
                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="flex items-center gap-2 text-sm">
                                <Gauge className="w-4 h-4 text-[#1e8900]" />
                                Pressure
                            </label>
                            <span className="text-lg font-mono text-[#ec7211]">{pressure} psi</span>
                        </div>
                        <input
                            type="range"
                            min="60"
                            max="120"
                            value={pressure}
                            onChange={(e) => setPressure(Number(e.target.value))}
                            className="w-full h-2 bg-[#37475a] rounded-lg appearance-none cursor-pointer accent-[#ec7211]"
                        />
                    </div>

                    {/* RPM */}
                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="flex items-center gap-2 text-sm">
                                <RefreshCw className="w-4 h-4 text-[#ff9900]" />
                                RPM
                            </label>
                            <span className="text-lg font-mono text-[#ec7211]">{rpm}</span>
                        </div>
                        <input
                            type="range"
                            min="800"
                            max="2000"
                            step="10"
                            value={rpm}
                            onChange={(e) => setRpm(Number(e.target.value))}
                            className="w-full h-2 bg-[#37475a] rounded-lg appearance-none cursor-pointer accent-[#ec7211]"
                        />
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="mt-6 flex gap-4">
                    <button
                        onClick={applyOverride}
                        disabled={status === 'sending'}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-[#ec7211] text-white rounded-lg font-medium hover:bg-[#eb5f07] transition disabled:opacity-50"
                    >
                        <Send className="w-4 h-4" />
                        {status === 'sending' ? 'Sending...' : 'Apply to Feedwater Pump'}
                    </button>
                    <button
                        onClick={clearOverride}
                        className="px-4 py-3 bg-[#37475a] text-white rounded-lg font-medium hover:bg-[#4a5b6e] transition"
                    >
                        <RotateCcw className="w-4 h-4" />
                    </button>
                </div>

                {/* Current Override Status */}
                {currentOverride && (
                    <div className="mt-6 p-4 bg-[#232f3e] rounded-lg border border-[#ec7211]">
                        <div className="flex items-center gap-2 text-[#ec7211] mb-2">
                            <AlertTriangle className="w-4 h-4" />
                            <span className="font-medium">Active Override</span>
                        </div>
                        <pre className="text-xs text-[#879596] overflow-auto">
                            {JSON.stringify(currentOverride, null, 2)}
                        </pre>
                    </div>
                )}

                {/* Instructions */}
                <div className="mt-8 p-4 bg-[#232f3e] rounded-lg text-sm text-[#879596]">
                    <h4 className="font-medium text-white mb-2">📋 Demo Instructions</h4>
                    <ol className="list-decimal list-inside space-y-1">
                        <li>Open main dashboard in another browser window</li>
                        <li>Use quick presets or sliders to change M-001 values</li>
                        <li>Click "Apply to M-001" to send changes</li>
                        <li>Watch health score and alerts update in real-time</li>
                        <li>Click reset (↺) to return to automatic mode</li>
                    </ol>
                </div>
            </div>
        </div>
    );
}

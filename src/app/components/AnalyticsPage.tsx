import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, TrendingDown, Activity, AlertTriangle, CheckCircle2, Clock, Target } from 'lucide-react';
import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    AreaChart,
    Area,
    PieChart,
    Pie,
    Cell
} from 'recharts';

interface MetricsData {
    prediction_accuracy: number;
    lead_time_hours: number;
    false_alarm_rate: number;
    true_positive_rate: number;
    machines_monitored: number;
    alerts_generated: number;
}

export function AnalyticsPage() {
    const [metrics, setMetrics] = useState<MetricsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [healthTrend, setHealthTrend] = useState<any[]>([]);

    useEffect(() => {
        // Simulate fetching metrics - these would come from the ML model evaluation
        const fetchMetrics = async () => {
            try {
                // Get real alert statistics
                const alertsRes = await fetch('http://localhost:5000/api/alerts/statistics');
                const alertStats = await alertsRes.json();

                // Calculate demo metrics (in production, these would come from model evaluation)
                setMetrics({
                    prediction_accuracy: 94.2,
                    lead_time_hours: 48.5,
                    false_alarm_rate: 5.8,
                    true_positive_rate: 92.3,
                    machines_monitored: 4,
                    alerts_generated: alertStats.total || 12
                });

                // Generate trend data
                const trend = [];
                for (let i = 30; i >= 0; i--) {
                    const date = new Date();
                    date.setDate(date.getDate() - i);
                    trend.push({
                        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                        health: Math.max(0, Math.min(100, 85 + Math.random() * 15 - i * 0.3)),
                        predictions: Math.floor(Math.random() * 5)
                    });
                }
                setHealthTrend(trend);

            } catch (error) {
                console.error('Error fetching metrics:', error);
                // Use fallback demo data
                setMetrics({
                    prediction_accuracy: 94.2,
                    lead_time_hours: 48.5,
                    false_alarm_rate: 5.8,
                    true_positive_rate: 92.3,
                    machines_monitored: 4,
                    alerts_generated: 12
                });
            }
            setLoading(false);
        };

        fetchMetrics();
    }, []);

    // Pie chart data for prediction outcomes
    const predictionOutcomes = [
        { name: 'True Positive', value: 45, color: '#1e8900' },
        { name: 'True Negative', value: 42, color: '#0073bb' },
        { name: 'False Positive', value: 8, color: '#ff9900' },
        { name: 'False Negative', value: 5, color: '#d13212' }
    ];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Activity className="w-8 h-8 animate-spin text-[#ec7211]" />
            </div>
        );
    }

    return (
        <div>
            {/* Page Header */}
            <div className="mb-6">
                <h1 className="text-2xl font-semibold text-[#16191f]">Analytics & Model Performance</h1>
                <p className="text-sm text-[#545b64] mt-1">
                    Predictive maintenance model metrics and performance tracking
                </p>
            </div>

            {/* Key Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                {/* Prediction Accuracy */}
                <div className="aws-card">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-[#545b64]">Prediction Accuracy</span>
                        <Target className="w-5 h-5 text-[#1e8900]" />
                    </div>
                    <div className="text-3xl font-bold text-[#1e8900]">
                        {metrics?.prediction_accuracy}%
                    </div>
                    <div className="flex items-center gap-1 text-sm text-[#1e8900] mt-1">
                        <TrendingUp className="w-4 h-4" />
                        <span>+2.3% from last week</span>
                    </div>
                </div>

                {/* Lead Time */}
                <div className="aws-card">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-[#545b64]">Avg Lead Time</span>
                        <Clock className="w-5 h-5 text-[#0073bb]" />
                    </div>
                    <div className="text-3xl font-bold text-[#0073bb]">
                        {metrics?.lead_time_hours}h
                    </div>
                    <div className="text-sm text-[#545b64] mt-1">
                        Before predicted failure
                    </div>
                </div>

                {/* False Alarm Rate */}
                <div className="aws-card">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-[#545b64]">False Alarm Rate</span>
                        <AlertTriangle className="w-5 h-5 text-[#ff9900]" />
                    </div>
                    <div className="text-3xl font-bold text-[#ff9900]">
                        {metrics?.false_alarm_rate}%
                    </div>
                    <div className="flex items-center gap-1 text-sm text-[#1e8900] mt-1">
                        <TrendingDown className="w-4 h-4" />
                        <span>-1.2% from last week</span>
                    </div>
                </div>

                {/* True Positive Rate */}
                <div className="aws-card">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-[#545b64]">True Positive Rate</span>
                        <CheckCircle2 className="w-5 h-5 text-[#1e8900]" />
                    </div>
                    <div className="text-3xl font-bold text-[#1e8900]">
                        {metrics?.true_positive_rate}%
                    </div>
                    <div className="text-sm text-[#545b64] mt-1">
                        Correctly predicted failures
                    </div>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
                {/* Health Trend Chart */}
                <div className="aws-card lg:col-span-2">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-medium text-[#16191f]">Fleet Health Trend (30 Days)</h3>
                        <BarChart3 className="w-5 h-5 text-[#545b64]" />
                    </div>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={healthTrend}>
                                <defs>
                                    <linearGradient id="healthGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#1e8900" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#1e8900" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#d5dbdb" />
                                <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#545b64" />
                                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} stroke="#545b64" />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#232f3e',
                                        border: 'none',
                                        borderRadius: '4px',
                                        color: '#fff'
                                    }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="health"
                                    stroke="#1e8900"
                                    fill="url(#healthGradient)"
                                    strokeWidth={2}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Prediction Outcomes Pie Chart */}
                <div className="aws-card">
                    <h3 className="font-medium text-[#16191f] mb-4">Prediction Outcomes</h3>
                    <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={predictionOutcomes}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={40}
                                    outerRadius={70}
                                    paddingAngle={2}
                                    dataKey="value"
                                >
                                    {predictionOutcomes.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#232f3e',
                                        border: 'none',
                                        borderRadius: '4px',
                                        color: '#fff'
                                    }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="grid grid-cols-2 gap-2 mt-2">
                        {predictionOutcomes.map((item) => (
                            <div key={item.name} className="flex items-center gap-2 text-xs">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                                <span className="text-[#545b64]">{item.name}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Model Info */}
            <div className="aws-card">
                <h3 className="font-medium text-[#16191f] mb-4">Model Information</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                        <div className="text-sm text-[#545b64]">Model Type</div>
                        <div className="font-medium">XGBoost Regressor</div>
                    </div>
                    <div>
                        <div className="text-sm text-[#545b64]">Training Data</div>
                        <div className="font-medium">NASA C-MAPSS</div>
                    </div>
                    <div>
                        <div className="text-sm text-[#545b64]">Last Updated</div>
                        <div className="font-medium">Jan 31, 2026</div>
                    </div>
                    <div>
                        <div className="text-sm text-[#545b64]">Machines Monitored</div>
                        <div className="font-medium">{metrics?.machines_monitored}</div>
                    </div>
                </div>
            </div>
        </div>
    );
}

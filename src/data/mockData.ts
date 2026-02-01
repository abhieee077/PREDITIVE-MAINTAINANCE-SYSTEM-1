export interface Component {
  id: string;
  name: string;
  type: 'Pump' | 'Motor' | 'HVAC';
  status: 'healthy' | 'warning' | 'critical';
  healthScore: number;
  predictedFailureTime?: string;
  lastMaintenance: string;
  plantId: string;
}

export interface Alert {
  id: string;
  componentId: string;
  componentName: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'not-completed' | 'in-progress' | 'completed';
  timestamp: string;
}

export interface Log {
  id: string;
  componentId: string;
  componentName: string;
  message: string;
  timestamp: string;
  type: 'info' | 'warning' | 'error';
}

export interface Plant {
  id: string;
  name: string;
  componentCount: number;
  alertCount: number;
  healthStatus: 'healthy' | 'warning' | 'critical';
}

export const plants: Plant[] = [
  {
    id: 'plant-a',
    name: 'Riverview Thermal Power Plant – Unit A',
    componentCount: 6,
    alertCount: 3,
    healthStatus: 'warning',
  },
  {
    id: 'plant-b',
    name: 'Riverview Thermal Power Plant – Unit B',
    componentCount: 6,
    alertCount: 1,
    healthStatus: 'healthy',
  },
];

export const components: Component[] = [
  // Plant A Components
  {
    id: 'comp-a1',
    name: 'Boiler Feed Water Pump – BFP-A1',
    type: 'Pump',
    status: 'critical',
    healthScore: 42,
    predictedFailureTime: '2-6 hours',
    lastMaintenance: '2025-12-15',
    plantId: 'plant-a',
  },
  {
    id: 'comp-a2',
    name: 'Primary Circulation Motor – PCM-A2',
    type: 'Motor',
    status: 'warning',
    healthScore: 68,
    predictedFailureTime: '24-48 hours',
    lastMaintenance: '2025-11-20',
    plantId: 'plant-a',
  },
  {
    id: 'comp-a3',
    name: 'Cooling Tower Fan – CTF-A3',
    type: 'HVAC',
    status: 'healthy',
    healthScore: 89,
    lastMaintenance: '2026-01-10',
    plantId: 'plant-a',
  },
  {
    id: 'comp-a4',
    name: 'Condensate Extraction Pump – CEP-A4',
    type: 'Pump',
    status: 'warning',
    healthScore: 72,
    predictedFailureTime: '36-48 hours',
    lastMaintenance: '2025-12-01',
    plantId: 'plant-a',
  },
  {
    id: 'comp-a5',
    name: 'Air Compressor Motor – ACM-A5',
    type: 'Motor',
    status: 'healthy',
    healthScore: 91,
    lastMaintenance: '2026-01-15',
    plantId: 'plant-a',
  },
  {
    id: 'comp-a6',
    name: 'HVAC Air Handler – AAH-A6',
    type: 'HVAC',
    status: 'healthy',
    healthScore: 85,
    lastMaintenance: '2026-01-05',
    plantId: 'plant-a',
  },
  // Plant B Components
  {
    id: 'comp-b1',
    name: 'Boiler Feed Water Pump – BFP-B1',
    type: 'Pump',
    status: 'healthy',
    healthScore: 88,
    lastMaintenance: '2026-01-12',
    plantId: 'plant-b',
  },
  {
    id: 'comp-b2',
    name: 'Primary Circulation Motor – PCM-B2',
    type: 'Motor',
    status: 'healthy',
    healthScore: 92,
    lastMaintenance: '2026-01-18',
    plantId: 'plant-b',
  },
  {
    id: 'comp-b3',
    name: 'Cooling Tower Fan – CTF-B3',
    type: 'HVAC',
    status: 'healthy',
    healthScore: 87,
    lastMaintenance: '2026-01-14',
    plantId: 'plant-b',
  },
  {
    id: 'comp-b4',
    name: 'Condensate Extraction Pump – CEP-B4',
    type: 'Pump',
    status: 'healthy',
    healthScore: 90,
    lastMaintenance: '2026-01-20',
    plantId: 'plant-b',
  },
  {
    id: 'comp-b5',
    name: 'Air Compressor Motor – ACM-B5',
    type: 'Motor',
    status: 'warning',
    healthScore: 75,
    predictedFailureTime: '48+ hours',
    lastMaintenance: '2025-11-30',
    plantId: 'plant-b',
  },
  {
    id: 'comp-b6',
    name: 'HVAC Air Handler – AAH-B6',
    type: 'HVAC',
    status: 'healthy',
    healthScore: 93,
    lastMaintenance: '2026-01-22',
    plantId: 'plant-b',
  },
];

export const alerts: Alert[] = [
  {
    id: 'alert-1',
    componentId: 'comp-a1',
    componentName: 'Boiler Feed Water Pump – BFP-A1',
    message: 'Critical vibration levels detected - Immediate maintenance required',
    severity: 'critical',
    status: 'not-completed',
    timestamp: '2026-01-31T08:45:00',
  },
  {
    id: 'alert-2',
    componentId: 'comp-a1',
    componentName: 'Boiler Feed Water Pump – BFP-A1',
    message: 'Temperature exceeding normal operating range',
    severity: 'high',
    status: 'in-progress',
    timestamp: '2026-01-31T07:30:00',
  },
  {
    id: 'alert-3',
    componentId: 'comp-a2',
    componentName: 'Primary Circulation Motor – PCM-A2',
    message: 'Anomaly detected in motor performance',
    severity: 'medium',
    status: 'not-completed',
    timestamp: '2026-01-31T06:15:00',
  },
  {
    id: 'alert-4',
    componentId: 'comp-a4',
    componentName: 'Condensate Extraction Pump – CEP-A4',
    message: 'Gradual decline in efficiency observed',
    severity: 'medium',
    status: 'not-completed',
    timestamp: '2026-01-30T14:20:00',
  },
  {
    id: 'alert-5',
    componentId: 'comp-b5',
    componentName: 'Air Compressor Motor – ACM-B5',
    message: 'Scheduled maintenance due within 2 weeks',
    severity: 'low',
    status: 'not-completed',
    timestamp: '2026-01-30T09:00:00',
  },
];

export const logs: Log[] = [
  {
    id: 'log-1',
    componentId: 'comp-a1',
    componentName: 'Boiler Feed Water Pump – BFP-A1',
    message: 'Vibration sensor reading: 8.5mm/s (Critical)',
    timestamp: '2026-01-31T08:45:00',
    type: 'error',
  },
  {
    id: 'log-2',
    componentId: 'comp-a1',
    componentName: 'Boiler Feed Water Pump – BFP-A1',
    message: 'Temperature reading: 85°C (High)',
    timestamp: '2026-01-31T07:30:00',
    type: 'warning',
  },
  {
    id: 'log-3',
    componentId: 'comp-a1',
    componentName: 'Boiler Feed Water Pump – BFP-A1',
    message: 'System diagnostics initiated',
    timestamp: '2026-01-31T07:00:00',
    type: 'info',
  },
  {
    id: 'log-4',
    componentId: 'comp-a2',
    componentName: 'Primary Circulation Motor – PCM-A2',
    message: 'Performance variance detected: -12%',
    timestamp: '2026-01-31T06:15:00',
    type: 'warning',
  },
  {
    id: 'log-5',
    componentId: 'comp-a3',
    componentName: 'Cooling Tower Fan – CTF-A3',
    message: 'Routine health check completed - All systems normal',
    timestamp: '2026-01-31T05:00:00',
    type: 'info',
  },
  {
    id: 'log-6',
    componentId: 'comp-a4',
    componentName: 'Condensate Extraction Pump – CEP-A4',
    message: 'Efficiency at 72% (Below optimal)',
    timestamp: '2026-01-30T14:20:00',
    type: 'warning',
  },
  {
    id: 'log-7',
    componentId: 'comp-b5',
    componentName: 'Air Compressor Motor – ACM-B5',
    message: 'Maintenance reminder: Service due Feb 14, 2026',
    timestamp: '2026-01-30T09:00:00',
    type: 'info',
  },
];

// Component detail data for BFP-A1
export const componentDetailData = {
  healthHistory: [
    { date: 'Jan 24', score: 85 },
    { date: 'Jan 25', score: 82 },
    { date: 'Jan 26', score: 78 },
    { date: 'Jan 27', score: 73 },
    { date: 'Jan 28', score: 65 },
    { date: 'Jan 29', score: 58 },
    { date: 'Jan 30', score: 51 },
    { date: 'Jan 31', score: 42 },
  ],
  vibrationData: [
    { time: '00:00', value: 2.1 },
    { time: '04:00', value: 2.3 },
    { time: '08:00', value: 3.5 },
    { time: '12:00', value: 4.8 },
    { time: '16:00', value: 6.2 },
    { time: '20:00', value: 7.5 },
    { time: '24:00', value: 8.5 },
  ],
  temperatureData: [
    { time: '00:00', value: 65 },
    { time: '04:00', value: 67 },
    { time: '08:00', value: 71 },
    { time: '12:00', value: 75 },
    { time: '16:00', value: 78 },
    { time: '20:00', value: 82 },
    { time: '24:00', value: 85 },
  ],
  anomalyData: [
    { time: 'Jan 24', score: 0.1 },
    { time: 'Jan 25', score: 0.15 },
    { time: 'Jan 26', score: 0.25 },
    { time: 'Jan 27', score: 0.4 },
    { time: 'Jan 28', score: 0.58 },
    { time: 'Jan 29', score: 0.72 },
    { time: 'Jan 30', score: 0.85 },
    { time: 'Jan 31', score: 0.95 },
  ],
  timeline: [
    {
      date: 'Jan 24-27',
      event: 'Normal Operation',
      status: 'healthy',
    },
    {
      date: 'Jan 28',
      event: 'Performance Degradation Detected',
      status: 'warning',
    },
    {
      date: 'Jan 30',
      event: 'High Severity Alert Triggered',
      status: 'critical',
    },
    {
      date: 'Feb 1 (Expected)',
      event: 'Urgent Maintenance Scheduled',
      status: 'action',
    },
  ],
};

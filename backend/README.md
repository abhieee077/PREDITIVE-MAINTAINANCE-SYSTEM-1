# Thermal Power Plant - Backend API

Predictive Maintenance API for **Main Power Block** thermal power plant simulation.

## Quick Start
```bash
cd backend
.\venv\Scripts\activate
python server.py
```
Server runs at `http://localhost:5000`

## Architecture

```
backend/
├── server.py           # Flask API (main entry point)
├── config.py           # Equipment profiles & settings
├── stateful_simulator.py   # Physics-based sensor simulation
├── rul_predictor.py    # RUL prediction (XGBoost + heuristic)
├── anomaly_detector.py # Isolation Forest anomaly detection
├── alert_manager.py    # Alert lifecycle management
├── ml_stabilizer.py    # EMA smoothing for predictions
├── ttf_forecaster.py   # Time-to-failure forecasting
├── database.py         # SQLite operations
├── data/
│   ├── maintenance.db  # Active database
│   └── nasa_ready.csv  # Training dataset
└── models/
    └── xgb.pkl         # Trained XGBoost model
```

## Equipment Simulated

| ID | Equipment | Type | Status |
|----|-----------|------|--------|
| M-001 | Feedwater Pump | FEEDWATER_PUMP | Demo machine |
| M-002 | ID Fan Motor | ID_FAN_MOTOR | Degrading |
| M-003 | HVAC Chiller | HVAC_CHILLER | Pre-failure |
| M-004 | Boiler Feed Motor | BOILER_FEED_MOTOR | Healthy |

## Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/machines` | List all equipment with status |
| GET | `/api/sensor-data?machine_id=M-001` | Get sensor readings |
| GET | `/api/alerts` | Active alerts |
| POST | `/api/demo/override` | Manual sensor control (demo) |

## Data Sources
- **NASA C-MAPSS**: Used to train XGBoost model
- **Simulated Streams**: Real-time physics-based sensor data

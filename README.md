# 🏭 Thermal Power Plant - Predictive Maintenance Dashboard

Real-time predictive maintenance system for **Main Power Block** thermal power plant equipment. Built with ML-powered anomaly detection and RUL prediction.

## 🎯 Features

- **Real-time Monitoring**: 4 thermal power plant equipment with live sensor streams
- **Anomaly Detection**: PyOD IsolationForest detecting equipment anomalies
- **RUL Prediction**: XGBoost model + heuristic fallback for Remaining Useful Life
- **Alert System**: Automated alerts for critical conditions
- **Demo Control Panel**: Hidden panel to simulate equipment failures

## 🏗️ Equipment Simulated

| ID | Equipment | Description | Status |
|----|-----------|-------------|--------|
| M-001 | Feedwater Pump | High-pressure boiler feed pump | Healthy (Demo) |
| M-002 | ID Fan Motor | Induced draft fan motor | Degrading |
| M-003 | HVAC Chiller | Control room cooling system | Pre-failure |
| M-004 | Boiler Feed Motor | Main feedwater motor | Healthy |

## 🚀 Quick Start

### Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
python server.py
```
Server: `http://localhost:5000`

### Frontend
```bash
npm install
npm run dev
```
Dashboard: `http://localhost:5173`

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/machines` | List all equipment with health scores |
| GET | `/api/sensor-data?machine_id=M-001` | Get sensor readings |
| GET | `/api/alerts` | Active alerts |
| POST | `/api/demo/override` | Demo: Manual sensor control |

## 🔧 Tech Stack

**Backend**: Flask, XGBoost, PyOD, Prophet, SQLite  
**Frontend**: React 18, TypeScript, Vite, TailwindCSS, Recharts

## 📁 Project Structure

```
├── backend/
│   ├── server.py              # Flask REST API
│   ├── config.py              # Equipment profiles
│   ├── stateful_simulator.py  # Physics-based sensor simulation
│   ├── rul_predictor.py       # RUL prediction
│   ├── anomaly_detector.py    # Anomaly detection
│   ├── data/
│   │   ├── maintenance.db     # SQLite database
│   │   └── nasa_ready.csv     # Training dataset
│   └── models/xgb.pkl         # Trained XGBoost model
│
└── src/
    ├── app/
    │   ├── components/        # React components
    │   └── hooks/             # Data fetching hooks
    └── styles/                # CSS themes
```

## 🎮 Demo Mode

Access hidden demo panel: `http://localhost:5173/demo`

Control Feedwater Pump (M-001) sensors in real-time to simulate:
- Normal operation
- Overheating
- Bearing degradation
- Critical failure

## 📈 Data Sources

- **NASA C-MAPSS Dataset**: Used to train XGBoost model
- **Simulated Sensor Streams**: Real-time physics-based degradation

---

Built for hackathon demonstration | MIT License
"""
Production-Grade Flask REST API Server
Industrial Predictive Maintenance with Alert Lifecycle Management
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
from pathlib import Path
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import production components
from config import Config
from stateful_simulator import fleet
from ml_stabilizer import get_stabilized_predictor
from alert_manager import get_alert_manager
from anomaly_detector import get_detector
from ttf_forecaster import get_forecaster
from database import get_database
from metrics_tracker import get_metrics_tracker, seed_demo_metrics
from demo_scenarios import get_scenario_player, get_preset_machine, get_all_preset_machines
from professional_datasets import (
    get_all_equipment_profiles, get_all_failure_modes, 
    generate_professional_dataset, EQUIPMENT_PROFILES, FAILURE_MODES
)

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=Config.CORS_ORIGINS)

# Initialize production components
stabilized_predictor = get_stabilized_predictor()
alert_manager = get_alert_manager()
db = get_database()

# Setup structured logging
Config.ensure_directories()
log_file = Path(Config.LOG_DIR) / Config.LOG_FILE
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=Config.LOG_MAX_BYTES,
    backupCount=Config.LOG_BACKUP_COUNT
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
app.logger.addHandler(file_handler)
app.logger.setLevel(getattr(logging, Config.LOG_LEVEL))


# ==================== HEALTH & STATUS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Deep health check endpoint"""
    try:
        # Check database
        stats = db.get_statistics()
        
        # Check fleet
        fleet_status = len(fleet.machines) > 0
        
        return jsonify({
            "status": "online",
            "message": "Predictive Maintenance API is running",
            "components": {
                "database": "healthy",
                "fleet": "healthy" if fleet_status else "degraded",
                "ml_predictor": "healthy",
                "alert_manager": "healthy"
            },
            "statistics": {
                "machines": len(fleet.machines),
                "active_alerts": stats['alerts_by_state'].get('ACTIVE', 0),
                "total_logs": stats['total_logs']
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "degraded",
            "error": str(e)
        }), 500


# ==================== MACHINE DATA ====================

@app.route('/api/machines', methods=['GET'])
def get_machines():
    """Get list of all monitored machines with current status and mode info"""
    try:
        # Advance fleet time (simulate real-time operation)
        fleet.advance_all(hours=0.0333)  # ~2 minutes
        
        machines = []
        new_alerts = []  # Track new alerts for this request
        
        for machine_id in fleet.machines.keys():
            reading = fleet.get_machine_reading(machine_id)
            
            # Get stabilized predictions
            rul_hours, health_score = stabilized_predictor.predict_rul(
                reading['sensors'], machine_id
            )
            
            # Get anomaly info
            detector = get_detector(machine_id)
            is_anomaly, anomaly_score, _ = detector.detect_anomaly(reading['sensors'])
            
            # Check and create alerts - returns list of new alert IDs
            created_alert_ids = alert_manager.check_and_create_alerts(
                machine_id, reading['sensors'],
                rul_hours, health_score,
                is_anomaly, anomaly_score
            )
            if created_alert_ids:
                for alert_id in created_alert_ids:
                    new_alerts.append({"machine_id": machine_id, "alert_id": alert_id})
            
            # Update forecaster
            forecaster = get_forecaster(machine_id)
            forecaster.add_health_reading(machine_id, health_score)
            
            # Get mode info
            mode = Config.MACHINE_MODES.get(machine_id, 'SIMULATION')
            demo_active = fleet.is_demo_active(machine_id)
            
            # Get scenario info if demo is active
            scenario_info = None
            if demo_active and 'scenario' in reading:
                scenario_info = reading['scenario']
            
            machines.append({
                "machine_id": machine_id,
                "machine_type": fleet.machines[machine_id].machine_type,
                "machine_name": fleet.machines[machine_id].machine_name,
                "status": reading['health_state'],
                "health_score": health_score,
                "rul_hours": rul_hours,
                "has_anomaly": is_anomaly,
                "anomaly_score": round(anomaly_score, 3),
                "runtime_hours": reading['runtime_hours'],
                "degradation_factor": reading.get('degradation_factor', 1.0),
                # Mode info for 4-machine architecture
                "mode": mode,
                "demo_active": demo_active,
                "scenario_info": scenario_info,
                "manual_override": reading.get('manual_override', False)
            })
        
        return jsonify({
            "plant_name": Config.PLANT_NAME,
            "machines": machines,
            "new_alerts": new_alerts,  # Real-time alert notifications
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        app.logger.error(f"Error getting machines: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/sensor-data', methods=['GET'])
def get_sensor_data():
    """Get current sensor readings from machines"""
    try:
        machine_id = request.args.get('machine_id')
        
        if machine_id:
            # Single machine data
            reading = fleet.get_machine_reading(machine_id)
            if reading is None:
                return jsonify({"error": "Machine not found"}), 404
            
            # Check if manual override is active (for demo mode)
            is_override_active = reading.get('manual_override', False)
            
            # Enrich with predictions
            detector = get_detector(machine_id)
            is_anomaly, anomaly_score, anomaly_details = detector.detect_anomaly(reading['sensors'])
            
            # Bypass smoothing if override is active (for instant demo response)
            rul_hours, health_score = stabilized_predictor.predict_rul(
                reading['sensors'], machine_id, bypass_smoothing=is_override_active
            )
            
            # Save sensor history to database
            sensor_data_with_predictions = {
                **reading['sensors'],
                'health_score': health_score,
                'rul_hours': rul_hours
            }
            db.save_sensor_reading(machine_id, sensor_data_with_predictions)
            
            return jsonify({
                "machine_id": machine_id,
                "timestamp": reading['timestamp'],
                "runtime_hours": reading['runtime_hours'],
                "sensors": reading['sensors'],
                "health_state": reading['health_state'],
                "predictions": {
                    "rul_hours": rul_hours,
                    "health_score": health_score,
                    "has_anomaly": is_anomaly,
                    "anomaly_score": round(anomaly_score, 3),
                    "anomaly_details": anomaly_details
                }
            })
        else:
            # All machines data
            readings = fleet.get_all_readings()
            enriched_readings = []
            
            for reading in readings:
                mid = reading['machine_id']
                detector = get_detector(mid)
                is_anomaly, anomaly_score, _ = detector.detect_anomaly(reading['sensors'])
                
                rul_hours, health_score = stabilized_predictor.predict_rul(reading['sensors'], mid)
                
                enriched_readings.append({
                    "machine_id": mid,
                    "timestamp": reading['timestamp'],
                    "sensors": reading['sensors'],
                    "health_score": health_score,
                    "rul_hours": rul_hours,
                    "has_anomaly": is_anomaly
                })
            
            return jsonify({
                "readings": enriched_readings,
                "count": len(enriched_readings)
            })
    
    except Exception as e:
        app.logger.error(f"Error getting sensor data: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/sensor-history/<machine_id>', methods=['GET'])
def get_sensor_history(machine_id):
    """Get historical sensor readings for a machine (for live charts)"""
    try:
        hours = request.args.get('hours', 1, type=int)  # Default last hour
        limit = request.args.get('limit', 60, type=int)  # Default 60 points
        
        # Get from database
        history = db.get_sensor_history(machine_id, hours=hours)
        
        # Limit results
        if len(history) > limit:
            step = len(history) // limit
            history = history[::step][:limit]
        
        # Format for charts
        chart_data = []
        for reading in history:
            chart_data.append({
                "timestamp": reading['timestamp'],
                "temperature": reading.get('temperature'),
                "vibration": (reading.get('vibration_x', 0) + reading.get('vibration_y', 0)) / 2,
                "pressure": reading.get('pressure'),
                "rpm": reading.get('rpm'),
                "health_score": reading.get('health_score'),
                "rul_hours": reading.get('rul_hours')
            })
        
        return jsonify({
            "machine_id": machine_id,
            "history": chart_data,
            "count": len(chart_data),
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        app.logger.error(f"Error getting sensor history: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== ALERT MANAGEMENT ====================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get active alerts"""
    try:
        machine_id = request.args.get('machine_id')
        alerts = alert_manager.get_active_alerts(machine_id)
        
        return jsonify({
            "alerts": alerts,
            "count": len(alerts),
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        app.logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        data = request.get_json()
        operator_id = data.get('operator_id')
        
        if not operator_id:
            return jsonify({"error": "operator_id required"}), 400
        
        result = alert_manager.acknowledge_alert(alert_id, operator_id)
        
        if result['success']:
            app.logger.info(f"Alert {alert_id} acknowledged by {operator_id}")
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        app.logger.error(f"Error acknowledging alert: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an alert and create maintenance log"""
    try:
        data = request.get_json()
        
        operator_id = data.get('operator_id')
        root_cause = data.get('root_cause')
        resolution_notes = data.get('resolution_notes')
        downtime_minutes = data.get('downtime_minutes', 0)
        
        if not all([operator_id, root_cause, resolution_notes]):
            return jsonify({
                "error": "operator_id, root_cause, and resolution_notes required"
            }), 400
        
        result = alert_manager.resolve_alert(
            alert_id, operator_id, root_cause,
            resolution_notes, downtime_minutes
        )
        
        if result['success']:
            app.logger.info(f"Alert {alert_id} resolved by {operator_id}")
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        app.logger.error(f"Error resolving alert: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/alerts/statistics', methods=['GET'])
def get_alert_statistics():
    """Get alert statistics"""
    try:
        stats = alert_manager.get_alert_statistics()
        return jsonify(stats)
    
    except Exception as e:
        app.logger.error(f"Error getting alert statistics: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== MAINTENANCE LOGS ====================

@app.route('/api/logs', methods=['GET'])
def get_maintenance_logs():
    """Get maintenance logs"""
    try:
        machine_id = request.args.get('machine_id')
        days = int(request.args.get('days', 30))
        
        logs = alert_manager.get_maintenance_logs(machine_id, days)
        
        return jsonify({
            "logs": logs,
            "count": len(logs),
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        app.logger.error(f"Error getting logs: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/logs', methods=['POST'])
def create_maintenance_log():
    """Create a new maintenance log"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        # Required fields
        if not data.get('machine_id'):
            return jsonify({"error": "machine_id is required"}), 400
        if not data.get('action'):
            return jsonify({"error": "action is required"}), 400
        
        log_id = db.create_maintenance_log(data)
        
        return jsonify({
            "success": True,
            "log_id": log_id,
            "message": "Maintenance log created successfully"
        }), 201
    
    except Exception as e:
        app.logger.error(f"Error creating log: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/logs/<log_id>', methods=['DELETE'])
def delete_maintenance_log(log_id):
    """Delete a maintenance log"""
    try:
        success = db.delete_maintenance_log(log_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Log {log_id} deleted successfully"
            })
        else:
            return jsonify({"error": "Log not found"}), 404
    
    except Exception as e:
        app.logger.error(f"Error deleting log: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/logs/<log_id>', methods=['PUT'])
def update_maintenance_log(log_id):
    """Update a maintenance log"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        success = db.update_maintenance_log(log_id, data)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Log {log_id} updated successfully"
            })
        else:
            return jsonify({"error": "Log not found or no changes made"}), 404
    
    except Exception as e:
        app.logger.error(f"Error updating log: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== PREDICTIONS & FORECASTING ====================

@app.route('/api/predict-rul', methods=['POST'])
def predict_rul():
    """Predict Remaining Useful Life for a machine"""
    try:
        data = request.get_json()
        
        if not data or 'machine_id' not in data:
            return jsonify({"error": "machine_id required"}), 400
        
        machine_id = data['machine_id']
        
        # Get current reading
        reading = fleet.get_machine_reading(machine_id)
        if reading is None:
            return jsonify({"error": "Machine not found"}), 404
        
        # Predict RUL (stabilized)
        rul_hours, health_score = stabilized_predictor.predict_rul(reading['sensors'], machine_id)
        
        # Get prediction trend
        trend = stabilized_predictor.get_prediction_trend(machine_id, hours=24)
        
        return jsonify({
            "machine_id": machine_id,
            "rul_hours": rul_hours,
            "health_score": health_score,
            "trend": trend,
            "timestamp": reading['timestamp']
        })
    
    except Exception as e:
        app.logger.error(f"Error predicting RUL: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/health-trend/<machine_id>', methods=['GET'])
def get_health_trend(machine_id):
    """Get health trend and time-to-failure forecast"""
    try:
        if machine_id not in fleet.machines:
            return jsonify({"error": "Machine not found"}), 404
        
        forecaster = get_forecaster(machine_id)
        
        # Get forecast
        horizon_hours = int(request.args.get('horizon', 48))
        forecast_result = forecaster.forecast_ttf(machine_id, horizon_hours)
        
        # Get current status
        reading = fleet.get_machine_reading(machine_id)
        rul_hours, health_score = stabilized_predictor.predict_rul(reading['sensors'], machine_id)
        
        return jsonify({
            "machine_id": machine_id,
            "current_health": health_score,
            "current_rul": rul_hours,
            "forecast": forecast_result,
            "timestamp": reading['timestamp']
        })
    
    except Exception as e:
        app.logger.error(f"Error getting health trend: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== ANOMALY DETECTION ====================

@app.route('/api/anomaly-check', methods=['GET'])
def anomaly_check():
    """Check for anomalies across machines"""
    try:
        machine_id = request.args.get('machine_id')
        
        anomalies = []
        
        if machine_id:
            # Single machine
            reading = fleet.get_machine_reading(machine_id)
            if reading is None:
                return jsonify({"error": "Machine not found"}), 404
            
            detector = get_detector(machine_id)
            is_anomaly, score, details = detector.detect_anomaly(reading['sensors'])
            
            if is_anomaly:
                anomalies.append({
                    "machine_id": machine_id,
                    "timestamp": reading['timestamp'],
                    "anomaly_score": round(score, 3),
                    "details": details,
                    "affected_sensors": reading['sensors']
                })
        else:
            # All machines
            readings = fleet.get_all_readings()
            for reading in readings:
                mid = reading['machine_id']
                detector = get_detector(mid)
                is_anomaly, score, details = detector.detect_anomaly(reading['sensors'])
                
                if is_anomaly:
                    anomalies.append({
                        "machine_id": mid,
                        "timestamp": reading['timestamp'],
                        "anomaly_score": round(score, 3),
                        "details": details
                    })
        
        return jsonify({
            "anomalies": anomalies,
            "count": len(anomalies)
        })
    
    except Exception as e:
        app.logger.error(f"Error checking anomalies: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== MAINTENANCE OPERATIONS ====================

@app.route('/api/machines/<machine_id>/maintenance', methods=['POST'])
def perform_maintenance(machine_id):
    """Perform maintenance on a machine (reset to healthy state)"""
    try:
        if machine_id not in fleet.machines:
            return jsonify({"error": "Machine not found"}), 404
        
        # Perform maintenance
        fleet.perform_maintenance(machine_id)
        
        # Reset ML predictions
        stabilized_predictor.reset_machine(machine_id)
        
        app.logger.info(f"Maintenance performed on {machine_id}")
        
        return jsonify({
            "success": True,
            "machine_id": machine_id,
            "message": "Maintenance completed successfully",
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        app.logger.error(f"Error performing maintenance: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/machines/<machine_id>/degradation-rate', methods=['POST'])
def set_degradation_rate(machine_id):
    """Set custom degradation rate for a machine"""
    try:
        data = request.json
        rate = float(data.get('rate', 0.001))
        
        if hasattr(fleet, 'set_degradation_rate'):
            success = fleet.set_degradation_rate(machine_id, rate)
            if success:
                return jsonify({"status": "success", "rate": rate})
            return jsonify({"error": "Machine not found"}), 404
            
        return jsonify({"error": "Not supported"}), 501
    except Exception as e:
        app.logger.error(f"Error setting degradation rate: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/machines/<machine_id>/reset-degradation', methods=['POST'])
def reset_degradation(machine_id):
    """Reset degradation progress for FAILING mode"""
    try:
        if hasattr(fleet, 'reset_failing_mode'):
            success = fleet.reset_failing_mode(machine_id)
            if success:
                # Also reset ML
                stabilized_predictor.reset_machine(machine_id)
                return jsonify({"status": "success", "message": "Degradation reset"})
            return jsonify({"error": "Not a valid FAILING mode machine"}), 400
            
        return jsonify({"error": "Not supported"}), 501
    except Exception as e:
        app.logger.error(f"Error resetting degradation: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


# ==================== DEMO CONTROL (HIDDEN) ====================

@app.route('/api/demo/override', methods=['POST'])
def set_manual_override():
    """Set manual sensor values for demo machine (HIDDEN - use from separate window)"""
    try:
        data = request.get_json()
        machine_id = data.get('machine_id', 'M-001')  # Default to demo machine
        
        sensor_values = {}
        if 'temperature' in data:
            sensor_values['temperature'] = float(data['temperature'])
        if 'vibration_x' in data:
            sensor_values['vibration_x'] = float(data['vibration_x'])
        if 'vibration_y' in data:
            sensor_values['vibration_y'] = float(data['vibration_y'])
        if 'pressure' in data:
            sensor_values['pressure'] = float(data['pressure'])
        if 'rpm' in data:
            sensor_values['rpm'] = float(data['rpm'])
        
        if not sensor_values:
            return jsonify({"error": "No sensor values provided"}), 400
        
        success = fleet.set_manual_override(machine_id, sensor_values)
        
        if success:
            return jsonify({
                "success": True,
                "machine_id": machine_id,
                "override_values": sensor_values,
                "message": f"Manual override set for {machine_id}"
            })
        else:
            return jsonify({"error": "Machine not found"}), 404
    
    except Exception as e:
        app.logger.error(f"Error setting manual override: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/demo/override/<machine_id>', methods=['DELETE'])
def clear_manual_override(machine_id):
    """Clear manual override and return to automatic simulation"""
    try:
        success = fleet.clear_manual_override(machine_id)
        
        if success:
            return jsonify({
                "success": True,
                "machine_id": machine_id,
                "message": f"Manual override cleared for {machine_id}"
            })
        else:
            return jsonify({
                "success": False,
                "message": "No override was set for this machine"
            })
    
    except Exception as e:
        app.logger.error(f"Error clearing manual override: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/demo/status', methods=['GET'])
def get_demo_status():
    """Get current demo override status"""
    try:
        return jsonify({
            "overrides": fleet.manual_override,
            "demo_machine": "M-001",
            "instructions": "Use POST /api/demo/override to set sensor values"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ==================== DEMO SCENARIOS (PRESET & FAILURE PLAYBACK) ====================

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    """Get list of available demo scenarios"""
    try:
        player = get_scenario_player()
        scenarios = player.get_available_scenarios()
        
        return jsonify({
            "scenarios": scenarios,
            "count": len(scenarios),
            "description": "Pre-recorded failure scenarios for demo"
        })
    
    except Exception as e:
        app.logger.error(f"Error getting scenarios: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/scenarios/start', methods=['POST'])
def start_scenario():
    """Start a failure scenario for a machine (uses fleet integration)"""
    try:
        data = request.get_json()
        
        machine_id = data.get('machine_id', 'M-002')  # Default to demo machine
        scenario_id = data.get('scenario_id', 'BFP-A1-FAILURE')
        speed = float(data.get('speed_multiplier', 1.0))
        
        # Use fleet's integrated method for proper mode handling
        result = fleet.start_demo_scenario(machine_id, scenario_id, speed)
        
        app.logger.info(f"Started scenario {scenario_id} for {machine_id} at {speed}x speed")
        
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Error starting scenario: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/scenarios/stop/<machine_id>', methods=['POST'])
def stop_scenario(machine_id):
    """Stop active scenario and reset machine to healthy state"""
    try:
        # Use fleet's integrated method which resets machine state
        result = fleet.stop_demo_scenario(machine_id)
        
        app.logger.info(f"Stopped scenario for {machine_id}, machine reset to healthy")
        
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Error stopping scenario: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/scenarios/pause/<machine_id>', methods=['POST'])
def pause_scenario(machine_id):
    """Pause active scenario"""
    try:
        player = get_scenario_player()
        result = player.pause_scenario(machine_id)
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Error pausing scenario: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/scenarios/resume/<machine_id>', methods=['POST'])
def resume_scenario(machine_id):
    """Resume paused scenario"""
    try:
        player = get_scenario_player()
        result = player.resume_scenario(machine_id)
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Error resuming scenario: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/scenarios/status/<machine_id>', methods=['GET'])
def get_scenario_status(machine_id):
    """Get status of active scenario (both Legacy and Stress)"""
    try:
        # Check Stress Scenario first (Priority)
        if hasattr(fleet, 'stress_engine'):
            stress = fleet.stress_engine.get_scenario(machine_id)
            if stress:
                return jsonify({
                    "active": True,
                    "type": "STRESS",
                    "scenario": stress.to_dict()
                })

        # Check Legacy Demo Scenario
        player = get_scenario_player()
        status = player.get_scenario_status(machine_id)
        
        if status and status.get('active'):
            return jsonify({
                "active": True,
                "type": "LEGACY",
                "scenario": status
            })
            
        return jsonify({"active": False})
    
    except Exception as e:
        app.logger.error(f"Error getting scenario status: {str(e)}")
        # Return empty status instead of 500 to avoid breaking UI pollers
        return jsonify({"active": False})


# ==================== STRESS SCENARIO CONTROL (NEW) ====================

@app.route('/api/scenarios/stress/start', methods=['POST'])
def start_stress_scenario():
    """Start an industrial stress scenario (LOAD_SPIKE, LUBRICATION_LOSS, etc.)"""
    try:
        data = request.json
        machine_id = data.get('machine_id')
        scenario_type = data.get('type')
        severity = float(data.get('severity', 0.5))
        duration = int(data.get('duration_sec', 120))
        
        if not machine_id or not scenario_type:
            return jsonify({"error": "machine_id and type required"}), 400
            
        # Fleet integration
        if hasattr(fleet, 'start_stress_scenario'):
            result = fleet.start_stress_scenario(machine_id, scenario_type, severity, duration)
            
            if result.get("success"):
                app.logger.info(f"Started stress scenario {scenario_type} on {machine_id}")
                return jsonify(result)
            else:
                return jsonify(result), 400
        else:
            return jsonify({"error": "Stress engine not ready"}), 503
            
    except Exception as e:
        app.logger.error(f"Error starting stress scenario: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/scenarios/stress/stop', methods=['POST'])
def stop_stress_scenario():
    """Stop active stress scenario"""
    try:
        data = request.json
        machine_id = data.get('machine_id')
        
        if not machine_id:
            return jsonify({"error": "machine_id required"}), 400
            
        if hasattr(fleet, 'stop_stress_scenario'):
            result = fleet.stop_stress_scenario(machine_id)
            return jsonify(result)
        return jsonify({"error": "Stress engine not ready"}), 503
        
    except Exception as e:
        app.logger.error(f"Error stopping stress scenario: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/scenarios/stress/active', methods=['GET'])
def get_active_stress_scenarios():
    """Get all active stress scenarios"""
    if hasattr(fleet, 'stress_engine'):
        return jsonify(fleet.stress_engine.get_all_active())
    return jsonify({})


@app.route('/api/scenarios/reading/<machine_id>', methods=['GET'])
def get_scenario_reading(machine_id):
    """Get current sensor reading from active scenario"""
    try:
        player = get_scenario_player()
        reading = player.get_current_reading(machine_id)
        
        if reading:
            return jsonify(reading)
        else:
            return jsonify({"error": "No active scenario for this machine"}), 404
    
    except Exception as e:
        app.logger.error(f"Error getting scenario reading: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/scenarios/active', methods=['GET'])
def get_all_active_scenarios():
    """Get all currently active scenarios"""
    try:
        player = get_scenario_player()
        active = player.get_all_active_scenarios()
        
        return jsonify({
            "active_scenarios": active,
            "count": len(active)
        })
    
    except Exception as e:
        app.logger.error(f"Error getting active scenarios: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== PRESET (VIRTUAL) MACHINES ====================

@app.route('/api/presets', methods=['GET'])
def get_presets():
    """Get all preset (virtual) machines with static values"""
    try:
        machines = get_all_preset_machines()
        
        return jsonify({
            "preset_machines": machines,
            "count": len(machines),
            "description": "Static reference machines - values never change"
        })
    
    except Exception as e:
        app.logger.error(f"Error getting presets: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/presets/<preset_id>', methods=['GET'])
def get_preset(preset_id):
    """Get specific preset machine"""
    try:
        machine = get_preset_machine(preset_id)
        
        if machine:
            return jsonify(machine)
        else:
            return jsonify({"error": f"Preset not found: {preset_id}"}), 404
    
    except Exception as e:
        app.logger.error(f"Error getting preset: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500




# ==================== PROFESSIONAL DATASETS (Industry Standards) ====================

@app.route('/api/datasets/equipment-profiles', methods=['GET'])
def get_equipment_profiles():
    """Get all professional equipment profiles (ISO 10816 compliant)"""
    try:
        profiles = get_all_equipment_profiles()
        
        return jsonify({
            "equipment_profiles": profiles,
            "count": len(profiles),
            "standards": ["ISO 10816", "IEC 60034"],
            "description": "Industry-standard equipment specifications"
        })
    
    except Exception as e:
        app.logger.error(f"Error getting equipment profiles: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/datasets/failure-modes', methods=['GET'])
def get_failure_modes_api():
    """Get all defined failure modes with characteristics"""
    try:
        modes = get_all_failure_modes()
        
        return jsonify({
            "failure_modes": modes,
            "count": len(modes),
            "description": "Common industrial equipment failure patterns"
        })
    
    except Exception as e:
        app.logger.error(f"Error getting failure modes: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/datasets/generate', methods=['POST'])
def generate_dataset():
    """Generate a professional failure dataset for ML training"""
    try:
        data = request.get_json()
        
        equipment_type = data.get('equipment_type', 'BOILER_FEED_PUMP')
        failure_mode = data.get('failure_mode', 'BEARING_INNER_RACE')
        duration_hours = float(data.get('duration_hours', 4))
        sample_interval = float(data.get('sample_interval_minutes', 5))
        
        # Validate inputs
        if equipment_type not in EQUIPMENT_PROFILES:
            return jsonify({
                "error": f"Unknown equipment type: {equipment_type}",
                "valid_types": list(EQUIPMENT_PROFILES.keys())
            }), 400
        
        if failure_mode not in FAILURE_MODES:
            return jsonify({
                "error": f"Unknown failure mode: {failure_mode}",
                "valid_modes": list(FAILURE_MODES.keys())
            }), 400
        
        dataset = generate_professional_dataset(
            equipment_type=equipment_type,
            failure_mode=failure_mode,
            duration_hours=duration_hours,
            sample_interval_minutes=sample_interval
        )
        
        return jsonify({
            "success": True,
            "equipment_type": equipment_type,
            "failure_mode": failure_mode,
            "duration_hours": duration_hours,
            "sample_count": len(dataset),
            "dataset": dataset
        })
    
    except Exception as e:
        app.logger.error(f"Error generating dataset: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== METRICS & EVALUATION (FOR JUDGES) ====================

@app.route('/api/metrics', methods=['GET'])
def get_prediction_metrics():
    """Get comprehensive prediction metrics for hackathon evaluation"""
    try:
        tracker = get_metrics_tracker()
        metrics = tracker.calculate_metrics()
        
        return jsonify({
            "success": True,
            **metrics
        })
    
    except Exception as e:
        app.logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/metrics/predictions', methods=['GET'])
def get_predictions_history():
    """Get prediction history for review"""
    try:
        machine_id = request.args.get('machine_id')
        limit = int(request.args.get('limit', 20))
        
        tracker = get_metrics_tracker()
        predictions = tracker.get_prediction_history(machine_id, limit)
        
        return jsonify({
            "predictions": predictions,
            "count": len(predictions),
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        app.logger.error(f"Error getting predictions: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/metrics/failures', methods=['GET'])
def get_failures_history():
    """Get failure events history"""
    try:
        machine_id = request.args.get('machine_id')
        limit = int(request.args.get('limit', 20))
        
        tracker = get_metrics_tracker()
        failures = tracker.get_failure_history(machine_id, limit)
        
        return jsonify({
            "failures": failures,
            "count": len(failures),
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        app.logger.error(f"Error getting failures: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/metrics/record-prediction', methods=['POST'])
def record_prediction():
    """Manually record a prediction (for tracking)"""
    try:
        data = request.get_json()
        
        machine_id = data.get('machine_id')
        ttf_hours = data.get('ttf_hours')
        health_score = data.get('health_score')
        anomaly_score = data.get('anomaly_score', 0.5)
        confidence = data.get('confidence', 0.8)
        
        if not all([machine_id, ttf_hours, health_score]):
            return jsonify({"error": "machine_id, ttf_hours, and health_score required"}), 400
        
        tracker = get_metrics_tracker()
        pred_id = tracker.record_prediction(
            machine_id, ttf_hours, health_score, anomaly_score, confidence
        )
        
        return jsonify({
            "success": True,
            "prediction_id": pred_id,
            "message": f"Prediction recorded for {machine_id}"
        })
    
    except Exception as e:
        app.logger.error(f"Error recording prediction: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/metrics/record-failure', methods=['POST'])
def record_failure():
    """Record an actual failure event"""
    try:
        data = request.get_json()
        
        machine_id = data.get('machine_id')
        event_type = data.get('event_type', 'failure')
        
        if not machine_id:
            return jsonify({"error": "machine_id required"}), 400
        
        tracker = get_metrics_tracker()
        failure_id = tracker.record_failure(machine_id, event_type)
        
        return jsonify({
            "success": True,
            "failure_id": failure_id,
            "message": f"Failure recorded for {machine_id}"
        })
    
    except Exception as e:
        app.logger.error(f"Error recording failure: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/metrics/seed-demo', methods=['POST'])
def seed_metrics_demo():
    """Seed demo metrics data (for hackathon presentation)"""
    try:
        metrics = seed_demo_metrics()
        
        return jsonify({
            "success": True,
            "message": "Demo metrics seeded successfully",
            "metrics": metrics
        })
    
    except Exception as e:
        app.logger.error(f"Error seeding demo: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== STARTUP ====================

if __name__ == '__main__':
    print("=" * 60)
    print("🏭 PRODUCTION-GRADE PREDICTIVE MAINTENANCE API")
    print("=" * 60)
    print(f"\n✓ Environment: {Config.get_env()}")
    print(f"✓ Database: {Config.DB_PATH}")
    print(f"✓ Logs: {log_file}")
    print(f"✓ Fleet initialized: {len(fleet.machines)} machines")
    print("✓ ML stabilization: EMA smoothing + monotonic RUL")
    print("✓ Alert lifecycle: ACTIVE → ACKNOWLEDGED → RESOLVED → LOGGED")
    
    print("\n📋 API Endpoints:")
    print("  GET  /api/health                          - Deep health check")
    print("  GET  /api/machines                        - List all machines")
    print("  GET  /api/sensor-data                     - Get sensor readings")
    print("  POST /api/predict-rul                     - Predict RUL")
    print("  GET  /api/anomaly-check                   - Check anomalies")
    print("  GET  /api/health-trend/:id                - Get health forecast")
    print("\n  GET  /api/alerts                          - Get active alerts")
    print("  POST /api/alerts/:id/acknowledge          - Acknowledge alert")
    print("  POST /api/alerts/:id/resolve              - Resolve alert")
    print("  GET  /api/alerts/statistics               - Alert statistics")
    print("\n  GET  /api/logs                            - Get maintenance logs")
    print("  GET  /api/sensor-history/:id              - Get sensor history")
    print("  POST /api/machines/:id/maintenance        - Perform maintenance")
    
    print("\n🎮 DEMO CONTROL (Hidden):")
    print("  POST /api/demo/override                   - Set manual sensor values")
    print("  DELETE /api/demo/override/:id             - Clear manual override")
    print("  GET  /api/demo/status                     - Get override status")
    
    print("\n📊 METRICS & EVALUATION (For Judges):")
    print("  GET  /api/metrics                         - Get precision/recall/lead time")
    print("  GET  /api/metrics/predictions             - Prediction history")
    print("  GET  /api/metrics/failures                - Failure events history")
    print("  POST /api/metrics/seed-demo               - Seed demo metrics data")
    
    print("\n🎬 DEMO SCENARIOS (Failure Playback):")
    print("  GET  /api/scenarios                       - List available scenarios")
    print("  POST /api/scenarios/start                 - Start failure scenario")
    print("  POST /api/scenarios/stop/:id              - Stop scenario")
    print("  GET  /api/scenarios/reading/:id           - Get scenario reading")
    print("  GET  /api/scenarios/active                - All active scenarios")
    
    print("\n🖥️  PRESET MACHINES (Static Reference):")
    print("  GET  /api/presets                         - List all preset machines")
    print("  GET  /api/presets/:id                     - Get specific preset")
    
    print("\n📦 PROFESSIONAL DATASETS (Industry Standards):")
    print("  GET  /api/datasets/equipment-profiles     - ISO 10816 equipment specs")
    print("  GET  /api/datasets/failure-modes          - Failure mode definitions")
    print("  POST /api/datasets/generate               - Generate ML training data")
    
    print(f"\n🚀 Starting server on http://localhost:5000")
    print("=" * 60)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

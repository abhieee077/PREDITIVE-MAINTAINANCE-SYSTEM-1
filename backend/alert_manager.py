"""
Alert Manager - Industrial Alert Lifecycle Management
ENHANCED: Evaluation windows, persistence, hysteresis, multi-sensor confirmation, rate limiting

COMPLETE FLOW:
    Sensor → ML → EMA → EVALUATION WINDOW → Persistence → Hysteresis → Alert
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid
from config import Config
from database import get_database
from evaluation_window import get_window_manager, calculate_risk_score
import threading


class PendingAlert:
    """Tracks a potential alert awaiting persistence window"""
    def __init__(self, alert_type: str, severity: str, first_triggered: datetime):
        self.alert_type = alert_type
        self.severity = severity
        self.first_triggered = first_triggered
        self.last_triggered = first_triggered
        self.trigger_count = 1
    
    def update(self):
        """Called when condition still met"""
        self.last_triggered = datetime.now()
        self.trigger_count += 1
    
    def is_persistent(self, required_seconds: int) -> bool:
        """Check if condition has persisted long enough"""
        duration = (self.last_triggered - self.first_triggered).total_seconds()
        return duration >= required_seconds


class AlertManager:
    """
    Production-grade alert lifecycle management with:
    - EVALUATION WINDOWS (sliding aggregation before alert creation)
    - Persistence windows (condition must be sustained)
    - Hysteresis (separate trigger/clear thresholds)
    - Multi-sensor confirmation for critical alerts
    - Rate limiting to prevent alert flooding
    
    METRIC PROTECTION:
    - Precision: Window rejects short spikes (pct_above check)
    - Recall: Window accumulates slow degradation
    - Lead Time: Shorter windows for critical alerts
    - False Alarms: Require trend + ratio + persistence
    """
    
    def __init__(self):
        self.db = get_database()
        
        # Evaluation window manager for sliding aggregation
        self.window_manager = get_window_manager()
        
        # Track pending alerts awaiting persistence confirmation
        # Key: (machine_id, alert_type)
        self.pending_alerts: Dict[Tuple[str, str], PendingAlert] = {}
        
        # Track recent alert creation times for rate limiting
        # Key: machine_id, Value: list of datetime
        self.recent_alerts: Dict[str, List[datetime]] = {}
        
        # Thread safety
        self._lock = threading.RLock()
    
    def check_and_create_alerts(self, machine_id: str, sensor_data: Dict,
                                rul_hours: float, health_score: float,
                                is_anomaly: bool, anomaly_score: float) -> List[str]:
        """
        INDUSTRIAL-GRADE alert creation with EVALUATION WINDOW LAYER:
        
        FLOW:
            1. Calculate risk score
            2. Feed sample to evaluation windows
            3. Evaluate windows (mean, trend, pct_above)
            4. If window approves → Persistence check
            5. If persistence passes → Hysteresis + Multi-sensor
            6. If all pass → Create alert
        
        METRIC PROTECTION:
            - Precision: Window rejects short spikes (pct_above check)
            - Recall: Window accumulates slow degradation
            - Lead Time: Shorter windows for critical alerts (45s vs 60s)
            - False Alarms: Require worsening trend + ratio + persistence
        
        Returns: List of created alert IDs
        """
        created_alerts = []
        
        with self._lock:
            # Clean up old tracking data
            self._cleanup_old_pending_alerts()
            self._cleanup_old_rate_limit_data()
            
            # Check rate limit before processing
            if not self._check_rate_limit(machine_id):
                return []  # Rate limited, skip this cycle
            
            # ==================== STEP 1: Calculate unified risk score ====================
            risk_score = calculate_risk_score(rul_hours, health_score, anomaly_score)
            
            # ==================== STEP 2: Feed samples to ALL relevant windows ====================
            # This ensures windows accumulate data even when below threshold
            alert_types = ["warning_rul", "critical_rul", "low_health_warning", 
                          "low_health_critical", "anomaly_detected"]
            
            for alert_type in alert_types:
                self.window_manager.add_sample(
                    machine_id, alert_type,
                    risk_score, health_score, rul_hours, sensor_data
                )
            
            # ==================== STEP 3: Evaluate each alert type ====================
            
            # --- CRITICAL RUL ---
            if rul_hours < Config.RUL_CRITICAL_TRIGGER:
                window_eval = self.window_manager.evaluate(machine_id, "critical_rul")
                
                if window_eval.may_proceed:
                    if self._check_multi_sensor_confirmation(sensor_data, "critical"):
                        alert_id = self._process_alert_with_persistence(
                            machine_id, "critical_rul", "critical",
                            f"Critical: RUL only {rul_hours:.1f} hours remaining",
                            {"rul_hours": rul_hours, "sensors": sensor_data,
                             "window_eval": {"mean_risk": window_eval.mean_risk,
                                           "trend": window_eval.risk_trend,
                                           "pct_above": window_eval.pct_above_threshold}}
                        )
                        if alert_id:
                            created_alerts.append(alert_id)
            
            # --- WARNING RUL ---
            elif rul_hours < Config.RUL_WARNING_TRIGGER:
                window_eval = self.window_manager.evaluate(machine_id, "warning_rul")
                
                if window_eval.may_proceed:
                    alert_id = self._process_alert_with_persistence(
                        machine_id, "warning_rul", "warning",
                        f"Warning: RUL {rul_hours:.1f} hours, maintenance recommended",
                        {"rul_hours": rul_hours,
                         "window_eval": {"mean_risk": window_eval.mean_risk,
                                       "trend": window_eval.risk_trend}}
                    )
                    if alert_id:
                        created_alerts.append(alert_id)
            else:
                # Clear pending alerts if condition improved (hysteresis)
                if rul_hours > Config.RUL_WARNING_CLEAR:
                    self._clear_pending_alert(machine_id, "warning_rul")
                if rul_hours > Config.RUL_CRITICAL_CLEAR:
                    self._clear_pending_alert(machine_id, "critical_rul")
            
            # --- CRITICAL HEALTH ---
            if health_score < Config.HEALTH_CRITICAL_TRIGGER:
                window_eval = self.window_manager.evaluate(machine_id, "low_health_critical")
                
                if window_eval.may_proceed:
                    if self._check_multi_sensor_confirmation(sensor_data, "critical"):
                        alert_id = self._process_alert_with_persistence(
                            machine_id, "low_health_critical", "critical",
                            f"Critical: Health score {health_score:.1f}%",
                            {"health_score": health_score, "sensors": sensor_data,
                             "window_eval": {"mean_risk": window_eval.mean_risk,
                                           "trend": window_eval.risk_trend}}
                        )
                        if alert_id:
                            created_alerts.append(alert_id)
            
            # --- WARNING HEALTH ---
            elif health_score < Config.HEALTH_WARNING_TRIGGER:
                window_eval = self.window_manager.evaluate(machine_id, "low_health_warning")
                
                if window_eval.may_proceed:
                    alert_id = self._process_alert_with_persistence(
                        machine_id, "low_health_warning", "warning",
                        f"Warning: Health score {health_score:.1f}%",
                        {"health_score": health_score}
                    )
                    if alert_id:
                        created_alerts.append(alert_id)
            else:
                # Clear pending alerts if condition improved (hysteresis)
                if health_score > Config.HEALTH_WARNING_CLEAR:
                    self._clear_pending_alert(machine_id, "low_health_warning")
                if health_score > Config.HEALTH_CRITICAL_CLEAR:
                    self._clear_pending_alert(machine_id, "low_health_critical")
            
            # --- ANOMALY ---
            if is_anomaly:
                window_eval = self.window_manager.evaluate(machine_id, "anomaly_detected")
                severity = "critical" if anomaly_score > Config.ANOMALY_CRITICAL_SCORE else "warning"
                
                if window_eval.may_proceed:
                    alert_id = self._process_alert_with_persistence(
                        machine_id, "anomaly_detected", severity,
                        f"Anomaly detected (score: {anomaly_score:.2f})",
                        {"anomaly_score": anomaly_score, "sensors": sensor_data}
                    )
                    if alert_id:
                        created_alerts.append(alert_id)
            else:
                # Clear anomaly pending if no longer anomalous
                self._clear_pending_alert(machine_id, "anomaly_detected")
        
        return created_alerts
    
    def _process_alert_with_persistence(self, machine_id: str, alert_type: str,
                                        severity: str, message: str,
                                        metadata: Dict = None) -> Optional[str]:
        """
        Process alert with persistence window requirement.
        Alert only fires if condition persists for required duration.
        """
        key = (machine_id, alert_type)
        required_seconds = Config.PERSISTENCE_WINDOWS.get(alert_type, 30)
        
        if key in self.pending_alerts:
            # Update existing pending alert
            pending = self.pending_alerts[key]
            pending.update()
            
            # Check if persistence window met
            if pending.is_persistent(required_seconds):
                # Persistence window met - create actual alert
                del self.pending_alerts[key]  # Clear pending
                return self._create_alert_if_new(machine_id, alert_type, severity, message, metadata)
        else:
            # Start new pending alert
            self.pending_alerts[key] = PendingAlert(alert_type, severity, datetime.now())
        
        return None  # Still pending
    
    def _clear_pending_alert(self, machine_id: str, alert_type: str):
        """Clear a pending alert (condition no longer met)"""
        key = (machine_id, alert_type)
        if key in self.pending_alerts:
            del self.pending_alerts[key]
    
    def _check_multi_sensor_confirmation(self, sensor_data: Dict, severity: str) -> bool:
        """
        For critical alerts, require multiple sensors to confirm degradation.
        Prevents false alarms from single faulty sensor.
        """
        if severity != "critical" or not Config.MULTI_SENSOR_REQUIRED_FOR_CRITICAL:
            return True  # No confirmation needed for warnings
        
        thresholds = Config.SENSOR_DEGRADATION_THRESHOLDS
        degraded_count = 0
        
        # Check each sensor against degradation threshold
        if sensor_data.get("vibration_x", 0) > thresholds.get("vibration_x", 1.5):
            degraded_count += 1
        if sensor_data.get("vibration_y", 0) > thresholds.get("vibration_y", 1.5):
            degraded_count += 1
        if sensor_data.get("temperature", 0) > thresholds.get("temperature", 85):
            degraded_count += 1
        if sensor_data.get("pressure", 200) < thresholds.get("pressure_low", 90):
            degraded_count += 1
        if sensor_data.get("rpm", 1500) < thresholds.get("rpm_low", 1350):
            degraded_count += 1
        
        return degraded_count >= Config.MIN_DEGRADED_SENSORS_FOR_CRITICAL
    
    def _check_rate_limit(self, machine_id: str) -> bool:
        """Check if we're within rate limits for this machine"""
        current_time = datetime.now()
        one_minute_ago = current_time - timedelta(minutes=1)
        
        # Get recent alerts for this machine
        recent = self.recent_alerts.get(machine_id, [])
        recent = [t for t in recent if t > one_minute_ago]
        self.recent_alerts[machine_id] = recent
        
        return len(recent) < Config.MAX_ALERTS_PER_MACHINE_PER_MINUTE
    
    def _cleanup_old_pending_alerts(self):
        """Remove pending alerts that are stale (condition not met recently)"""
        stale_threshold = datetime.now() - timedelta(seconds=120)
        stale_keys = [
            key for key, pending in self.pending_alerts.items()
            if pending.last_triggered < stale_threshold
        ]
        for key in stale_keys:
            del self.pending_alerts[key]
    
    def _cleanup_old_rate_limit_data(self):
        """Clean up old rate limit tracking data"""
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        for machine_id in list(self.recent_alerts.keys()):
            self.recent_alerts[machine_id] = [
                t for t in self.recent_alerts[machine_id] if t > one_minute_ago
            ]
            if not self.recent_alerts[machine_id]:
                del self.recent_alerts[machine_id]
    
    def _create_alert_if_new(self, machine_id: str, alert_type: str,
                            severity: str, message: str, metadata: Dict = None) -> Optional[str]:
        """Create alert only if no active alert of this type exists"""
        
        # Check for duplicate
        if self.db.check_duplicate_alert(machine_id, alert_type):
            return None  # Alert already exists
        
        # Create new alert
        alert_id = f"ALERT-{uuid.uuid4().hex[:8].upper()}"
        
        alert_data = {
            'id': alert_id,
            'machine_id': machine_id,
            'alert_type': alert_type,
            'severity': severity,
            'message': message,
            'created_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.db.create_alert(alert_data)
        
        # Track for rate limiting
        if machine_id not in self.recent_alerts:
            self.recent_alerts[machine_id] = []
        self.recent_alerts[machine_id].append(datetime.now())
        
        print(f"✓ Alert created (persistence verified): {alert_id} - {message}")
        
        return alert_id
    
    def get_active_alerts(self, machine_id: Optional[str] = None) -> List[Dict]:
        """Get all active alerts"""
        return self.db.get_active_alerts(machine_id)
    
    def acknowledge_alert(self, alert_id: str, operator_id: str) -> Dict:
        """Acknowledge an alert"""
        # Validate operator ID
        if not operator_id or len(operator_id) < 3:
            return {
                "success": False,
                "error": "Invalid operator ID"
            }
        
        # Get alert to check state
        alert = self.db.get_alert(alert_id)
        if not alert:
            return {
                "success": False,
                "error": "Alert not found"
            }
        
        if alert['state'] != 'ACTIVE':
            return {
                "success": False,
                "error": f"Alert is {alert['state']}, can only acknowledge ACTIVE alerts"
            }
        
        # Acknowledge
        success = self.db.acknowledge_alert(alert_id, operator_id)
        
        if success:
            print(f"✓ Alert {alert_id} acknowledged by {operator_id}")
            return {
                "success": True,
                "alert_id": alert_id,
                "operator_id": operator_id,
                "acknowledged_at": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Failed to acknowledge alert"
            }
    
    def resolve_alert(self, alert_id: str, operator_id: str,
                     root_cause: str, resolution_notes: str,
                     downtime_minutes: int) -> Dict:
        """Resolve an alert and create maintenance log"""
        
        # Validate inputs
        if not operator_id or len(operator_id) < 3:
            return {"success": False, "error": "Invalid operator ID"}
        
        if not root_cause or len(root_cause) < Config.MIN_ROOT_CAUSE_LENGTH:
            return {"success": False, "error": f"Root cause must be at least {Config.MIN_ROOT_CAUSE_LENGTH} characters"}
        
        if not resolution_notes or len(resolution_notes) < Config.MIN_RESOLUTION_NOTES_LENGTH:
            return {"success": False, "error": f"Resolution notes must be at least {Config.MIN_RESOLUTION_NOTES_LENGTH} characters"}
        
        if downtime_minutes < 0:
            return {"success": False, "error": "Downtime cannot be negative"}
        
        # Get alert to check state
        alert = self.db.get_alert(alert_id)
        if not alert:
            return {"success": False, "error": "Alert not found"}
        
        if alert['state'] not in ['ACKNOWLEDGED', 'IN_PROGRESS']:
            return {
                "success": False,
                "error": f"Alert is {alert['state']}, can only resolve ACKNOWLEDGED or IN_PROGRESS alerts"
            }
        
        # Resolve
        success = self.db.resolve_alert(
            alert_id, operator_id, root_cause,
            resolution_notes, downtime_minutes
        )
        
        if success:
            print(f"✓ Alert {alert_id} resolved by {operator_id}")
            print(f"  Root cause: {root_cause}")
            print(f"  Downtime: {downtime_minutes} minutes")
            
            return {
                "success": True,
                "alert_id": alert_id,
                "operator_id": operator_id,
                "resolved_at": datetime.now().isoformat(),
                "log_id": f"LOG-{alert_id}"
            }
        else:
            return {
                "success": False,
                "error": "Failed to resolve alert"
            }
    
    def get_maintenance_logs(self, machine_id: Optional[str] = None,
                            days: int = 30) -> List[Dict]:
        """Get maintenance logs"""
        from datetime import timedelta
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        return self.db.get_maintenance_logs(
            machine_id=machine_id,
            start_date=start_date
        )
    
    def get_alert_statistics(self) -> Dict:
        """Get alert statistics for monitoring"""
        stats = self.db.get_statistics()
        
        # Add additional metrics
        active_count = stats['alerts_by_state'].get('ACTIVE', 0)
        acknowledged_count = stats['alerts_by_state'].get('ACKNOWLEDGED', 0)
        resolved_count = stats['alerts_by_state'].get('RESOLVED', 0)
        
        return {
            "active_alerts": active_count,
            "acknowledged_alerts": acknowledged_count,
            "resolved_alerts": resolved_count,
            "total_logs": stats['total_logs'],
            "alerts_by_state": stats['alerts_by_state'],
            "requires_attention": active_count + acknowledged_count
        }


# Global alert manager instance
_alert_manager = None

def get_alert_manager() -> AlertManager:
    """Get or create alert manager singleton"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


if __name__ == "__main__":
    # Test alert manager
    print("Testing Alert Manager...")
    print("=" * 60)
    
    manager = AlertManager()
    
    # Test alert creation
    print("\n1. Creating test alerts...")
    alerts = manager.check_and_create_alerts(
        machine_id="M-TEST",
        sensor_data={"temperature": 85, "vibration_x": 1.2},
        rul_hours=20,  # Critical
        health_score=45,  # Warning
        is_anomaly=True,
        anomaly_score=6.5  # Critical
    )
    print(f"   Created {len(alerts)} alerts: {alerts}")
    
    # Test duplicate prevention
    print("\n2. Testing duplicate prevention...")
    alerts2 = manager.check_and_create_alerts(
        machine_id="M-TEST",
        sensor_data={"temperature": 85, "vibration_x": 1.2},
        rul_hours=20,
        health_score=45,
        is_anomaly=True,
        anomaly_score=6.5
    )
    print(f"   Created {len(alerts2)} alerts (should be 0)")
    
    # Test acknowledge
    if alerts:
        print("\n3. Testing acknowledge...")
        result = manager.acknowledge_alert(alerts[0], "OP-TEST-001")
        print(f"   Success: {result['success']}")
    
    # Test resolve
    if alerts:
        print("\n4. Testing resolve...")
        result = manager.resolve_alert(
            alerts[0],
            "OP-TEST-001",
            "Bearing wear detected",
            "Replaced bearing assembly, lubricated components, tested operation",
            120
        )
        print(f"   Success: {result['success']}")
        if result['success']:
            print(f"   Log ID: {result['log_id']}")
    
    # Test statistics
    print("\n5. Getting statistics...")
    stats = manager.get_alert_statistics()
    print(f"   Active alerts: {stats['active_alerts']}")
    print(f"   Total logs: {stats['total_logs']}")
    print(f"   Requires attention: {stats['requires_attention']}")
    
    print("\n" + "=" * 60)
    print("✓ Alert Manager working correctly!")

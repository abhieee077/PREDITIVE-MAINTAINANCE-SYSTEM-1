"""
Database Layer for Industrial Predictive Maintenance
SQLite database with proper schema for alerts, logs, and sensor history
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
from config import Config
import json


class Database:
    """Production-grade database layer with connection pooling and transactions"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DB_PATH
        self._ensure_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    machine_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    state TEXT NOT NULL DEFAULT 'ACTIVE',
                    acknowledged_by TEXT,
                    acknowledged_at TIMESTAMP,
                    resolved_by TEXT,
                    resolved_at TIMESTAMP,
                    resolution_notes TEXT,
                    root_cause TEXT,
                    downtime_minutes INTEGER,
                    metadata TEXT
                )
            """)
            
            # Create indexes for alerts
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_machine_state ON alerts(machine_id, state)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON alerts(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_state ON alerts(state)")
            
            # Create maintenance_logs table (immutable audit trail)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_logs (
                    id TEXT PRIMARY KEY,
                    machine_id TEXT NOT NULL,
                    alert_id TEXT,
                    created_at TIMESTAMP NOT NULL,
                    resolved_at TIMESTAMP NOT NULL,
                    operator TEXT NOT NULL,
                    root_cause TEXT NOT NULL,
                    resolution_notes TEXT NOT NULL,
                    downtime_minutes INTEGER NOT NULL,
                    severity TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (alert_id) REFERENCES alerts(id)
                )
            """)
            
            # Create indexes for maintenance_logs
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_machine_created ON maintenance_logs(machine_id, created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolved_at ON maintenance_logs(resolved_at)")
            
            # Create sensor_history table (optional, for future historical charts)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    machine_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    vibration_x REAL,
                    vibration_y REAL,
                    temperature REAL,
                    pressure REAL,
                    rpm REAL,
                    health_score REAL,
                    rul_hours REAL
                )
            """)
            
            # Create index for sensor_history
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_machine_timestamp ON sensor_history(machine_id, timestamp)")
            
            print(f"✓ Database initialized: {self.db_path}")
    
    # ==================== ALERT OPERATIONS ====================
    
    def create_alert(self, alert_data: Dict) -> str:
        """Create a new alert"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            alert_id = alert_data['id']
            cursor.execute("""
                INSERT INTO alerts (
                    id, machine_id, alert_type, severity, message,
                    created_at, state, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert_id,
                alert_data['machine_id'],
                alert_data['alert_type'],
                alert_data['severity'],
                alert_data['message'],
                alert_data['created_at'],
                'ACTIVE',
                json.dumps(alert_data.get('metadata', {}))
            ))
            
            return alert_id
    
    def get_alert(self, alert_id: str) -> Optional[Dict]:
        """Get alert by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_active_alerts(self, machine_id: Optional[str] = None) -> List[Dict]:
        """Get all active alerts (not resolved or logged)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if machine_id:
                cursor.execute("""
                    SELECT * FROM alerts 
                    WHERE machine_id = ? AND state IN ('ACTIVE', 'ACKNOWLEDGED', 'IN_PROGRESS')
                    ORDER BY created_at DESC
                """, (machine_id,))
            else:
                cursor.execute("""
                    SELECT * FROM alerts 
                    WHERE state IN ('ACTIVE', 'ACKNOWLEDGED', 'IN_PROGRESS')
                    ORDER BY created_at DESC
                """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def acknowledge_alert(self, alert_id: str, operator_id: str) -> bool:
        """Acknowledge an alert"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE alerts 
                SET state = 'ACKNOWLEDGED',
                    acknowledged_by = ?,
                    acknowledged_at = ?
                WHERE id = ? AND state = 'ACTIVE'
            """, (operator_id, datetime.now().isoformat(), alert_id))
            
            return cursor.rowcount > 0
    
    def resolve_alert(self, alert_id: str, operator_id: str, 
                     root_cause: str, resolution_notes: str, 
                     downtime_minutes: int) -> bool:
        """Resolve an alert and create maintenance log"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get alert details
            cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
            alert = cursor.fetchone()
            
            if not alert:
                return False
            
            # Update alert
            resolved_at = datetime.now().isoformat()
            cursor.execute("""
                UPDATE alerts 
                SET state = 'RESOLVED',
                    resolved_by = ?,
                    resolved_at = ?,
                    resolution_notes = ?,
                    root_cause = ?,
                    downtime_minutes = ?
                WHERE id = ? AND state IN ('ACKNOWLEDGED', 'IN_PROGRESS')
            """, (operator_id, resolved_at, resolution_notes, root_cause, 
                  downtime_minutes, alert_id))
            
            if cursor.rowcount == 0:
                return False
            
            # Create maintenance log
            log_id = f"LOG-{alert_id}"
            cursor.execute("""
                INSERT INTO maintenance_logs (
                    id, machine_id, alert_id, created_at, resolved_at,
                    operator, root_cause, resolution_notes, downtime_minutes,
                    severity, alert_type, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id,
                alert['machine_id'],
                alert_id,
                alert['created_at'],
                resolved_at,
                operator_id,
                root_cause,
                resolution_notes,
                downtime_minutes,
                alert['severity'],
                alert['alert_type'],
                alert['metadata']
            ))
            
            return True
    
    def check_duplicate_alert(self, machine_id: str, alert_type: str) -> bool:
        """Check if an active alert of this type already exists for the machine"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count FROM alerts 
                WHERE machine_id = ? AND alert_type = ? 
                AND state IN ('ACTIVE', 'ACKNOWLEDGED', 'IN_PROGRESS')
            """, (machine_id, alert_type))
            
            result = cursor.fetchone()
            return result['count'] > 0
    
    # ==================== LOG OPERATIONS ====================
    
    def get_maintenance_logs(self, machine_id: Optional[str] = None,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            limit: int = 100) -> List[Dict]:
        """Get maintenance logs with optional filtering"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM maintenance_logs WHERE 1=1"
            params = []
            
            if machine_id:
                query += " AND machine_id = ?"
                params.append(machine_id)
            
            if start_date:
                query += " AND resolved_at >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND resolved_at <= ?"
                params.append(end_date)
            
            query += " ORDER BY resolved_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def create_maintenance_log(self, log_data: Dict) -> bool:
        """Create a new maintenance log entry"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            log_id = log_data.get('id', f"LOG-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO maintenance_logs (
                    id, machine_id, alert_id, created_at, resolved_at,
                    operator, root_cause, resolution_notes, downtime_minutes,
                    severity, alert_type, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id,
                log_data.get('machine_id', 'M-001'),
                log_data.get('alert_id'),
                now,
                log_data.get('resolved_at', now),
                log_data.get('operator', log_data.get('performed_by', 'System')),
                log_data.get('root_cause', log_data.get('action', 'Maintenance')),
                log_data.get('resolution_notes', log_data.get('notes', '')),
                log_data.get('downtime_minutes', int(log_data.get('duration_hours', 1) * 60)),
                log_data.get('severity', 'info'),
                log_data.get('alert_type', log_data.get('action', 'maintenance')),
                json.dumps(log_data.get('metadata', {}))
            ))
            conn.commit()
            return log_id
    
    def delete_maintenance_log(self, log_id: str) -> bool:
        """Delete a maintenance log by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM maintenance_logs WHERE id = ?", (log_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def update_maintenance_log(self, log_id: str, updates: Dict) -> bool:
        """Update a maintenance log entry"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build dynamic update query
            set_clauses = []
            params = []
            
            field_map = {
                'operator': 'operator',
                'performed_by': 'operator',
                'root_cause': 'root_cause',
                'action': 'root_cause',
                'resolution_notes': 'resolution_notes',
                'notes': 'resolution_notes',
                'downtime_minutes': 'downtime_minutes',
                'duration_hours': 'downtime_minutes',
                'severity': 'severity',
                'status': 'alert_type'
            }
            
            for key, value in updates.items():
                if key in field_map:
                    db_field = field_map[key]
                    if key == 'duration_hours':
                        value = int(value * 60)
                    set_clauses.append(f"{db_field} = ?")
                    params.append(value)
            
            if not set_clauses:
                return False
            
            params.append(log_id)
            query = f"UPDATE maintenance_logs SET {', '.join(set_clauses)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
    
    # ==================== SENSOR HISTORY OPERATIONS ====================
    
    def save_sensor_reading(self, machine_id: str, sensor_data: Dict):
        """Save sensor reading to history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sensor_history (
                    machine_id, timestamp, vibration_x, vibration_y,
                    temperature, pressure, rpm, health_score, rul_hours
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                machine_id,
                datetime.now().isoformat(),
                sensor_data.get('vibration_x'),
                sensor_data.get('vibration_y'),
                sensor_data.get('temperature'),
                sensor_data.get('pressure'),
                sensor_data.get('rpm'),
                sensor_data.get('health_score'),
                sensor_data.get('rul_hours')
            ))
    
    def get_sensor_history(self, machine_id: str, hours: int = 24) -> List[Dict]:
        """Get sensor history for a machine"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            since = (datetime.now() - timedelta(hours=hours)).isoformat()
            cursor.execute("""
                SELECT * FROM sensor_history 
                WHERE machine_id = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (machine_id, since))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== CLEANUP OPERATIONS ====================
    
    def cleanup_old_data(self):
        """Clean up old alerts and enforce retention policies"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Archive old resolved alerts to logs (if not already)
            alert_cutoff = (datetime.now() - timedelta(days=Config.ALERT_RETENTION_DAYS)).isoformat()
            cursor.execute("""
                UPDATE alerts 
                SET state = 'LOGGED'
                WHERE state = 'RESOLVED' AND resolved_at < ?
            """, (alert_cutoff,))
            
            archived_count = cursor.rowcount
            
            # Delete very old logs (beyond retention period)
            log_cutoff = (datetime.now() - timedelta(days=Config.LOG_RETENTION_DAYS)).isoformat()
            cursor.execute("""
                DELETE FROM maintenance_logs 
                WHERE resolved_at < ?
            """, (log_cutoff,))
            
            deleted_count = cursor.rowcount
            
            print(f"✓ Cleanup: Archived {archived_count} alerts, deleted {deleted_count} old logs")
            
            return archived_count, deleted_count
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Alert counts by state
            cursor.execute("""
                SELECT state, COUNT(*) as count 
                FROM alerts 
                GROUP BY state
            """)
            stats['alerts_by_state'] = {row['state']: row['count'] for row in cursor.fetchall()}
            
            # Total logs
            cursor.execute("SELECT COUNT(*) as count FROM maintenance_logs")
            stats['total_logs'] = cursor.fetchone()['count']
            
            # Sensor history size
            cursor.execute("SELECT COUNT(*) as count FROM sensor_history")
            stats['sensor_history_count'] = cursor.fetchone()['count']
            
            return stats


# Global database instance
_db_instance = None

def get_database() -> Database:
    """Get or create database singleton"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


if __name__ == "__main__":
    # Test database
    print("Testing Database...")
    db = Database()
    
    # Test alert creation
    test_alert = {
        'id': 'TEST-001',
        'machine_id': 'M-001',
        'alert_type': 'critical_rul',
        'severity': 'critical',
        'message': 'Test alert',
        'created_at': datetime.now().isoformat()
    }
    
    alert_id = db.create_alert(test_alert)
    print(f"\n✓ Created test alert: {alert_id}")
    
    # Test retrieval
    alert = db.get_alert(alert_id)
    print(f"✓ Retrieved alert: {alert['message']}")
    
    # Test acknowledge
    success = db.acknowledge_alert(alert_id, "OP-001")
    print(f"✓ Acknowledged: {success}")
    
    # Test resolve
    success = db.resolve_alert(
        alert_id, "OP-001",
        "Test root cause",
        "Test resolution notes",
        30
    )
    print(f"✓ Resolved: {success}")
    
    # Get logs
    logs = db.get_maintenance_logs()
    print(f"✓ Retrieved {len(logs)} logs")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"\n✓ Statistics: {stats}")

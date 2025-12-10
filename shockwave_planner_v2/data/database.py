"""
SHOCKWAVE PLANNER v2.0 - Database Layer
SQLite database interface with Space Devs API integration

Author: Remix Astronautics
Date: December 2025
Version: 2.0.0
"""
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

DEFAULT_DB_PATH = r'./shockwave_planner_v2/shockwave_planner.db'

class LaunchDatabase:
    """Database operations for SHOCKWAVE PLANNER"""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """Initialize database connection"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()
        
        # Launch Sites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS launch_sites (
                site_id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT NOT NULL,
                launch_pad TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                country TEXT,
                site_type TEXT DEFAULT 'LAUNCH',
                external_id TEXT,
                UNIQUE(location, launch_pad)
            )
        ''')
        
        # Rockets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rockets (
                rocket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                family TEXT,
                variant TEXT,
                manufacturer TEXT,
                country TEXT,
                payload_leo INTEGER,
                payload_gto INTEGER,
                height REAL,
                diameter REAL,
                mass REAL,
                stages INTEGER,
                external_id TEXT
            )
        ''')
        
        # Launch Vehicles table (specific configurations)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS launch_vehicles (
                vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                rocket_id INTEGER,
                serial_number TEXT,
                first_flight DATE,
                status TEXT,
                FOREIGN KEY (rocket_id) REFERENCES rockets(rocket_id)
            )
        ''')
        
        # Launch Status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS launch_status (
                status_id INTEGER PRIMARY KEY AUTOINCREMENT,
                status_name TEXT NOT NULL UNIQUE,
                status_abbr TEXT,
                status_color TEXT,
                description TEXT
            )
        ''')
        
        # Launches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS launches (
                launch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                launch_date DATE NOT NULL,
                launch_time TIME,
                launch_window_start DATETIME,
                launch_window_end DATETIME,
                site_id INTEGER,
                rocket_id INTEGER,
                vehicle_id INTEGER,
                mission_name TEXT,
                payload_name TEXT,
                payload_mass REAL,
                orbit_type TEXT,
                orbit_altitude REAL,
                inclination REAL,
                status_id INTEGER,
                success BOOLEAN,
                failure_reason TEXT,
                remarks TEXT,
                source_url TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                notam_reference TEXT,
                data_source TEXT DEFAULT 'MANUAL',
                external_id TEXT,
                last_synced DATETIME,
                FOREIGN KEY (site_id) REFERENCES launch_sites(site_id),
                FOREIGN KEY (rocket_id) REFERENCES rockets(rocket_id),
                FOREIGN KEY (vehicle_id) REFERENCES launch_vehicles(vehicle_id),
                FOREIGN KEY (status_id) REFERENCES launch_status(status_id)
            )
        ''')
        
        # Launch TLEs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS launch_tles (
                tle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                launch_id INTEGER,
                norad_id INTEGER,
                object_name TEXT,
                tle_line1 TEXT,
                tle_line2 TEXT,
                epoch DATETIME,
                source TEXT,
                FOREIGN KEY (launch_id) REFERENCES launches(launch_id)
            )
        ''')
        
        # Launch Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS launch_predictions (
                prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                launch_id INTEGER,
                predicted_time DATETIME,
                confidence REAL,
                prediction_source TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (launch_id) REFERENCES launches(launch_id)
            )
        ''')
        
        # Re-entry Sites table (NEW in v2.0)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reentry_sites (
                reentry_site_id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT NOT NULL,
                drop_zone TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                country TEXT,
                zone_type TEXT,
                external_id TEXT,
                UNIQUE(location, drop_zone)
            )
        ''')
        
        # Re-entries table (NEW in v2.0)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reentries (
                reentry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                launch_id INTEGER,
                reentry_date DATE,
                reentry_time TIME,
                reentry_site_id INTEGER,
                vehicle_component TEXT,
                reentry_type TEXT,
                status_id INTEGER,
                remarks TEXT,
                data_source TEXT DEFAULT 'MANUAL',
                external_id TEXT,
                FOREIGN KEY (launch_id) REFERENCES launches(launch_id),
                FOREIGN KEY (reentry_site_id) REFERENCES reentry_sites(reentry_site_id),
                FOREIGN KEY (status_id) REFERENCES launch_status(status_id)
            )
        ''')
        
        # Sync Log table (NEW in v2.0)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_log (
                sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_source TEXT,
                records_added INTEGER,
                records_updated INTEGER,
                status TEXT,
                error_message TEXT
            )
        ''')
        
        # Initialize default statuses if empty
        cursor.execute("SELECT COUNT(*) FROM launch_status")
        if cursor.fetchone()[0] == 0:
            self._init_default_statuses()
        
        self.conn.commit()
    
    def _init_default_statuses(self):
        """Initialize default launch status values"""
        statuses = [
            ('Scheduled', 'SCH', '#FFFF00', 'Launch is scheduled'),
            ('Go for Launch', 'GO', '#00FF00', 'Cleared for launch'),
            ('Success', 'SUC', '#00AA00', 'Launch successful'),
            ('Failure', 'FAIL', '#FF0000', 'Launch failed'),
            ('Partial Failure', 'PF', '#FFA500', 'Partial failure'),
            ('Scrubbed', 'SCR', '#808080', 'Launch scrubbed'),
            ('Hold', 'HOLD', '#FFAA00', 'Launch on hold'),
            ('In Flight', 'FLT', '#00AAFF', 'Vehicle in flight'),
        ]
        
        cursor = self.conn.cursor()
        cursor.executemany('''
            INSERT INTO launch_status (status_name, status_abbr, status_color, description)
            VALUES (?, ?, ?, ?)
        ''', statuses)
        self.conn.commit()
    
    # ==================== SITE OPERATIONS ====================
    
    def get_all_sites(self, site_type: str = 'LAUNCH') -> List[Dict]:
        """Get all launch/reentry sites"""
        if site_type == 'REENTRY':
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT reentry_site_id as site_id, location, drop_zone as launch_pad,
                       latitude, longitude, country, zone_type
                FROM reentry_sites
                ORDER BY location, drop_zone
            ''')
        else:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT site_id, location, launch_pad, latitude, longitude, country
                FROM launch_sites
                ORDER BY location, launch_pad
            ''')
        
        return [dict(row) for row in cursor.fetchall()]
    
    def add_site(self, site_data: Dict, site_type: str = 'LAUNCH') -> int:
        """Add a new launch or reentry site"""
        cursor = self.conn.cursor()
        
        if site_type == 'REENTRY':
            cursor.execute('''
                INSERT INTO reentry_sites (location, drop_zone, latitude, longitude, country, zone_type, external_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                site_data['location'],
                site_data.get('drop_zone', 'Unknown'),
                site_data.get('latitude'),
                site_data.get('longitude'),
                site_data.get('country'),
                site_data.get('zone_type'),
                site_data.get('external_id')
            ))
        else:
            cursor.execute('''
                INSERT INTO launch_sites (location, launch_pad, latitude, longitude, country, site_type, external_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                site_data['location'],
                site_data['launch_pad'],
                site_data.get('latitude'),
                site_data.get('longitude'),
                site_data.get('country'),
                site_type,
                site_data.get('external_id')
            ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def update_site(self, site_id: int, site_data: Dict):
        """Update an existing launch site"""
        cursor = self.conn.cursor()
        
        site_type = site_data.get('site_type', 'LAUNCH')
        
        if site_type == 'REENTRY':
            cursor.execute('''
                UPDATE reentry_sites SET
                    location = ?, drop_zone = ?, latitude = ?, longitude = ?,
                    country = ?, zone_type = ?
                WHERE reentry_site_id = ?
            ''', (
                site_data['location'],
                site_data.get('drop_zone', site_data.get('launch_pad')),
                site_data.get('latitude'),
                site_data.get('longitude'),
                site_data.get('country'),
                site_data.get('zone_type'),
                site_id
            ))
        else:
            cursor.execute('''
                UPDATE launch_sites SET
                    location = ?, launch_pad = ?, latitude = ?, longitude = ?,
                    country = ?
                WHERE site_id = ?
            ''', (
                site_data['location'],
                site_data['launch_pad'],
                site_data.get('latitude'),
                site_data.get('longitude'),
                site_data.get('country'),
                site_id
            ))
        
        self.conn.commit()
    
    def delete_site(self, site_id: int):
        """Delete a launch site"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM launch_sites WHERE site_id = ?', (site_id,))
        self.conn.commit()
    
    # ==================== ROCKET OPERATIONS ====================
    
    def get_all_rockets(self) -> List[Dict]:
        """Get all rockets"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT rocket_id, name, family, variant, manufacturer, country,
                   payload_leo, payload_gto
            FROM rockets
            ORDER BY name
        ''')
        return [dict(row) for row in cursor.fetchall()]
    
    def add_rocket(self, rocket_data: Dict) -> int:
        """Add a new rocket"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO rockets (name, family, variant, manufacturer, country,
                               payload_leo, payload_gto, height, diameter, mass, stages, external_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rocket_data['name'],
            rocket_data.get('family'),
            rocket_data.get('variant'),
            rocket_data.get('manufacturer'),
            rocket_data.get('country'),
            rocket_data.get('payload_leo'),
            rocket_data.get('payload_gto'),
            rocket_data.get('height'),
            rocket_data.get('diameter'),
            rocket_data.get('mass'),
            rocket_data.get('stages'),
            rocket_data.get('external_id')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_rocket(self, rocket_id: int, rocket_data: Dict):
        """Update an existing rocket"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE rockets SET
                name = ?, family = ?, variant = ?, manufacturer = ?,
                country = ?, payload_leo = ?, payload_gto = ?,
                height = ?, diameter = ?, mass = ?, stages = ?
            WHERE rocket_id = ?
        ''', (
            rocket_data['name'],
            rocket_data.get('family'),
            rocket_data.get('variant'),
            rocket_data.get('manufacturer'),
            rocket_data.get('country'),
            rocket_data.get('payload_leo'),
            rocket_data.get('payload_gto'),
            rocket_data.get('height'),
            rocket_data.get('diameter'),
            rocket_data.get('mass'),
            rocket_data.get('stages'),
            rocket_id
        ))
        self.conn.commit()
    
    def delete_rocket(self, rocket_id: int):
        """Delete a rocket"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM rockets WHERE rocket_id = ?', (rocket_id,))
        self.conn.commit()
    
    def find_or_create_rocket(self, name: str, external_id: str = None) -> int:
        """Find existing rocket or create new one"""
        cursor = self.conn.cursor()
        
        # Try to find by external_id first
        if external_id:
            cursor.execute('SELECT rocket_id FROM rockets WHERE external_id = ?', (external_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
        
        # Try to find by name
        cursor.execute('SELECT rocket_id FROM rockets WHERE name = ?', (name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        
        # Create new rocket
        return self.add_rocket({'name': name, 'external_id': external_id})
    
    # ==================== RE-ENTRY VEHICLE OPERATIONS ====================
    
    def get_all_reentry_vehicles(self) -> List[Dict]:
        """Get all re-entry vehicles"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT vehicle_id as reentry_vehicle_id, name, alternative_name, family, variant,
                   manufacturer, country, payload, decelerator, remarks, external_id
            FROM reentry_vehicle
            ORDER BY name
        ''')
        return [dict(row) for row in cursor.fetchall()]
    
    def add_reentry_vehicle(self, vehicle_data: Dict) -> int:
        """Add a new re-entry vehicle"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO reentry_vehicle (
                name, alternative_name, family, variant, manufacturer, country,
                payload, decelerator, remarks, external_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            vehicle_data['name'],
            vehicle_data.get('alternative_name'),
            vehicle_data.get('family'),
            vehicle_data.get('variant'),
            vehicle_data.get('manufacturer'),
            vehicle_data.get('country'),
            vehicle_data.get('payload'),
            vehicle_data.get('decelerator'),
            vehicle_data.get('remarks'),
            vehicle_data.get('external_id')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_reentry_vehicle(self, vehicle_id: int, vehicle_data: Dict):
        """Update an existing re-entry vehicle"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE reentry_vehicle SET
                name = ?, alternative_name = ?, family = ?, variant = ?,
                manufacturer = ?, country = ?, payload = ?, decelerator = ?,
                remarks = ?, external_id = ?
            WHERE vehicle_id = ?
        ''', (
            vehicle_data['name'],
            vehicle_data.get('alternative_name'),
            vehicle_data.get('family'),
            vehicle_data.get('variant'),
            vehicle_data.get('manufacturer'),
            vehicle_data.get('country'),
            vehicle_data.get('payload'),
            vehicle_data.get('decelerator'),
            vehicle_data.get('remarks'),
            vehicle_data.get('external_id'),
            vehicle_id
        ))
        self.conn.commit()
    
    def delete_reentry_vehicle(self, vehicle_id: int):
        """Delete a re-entry vehicle"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM reentry_vehicle WHERE vehicle_id = ?', (vehicle_id,))
        self.conn.commit()
        
    # ==================== STATUS OPERATIONS ====================
    
    def get_all_statuses(self) -> List[Dict]:
        """Get all launch statuses"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT status_id, status_name, status_abbr, status_color, description
            FROM launch_status
            ORDER BY status_id
        ''')
        return [dict(row) for row in cursor.fetchall()]
    
    def find_status_by_name(self, name: str) -> Optional[int]:
        """Find status ID by name (case-insensitive)"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT status_id FROM launch_status WHERE LOWER(status_name) = LOWER(?)', (name,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    # ==================== LAUNCH OPERATIONS ====================
    
    def add_launch(self, launch_data: Dict) -> int:
        """Add a new launch"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO launches (
                launch_date, launch_time, launch_window_start, launch_window_end,
                site_id, rocket_id, vehicle_id, mission_name, payload_name,
                payload_mass, orbit_type, orbit_altitude, inclination,
                status_id, success, failure_reason, remarks, source_url,
                notam_reference, data_source, external_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            launch_data['launch_date'],
            launch_data.get('launch_time'),
            launch_data.get('launch_window_start'),
            launch_data.get('launch_window_end'),
            launch_data.get('site_id'),
            launch_data.get('rocket_id'),
            launch_data.get('vehicle_id'),
            launch_data.get('mission_name'),
            launch_data.get('payload_name'),
            launch_data.get('payload_mass'),
            launch_data.get('orbit_type'),
            launch_data.get('orbit_altitude'),
            launch_data.get('inclination'),
            launch_data.get('status_id'),
            launch_data.get('success'),
            launch_data.get('failure_reason'),
            launch_data.get('remarks'),
            launch_data.get('source_url'),
            launch_data.get('notam_reference'),
            launch_data.get('data_source', 'MANUAL'),
            launch_data.get('external_id')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_launch(self, launch_id: int, launch_data: Dict):
        """Update an existing launch"""
        cursor = self.conn.cursor()
        
        # Build UPDATE query dynamically based on provided fields
        fields = []
        values = []
        
        field_mapping = {
            'launch_date': 'launch_date',
            'launch_time': 'launch_time',
            'launch_window_start': 'launch_window_start',
            'launch_window_end': 'launch_window_end',
            'site_id': 'site_id',
            'rocket_id': 'rocket_id',
            'vehicle_id': 'vehicle_id',
            'mission_name': 'mission_name',
            'payload_name': 'payload_name',
            'payload_mass': 'payload_mass',
            'orbit_type': 'orbit_type',
            'orbit_altitude': 'orbit_altitude',
            'inclination': 'inclination',
            'status_id': 'status_id',
            'success': 'success',
            'failure_reason': 'failure_reason',
            'remarks': 'remarks',
            'source_url': 'source_url',
            'notam_reference': 'notam_reference',
            'data_source': 'data_source',
            'external_id': 'external_id'
        }
        
        for key, db_field in field_mapping.items():
            if key in launch_data:
                fields.append(f"{db_field} = ?")
                values.append(launch_data[key])
        
        if not fields:
            return
        
        values.append(launch_id)
        query = f"UPDATE launches SET {', '.join(fields)}, last_updated = CURRENT_TIMESTAMP WHERE launch_id = ?"
        
        cursor.execute(query, values)
        self.conn.commit()
    
    def delete_launch(self, launch_id: int):
        """Delete a launch"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM launches WHERE launch_id = ?', (launch_id,))
        self.conn.commit()
    
    def get_all_launches(self) -> List[Dict]:
        """Get all launches from database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT l.*, 
                   ls.location, ls.launch_pad,
                   r.name as rocket_name,
                   st.status_name, st.status_color
            FROM launches l
            LEFT JOIN launch_sites ls ON l.site_id = ls.site_id
            LEFT JOIN rockets r ON l.rocket_id = r.rocket_id
            LEFT JOIN launch_status st ON l.status_id = st.status_id
            ORDER BY l.launch_date DESC, l.launch_time DESC
            LIMIT 1000
        ''')
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_launches_by_month(self, year: int, month: int) -> List[Dict]:
        """Get all launches for a specific month"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT l.*, 
                   ls.location, ls.launch_pad,
                   r.name as rocket_name,
                   st.status_name, st.status_color
            FROM launches l
            LEFT JOIN launch_sites ls ON l.site_id = ls.site_id
            LEFT JOIN rockets r ON l.rocket_id = r.rocket_id
            LEFT JOIN launch_status st ON l.status_id = st.status_id
            WHERE strftime('%Y', l.launch_date) = ? AND strftime('%m', l.launch_date) = ?
            ORDER BY l.launch_date, l.launch_time
        ''', (str(year), f'{month:02d}'))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_launches_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get launches within a date range"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT l.*, 
                   ls.location, ls.launch_pad,
                   r.name as rocket_name,
                   st.status_name, st.status_color
            FROM launches l
            LEFT JOIN launch_sites ls ON l.site_id = ls.site_id
            LEFT JOIN rockets r ON l.rocket_id = r.rocket_id
            LEFT JOIN launch_status st ON l.status_id = st.status_id
            WHERE l.launch_date BETWEEN ? AND ?
            ORDER BY l.launch_date, l.launch_time
        ''', (start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def find_launch_by_external_id(self, external_id: str) -> Optional[Dict]:
        """Find launch by external ID (e.g., Space Devs ID)"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT l.*, 
                   ls.location, ls.launch_pad,
                   r.name as rocket_name,
                   st.status_name, st.status_color
            FROM launches l
            LEFT JOIN launch_sites ls ON l.site_id = ls.site_id
            LEFT JOIN rockets r ON l.rocket_id = r.rocket_id
            LEFT JOIN launch_status st ON l.status_id = st.status_id
            WHERE l.external_id = ?
        ''', (external_id,))
        
        result = cursor.fetchone()
        return dict(result) if result else None
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self) -> Dict:
        """Get launch statistics"""
        cursor = self.conn.cursor()
        
        # Total launches
        cursor.execute('SELECT COUNT(*) FROM launches')
        total = cursor.fetchone()[0]
        
        # Success/failure counts
        cursor.execute('SELECT COUNT(*) FROM launches WHERE success = 1')
        successful = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM launches WHERE success = 0 AND success IS NOT NULL')
        failed = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM launches WHERE success IS NULL')
        pending = cursor.fetchone()[0]
        
        # Top rockets
        cursor.execute('''
            SELECT r.name, COUNT(*) as count
            FROM launches l
            JOIN rockets r ON l.rocket_id = r.rocket_id
            GROUP BY r.rocket_id
            ORDER BY count DESC
            LIMIT 10
        ''')
        by_rocket = [dict(row) for row in cursor.fetchall()]
        
        # By site
        cursor.execute('''
            SELECT ls.location, COUNT(*) as count
            FROM launches l
            JOIN launch_sites ls ON l.site_id = ls.site_id
            GROUP BY ls.location
            ORDER BY count DESC
        ''')
        by_site = [dict(row) for row in cursor.fetchall()]
        
        return {
            'total_launches': total,
            'successful': successful,
            'failed': failed,
            'pending': pending,
            'by_rocket': by_rocket,
            'by_site': by_site
        }
    
    # ==================== RE-ENTRY OPERATIONS (NEW in v2.0) ====================
    
    def add_reentry_site(self, site_data: Dict) -> int:
        """Add a new re-entry site"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO reentry_sites (
                location, drop_zone, latitude, longitude,
                country, zone_type, external_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            site_data['location'],
            site_data['drop_zone'],
            site_data.get('latitude'),
            site_data.get('longitude'),
            site_data.get('country'),
            site_data.get('zone_type'),
            site_data.get('external_id')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def add_reentry(self, reentry_data: Dict) -> int:
        """Add a new re-entry record"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO reentries (
                launch_id, reentry_date, reentry_time, reentry_site_id,
                vehicle_component, reentry_type, status_id, remarks,
                data_source, external_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            reentry_data.get('launch_id'),
            reentry_data['reentry_date'],
            reentry_data.get('reentry_time'),
            reentry_data.get('reentry_site_id'),
            reentry_data.get('vehicle_component'),
            reentry_data.get('reentry_type'),
            reentry_data.get('status_id'),
            reentry_data.get('remarks'),
            reentry_data.get('data_source', 'MANUAL'),
            reentry_data.get('external_id')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_reentries_by_month(self, year: int, month: int) -> List[Dict]:
        """Get all re-entries for a specific month"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT re.*, 
                   rs.location, rs.drop_zone,
                   l.mission_name, l.payload_name,
                   st.status_name, st.status_color
            FROM reentries re
            LEFT JOIN reentry_sites rs ON re.reentry_site_id = rs.reentry_site_id
            LEFT JOIN launches l ON re.launch_id = l.launch_id
            LEFT JOIN launch_status st ON re.status_id = st.status_id
            WHERE strftime('%Y', re.reentry_date) = ? AND strftime('%m', re.reentry_date) = ?
            ORDER BY re.reentry_date, re.reentry_time
        ''', (str(year), f'{month:02d}'))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # ==================== SYNC OPERATIONS (NEW in v2.0) ====================
    
    def log_sync(self, data_source: str, records_added: int, records_updated: int, 
                 status: str, error_message: str = None):
        """Log a sync operation"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sync_log (data_source, records_added, records_updated, status, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (data_source, records_added, records_updated, status, error_message))
        self.conn.commit()
    
    def get_last_sync(self, data_source: str) -> Optional[Dict]:
        """Get last successful sync for a data source"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM sync_log
            WHERE data_source = ? AND status = 'SUCCESS'
            ORDER BY sync_time DESC
            LIMIT 1
        ''', (data_source,))
        
        result = cursor.fetchone()
        return dict(result) if result else None
    
    # ==================== UTILITY ====================
    
    def close(self):
        """Close database connection"""
        self.conn.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.conn.close()
        except:
            pass

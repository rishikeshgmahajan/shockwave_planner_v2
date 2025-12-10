"""
SHOCKWAVE PLANNER v2.0 - Main Window
Enhanced with Space Devs Integration, Re-entry Tracking, and Timeline Views

Author: Remix Astronautics
Date: December 2025
Version: 2.0.0
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QTabWidget, QGroupBox,
                              QDialog, QFormLayout, QDialogButtonBox, QLineEdit,
                              QComboBox, QDateEdit, QTimeEdit, QTextEdit,
                              QMessageBox, QProgressDialog)
from PyQt6.QtCore import Qt, QDate, QTime, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QFont
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.database import LaunchDatabase
from data.space_devs import SpaceDevsAPI
from gui.timeline_view import TimelineView
from gui.enhanced_list_view import EnhancedListView
from gui.timeline_view_reentry import ReentryTimelineView
from gui.reentry_dialog import ReentryDialog
from gui.launch_sites_view import LaunchSitesView
from gui.drop_zones_view import DropZonesView
from gui.rockets_view import RocketsView
from gui.reentry_vehicles_view import ReentryVehiclesView

class SyncWorker(QThread):
    """Background worker for Space Devs sync"""
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)
    
    def __init__(self, db_path, sync_type='upcoming', limit=100):
        super().__init__()
        self.db_path = db_path
        self.sync_type = sync_type
        self.limit = limit
    
    def run(self):
        try:
            # Create a new database connection in this thread
            db = LaunchDatabase(self.db_path)
            api = SpaceDevsAPI(db)
            
            if self.sync_type == 'upcoming':
                self.progress.emit("Fetching upcoming launches...")
                result = api.sync_upcoming_launches(limit=self.limit)
            elif self.sync_type == 'previous':
                self.progress.emit("Fetching previous launches...")
                result = api.sync_previous_launches(limit=self.limit)
            elif self.sync_type == 'rockets':
                self.progress.emit("Updating rocket details...")
                result = api.sync_rocket_details()
            else:
                result = {'added': 0, 'updated': 0, 'errors': []}
            
            # Close the database connection
            db.close()
            
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({'added': 0, 'updated': 0, 'errors': [str(e)]})


class LaunchEditorDialog(QDialog):
    """Dialog for adding/editing launch records"""
    
    def __init__(self, db: LaunchDatabase, launch_id: int = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.launch_id = launch_id
        self.init_ui()
        
        if launch_id:
            self.load_launch_data()
    
    def init_ui(self):
        self.setWindowTitle("Launch Editor" if not self.launch_id else "Edit Launch")
        self.setMinimumWidth(600)
        
        layout = QFormLayout()
        
        # Date and Time
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        layout.addRow("Launch Date:", self.date_edit)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss")
        layout.addRow("Launch Time:", self.time_edit)
        
        # Launch Site
        self.site_combo = QComboBox()
        self.site_combo.setEditable(True)
        sites = self.db.get_all_sites()
        for site in sites:
            self.site_combo.addItem(f"{site['location']} - {site['launch_pad']}", site['site_id'])
        layout.addRow("Launch Site:", self.site_combo)
        
        # Add Site button
        add_site_btn = QPushButton("Add New Site...")
        add_site_btn.clicked.connect(self.add_new_site)
        layout.addRow("", add_site_btn)
        
        # Rocket
        self.rocket_combo = QComboBox()
        self.rocket_combo.setEditable(True)
        rockets = self.db.get_all_rockets()
        for rocket in rockets:
            self.rocket_combo.addItem(rocket['name'], rocket['rocket_id'])
        layout.addRow("Rocket:", self.rocket_combo)
        
        # Add Rocket button
        add_rocket_btn = QPushButton("Add New Rocket...")
        add_rocket_btn.clicked.connect(self.add_new_rocket)
        layout.addRow("", add_rocket_btn)
        
        # Mission Details
        self.mission_edit = QLineEdit()
        layout.addRow("Mission Name:", self.mission_edit)
        
        self.payload_edit = QLineEdit()
        layout.addRow("Payload:", self.payload_edit)
        
        # Orbit
        self.orbit_combo = QComboBox()
        self.orbit_combo.addItems(['LEO', 'SSO', 'GTO', 'GEO', 'MEO', 'HEO', 'Lunar', 'Other'])
        layout.addRow("Orbit Type:", self.orbit_combo)
        
        # NOTAM
        self.notam_edit = QLineEdit()
        self.notam_edit.setPlaceholderText("e.g., A1234/25")
        layout.addRow("NOTAM Reference:", self.notam_edit)
        
        # Status
        self.status_combo = QComboBox()
        statuses = self.db.get_all_statuses()
        for status in statuses:
            self.status_combo.addItem(status['status_name'], status['status_id'])
        layout.addRow("Status:", self.status_combo)
        
        # Remarks
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setMaximumHeight(100)
        layout.addRow("Remarks:", self.remarks_edit)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_launch)
        button_box.rejected.connect(self.reject)
        
        layout.addRow(button_box)
        self.setLayout(layout)
    
    def load_launch_data(self):
        """Load existing launch data"""
        launches = self.db.get_launches_by_date_range('1900-01-01', '2100-01-01')
        launch = next((l for l in launches if l['launch_id'] == self.launch_id), None)
        
        if launch:
            if launch['launch_date']:
                date_obj = datetime.strptime(launch['launch_date'], '%Y-%m-%d')
                self.date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
            
            if launch['launch_time']:
                time_obj = datetime.strptime(launch['launch_time'], '%H:%M:%S').time()
                self.time_edit.setTime(QTime(time_obj.hour, time_obj.minute, time_obj.second))
            
            if launch['site_id']:
                index = self.site_combo.findData(launch['site_id'])
                if index >= 0:
                    self.site_combo.setCurrentIndex(index)
            
            if launch['rocket_id']:
                index = self.rocket_combo.findData(launch['rocket_id'])
                if index >= 0:
                    self.rocket_combo.setCurrentIndex(index)
            
            if launch['status_id']:
                index = self.status_combo.findData(launch['status_id'])
                if index >= 0:
                    self.status_combo.setCurrentIndex(index)
            
            self.mission_edit.setText(launch.get('mission_name') or '')
            self.payload_edit.setText(launch.get('payload_name') or '')
            self.notam_edit.setText(launch.get('notam_reference') or '')
            
            if launch.get('orbit_type'):
                index = self.orbit_combo.findText(launch['orbit_type'])
                if index >= 0:
                    self.orbit_combo.setCurrentIndex(index)
            
            self.remarks_edit.setPlainText(launch.get('remarks') or '')
    
    def add_new_site(self):
        """Open dialog to add a new launch site"""
        from PyQt6.QtWidgets import QDoubleSpinBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Launch Site")
        dialog.setModal(True)
        
        layout = QFormLayout()
        
        location_edit = QLineEdit()
        location_edit.setPlaceholderText("e.g., Cape Canaveral, Vandenberg")
        layout.addRow("Location:", location_edit)
        
        pad_edit = QLineEdit()
        pad_edit.setPlaceholderText("e.g., LC-39A, SLC-4E")
        layout.addRow("Launch Pad:", pad_edit)
        
        country_edit = QLineEdit()
        country_edit.setPlaceholderText("e.g., USA, China, Russia")
        layout.addRow("Country:", country_edit)
        
        lat_spin = QDoubleSpinBox()
        lat_spin.setRange(-90, 90)
        lat_spin.setDecimals(4)
        lat_spin.setSuffix("°")
        layout.addRow("Latitude:", lat_spin)
        
        lon_spin = QDoubleSpinBox()
        lon_spin.setRange(-180, 180)
        lon_spin.setDecimals(4)
        lon_spin.setSuffix("°")
        layout.addRow("Longitude:", lon_spin)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save new site
            site_data = {
                'location': location_edit.text(),
                'launch_pad': pad_edit.text(),
                'country': country_edit.text(),
                'latitude': lat_spin.value() if lat_spin.value() != 0 else None,
                'longitude': lon_spin.value() if lon_spin.value() != 0 else None,
                'site_type': 'LAUNCH'
            }
            
            try:
                site_id = self.db.add_site(site_data)
                
                # Add to combo box
                display = f"{site_data['location']} - {site_data['launch_pad']}"
                self.site_combo.addItem(display, site_id)
                self.site_combo.setCurrentIndex(self.site_combo.count() - 1)
                
                QMessageBox.information(self, "Success", "Launch site added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add site: {e}")
    
    def add_new_rocket(self):
        """Open dialog to add a new rocket"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Rocket")
        dialog.setModal(True)
        
        layout = QFormLayout()
        
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("e.g., Falcon 9 Block 5, Long March 2D")
        layout.addRow("Rocket Name:", name_edit)
        
        family_edit = QLineEdit()
        family_edit.setPlaceholderText("e.g., Falcon, Long March")
        layout.addRow("Family (optional):", family_edit)
        
        variant_edit = QLineEdit()
        variant_edit.setPlaceholderText("e.g., Block 5, CZ-2D")
        layout.addRow("Variant (optional):", variant_edit)
        
        country_edit = QLineEdit()
        country_edit.setPlaceholderText("e.g., USA, China, Russia")
        layout.addRow("Country (optional):", country_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            rocket_name = name_edit.text().strip()
            
            if not rocket_name:
                QMessageBox.warning(self, "Validation Error", "Please enter a rocket name.")
                return
            
            # Save new rocket
            rocket_data = {
                'name': rocket_name,
                'family': family_edit.text().strip() or None,
                'variant': variant_edit.text().strip() or None,
                'country': country_edit.text().strip() or None
            }
            
            try:
                rocket_id = self.db.add_rocket(rocket_data)
                
                # Add to combo box
                self.rocket_combo.addItem(rocket_name, rocket_id)
                self.rocket_combo.setCurrentIndex(self.rocket_combo.count() - 1)
                
                QMessageBox.information(self, "Success", "Rocket added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add rocket: {e}")
    
    def save_launch(self):
        """Save launch data"""
        
        # Get site_id (if selected from dropdown)
        site_id = self.site_combo.currentData()
        
        # If site was typed in manually, create it
        if site_id is None and self.site_combo.currentText().strip():
            site_text = self.site_combo.currentText().strip()
            # Quick site creation - parse "Location - Pad" format
            parts = site_text.split('-', 1)
            location = parts[0].strip() if parts else site_text
            pad = parts[1].strip() if len(parts) > 1 else "Main Pad"
            
            site_data = {
                'location': location,
                'launch_pad': pad,
                'country': None,
                'latitude': None,
                'longitude': None,
                'site_type': 'LAUNCH'
            }
            
            try:
                site_id = self.db.add_site(site_data)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create site: {e}")
                return
        
        # Get rocket_id (if selected from dropdown)
        rocket_id = self.rocket_combo.currentData()
        
        # If rocket was typed in manually, create it
        if rocket_id is None and self.rocket_combo.currentText().strip():
            rocket_name = self.rocket_combo.currentText().strip()
            
            rocket_data = {
                'name': rocket_name,
                'family': None,
                'variant': None,
                'country': None
            }
            
            try:
                rocket_id = self.db.add_rocket(rocket_data)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create rocket: {e}")
                return
        
        # Validate we have required data
        if not site_id:
            QMessageBox.warning(self, "Validation Error", "Please select or enter a launch site.")
            return
        
        if not rocket_id:
            QMessageBox.warning(self, "Validation Error", "Please select or enter a rocket.")
            return
        
        launch_data = {
            'launch_date': self.date_edit.date().toString('yyyy-MM-dd'),
            'launch_time': self.time_edit.time().toString('HH:mm:ss'),
            'site_id': site_id,
            'rocket_id': rocket_id,
            'mission_name': self.mission_edit.text(),
            'payload_name': self.payload_edit.text(),
            'orbit_type': self.orbit_combo.currentText(),
            'status_id': self.status_combo.currentData(),
            'notam_reference': self.notam_edit.text(),
            'remarks': self.remarks_edit.toPlainText(),
            'data_source': 'MANUAL'
        }
        
        try:
            if self.launch_id:
                self.db.update_launch(self.launch_id, launch_data)
                QMessageBox.information(self, "Success", "Launch updated successfully!")
            else:
                self.db.add_launch(launch_data)
                QMessageBox.information(self, "Success", "Launch added successfully!")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save launch: {e}")


class MainWindow(QMainWindow):
    """Main application window for SHOCKWAVE PLANNER v2.0"""
    
    def __init__(self):
        super().__init__()
        self.db = LaunchDatabase()
        self.sync_worker = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("SHOCKWAVE PLANNER v2.0 - Launch Operations Planning System")
        self.setGeometry(100, 100, 1600, 900)
        
        # Menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_launch_action = QAction('New Launch', self)
        new_launch_action.setShortcut('Ctrl+N')
        new_launch_action.triggered.connect(self.new_launch)
        file_menu.addAction(new_launch_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        refresh_action = QAction('Refresh', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_all)
        view_menu.addAction(refresh_action)
        
        # Data menu
        data_menu = menubar.addMenu('Data')
        
        sync_upcoming_action = QAction('Sync Upcoming Launches (Space Devs)', self)
        sync_upcoming_action.triggered.connect(self.sync_upcoming_launches)
        data_menu.addAction(sync_upcoming_action)
        
        sync_previous_action = QAction('Sync Previous Launches (Space Devs)', self)
        sync_previous_action.triggered.connect(self.sync_previous_launches)
        data_menu.addAction(sync_previous_action)
        
        data_menu.addSeparator()
        
        sync_rockets_action = QAction('Sync Rocket Details (Space Devs)', self)
        sync_rockets_action.triggered.connect(self.sync_rocket_details)
        data_menu.addAction(sync_rockets_action)
        
        data_menu.addSeparator()
        
        sync_history_action = QAction('View Sync History', self)
        sync_history_action.triggered.connect(self.show_sync_history)
        data_menu.addAction(sync_history_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Master Activity Schedule - Launch
        self.timeline_view = TimelineView(self.db)
        self.timeline_view.launch_selected.connect(self.edit_launch)
        self.tab_widget.addTab(self.timeline_view, "Master Activity Schedule - Launch")
        
        # Master Activity Schedule - Re-entry  
        self.reentry_timeline_view = ReentryTimelineView(self.db)
        self.reentry_timeline_view.reentry_selected.connect(self.edit_reentry)
        self.tab_widget.addTab(self.reentry_timeline_view, "Master Activity Schedule - Re-entry")
        
        # Enhanced List view
        self.list_view = EnhancedListView(self.db)
        self.list_view.launch_selected.connect(self.edit_launch)
        self.tab_widget.addTab(self.list_view, "Launch List View")
        
        # Statistics view
        stats_widget = self.create_statistics_widget()
        self.tab_widget.addTab(stats_widget, "Launch Statistics")
        
        # Launch Sites view
        self.sites_view = LaunchSitesView(self.db, parent=self)
        self.tab_widget.addTab(self.sites_view, "Launch Sites")
        
        # Drop Zones view
        self.drop_zones_view = DropZonesView(self.db, parent=self)
        self.tab_widget.addTab(self.drop_zones_view, "Drop Zones")
        
        # Rockets view
        self.rockets_view = RocketsView(self.db, parent=self)
        self.tab_widget.addTab(self.rockets_view, "Launch Vehicles")
        # Re-entry vehicle view
        self.reentry_vehicles_tab = ReentryVehiclesView(self.db)
        self.tab_widget.addTab(self.reentry_vehicles_tab, "Re-entry Vehicles")
        
        main_layout.addWidget(self.tab_widget)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        new_btn = QPushButton("+ New Launch")
        new_btn.clicked.connect(self.new_launch)
        button_layout.addWidget(new_btn)
        
        new_reentry_btn = QPushButton("+ New Re-entry")
        new_reentry_btn.clicked.connect(self.new_reentry)
        button_layout.addWidget(new_reentry_btn)
        
        sync_btn = QPushButton("🔄 Sync Space Devs")
        sync_btn.clicked.connect(self.sync_upcoming_launches)
        button_layout.addWidget(sync_btn)
        
        refresh_btn = QPushButton("♻️ Refresh")
        refresh_btn.clicked.connect(self.refresh_all)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        # Version label
        version_label = QLabel("v2.0.0")
        version_label.setStyleSheet("color: gray; font-weight: bold;")
        button_layout.addWidget(version_label)
        
        main_layout.addLayout(button_layout)
        
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready - SHOCKWAVE PLANNER v2.0")
    
    def create_statistics_widget(self):
        """Create statistics display"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        stats = self.db.get_statistics()
        
        overview_group = QGroupBox("Launch Overview")
        overview_layout = QFormLayout()
        overview_layout.addRow("Total Launches:", QLabel(str(stats['total_launches'])))
        overview_layout.addRow("Successful:", QLabel(str(stats['successful'])))
        overview_layout.addRow("Failed:", QLabel(str(stats['failed'])))
        overview_layout.addRow("Pending:", QLabel(str(stats['pending'])))
        
        success_rate = 0
        if stats['successful'] + stats['failed'] > 0:
            success_rate = (stats['successful'] / (stats['successful'] + stats['failed'])) * 100
        overview_layout.addRow("Success Rate:", QLabel(f"{success_rate:.1f}%"))
        
        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)
        
        rockets_group = QGroupBox("Top 10 Rockets")
        rockets_layout = QVBoxLayout()
        rockets_text = QTextEdit()
        rockets_text.setReadOnly(True)
        rocket_stats = "\n".join([f"{r['name']}: {r['count']} launches" 
                                 for r in stats['by_rocket']])
        rockets_text.setPlainText(rocket_stats if rocket_stats else "No data")
        rockets_layout.addWidget(rockets_text)
        rockets_group.setLayout(rockets_layout)
        layout.addWidget(rockets_group)
        
        sites_group = QGroupBox("Launches by Site")
        sites_layout = QVBoxLayout()
        sites_text = QTextEdit()
        sites_text.setReadOnly(True)
        site_stats = "\n".join([f"{s['location']}: {s['count']} launches" 
                               for s in stats['by_site']])
        sites_text.setPlainText(site_stats if site_stats else "No data")
        sites_layout.addWidget(sites_text)
        sites_group.setLayout(sites_layout)
        layout.addWidget(sites_group)
        
        # Sync status
        last_sync = self.db.get_last_sync('SPACE_DEVS_UPCOMING')
        if last_sync:
            sync_group = QGroupBox("Last Space Devs Sync")
            sync_layout = QFormLayout()
            sync_time = datetime.fromisoformat(last_sync['sync_time']).strftime('%Y-%m-%d %H:%M:%S')
            sync_layout.addRow("Time:", QLabel(sync_time))
            sync_layout.addRow("Added:", QLabel(str(last_sync['records_added'])))
            sync_layout.addRow("Updated:", QLabel(str(last_sync['records_updated'])))
            sync_layout.addRow("Status:", QLabel(last_sync['status']))
            sync_group.setLayout(sync_layout)
            layout.addWidget(sync_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        
        return widget
    
    def new_launch(self):
        """Create new launch"""
        dialog = LaunchEditorDialog(self.db, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_all()
            self.statusBar().showMessage("Launch added successfully", 3000)
    
    def new_reentry(self):
        """Create new re-entry"""
        dialog = ReentryDialog(self.db, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_all()
            self.statusBar().showMessage("Re-entry added successfully", 3000)
    
    def edit_launch(self, launch_id: int):
        """Edit existing launch"""
        dialog = LaunchEditorDialog(self.db, launch_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_all()
            self.statusBar().showMessage("Launch updated successfully", 3000)
    
    def edit_reentry(self, reentry_id: int):
        """Edit existing re-entry"""
        dialog = ReentryDialog(self.db, parent=self, reentry_id=reentry_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_all()
            self.statusBar().showMessage("Re-entry updated successfully", 3000)
    
    def sync_upcoming_launches(self):
        """Sync upcoming launches from Space Devs"""
        reply = QMessageBox.question(
            self,
            'Sync Upcoming Launches',
            'Fetch upcoming launches from The Space Devs API?\n\n'
            'This will download up to 100 upcoming launches and merge them with existing data.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_sync('upcoming', 100)
    
    def sync_previous_launches(self):
        """Sync previous launches from Space Devs"""
        reply = QMessageBox.question(
            self,
            'Sync Previous Launches',
            'Fetch previous launches from The Space Devs API?\n\n'
            'This will download up to 50 recent previous launches for historical data.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_sync('previous', 50)
    
    def sync_rocket_details(self):
        """Sync rocket details from Space Devs"""
        rockets_count = len(self.db.get_all_rockets())
        
        reply = QMessageBox.question(
            self,
            'Sync Rocket Details',
            f'Update rocket details from The Space Devs API?\n\n'
            f'This will fetch family, variant, manufacturer, and country\n'
            f'for {rockets_count} rockets in your database.\n\n'
            f'Note: Only rockets synced from Space Devs can be updated.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_sync('rockets', 0)
    
    def start_sync(self, sync_type: str, limit: int):
        """Start background sync"""
        self.sync_worker = SyncWorker(self.db.db_path, sync_type, limit)
        self.sync_worker.finished.connect(self.sync_finished)
        self.sync_worker.progress.connect(lambda msg: self.statusBar().showMessage(msg))
        
        self.statusBar().showMessage(f"Syncing {sync_type} launches...")
        self.sync_worker.start()
    
    def sync_finished(self, result: dict):
        """Handle sync completion"""
        self.refresh_all()
        
        message = f"Sync Complete!\n\n"
        
        # Handle different sync types
        if 'added' in result:
            message += f"Added: {result['added']}\n"
        if 'updated' in result:
            message += f"Updated: {result['updated']}\n"
        
        if result.get('errors'):
            message += f"\nErrors: {len(result['errors'])}"
            QMessageBox.warning(self, "Sync Complete (with errors)", message)
        else:
            QMessageBox.information(self, "Sync Complete", message)
        
        # Status bar message
        if 'added' in result and 'updated' in result:
            self.statusBar().showMessage(f"Sync complete: {result['added']} added, {result['updated']} updated", 5000)
        elif 'updated' in result:
            self.statusBar().showMessage(f"Sync complete: {result['updated']} updated", 5000)
        else:
            self.statusBar().showMessage("Sync complete", 5000)
    
    def show_sync_history(self):
        """Show sync history"""
        QMessageBox.information(
            self,
            "Sync History",
            "Sync history viewer coming soon!\n\n"
            "For now, check the sync_log table in the database directly."
        )
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About SHOCKWAVE PLANNER",
            "<h2>SHOCKWAVE PLANNER v2.0</h2>"
            "<p><b>Desktop Launch Operations Planning System</b></p>"
            "<p>Created for Remix Astronautics</p>"
            "<p>Built with Python & PyQt6</p>"
            "<br>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Comprehensive launch tracking</li>"
            "<li>Re-entry operations management</li>"
            "<li>Space Devs API integration</li>"
            "<li>Timeline visualization</li>"
            "<li>NOTAM tracking</li>"
            "</ul>"
            "<br>"
            "<p>Author: Remix Astronautics</p>"
            "<p>December 2025</p>"
        )
    
    def refresh_all(self):
        """Refresh all views"""
        # Update all pad turnarounds from launch history
        self.db.update_all_pad_turnarounds_from_history()
        
        self.timeline_view.update_timeline()
        self.reentry_timeline_view.update_timeline()
        self.list_view.refresh()
        self.sites_view.refresh_table()
        self.drop_zones_view.refresh_table()
        self.rockets_view.refresh_table()
        self.reentry_vehicles_tab.refresh_table()
        
        # Recreate statistics tab
        stats_widget = self.create_statistics_widget()
        self.tab_widget.removeTab(3)
        self.tab_widget.insertTab(3, stats_widget, "📊 Statistics")
        
        self.statusBar().showMessage("Refreshed", 2000)
    
    def closeEvent(self, event):
        """Handle window close"""
        self.db.close()
        event.accept()

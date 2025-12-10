"""
SHOCKWAVE PLANNER v2.0 - Drop Zones Management View
View, edit, and delete re-entry drop zones

Author: Remix Astronautics
Date: December 2025
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QDialog, QFormLayout, QLineEdit,
                              QDialogButtonBox, QDoubleSpinBox, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt


class DropZonesView(QWidget):
    """Management view for re-entry drop zones"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("+ Add Drop Zone")
        add_btn.clicked.connect(self.add_zone)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ Edit Selected")
        edit_btn.clicked.connect(self.edit_zone)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.clicked.connect(self.delete_zone)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_table)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Location', 'Drop Zone', 'Country', 'Recovery (days)', 'Latitude', 'Longitude'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_zone)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.refresh_table()
    
    def refresh_table(self):
        """Refresh the zones table"""
        zones = self.db.get_all_sites(site_type='REENTRY')
        
        self.table.setRowCount(len(zones))
        
        for row, zone in enumerate(zones):
            self.table.setItem(row, 0, QTableWidgetItem(str(zone.get('site_id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(zone.get('location', '')))
            self.table.setItem(row, 2, QTableWidgetItem(zone.get('launch_pad', '')))  # launch_pad is aliased to drop_zone
            self.table.setItem(row, 3, QTableWidgetItem(zone.get('country', '')))
            
            # Recovery time
            turnaround = zone.get('turnaround_days', 7)
            self.table.setItem(row, 4, QTableWidgetItem(str(turnaround)))
            
            lat = zone.get('latitude')
            self.table.setItem(row, 5, QTableWidgetItem(f"{lat:.4f}°" if lat else ''))
            
            lon = zone.get('longitude')
            self.table.setItem(row, 6, QTableWidgetItem(f"{lon:.4f}°" if lon else ''))
    
    def add_zone(self):
        """Add a new drop zone"""
        dialog = ZoneEditorDialog(self.db, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.window():
                self.window().refresh_all()
    
    def edit_zone(self):
        """Edit the selected zone"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a drop zone to edit.")
            return
        
        zone_id = int(self.table.item(current_row, 0).text())
        dialog = ZoneEditorDialog(self.db, zone_id=zone_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.window():
                self.window().refresh_all()
    
    def delete_zone(self):
        """Delete the selected zone"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a drop zone to delete.")
            return
        
        zone_id = int(self.table.item(current_row, 0).text())
        location = self.table.item(current_row, 1).text()
        zone = self.table.item(current_row, 2).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this drop zone?\n\n{location} - {zone}\n\n"
            "This will NOT delete re-entries from this zone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_site(zone_id, site_type='REENTRY')
                self.refresh_table()
                if self.window():
                    self.window().refresh_all()
                QMessageBox.information(self, "Success", "Drop zone deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete drop zone: {e}")


class ZoneEditorDialog(QDialog):
    """Dialog for adding/editing drop zones"""
    
    def __init__(self, db, zone_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.zone_id = zone_id
        self.setWindowTitle("Add Drop Zone" if not zone_id else "Edit Drop Zone")
        self.setModal(True)
        self.init_ui()
        
        if zone_id:
            self.load_zone_data()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QFormLayout()
        
        # Location
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("e.g., Pacific Ocean, Atlantic Ocean, Inner Mongolia")
        layout.addRow("Region/Location:", self.location_edit)
        
        # Drop Zone
        self.zone_edit = QLineEdit()
        self.zone_edit.setPlaceholderText("e.g., Zone A, LZ-1, Recovery Area 3")
        layout.addRow("Drop Zone:", self.zone_edit)
        
        # Country
        self.country_edit = QLineEdit()
        self.country_edit.setPlaceholderText("e.g., USA, China, Russia")
        layout.addRow("Country:", self.country_edit)
        
        # Recovery Time
        self.recovery_spin = QSpinBox()
        self.recovery_spin.setRange(1, 90)
        self.recovery_spin.setValue(7)
        self.recovery_spin.setSuffix(" days")
        self.recovery_spin.setToolTip("Number of days required for zone recovery/cleanup after re-entry")
        layout.addRow("Zone Recovery:", self.recovery_spin)
        
        # Latitude
        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(-90, 90)
        self.lat_spin.setDecimals(4)
        self.lat_spin.setSuffix("°")
        self.lat_spin.setSpecialValueText("Not Set")
        layout.addRow("Latitude:", self.lat_spin)
        
        # Longitude
        self.lon_spin = QDoubleSpinBox()
        self.lon_spin.setRange(-180, 180)
        self.lon_spin.setDecimals(4)
        self.lon_spin.setSuffix("°")
        self.lon_spin.setSpecialValueText("Not Set")
        layout.addRow("Longitude:", self.lon_spin)
        
        # Zone Type (optional)
        self.zone_type_edit = QLineEdit()
        self.zone_type_edit.setPlaceholderText("e.g., Ocean, Land, Desert (optional)")
        layout.addRow("Zone Type:", self.zone_type_edit)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_zone)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def load_zone_data(self):
        """Load existing zone data"""
        zones = self.db.get_all_sites(site_type='REENTRY')
        zone = next((z for z in zones if z['site_id'] == self.zone_id), None)
        
        if zone:
            self.location_edit.setText(zone.get('location', ''))
            self.zone_edit.setText(zone.get('launch_pad', ''))  # launch_pad is aliased to drop_zone
            self.country_edit.setText(zone.get('country', ''))
            
            # Recovery time
            if zone.get('turnaround_days'):
                self.recovery_spin.setValue(zone['turnaround_days'])
            
            if zone.get('latitude'):
                self.lat_spin.setValue(zone['latitude'])
            
            if zone.get('longitude'):
                self.lon_spin.setValue(zone['longitude'])
            
            # Zone type (if available from database)
            if zone.get('zone_type'):
                self.zone_type_edit.setText(zone['zone_type'])
    
    def save_zone(self):
        """Save the drop zone"""
        location = self.location_edit.text().strip()
        zone = self.zone_edit.text().strip()
        
        if not location or not zone:
            QMessageBox.warning(self, "Validation Error", 
                              "Please enter both location and drop zone.")
            return
        
        zone_data = {
            'location': location,
            'drop_zone': zone,
            'country': self.country_edit.text().strip() or None,
            'turnaround_days': self.recovery_spin.value(),
            'latitude': self.lat_spin.value() if self.lat_spin.value() != 0 else None,
            'longitude': self.lon_spin.value() if self.lon_spin.value() != 0 else None,
            'zone_type': self.zone_type_edit.text().strip() or None,
            'site_type': 'REENTRY'
        }
        
        try:
            if self.zone_id:
                self.db.update_site(self.zone_id, zone_data)
                QMessageBox.information(self, "Success", "Drop zone updated successfully!")
            else:
                self.db.add_site(zone_data, site_type='REENTRY')
                QMessageBox.information(self, "Success", "Drop zone added successfully!")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save drop zone: {e}")

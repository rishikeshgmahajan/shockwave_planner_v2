"""
SHOCKWAVE PLANNER v2.0 - Launch Sites Management View
View, edit, and delete launch sites

Author: Remix Astronautics
Date: December 2025
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QDialog, QFormLayout, QLineEdit,
                              QDialogButtonBox, QDoubleSpinBox, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt


class LaunchSitesView(QWidget):
    """Management view for launch sites"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("+ Add Launch Site")
        add_btn.clicked.connect(self.add_site)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ Edit Selected")
        edit_btn.clicked.connect(self.edit_site)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.clicked.connect(self.delete_site)
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
            'ID', 'Location', 'Launch Pad', 'Country', 'Turnaround (days)', 'Latitude', 'Longitude'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_site)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.refresh_table()
    
    def refresh_table(self):
        """Refresh the sites table"""
        sites = self.db.get_all_sites(site_type='LAUNCH')
        
        self.table.setRowCount(len(sites))
        
        for row, site in enumerate(sites):
            self.table.setItem(row, 0, QTableWidgetItem(str(site.get('site_id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(site.get('location', '')))
            self.table.setItem(row, 2, QTableWidgetItem(site.get('launch_pad', '')))
            self.table.setItem(row, 3, QTableWidgetItem(site.get('country', '')))
            
            # Turnaround days
            turnaround = site.get('turnaround_days', 7)
            self.table.setItem(row, 4, QTableWidgetItem(str(turnaround)))
            
            lat = site.get('latitude')
            self.table.setItem(row, 5, QTableWidgetItem(f"{lat:.4f}°" if lat else ''))
            
            lon = site.get('longitude')
            self.table.setItem(row, 6, QTableWidgetItem(f"{lon:.4f}°" if lon else ''))
    
    def add_site(self):
        """Add a new launch site"""
        dialog = SiteEditorDialog(self.db, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.window():
                self.window().refresh_all()
    
    def edit_site(self):
        """Edit the selected site"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a site to edit.")
            return
        
        site_id = int(self.table.item(current_row, 0).text())
        dialog = SiteEditorDialog(self.db, site_id=site_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.window():
                self.window().refresh_all()
    
    def delete_site(self):
        """Delete the selected site"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a site to delete.")
            return
        
        site_id = int(self.table.item(current_row, 0).text())
        location = self.table.item(current_row, 1).text()
        pad = self.table.item(current_row, 2).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this site?\n\n{location} - {pad}\n\n"
            "This will NOT delete launches from this site.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_site(site_id)
                self.refresh_table()
                if self.window():
                    self.window().refresh_all()
                QMessageBox.information(self, "Success", "Site deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete site: {e}")


class SiteEditorDialog(QDialog):
    """Dialog for adding/editing launch sites"""
    
    def __init__(self, db, site_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.site_id = site_id
        self.setWindowTitle("Add Launch Site" if not site_id else "Edit Launch Site")
        self.setModal(True)
        self.init_ui()
        
        if site_id:
            self.load_site_data()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QFormLayout()
        
        # Location
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("e.g., Cape Canaveral, Vandenberg, Jiuquan")
        layout.addRow("Location:", self.location_edit)
        
        # Launch Pad
        self.pad_edit = QLineEdit()
        self.pad_edit.setPlaceholderText("e.g., LC-39A, SLC-4E, LC-43/95")
        layout.addRow("Launch Pad:", self.pad_edit)
        
        # Country
        self.country_edit = QLineEdit()
        self.country_edit.setPlaceholderText("e.g., USA, China, Russia")
        layout.addRow("Country:", self.country_edit)
        
        # Turnaround Days
        self.turnaround_spin = QSpinBox()
        self.turnaround_spin.setRange(1, 90)
        self.turnaround_spin.setValue(7)
        self.turnaround_spin.setSuffix(" days")
        self.turnaround_spin.setToolTip("Number of days required between launches at this pad")
        layout.addRow("Pad Turnaround:", self.turnaround_spin)
        
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
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_site)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def load_site_data(self):
        """Load existing site data"""
        sites = self.db.get_all_sites()
        site = next((s for s in sites if s['site_id'] == self.site_id), None)
        
        if site:
            self.location_edit.setText(site.get('location', ''))
            self.pad_edit.setText(site.get('launch_pad', ''))
            self.country_edit.setText(site.get('country', ''))
            
            # Turnaround days
            if site.get('turnaround_days'):
                self.turnaround_spin.setValue(site['turnaround_days'])
            
            if site.get('latitude'):
                self.lat_spin.setValue(site['latitude'])
            
            if site.get('longitude'):
                self.lon_spin.setValue(site['longitude'])
    
    def save_site(self):
        """Save the site"""
        location = self.location_edit.text().strip()
        pad = self.pad_edit.text().strip()
        
        if not location or not pad:
            QMessageBox.warning(self, "Validation Error", 
                              "Please enter both location and launch pad.")
            return
        
        site_data = {
            'location': location,
            'launch_pad': pad,
            'country': self.country_edit.text().strip() or None,
            'turnaround_days': self.turnaround_spin.value(),
            'latitude': self.lat_spin.value() if self.lat_spin.value() != 0 else None,
            'longitude': self.lon_spin.value() if self.lon_spin.value() != 0 else None,
            'site_type': 'LAUNCH'
        }
        
        try:
            if self.site_id:
                self.db.update_site(self.site_id, site_data)
                QMessageBox.information(self, "Success", "Site updated successfully!")
            else:
                self.db.add_site(site_data)
                QMessageBox.information(self, "Success", "Site added successfully!")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save site: {e}")

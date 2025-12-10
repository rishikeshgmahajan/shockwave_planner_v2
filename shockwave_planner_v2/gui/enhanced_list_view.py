"""
SHOCKWAVE PLANNER v1.1 - Enhanced List View
With quick date range filters and NOTAM field
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                              QTableWidgetItem, QLabel, QLineEdit, QComboBox,
                              QPushButton, QHeaderView, QGroupBox, QDateEdit)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor
from datetime import datetime, timedelta


class EnhancedListView(QWidget):
    """
    List view with quick date range filters
    - Previous 7 days
    - Previous 30 days
    - Current (today)
    - Next 30 days
    - Custom range
    """
    
    launch_selected = pyqtSignal(int)
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_filter = 'current'
        self.custom_start = None
        self.custom_end = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Filters section
        filter_group = QGroupBox("Filters")
        filter_layout = QVBoxLayout()
        
        # Date range filter
        date_range_layout = QHBoxLayout()
        date_range_layout.addWidget(QLabel("Date Range:"))
        
        self.date_range_combo = QComboBox()
        self.date_range_combo.addItems([
            "Previous 7 Days",
            "Previous 30 Days", 
            "Current (Today)",
            "Next 30 Days",
            "Custom Range..."
        ])
        self.date_range_combo.setCurrentIndex(2)  # Default to "Current"
        self.date_range_combo.currentIndexChanged.connect(self.on_date_range_changed)
        date_range_layout.addWidget(self.date_range_combo)
        
        # Custom range inputs (hidden by default)
        self.custom_range_widget = QWidget()
        custom_layout = QHBoxLayout()
        custom_layout.setContentsMargins(0, 0, 0, 0)
        
        custom_layout.addWidget(QLabel("From:"))
        self.custom_start_date = QDateEdit()
        self.custom_start_date.setCalendarPopup(True)
        self.custom_start_date.setDate(QDate.currentDate().addDays(-30))
        custom_layout.addWidget(self.custom_start_date)
        
        custom_layout.addWidget(QLabel("To:"))
        self.custom_end_date = QDateEdit()
        self.custom_end_date.setCalendarPopup(True)
        self.custom_end_date.setDate(QDate.currentDate().addDays(30))
        custom_layout.addWidget(self.custom_end_date)
        
        self.apply_custom_btn = QPushButton("Apply")
        self.apply_custom_btn.clicked.connect(self.apply_custom_range)
        custom_layout.addWidget(self.apply_custom_btn)
        
        self.custom_range_widget.setLayout(custom_layout)
        self.custom_range_widget.setVisible(False)
        
        date_range_layout.addStretch()
        filter_layout.addLayout(date_range_layout)
        filter_layout.addWidget(self.custom_range_widget)
        
        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by mission, payload, rocket, or NOTAM...")
        self.search_edit.textChanged.connect(self.perform_search)
        search_layout.addWidget(self.search_edit)
        
        filter_layout.addLayout(search_layout)
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Launch table
        self.launch_table = QTableWidget()
        self.launch_table.setColumnCount(9)
        self.launch_table.setHorizontalHeaderLabels([
            'Date', 'Time', 'Site', 'Rocket', 'Mission', 
            'Payload', 'Orbit','NOTAM', 'Status'
        ])
        self.launch_table.verticalHeader().setDefaultSectionSize(45)
        self.launch_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.launch_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.launch_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.launch_table.cellDoubleClicked.connect(self.on_launch_double_clicked)
        self.launch_table.setStyleSheet("""
            QTableWidget {
                font-size: 17px;
            }
            QHeaderView::section {
                font-size: 12px;
                font-weight: bold;
                height: 35px;
            }
        """)
        
        layout.addWidget(self.launch_table)
        
        # Status bar
        self.status_label = QLabel("Loading...")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.load_launches()
    
    def get_date_range(self):
        """Get start and end dates based on current filter"""
        today = datetime.now().date()
        
        if self.current_filter == 'previous_7':
            start = today - timedelta(days=7)
            end = today
        elif self.current_filter == 'previous_30':
            start = today - timedelta(days=30)
            end = today
        elif self.current_filter == 'current':
            start = today
            end = today
        elif self.current_filter == 'next_30':
            start = today
            end = today + timedelta(days=30)
        elif self.current_filter == 'custom':
            start = self.custom_start
            end = self.custom_end
        else:
            start = today - timedelta(days=30)
            end = today + timedelta(days=30)
        
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
    
    def on_date_range_changed(self, index):
        """Handle date range selection change"""
        filters = ['previous_7', 'previous_30', 'current', 'next_30', 'custom']
        self.current_filter = filters[index]
        
        # Show/hide custom range inputs
        self.custom_range_widget.setVisible(self.current_filter == 'custom')
        
        if self.current_filter != 'custom':
            self.load_launches()
    
    def apply_custom_range(self):
        """Apply custom date range"""
        self.custom_start = self.custom_start_date.date().toPyDate()
        self.custom_end = self.custom_end_date.date().toPyDate()
        self.load_launches()
    
    def load_launches(self, launches=None):
        """Load launches into table"""
        if launches is None:
            # Get launches for current date range
            start_date, end_date = self.get_date_range()
            launches = self.db.get_launches_by_date_range(start_date, end_date)
        
        self.launch_table.setRowCount(len(launches))

        def create_centered_item(text):
            item = QTableWidgetItem(str(text))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) 
            return item
        
        for row, launch in enumerate(launches):
            # Date
            self.launch_table.setItem(row, 0, create_centered_item(launch.get('launch_date', '')))
            
            # Time
            time_str = launch.get('launch_time', '')[:5] if launch.get('launch_time') else ''
            self.launch_table.setItem(row, 1, create_centered_item(time_str))
            
            # Site
            site_str = f"{launch.get('location', '')} {launch.get('launch_pad', '')}"
            self.launch_table.setItem(row, 2, create_centered_item(site_str))
            
            # Rocket
            self.launch_table.setItem(row, 3, create_centered_item(launch.get('rocket_name', '')))
            
            # Mission
            self.launch_table.setItem(row, 4, create_centered_item(launch.get('mission_name', '')))
            
            # Payload
            self.launch_table.setItem(row, 5, create_centered_item(launch.get('payload_name', '')))
            
            # Orbit
            self.launch_table.setItem(row, 6, create_centered_item(launch.get('orbit_type', '')))
            
            # NOTAM
            notam_item = create_centered_item(launch.get('notam_reference', ''))
            if launch.get('notam_reference'):
                notam_item.setBackground(QColor(255, 255, 200))  # Light yellow highlight
            self.launch_table.setItem(row, 7, notam_item)
            
            # Status
            status_item = create_centered_item(launch.get('status_name', ''))
            if launch.get('status_color'):
                status_item.setBackground(QColor(launch['status_color']))
            self.launch_table.setItem(row, 8, status_item)
            
            # Store launch_id in first column
            self.launch_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, launch['launch_id'])
        
        # Update status
        filter_names = {
            'previous_7': 'Previous 7 Days',
            'previous_30': 'Previous 30 Days',
            'current': 'Current (Today)',
            'next_30': 'Next 30 Days',
            'custom': 'Custom Range'
        }
        filter_name = filter_names.get(self.current_filter, 'All')
        self.status_label.setText(f"Showing {len(launches)} launches ({filter_name})")
    
    def perform_search(self):
        """Search launches"""
        search_term = self.search_edit.text()
        if search_term:
            # Get launches in current date range
            start_date, end_date = self.get_date_range()
            all_launches = self.db.get_launches_by_date_range(start_date, end_date)
            
            # Filter by search term
            search_lower = search_term.lower()
            filtered = [l for l in all_launches if (
                search_lower in l.get('mission_name', '').lower() or
                search_lower in l.get('payload_name', '').lower() or
                search_lower in l.get('rocket_name', '').lower() or
                search_lower in l.get('notam_reference', '').lower()
            )]
            
            self.load_launches(filtered)
        else:
            self.load_launches()
    
    def on_launch_double_clicked(self, row, col):
        """Handle double click on launch"""
        item = self.launch_table.item(row, 0)
        if item:
            launch_id = item.data(Qt.ItemDataRole.UserRole)
            self.launch_selected.emit(launch_id)
    
    def refresh(self):
        """Refresh the view"""
        self.load_launches()


# Example quick date range helper functions
def get_previous_7_days():
    """Get date range for previous 7 days"""
    end = datetime.now().date()
    start = end - timedelta(days=7)
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

def get_previous_30_days():
    """Get date range for previous 30 days"""
    end = datetime.now().date()
    start = end - timedelta(days=30)
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

def get_current_day():
    """Get date range for current day"""
    today = datetime.now().date()
    return today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')

def get_next_30_days():
    """Get date range for next 30 days"""
    start = datetime.now().date()
    end = start + timedelta(days=30)
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

# shockwave_planner_v2
# SHOCKWAVE PLANNER v2.0
## Desktop Launch Operations Planning System

**Version**: 2.0.0  
**Created**: December 2025  
**For**: Remix Astronautics 
**Author**: Phil Holdstock

---

## 🚀 What's New in v2.0

### Major Features

✅ **Space Devs API Integration** - Automated launch data from The Space Devs  
✅ **Re-entry Tracking** - Dedicated re-entry operations timeline  
✅ **Improved Database** - Enhanced schema with sync tracking  
✅ **Timeline Views** - Gantt-style visualizations for both launches and re-entries  
✅ **NOTAM Support** - Track Notice to Airmen references  
✅ **Data Sync System** - Automated updates from external sources  
✅ **Enhanced Architecture** - Clean, modular codebase  
✅ **Splash Screen** - Professional startup experience  

### Architecture Restoration

The v2.0 release restores the clean modular architecture:
- Proper separation of concerns (GUI, Data, Business Logic)
- Comprehensive database layer with proper foreign keys
- API integration module with sync management
- Thread-safe background operations

---

## 📁 Project Structure

```
shockwave_v2/
│
├── main.py                          # Application entry point
├── __init__.py
│
├── gui/                             # User Interface Layer
│   ├── __init__.py
│   ├── main_window.py              # Main application window
│   ├── timeline_view.py            # Launch timeline Gantt chart
│   ├── timeline_view_reentry.py    # Re-entry timeline Gantt chart
│   └── enhanced_list_view.py       # Launch list with filters
│
├── data/                            # Data Access Layer
│   ├── __init__.py
│   ├── database.py                 # SQLite database interface
│   └── space_devs.py               # Space Devs API integration
│
├── resources/                       # Application Resources
│   └── splash_intro.png            # Splash screen image
│
├── shockwave_planner.db            # SQLite database file
│
└── docs/                            # Documentation
    ├── README.md                   # This file
    ├── INSTALLATION.md             # Setup instructions
    ├── USER_GUIDE.md               # User manual
    ├── API_INTEGRATION.md          # Space Devs integration guide
    └── ARCHITECTURE.md             # Technical architecture
```

---

## ⚡ Quick Start

### Installation (1 minute)

```bash
# Install PyQt6
pip install PyQt6 --break-system-packages

# Install requests for API integration
pip install requests --break-system-packages

# Run the application
cd shockwave_v2
python3 main.py
```

### First Sync

1. Launch SHOCKWAVE PLANNER
2. Go to **Data → Sync Upcoming Launches**
3. Wait for sync to complete (~30 seconds)
4. Explore the timeline views!

---

## 🎯 Core Features

### 1. Master Activity Schedule - Launch

Gantt-chart style timeline showing:
- Monthly view of all launches
- Grouped by country/region (China, USA, Russia, etc.)
- Expandable/collapsible groups
- Color-coded launch status
- Pad turnaround time visualization
- Filter: Show only active sites

**Usage:**
- Click on date cells to view/edit launches
- Use Previous/Next buttons to navigate months
- Toggle checkbox to filter empty sites
- Adjust turnaround days with spinner

### 2. Master Activity Schedule - Re-entry

Dedicated re-entry operations timeline:
- Monthly view of re-entry events
- Grouped by landing region
- Drop zone tracking
- Recovery period visualization
- Vehicle component tracking

### 3. Launch List View

Comprehensive searchable list with:
- **Date Range Filters:**
  - Previous 7 days
  - Previous 30 days
  - Current (today)
  - Next 30 days
  - Custom date range
- **Real-time Search**: Mission, payload, rocket, NOTAM
- **Quick Access**: Double-click to edit
- **NOTAM Highlighting**: Yellow highlight for NOTAM entries

### 4. Statistics Dashboard

Real-time analytics:
- Total launches tracked
- Success/failure rates
- Top 10 most-used rockets
- Launch activity by site
- Last sync status

---

## 🔄 Space Devs Integration

### What is Space Devs?

The Space Devs provides a comprehensive API for rocket launch data worldwide. SHOCKWAVE PLANNER integrates with their Launch Library API to automatically populate and update launch information.

### Sync Operations

**Sync Upcoming Launches:**
- Fetches next 100 upcoming launches
- Updates existing records if already in database
- Adds new launches automatically
- Menu: Data → Sync Upcoming Launches

**Sync Previous Launches:**
- Fetches 50 recent historical launches
- Useful for backfilling data
- Menu: Data → Sync Previous Launches

### What Gets Synced?

- ✅ Launch date and time
- ✅ Launch site and pad
- ✅ Rocket configuration
- ✅ Mission name and description
- ✅ Payload information
- ✅ Orbit type
- ✅ Status (scheduled, success, failure, etc.)
- ✅ Source URL for reference

### Sync Tracking

All sync operations are logged in the database:
- Timestamp
- Records added/updated
- Success/error status
- View in Statistics tab

---

## 🗄️ Database Schema

### Core Tables

**launch_sites** - Launch facilities
- location, launch_pad, coordinates
- country, site_type
- external_id (for API correlation)

**rockets** - Rocket types
- name, family, variant
- manufacturer, specs
- external_id (Space Devs ID)

**launches** - Launch records
- date, time, window
- site_id, rocket_id references
- mission, payload, orbit details
- status, success, remarks
- **notam_reference** - NOTAM tracking (NEW in v2.0)
- **data_source** - Manual vs. Space Devs (NEW in v2.0)
- **external_id** - Space Devs launch ID (NEW in v2.0)
- **last_synced** - Sync timestamp (NEW in v2.0)

**reentry_sites** - Landing/drop zones (NEW in v2.0)
- location, drop_zone, coordinates
- country, zone_type

**reentries** - Re-entry records (NEW in v2.0)
- reentry_date, reentry_time
- reentry_site_id reference
- vehicle_component, reentry_type
- Associated with launch_id

**sync_log** - Sync operations log (NEW in v2.0)
- sync_time, data_source
- records_added, records_updated
- status, error_message

---

## 🎮 User Guide

### Adding a Launch Manually

1. Click **âž• New Launch** button or **Ctrl+N**
2. Fill in the form:
   - Launch Date (required)
   - Launch Time
   - Launch Site (dropdown)
   - Rocket (dropdown)
   - Mission Name
   - Payload
   - Orbit Type
   - NOTAM Reference (if applicable)
   - Status
   - Remarks
3. Click **Save**

### Editing a Launch

1. Find launch in timeline or list view
2. Double-click on the launch
3. Modify fields as needed
4. Click **Save**

### Syncing with Space Devs

**First Time:**
1. Data → Sync Upcoming Launches
2. Wait for sync (~30 seconds for 100 launches)
3. Review sync results
4. Check Statistics tab for sync status

**Regular Updates:**
- Sync weekly for upcoming launches
- Sync previous launches to backfill history
- All syncs are logged and tracked

### Using Date Filters

**In List View:**
1. Select date range from dropdown:
   - Previous 7/30 days
   - Current (today)
   - Next 30 days
   - Custom range
2. For custom range:
   - Select "Custom Range..."
   - Choose start and end dates
   - Click **Apply**

### Timeline Navigation

1. Use **◀ Previous Month** / **Next Month ▶** buttons
2. Click on country/region headers to expand/collapse
3. Click on date cells with numbers to view launches
4. Adjust turnaround/recovery days with spinner

### Searching

In List View:
1. Type in search box
2. Searches across:
   - Mission names
   - Payload names
   - Rocket names
   - NOTAM references
3. Results update in real-time

---

## 🔧 Advanced Usage

### Manual Sync Script

For automated/scheduled syncs:

```bash
# Sync upcoming launches (100)
python3 data/space_devs.py upcoming 100

# Sync previous launches (50)
python3 data/space_devs.py previous 50

# Sync specific date range
python3 data/space_devs.py range 2025-01-01 2025-12-31
```

### Database Access

The SQLite database can be accessed directly:

```bash
# Using Python
python3 -c "
from data.database import LaunchDatabase
db = LaunchDatabase()
stats = db.get_statistics()
print(stats)
db.close()
"

# Or via sqlite3 (if available)
sqlite3 shockwave_planner.db "SELECT * FROM launches LIMIT 10"
```

### Backup

```bash
# Backup database
cp shockwave_planner.db backup_$(date +%Y%m%d).db

# Restore from backup
cp backup_20251207.db shockwave_planner.db
```

---

## 🛡️ Data Integrity

### Conflict Resolution

When syncing from Space Devs:
- Existing launches (matched by external_id) are **updated**
- New launches are **added**
- Manual entries (no external_id) are **preserved**
- Local modifications persist unless overwritten by sync

### Manual vs. API Data

- **Manual entries**: `data_source = 'MANUAL'`
- **API entries**: `data_source = 'SPACE_DEVS'`
- Both coexist peacefully
- API data can be updated without affecting manual entries

---

## 📝 Tips & Best Practices

### For Daily Operations

1. **Start your day**: Sync upcoming launches to get latest data
2. **Use filters**: "Current" or "Next 30 days" for operational planning
3. **NOTAM tracking**: Add NOTAM references as you receive them
4. **Color coding**: Status colors help quick visual assessment

### For Historical Analysis

1. **Sync previous**: Get historical launch data
2. **Statistics tab**: Review success rates and trends
3. **Export data**: Access database directly for custom reports

### For Planning

1. **Timeline view**: Best for visualizing operational tempo
2. **Turnaround days**: Adjust to see pad availability
3. **Group by region**: Expand/collapse as needed
4. **Re-entry view**: Plan recovery operations

---

## 🐛 Troubleshooting

### Application Won't Start

```bash
# Check Python version (need 3.9+)
python3 --version

# Install dependencies
pip install PyQt6 requests --break-system-packages

# Check for errors
python3 main.py
```

### Sync Fails

**Check internet connection:**
```bash
curl -I https://ll.thespacedevs.com
```

**Check sync log:**
- View Statistics tab
- Look for error messages
- Check Data → View Sync History (coming soon)

### Database Locked

```bash
# Close all instances
killall python3

# Remove lock file
rm shockwave_planner.db-journal

# Restart application
python3 main.py
```

### Missing Data

1. Check date filters (may be filtering out data)
2. Try "Show all" options in timeline views
3. Sync from Space Devs to populate
4. Check database directly for corruption

---

## 🔐 Security Notes

### API Keys

Currently using public Space Devs API (no key required). If you need higher rate limits:
1. Register at https://thespacedevs.com
2. Get API key
3. Modify `space_devs.py` to include key in headers

### Database Security

- Database is local SQLite (no network exposure)
- Suitable for air-gapped environments
- For classified operations:
  - Disable Space Devs sync
  - Use manual data entry only
  - Store database on secure network drive

---

## 📚 Additional Documentation

- **INSTALLATION.md** - Detailed setup instructions
- **USER_GUIDE.md** - Comprehensive user manual
- **API_INTEGRATION.md** - Space Devs integration details
- **ARCHITECTURE.md** - Technical architecture documentation

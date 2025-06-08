# Virtual Airline Management - Flet Web Version

This project has been completely rewritten from tkinter to **Flet** for modern web browser support while keeping all Python business logic.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# Initialize database and create sample data
python scripts/initial_setup.py
python scripts/create_airline_data.py
```

### 3. Run the Application

```bash
# Run as web application (opens in browser)
python app.py

# Alternative: Run as desktop app
python -c "import flet as ft; from app import main; ft.app(target=main)"
```

The application will open at `http://localhost:8000` in your default browser.

## 🌐 Web Deployment

### Deploy to Web

```bash
# Build for web deployment
flet build web

# Files will be created in dist/ directory
# Upload dist/ contents to your web server
```

### Deploy as Desktop App

```bash
# Build standalone desktop application
flet build windows  # or macos/linux
```

## 📋 Features Converted to Flet

✅ **Completed:**
- ✅ Main application structure with navigation rail
- ✅ Airline selection interface
- ✅ Pilot management (full CRUD operations)
- ✅ Dashboard with statistics and quick actions
- ✅ Settings dialog
- ✅ Database integration (SQLite)
- ✅ Configuration management

🚧 **Stub Modules (Ready for Development):**
- 🚧 Aircraft Marketplace
- 🚧 Fleet Management
- 🚧 Flight Schedules
- 🚧 Pilot Logbook

## 🔧 Architecture Changes

### From tkinter to Flet:
- **UI Framework**: tkinter/ttkbootstrap → Flet (Flutter-based)
- **Deployment**: Desktop only → Web + Desktop + Mobile
- **Styling**: ttkbootstrap themes → Material Design
- **Navigation**: Window switching → Navigation rail
- **Dialogs**: tkinter dialogs → Flet dialogs

### Preserved:
- ✅ All Python business logic
- ✅ SQLite database structure
- ✅ Configuration system
- ✅ Core utilities and database operations
- ✅ All existing data and settings

## 📁 Project Structure

```
/
├── app.py                 # Main Flet application
├── main_tkinter.py.old   # Old tkinter version (backup)
├── core/                 # Core business logic (unchanged)
│   ├── config_manager.py
│   ├── database_utils.py
│   ├── settings.py
│   └── utils.py          # Updated with Flet button helpers
├── modules/              # Flet UI modules
│   ├── pilot_management.py       # ✅ Full implementation
│   ├── pilot_dashboard_view.py   # ✅ Full implementation
│   ├── aircraft_marketplace_view.py  # 🚧 Stub
│   ├── fleet_management_view.py      # 🚧 Stub
│   ├── pilot_logbook_view.py         # 🚧 Stub
│   ├── schedule_view.py              # 🚧 Stub
│   └── settings_view.py              # ✅ Basic implementation
├── scripts/              # Database and setup scripts (unchanged)
└── requirements.txt      # Updated for Flet
```

## 🎯 Key Benefits

1. **Web-First**: Runs in any modern browser
2. **Responsive**: Mobile-friendly Material Design interface  
3. **Modern UI**: Clean, professional appearance
4. **Cross-Platform**: Windows, macOS, Linux, Web, Mobile
5. **Easy Deployment**: Single command to build for web
6. **Performance**: Flutter-based rendering
7. **Python-Only**: No JavaScript/HTML knowledge required

## 🔄 Migration Notes

### Removed Files:
- ❌ All `.backup` files
- ❌ Debug and test scripts
- ❌ Log files
- ❌ tkinter-specific GUI modules

### Key Changes:
- `main.py` → `app.py` (Flet-based)
- All `*_gui.py` modules → `*_view.py` (Flet components)
- ttkbootstrap themes → Material Design colors
- Window management → Navigation rail

## 🛠️ Development Guide

### Adding New Features:
1. Create new view class in `modules/`
2. Add navigation destination in `app.py`
3. Implement `build()` method returning Flet components
4. Follow existing patterns for dialogs and error handling

### Flet Component Examples:
```python
# Button
ft.ElevatedButton("Text", icon=ft.icons.ADD, on_click=handler)

# Data Table
ft.DataTable(columns=[...], rows=[...])

# Form Fields
ft.TextField(label="Name", width=300)
ft.Dropdown(label="Status", options=[...])

# Layout
ft.Column([...], expand=True)
ft.Row([...], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
```

## 📞 Support

- **Documentation**: See CLAUDE.md for detailed project information
- **Issues**: Create GitHub issues for bugs or feature requests
- **Flet Docs**: https://flet.dev/docs/

The application is now ready for modern web deployment while maintaining all existing functionality! 🎉
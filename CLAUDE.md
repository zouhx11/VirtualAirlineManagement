# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

Virtual Airline Management is a Python-based desktop application built with ttkbootstrap (tkinter extension) that simulates airline operations. The application uses SQLite for data persistence and integrates with FlightAware AeroAPI for real-time flight data.

### Core Components

- **Main Application (`main.py`)**: Entry point with MainApp class managing the GUI and navigation
- **Core Modules (`core/`)**: 
  - `config_manager.py`: Singleton ConfigManager for handling config.ini preferences
  - `database_utils.py`: Database operations and SQL utilities
  - `settings.py`: Settings GUI implementation
  - `utils.py`: Shared utility functions
- **Feature Modules (`modules/`)**: Separate GUI modules for pilot management, fleet management, scheduling, logbook, dashboard, and aircraft marketplace
- **Setup Scripts (`scripts/`)**: Database initialization and migration utilities

### Configuration System

The application uses a config.ini file with sections:
- `[DATABASES]`: Database file paths
- `[PREFERENCES]`: User preferences (theme, refresh rates, selected airline)
- `[AeroAPI]`: FlightAware API credentials
- `[AIRCRAFT_MARKETPLACE]`: Marketplace simulation settings
- `[SIMULATION]`: Game simulation parameters

The ConfigManager class is a singleton that handles all configuration operations.

### Database Architecture

Uses SQLite with a main userdata.db file containing tables for pilots, aircraft, logbook entries, and airline data. The database schema supports airline associations and can be extended for multi-airline operations.

## Development Commands

### Setup and Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Initial database setup
python scripts/initial_setup.py

# Create sample airline data
python scripts/create_airline_data.py
```

### Running the Application
```bash
python main.py
```

### Database Management
```bash
# Initialize/recreate database tables
python scripts/initial_setup.py

# Update database schema
python scripts/update_database_schema.py

# Migrate aircraft system
python scripts/migrate_aircraft_system.py

# Diagnose database issues
python scripts/diagnose_issues.py
```

### Testing and Debugging
```bash
# Test logbook data fetching
python scripts/test_fetch_logbook_data.py

# Debug main application
python scripts/debug_main.py

# Complete system fix (comprehensive repair)
python scripts/complete_fix.py
```

## Key Development Patterns

### Module Structure
Each GUI module follows a consistent pattern:
- Constructor takes a parent window and relevant IDs
- Uses ttkbootstrap for consistent theming
- Integrates with ConfigManager for preferences
- Handles database operations through core.database_utils

### Error Handling
The application uses `show_large_error()` function for comprehensive error dialogs that provide:
- Detailed error messages
- Possible causes
- Suggested solutions
- Technical details

### Configuration Access
Always use ConfigManager for configuration:
```python
from core.config_manager import ConfigManager
config_manager = ConfigManager()
db_path = config_manager.get_database_path('userdata')
theme = config_manager.get_preference('theme', 'flatly')
```

### Database Operations
Use the database_utils module for consistent database operations and error handling. The database structure supports multi-airline operations through airline_id foreign keys.

## Development Roadmap

🛫 **Virtual Airline Tycoon Development Roadmap**

### 📊 Phase Overview
Transforming VirtualAirlineManagement into a comprehensive airline tycoon simulation over 6 phases in 12 months.

**✅ Phase 1: Enhanced Aircraft System (Months 1-2) - COMPLETED**
- Aircraft Marketplace with 12+ real aircraft models (A320neo, B737 MAX, A350, etc.)
- Financial System with cash, loan, and lease purchasing with realistic depreciation
- Fleet Management tracking aircraft value, monthly costs, utilization
- Professional GUI integrated with ttkbootstrap interface
- Economic features: 4% annual depreciation, loan financing (20-year, 5% interest), leasing (10-year, 0.8-1.2% monthly)

**🗺️ Phase 2: Route Economics (Months 3-4) - NEXT**
- Route Network with city-pair routes, distance, demand, competition
- Revenue Calculator based on aircraft capacity and pricing
- Operating Costs including fuel burn, crew costs, airport fees, maintenance
- Profitability Analysis with route P&L
- Aircraft Assignment optimization
- Dynamic Pricing based on demand and competition

**🏢 Phase 3: Market Competition (Months 5-6)**
- AI Competitor Airlines (5-10 computer-controlled airlines)
- Market Share Battles and dynamic demand
- Pricing Wars and route blocking
- Alliance System for route sharing

**🌦️ Phase 4: Weather & Operations (Months 7-8)**
- Weather System affecting operations
- Flight Delays/Cancellations and seasonal demand
- Maintenance Scheduling and crew management
- Airport Congestion modeling

**📊 Phase 5: Advanced Analytics (Months 9-10)**
- Interactive World Map with real-time flight tracking
- Financial Dashboards and performance metrics
- Forecasting Tools and optimization engine
- Scenario Planning capabilities

**🚀 Phase 6: Advanced Features (Months 11-12)**
- Aircraft Leasing Market and M&A
- Cargo Operations and international expansion
- Reputation System and advanced financing

### 🎯 Key Success Metrics by Phase
- Phase 1: ✅ Buy/lease aircraft, manage fleet costs
- Phase 2: Generate positive route revenue
- Phase 3: Outcompete AI airlines for market share
- Phase 4: Maintain operations during disruptions
- Phase 5: Optimize network for maximum ROI
- Phase 6: Build dominant airline empire

### 🔧 Technical Architecture
- **Core Engine**: Python + SQLite for simulation logic
- **GUI**: TTKBootstrap for professional interface
- **Data**: Real aircraft specs, airport data, route economics
- **Simulation**: Turn-based monthly cycles with real-time elements
- **Scalability**: Modular design allows feature additions

## Important Files

- `config.ini`: Main configuration file (not tracked in git)
- `userdata.db`: SQLite database file (not tracked in git)
- `airline_data.json`: Airline reference data
- `requirements.txt`: Python dependencies
- `scripts/initial_setup.py`: Database initialization script
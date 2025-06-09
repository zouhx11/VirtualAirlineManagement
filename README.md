# ✈️ Virtual Airline Management - Real-Time Flight Tracking

A modern web-based airline management system with **real-time aircraft tracking**, **economics simulation**, and **smooth WebSocket updates** - no page refreshes!

## 🚀 Features

### **Real-Time Flight Tracking**
- **Live aircraft movement** on interactive Leaflet maps
- **WebSocket-powered updates** - no page refreshes, no eye strain
- **Dynamic aircraft markers** with heading, altitude, and status
- **Route visualization** with flight paths and airports

### **Economics & Financial Management**
- **Real-time profit/loss tracking** with monthly financial reports  
- **Route profitability analysis** with instant recommendations
- **Aircraft marketplace** - buy/lease aircraft with financial impact
- **Cost breakdown** - fuel, crew, maintenance, airport fees
- **Cash balance monitoring** and ROI calculations

### **Professional Interface**
- **Dark theme** optimized for extended use
- **Map-centric design** with maximum screen real estate
- **Responsive controls** with live financial displays
- **Tabbed management panels** for fleet, routes, and marketplace

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Node.js (for some dependencies)

### Quick Setup
```bash
# Clone and enter project
git clone <your-repository-url>
cd VirtualAirlineManagement

# Install dependencies with uv (recommended)
uv sync

# Or use pip
pip install -r requirements.txt

# Initialize database
python scripts/initial_setup.py

# Create sample data
python scripts/create_airline_data.py

# Launch the app
python flask_app.py
```

**🌐 Open http://127.0.0.1:5000 in your browser**

## 📁 Project Structure

```
VirtualAirlineManagement/
├── flask_app.py              # Main Flask application with WebSocket
├── templates/index.html      # Frontend HTML
├── static/
│   ├── css/style.css        # Dark theme styling
│   └── js/app.js            # Real-time JavaScript client
├── core/
│   ├── config_manager.py    # Configuration management
│   ├── database_utils.py    # Database operations
│   └── utils.py            # Shared utilities
├── modules/
│   ├── aircraft_marketplace.py  # Aircraft buying/leasing
│   ├── route_management.py     # Route economics & assignments
│   ├── market_competition.py   # AI competition system
│   ├── forecasting_engine.py   # Economic forecasting
│   └── secondary_aircraft_market.py  # Used aircraft market
├── scripts/
│   ├── initial_setup.py     # Database initialization
│   ├── create_airline_data.py  # Sample data generation
│   └── migrate_aircraft_system.py  # Schema updates
├── config.ini              # Configuration file
├── userdata.db            # SQLite database
└── airline_data.json      # Reference airline data
```

## 🎮 How to Use

### **Getting Started**
1. **Launch the app** and visit http://127.0.0.1:5000
2. **Generate routes** using the sidebar panel
3. **Buy aircraft** from the marketplace
4. **Assign routes** and watch aircraft fly in real-time!

### **Key Controls**
- **⚡ Time Speed**: 1x to 20x speed multipliers for faster flights
- **💰 Financial Display**: Live cash balance and monthly profit/loss
- **🎮 Management Tabs**: Switch between flights, economics, marketplace, routes, and fleet
- **📊 Route Analysis**: See profitability before assigning aircraft

### **Economics Features**
- **Route Analysis**: See revenue, costs, and profit before assignment
- **Cost Tracking**: Monitor fuel, crew, maintenance, and airport fees
- **Performance Monitoring**: Track ROI and profit margins
- **Smart Recommendations**: Color-coded profitability indicators

## 🔧 Configuration

Edit `config.ini` for:
- Database paths
- FlightAware API credentials (optional)
- Economic simulation parameters
- Aircraft marketplace settings

## 🚀 Architecture

### **Backend (Flask + Socket.IO)**
- **Real-time WebSocket communication** for aircraft updates
- **RESTful APIs** for aircraft, routes, and financial data
- **Economics engine** for route profitability calculations
- **Background threads** for continuous aircraft position updates

### **Frontend (JavaScript + Leaflet)**
- **Interactive Leaflet maps** with dark CartoDB tiles
- **WebSocket client** for real-time position updates
- **Responsive UI** with professional dark theme
- **No page refreshes** - only aircraft positions update

## 📈 Development

### **Key Technologies**
- **Flask + Socket.IO**: Real-time web framework
- **Leaflet**: Interactive mapping library
- **SQLite**: Embedded database
- **JavaScript ES6**: Modern frontend development

### **Adding Features**
1. **Backend**: Add API endpoints in `flask_app.py`
2. **Frontend**: Extend `static/js/app.js` for UI features
3. **Styling**: Update `static/css/style.css` for visual changes
4. **Database**: Use scripts in `scripts/` for schema changes

## 🎯 Next Steps

The application is designed for expansion:
- **AI Competition**: Market competition with computer airlines
- **Weather System**: Weather-based flight delays and seasonal demand  
- **Advanced Analytics**: Forecasting and optimization tools
- **Multiplayer**: Multi-user airline competition

## 📝 License

MIT License - Build amazing airline simulations!
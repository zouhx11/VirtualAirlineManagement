# scripts/initial_setup.py

import sqlite3
import os
import sys
import configparser
from datetime import datetime

def create_config_file():
    """Create initial config.ini file"""
    config_path = "config.ini"
    
    if os.path.exists(config_path):
        print(f"✅ Config file already exists at {config_path}")
        return config_path
    
    print("📝 Creating initial config.ini file...")
    
    config = configparser.ConfigParser()
    
    config['DATABASES'] = {
        'userdata': 'userdata.db'
    }
    
    config['PREFERENCES'] = {
        'theme': 'cyborg',
        'data_refresh_rate': '30',
        'selected_airline': 'Your Airline',
        'homehub': 'KJFK',
        'current_location': 'KJFK'
    }
    
    config['AeroAPI'] = {
        'api_key': 'YOUR_API_KEY',
        'api_secret': 'YOUR_API_SECRET'
    }
    
    config['AIRCRAFT_MARKETPLACE'] = {
        'default_market_size': '50',
        'auto_refresh_hours': '24',
        'enable_market_fluctuations': 'true',
        'default_financing_rate': '0.05'
    }
    
    config['SIMULATION'] = {
        'time_acceleration': '1.0',
        'auto_save_interval': '300',
        'enable_weather_effects': 'true',
        'enable_competition': 'false'
    }
    
    with open(config_path, 'w') as configfile:
        config.write(configfile)
    
    print(f"✅ Created config.ini at {config_path}")
    return config_path

def create_initial_database(db_path: str):
    """Create initial database with all required tables"""
    print(f"🗄️  Creating initial database at {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Original VirtualAirlineManagement tables
        print("Creating original tables...")
        
        # Pilots table (from original system)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pilots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                license_number TEXT UNIQUE,
                rating TEXT,
                hours INTEGER DEFAULT 0,
                hire_date TEXT,
                status TEXT DEFAULT 'active',
                airline_id INTEGER DEFAULT 1,
                homeHub TEXT DEFAULT 'Unknown',
                currentLocation TEXT DEFAULT 'Unknown'
            )
        ''')
        
        # Original fleet table (basic version)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fleet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aircraft_id TEXT UNIQUE,
                model TEXT,
                registration TEXT,
                status TEXT DEFAULT 'active',
                location TEXT,
                last_updated TEXT
            )
        ''')
        
        # Flight schedules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flight_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flight_number TEXT,
                aircraft_id TEXT,
                pilot_id INTEGER,
                departure_airport TEXT,
                arrival_airport TEXT,
                departure_time TEXT,
                arrival_time TEXT,
                status TEXT DEFAULT 'scheduled',
                FOREIGN KEY (pilot_id) REFERENCES pilots (id),
                FOREIGN KEY (aircraft_id) REFERENCES fleet (aircraft_id)
            )
        ''')
        
        # Pilot logbook table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pilot_logbook (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pilot_id INTEGER,
                flight_number TEXT,
                aircraft_type TEXT,
                departure_airport TEXT,
                arrival_airport TEXT,
                flight_date TEXT,
                flight_hours REAL,
                FOREIGN KEY (pilot_id) REFERENCES pilots (id)
            )
        ''')
        
        # New Aircraft Marketplace tables
        print("Creating aircraft marketplace tables...")
        
        # Market aircraft table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_aircraft (
                id TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                condition TEXT NOT NULL,
                age_years REAL NOT NULL,
                total_flight_hours INTEGER NOT NULL,
                cycles INTEGER NOT NULL,
                asking_price REAL NOT NULL,
                lease_rate_monthly REAL NOT NULL,
                seller_type TEXT NOT NULL,
                location TEXT NOT NULL,
                available_until TEXT NOT NULL,
                maintenance_due_hours INTEGER NOT NULL,
                financing_available TEXT NOT NULL,
                spec_data TEXT NOT NULL
            )
        ''')
        
        # Owned aircraft table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS owned_aircraft (
                id TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                condition TEXT NOT NULL,
                age_years REAL NOT NULL,
                total_flight_hours INTEGER NOT NULL,
                cycles INTEGER NOT NULL,
                purchase_price REAL NOT NULL,
                current_value REAL NOT NULL,
                financing_type TEXT NOT NULL,
                monthly_payment REAL NOT NULL,
                remaining_payments INTEGER NOT NULL,
                location TEXT NOT NULL,
                maintenance_due_hours INTEGER NOT NULL,
                last_maintenance TEXT NOT NULL,
                utilization_hours_month REAL NOT NULL,
                route_assignments TEXT NOT NULL,
                spec_data TEXT NOT NULL
            )
        ''')
        
        # Aircraft transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aircraft_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aircraft_id TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_date TEXT NOT NULL,
                details TEXT
            )
        ''')
        
        # Airline financial data (for future phases)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS airline_finances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                cash_balance REAL DEFAULT 250000000,
                revenue REAL DEFAULT 0,
                expenses REAL DEFAULT 0,
                profit_loss REAL DEFAULT 0,
                notes TEXT
            )
        ''')
        
        # Routes table (for Phase 2)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS routes (
                id TEXT PRIMARY KEY,
                departure_airport TEXT NOT NULL,
                arrival_airport TEXT NOT NULL,
                distance_nm INTEGER NOT NULL,
                demand_passengers INTEGER DEFAULT 0,
                demand_cargo REAL DEFAULT 0,
                competition_level INTEGER DEFAULT 1,
                base_ticket_price REAL DEFAULT 200,
                created_date TEXT NOT NULL
            )
        ''')
        
        print("Creating database indexes...")
        
        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pilots_name ON pilots(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fleet_model ON fleet(model)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_aircraft_model ON market_aircraft(model)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_owned_aircraft_model ON owned_aircraft(model)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_aircraft ON aircraft_transactions(aircraft_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON aircraft_transactions(transaction_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_routes_airports ON routes(departure_airport, arrival_airport)")
        
        print("Creating database views...")
        
        # Views for reporting
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS fleet_summary AS
            SELECT 
                model,
                COUNT(*) as aircraft_count,
                AVG(age_years) as avg_age,
                SUM(current_value) as total_value,
                SUM(monthly_payment) as total_monthly_payments
            FROM owned_aircraft 
            GROUP BY model
        ''')
        
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS monthly_costs AS
            SELECT 
                SUM(monthly_payment) as total_financing,
                SUM(current_value * 0.02 / 12) as estimated_maintenance,
                SUM(monthly_payment + current_value * 0.02 / 12) as total_monthly
            FROM owned_aircraft
        ''')
        
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS pilot_summary AS
            SELECT 
                COUNT(*) as total_pilots,
                AVG(hours) as avg_hours,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_pilots
            FROM pilots
        ''')
        
        # Insert initial data
        print("Adding initial data...")
        
        # Initial airline financial record
        cursor.execute('''
            INSERT OR IGNORE INTO airline_finances 
            (date, cash_balance, revenue, expenses, profit_loss, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            250000000,  # $250M starting cash - reasonable for airline tycoon
            0, 0, 0,
            "Initial airline setup"
        ))
        
        # Sample pilot data
        sample_pilots = [
            ("John Smith", "ATP001", "ATP", 5500, datetime.now().isoformat()),
            ("Sarah Johnson", "ATP002", "ATP", 4200, datetime.now().isoformat()),
            ("Mike Wilson", "CPL001", "Commercial", 2800, datetime.now().isoformat()),
            ("Emily Davis", "ATP003", "ATP", 6100, datetime.now().isoformat()),
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO pilots (name, license_number, rating, hours, hire_date)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_pilots)
        
        conn.commit()
        print("✅ Database created successfully!")
        
        # Print summary
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Created {len(tables)} tables: {', '.join(tables)}")
        
        cursor.execute("SELECT COUNT(*) FROM pilots")
        pilot_count = cursor.fetchone()[0]
        print(f"👨‍✈️ Added {pilot_count} sample pilots")
        
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        conn.rollback()
        raise e
    
    finally:
        conn.close()

def create_initial_market_data(db_path: str):
    """Create initial aircraft market data"""
    print("🛩️  Creating initial aircraft market...")
    
    try:
        # Add the modules directory to Python path
        modules_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'modules')
        if modules_path not in sys.path:
            sys.path.insert(0, modules_path)
        
        from aircraft_marketplace import AircraftMarketplace
        
        marketplace = AircraftMarketplace(db_path)
        
        # Generate diverse market with good mix of aircraft
        market_aircraft = marketplace.generate_market_aircraft(75)
        marketplace.save_market_aircraft(market_aircraft)
        
        print(f"✅ Created {len(market_aircraft)} aircraft in marketplace")
        
        # Show sample aircraft by category
        from aircraft_marketplace import AircraftCategory
        
        for category in AircraftCategory:
            category_aircraft = [a for a in market_aircraft if a.spec.category == category]
            if category_aircraft:
                print(f"  {category.value.replace('_', ' ').title()}: {len(category_aircraft)} aircraft")
        
        print("\n📋 Sample Market Aircraft:")
        for i, aircraft in enumerate(market_aircraft[:8]):
            print(f"  {aircraft.spec.model} ({aircraft.age_years:.1f}y) - ${aircraft.asking_price:.1f}M - {aircraft.location}")
        
        if len(market_aircraft) > 8:
            print(f"  ... and {len(market_aircraft) - 8} more aircraft")
        
    except ImportError as e:
        print(f"⚠️  Could not import aircraft marketplace: {e}")
        print("   Market data will be created when you first run the application")
    except Exception as e:
        print(f"⚠️  Could not create market data: {e}")
        print("   You can generate market data later from the application")

def main():
    """Main setup function"""
    print("🚀 VirtualAirlineManagement Initial Setup")
    print("==========================================\n")
    
    # Check if we're in the right directory
    if not os.path.exists("flask_app.py"):
        print("❌ Error: flask_app.py not found!")
        print("   Please run this script from the VirtualAirlineManagement root directory")
        print("   (the same directory that contains flask_app.py)")
        sys.exit(1)
    
    try:
        # Step 1: Create config file
        config_path = create_config_file()
        
        # Step 2: Read database path from config
        config = configparser.ConfigParser()
        config.read(config_path)
        db_path = config.get('DATABASES', 'userdata', fallback='userdata.db')
        
        print(f"📍 Database will be created at: {db_path}")
        
        # Step 3: Create database
        create_initial_database(db_path)
        
        # Step 4: Create initial market data
        create_initial_market_data(db_path)
        
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Update config.ini with your FlightAware API credentials (optional)")
        print("2. Run: uv run python flask_app.py")
        print("3. Check out the new 'Aircraft Market' and 'My Fleet' tabs")
        print("4. Start by browsing and purchasing your first aircraft!")
        
        print(f"\n💰 Starting Cash: $100B")
        print(f"🛩️  Available Aircraft: Check the marketplace")
        print(f"👨‍✈️ Sample Pilots: 4 pilots ready for duty")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
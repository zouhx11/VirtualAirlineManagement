# scripts/migrate_aircraft_system.py

import sqlite3
import os
import sys
from datetime import datetime

def migrate_database(db_path: str):
    """Migrate existing database to support new aircraft marketplace system"""
    
    print(f"Starting database migration for: {db_path}")
    
    # Backup existing database
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Database backed up to: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if new tables already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        tables_to_create = []
        
        if 'market_aircraft' not in existing_tables:
            tables_to_create.append('market_aircraft')
        
        if 'owned_aircraft' not in existing_tables:
            tables_to_create.append('owned_aircraft')
        
        if 'aircraft_transactions' not in existing_tables:
            tables_to_create.append('aircraft_transactions')
        
        # Create new tables
        if 'market_aircraft' in tables_to_create:
            print("Creating market_aircraft table...")
            cursor.execute('''
                CREATE TABLE market_aircraft (
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
        
        if 'owned_aircraft' in tables_to_create:
            print("Creating owned_aircraft table...")
            cursor.execute('''
                CREATE TABLE owned_aircraft (
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
        
        if 'aircraft_transactions' in tables_to_create:
            print("Creating aircraft_transactions table...")
            cursor.execute('''
                CREATE TABLE aircraft_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aircraft_id TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    transaction_date TEXT NOT NULL,
                    details TEXT
                )
            ''')
        
        # Migrate existing fleet data if it exists
        if 'fleet' in existing_tables and 'owned_aircraft' in tables_to_create:
            print("Migrating existing fleet data...")
            cursor.execute("SELECT * FROM fleet")
            existing_fleet = cursor.fetchall()
            
            # Get column names from existing fleet table
            cursor.execute("PRAGMA table_info(fleet)")
            fleet_columns = [column[1] for column in cursor.fetchall()]
            
            for row in existing_fleet:
                # Create basic aircraft data from existing fleet
                # This assumes the existing fleet table has at least aircraft model
                aircraft_id = f"migrated_{row[0]}" if 'id' in fleet_columns else f"migrated_{hash(str(row))}"
                model = row[fleet_columns.index('model')] if 'model' in fleet_columns else 'Unknown Aircraft'
                
                # Create basic owned aircraft record
                cursor.execute('''
                    INSERT OR IGNORE INTO owned_aircraft 
                    (id, model, condition, age_years, total_flight_hours, cycles, 
                     purchase_price, current_value, financing_type, monthly_payment, 
                     remaining_payments, location, maintenance_due_hours, last_maintenance, 
                     utilization_hours_month, route_assignments, spec_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    aircraft_id, model, 'good', 5.0, 15000, 7500, 50.0, 45.0, 
                    'cash', 0.0, 0, 'JFK', 500, datetime.now().isoformat(), 
                    0.0, '[]', '{"model": "' + model + '", "category": "narrow_body"}'
                ))
        
        # Create indexes for performance
        print("Creating database indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_aircraft_model ON market_aircraft(model)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_aircraft_category ON market_aircraft(spec_data)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_owned_aircraft_model ON owned_aircraft(model)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_aircraft ON aircraft_transactions(aircraft_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON aircraft_transactions(transaction_date)")
        
        # Create views for easy reporting
        print("Creating database views...")
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
        
        conn.commit()
        print("Database migration completed successfully!")
        
        # Print summary
        cursor.execute("SELECT COUNT(*) FROM market_aircraft")
        market_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM owned_aircraft")
        owned_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM aircraft_transactions")
        transaction_count = cursor.fetchone()[0]
        
        print(f"\nMigration Summary:")
        print(f"- Market aircraft records: {market_count}")
        print(f"- Owned aircraft records: {owned_count}")
        print(f"- Transaction records: {transaction_count}")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        conn.rollback()
        # Restore backup if migration failed
        if os.path.exists(backup_path):
            import shutil
            shutil.copy2(backup_path, db_path)
            print("Database restored from backup due to migration failure.")
        raise e
    
    finally:
        conn.close()

def create_initial_market_data(db_path: str):
    """Create initial market data for testing"""
    print("Creating initial market data...")
    
    try:
        # Import marketplace after ensuring database is migrated
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from modules.aircraft_marketplace import AircraftMarketplace
        
        marketplace = AircraftMarketplace(db_path)
        
        # Generate initial market aircraft
        market_aircraft = marketplace.generate_market_aircraft(100)
        marketplace.save_market_aircraft(market_aircraft)
        
        print(f"Created {len(market_aircraft)} aircraft in marketplace")
        
        # Display some sample aircraft
        print("\nSample Market Aircraft:")
        for i, aircraft in enumerate(market_aircraft[:5]):
            print(f"{i+1}. {aircraft.spec.model} ({aircraft.age_years:.1f}y) - ${aircraft.asking_price:.1f}M")
        
    except ImportError as e:
        print(f"Could not import marketplace module: {e}")
        print("Please ensure the aircraft_marketplace.py module is in the modules/ directory")
    except Exception as e:
        print(f"Failed to create initial market data: {e}")

def verify_migration(db_path: str):
    """Verify that migration was successful"""
    print("\nVerifying migration...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check table existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['market_aircraft', 'owned_aircraft', 'aircraft_transactions']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        else:
            print("✅ All required tables exist")
        
        # Check table schemas
        for table in required_tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"✅ Table '{table}' has {len(columns)} columns")
        
        # Check views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]
        expected_views = ['fleet_summary', 'monthly_costs']
        
        for view in expected_views:
            if view in views:
                print(f"✅ View '{view}' exists")
            else:
                print(f"⚠️  View '{view}' missing")
        
        # Test basic queries
        cursor.execute("SELECT COUNT(*) FROM market_aircraft")
        market_count = cursor.fetchone()[0]
        print(f"✅ Market aircraft table accessible ({market_count} records)")
        
        cursor.execute("SELECT COUNT(*) FROM owned_aircraft")
        owned_count = cursor.fetchone()[0]
        print(f"✅ Owned aircraft table accessible ({owned_count} records)")
        
        cursor.execute("SELECT COUNT(*) FROM aircraft_transactions")
        transaction_count = cursor.fetchone()[0]
        print(f"✅ Transactions table accessible ({transaction_count} records)")
        
        print("\n✅ Migration verification completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main migration script"""
    print("=== Aircraft Marketplace Database Migration ===")
    
    # Get database path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default path based on the original repo structure
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "userdata.db")
    
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
    
    print(f"Database path: {db_path}")
    
    try:
        # Step 1: Migrate database schema
        migrate_database(db_path)
        
        # Step 2: Verify migration
        if verify_migration(db_path):
            # Step 3: Create initial market data
            create_initial_market_data(db_path)
            
            print("\n🎉 Migration completed successfully!")
            print("\nNext steps:")
            print("1. Update your main.py to import the new aircraft marketplace GUI")
            print("2. Add the marketplace tabs to your main application")
            print("3. Test the aircraft purchasing functionality")
            
        else:
            print("\n❌ Migration verification failed. Please check the logs above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
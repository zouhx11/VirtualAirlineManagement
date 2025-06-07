# scripts/complete_fix.py

import os
import sys
import shutil
import json

def backup_existing_files():
    """Backup existing files before making changes"""
    print("💾 Creating backups of existing files...")
    
    files_to_backup = ['core/utils.py', 'core/database_utils.py', 'config.ini']
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            try:
                shutil.copy2(file_path, backup_path)
                print(f"   ✅ Backed up {file_path} to {backup_path}")
            except Exception as e:
                print(f"   ⚠️ Could not backup {file_path}: {e}")

def create_core_utils():
    """Create the complete core/utils.py file"""
    print("📝 Creating complete core/utils.py...")
    
    os.makedirs('core', exist_ok=True)
    
    utils_content = '''# core/utils.py - Complete version with all required functions

import json
import sqlite3
import os
import threading
import time
from functools import wraps

def load_airlines_json():
    """Load airlines from JSON file or database - handles both formats correctly"""
    
    # Try JSON file first
    json_file = 'airline_data.json'
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                airlines = json.load(f)
                print(f"✅ Loaded {len(airlines)} airlines from {json_file}")
                return airlines
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"❌ Error loading {json_file}: {e}")
        except Exception as e:
            print(f"❌ Unexpected error loading {json_file}: {e}")
    
    # Try SQLite database
    db_file = 'airline_data.db'
    if os.path.exists(db_file):
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Check if airlines table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='airlines'")
            if cursor.fetchone():
                cursor.execute("SELECT id, name, icao, iata, country, hub FROM airlines")
                rows = cursor.fetchall()
                conn.close()
                
                airlines = []
                for row in rows:
                    airlines.append({
                        'id': row[0],
                        'name': row[1],
                        'icao': row[2] or '',
                        'iata': row[3] or '',
                        'country': row[4] or 'Unknown',
                        'hub': row[5] or 'KJFK'
                    })
                
                print(f"✅ Loaded {len(airlines)} airlines from {db_file}")
                return airlines
            else:
                print(f"❌ No 'airlines' table found in {db_file}")
                conn.close()
                
        except sqlite3.Error as e:
            print(f"❌ SQLite error loading {db_file}: {e}")
        except Exception as e:
            print(f"❌ Unexpected error loading {db_file}: {e}")
    
    # Return default airlines if no data source found
    print("⚠️ No airline data found, creating default airlines")
    
    default_airlines = [
        {"id": 1, "name": "SkyLine Airways", "icao": "SKY", "iata": "SL", "country": "United States", "hub": "KJFK"},
        {"id": 2, "name": "Pacific Airlines", "icao": "PAC", "iata": "PA", "country": "United States", "hub": "KLAX"},
        {"id": 3, "name": "Atlantic Express", "icao": "ATL", "iata": "AE", "country": "United States", "hub": "KATL"},
        {"id": 4, "name": "Continental Airways", "icao": "CON", "iata": "CO", "country": "United States", "hub": "KORD"},
        {"id": 5, "name": "Your Custom Airline", "icao": "YCA", "iata": "YC", "country": "United States", "hub": "KJFK"}
    ]
    
    # Save default airlines to JSON for future use
    try:
        with open('airline_data.json', 'w', encoding='utf-8') as f:
            json.dump(default_airlines, f, indent=2, ensure_ascii=False)
        print("✅ Created airline_data.json with default airlines")
    except Exception as e:
        print(f"⚠️ Could not save default airlines: {e}")
    
    return default_airlines

def create_button(parent, text, style, command, icon=None):
    """Create a button with optional icon"""
    try:
        import ttkbootstrap as ttk
        if icon and icon is not None:
            btn = ttk.Button(parent, text=text, bootstyle=style, command=command, image=icon, compound='top')
        else:
            btn = ttk.Button(parent, text=text, bootstyle=style, command=command)
        return btn
    except Exception as e:
        print(f"⚠️ Error creating button '{text}': {e}")
        # Fallback button without icon
        import ttkbootstrap as ttk
        return ttk.Button(parent, text=text, bootstyle=style, command=command)

def debounce(wait_time):
    """Decorator to debounce function calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def call_func():
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    print(f"⚠️ Debounced function error: {e}")
            
            # Cancel previous call if exists
            if hasattr(wrapper, '_timer'):
                wrapper._timer.cancel()
            
            # Schedule new call
            wrapper._timer = threading.Timer(wait_time / 1000.0, call_func)
            wrapper._timer.start()
        
        return wrapper
    return decorator

# Required functions for database_utils.py compatibility
def convert_to_int(value, default=0):
    """Convert a value to integer with a default fallback"""
    if value is None:
        return default
    
    try:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
            return int(float(value))  # float first to handle "123.0" strings
        
        if isinstance(value, (int, float)):
            return int(value)
        
        return int(value)
        
    except (ValueError, TypeError, OverflowError):
        print(f"⚠️ Could not convert '{value}' to int, using default {default}")
        return default

def convert_to_float(value, default=0.0):
    """Convert a value to float with a default fallback"""
    if value is None:
        return default
    
    try:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
            return float(value)
        
        if isinstance(value, (int, float)):
            return float(value)
        
        return float(value)
        
    except (ValueError, TypeError, OverflowError):
        print(f"⚠️ Could not convert '{value}' to float, using default {default}")
        return default

def convert_to_integer(value, default=0):
    """Alias for convert_to_int for backward compatibility"""
    return convert_to_int(value, default)

def safe_get_config_value(config, section, key, default=None, value_type=str):
    """Safely get a configuration value with type conversion"""
    try:
        if not config.has_section(section):
            return default
        
        if not config.has_option(section, key):
            return default
        
        value = config.get(section, key)
        
        if value_type == int:
            return convert_to_int(value, default)
        elif value_type == float:
            return convert_to_float(value, default)
        elif value_type == bool:
            return config.getboolean(section, key, fallback=default)
        else:
            return value
            
    except Exception as e:
        print(f"⚠️ Error getting config value [{section}][{key}]: {e}")
        return default

def validate_airport_code(code):
    """Validate airport code format (ICAO or IATA)"""
    if not code or not isinstance(code, str):
        return False
    
    code = code.strip().upper()
    
    # ICAO codes are 4 characters, IATA codes are 3
    if len(code) == 4:
        return code.isalpha()  # ICAO: 4 letters
    elif len(code) == 3:
        return code.isalpha()  # IATA: 3 letters
    
    return False

def format_currency(amount, currency_symbol="$"):
    """Format a number as currency"""
    try:
        if amount is None:
            return f"{currency_symbol}0.00"
        
        amount = float(amount)
        
        if abs(amount) >= 1_000_000:
            return f"{currency_symbol}{amount/1_000_000:.1f}M"
        elif abs(amount) >= 1_000:
            return f"{currency_symbol}{amount/1_000:.1f}k"
        else:
            return f"{currency_symbol}{amount:.2f}"
            
    except (ValueError, TypeError):
        return f"{currency_symbol}0.00"

def format_distance(distance_nm):
    """Format distance in nautical miles"""
    try:
        distance = float(distance_nm)
        return f"{distance:,.0f} nm"
    except (ValueError, TypeError):
        return "0 nm"

def format_time_duration(hours):
    """Format time duration in hours to hours:minutes"""
    try:
        total_hours = float(hours)
        hours_part = int(total_hours)
        minutes_part = int((total_hours - hours_part) * 60)
        return f"{hours_part:02d}:{minutes_part:02d}"
    except (ValueError, TypeError):
        return "00:00"
'''
    
    with open('core/utils.py', 'w', encoding='utf-8') as f:
        f.write(utils_content)
    
    print("   ✅ Created complete core/utils.py")

def create_airline_data():
    """Create airline data files"""
    print("🛩️ Creating airline data...")
    
    # Create JSON file
    airlines_data = [
        {"id": 1, "name": "SkyLine Airways", "icao": "SKY", "iata": "SL", "country": "United States", "hub": "KJFK"},
        {"id": 2, "name": "Pacific Airlines", "icao": "PAC", "iata": "PA", "country": "United States", "hub": "KLAX"},
        {"id": 3, "name": "Atlantic Express", "icao": "ATL", "iata": "AE", "country": "United States", "hub": "KATL"},
        {"id": 4, "name": "Continental Airways", "icao": "CON", "iata": "CO", "country": "United States", "hub": "KORD"},
        {"id": 5, "name": "Sunrise Airlines", "icao": "SUN", "iata": "SR", "country": "United States", "hub": "KMIA"},
        {"id": 6, "name": "Mountain Air", "icao": "MTN", "iata": "MA", "country": "United States", "hub": "KDEN"},
        {"id": 7, "name": "Coastal Airlines", "icao": "CST", "iata": "CS", "country": "United States", "hub": "KSEA"},
        {"id": 8, "name": "Desert Wings", "icao": "DST", "iata": "DW", "country": "United States", "hub": "KPHX"},
        {"id": 9, "name": "Northern Express", "icao": "NOR", "iata": "NE", "country": "United States", "hub": "KMSP"},
        {"id": 10, "name": "Golden State Air", "icao": "GSA", "iata": "GS", "country": "United States", "hub": "KSFO"}
    ]
    
    # Remove corrupted airline_data.db if it exists
    if os.path.exists('airline_data.db'):
        try:
            with open('airline_data.db', 'rb') as f:
                header = f.read(16)
            
            if not header.startswith(b'SQLite format 3'):
                print("   🗑️ Removing corrupted airline_data.db...")
                os.remove('airline_data.db')
        except Exception as e:
            print(f"   ⚠️ Could not check airline_data.db: {e}")
    
    # Create JSON file
    try:
        with open('airline_data.json', 'w', encoding='utf-8') as f:
            json.dump(airlines_data, f, indent=2, ensure_ascii=False)
        print("   ✅ Created airline_data.json")
    except Exception as e:
        print(f"   ❌ Failed to create airline_data.json: {e}")

def create_config_file():
    """Create config.ini if it doesn't exist"""
    if os.path.exists('config.ini'):
        print("✅ config.ini already exists")
        return
    
    print("📝 Creating config.ini...")
    
    config_content = '''[DATABASES]
userdata = userdata.db

[PREFERENCES]
theme = flatly
data_refresh_rate = 30
selected_airline = 
homehub = KJFK
current_location = KJFK

[AeroAPI]
api_key = YOUR_API_KEY
api_secret = YOUR_API_SECRET

[AIRCRAFT_MARKETPLACE]
default_market_size = 50
auto_refresh_hours = 24
enable_market_fluctuations = true
default_financing_rate = 0.05

[SIMULATION]
time_acceleration = 1.0
auto_save_interval = 300
enable_weather_effects = true
enable_competition = false
'''
    
    try:
        with open('config.ini', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("   ✅ Created config.ini")
    except Exception as e:
        print(f"   ❌ Failed to create config.ini: {e}")

def test_imports():
    """Test if all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        # Test core utils
        sys.path.insert(0, '.')
        from core.utils import convert_to_int, load_airlines_json
        print("   ✅ core.utils imports working")
        
        # Test airline data loading
        airlines = load_airlines_json()
        print(f"   ✅ Loaded {len(airlines)} airlines")
        
        # Test convert_to_int function
        result = convert_to_int("123", 0)
        print(f"   ✅ convert_to_int('123') = {result}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def main():
    """Run complete fix"""
    print("🔧 VIRTUAL AIRLINE MANAGEMENT - COMPLETE FIX")
    print("=" * 50)
    
    # Step 1: Backup existing files
    backup_existing_files()
    
    # Step 2: Create complete core/utils.py
    create_core_utils()
    
    # Step 3: Create airline data
    create_airline_data()
    
    # Step 4: Create config file
    create_config_file()
    
    # Step 5: Test imports
    if test_imports():
        print("\n🎉 ALL FIXES COMPLETED SUCCESSFULLY!")
        print("\n📋 Next steps:")
        print("1. Run: python scripts/initial_setup.py")
        print("2. Run: python main.py")
        print("\n✅ Your application should now work correctly!")
    else:
        print("\n❌ Some issues remain. Please check the error messages above.")
        print("   You may need to manually verify the file contents.")

if __name__ == "__main__":
    main()
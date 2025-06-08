# core/utils.py - Complete version with all required functions

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

def create_flet_button(text, icon, on_click, style="primary"):
    """Create a Flet button with icon and text"""
    import flet as ft
    
    style_map = {
        "primary": ft.ButtonStyle(bgcolor="#2196f3", color="#ffffff"),
        "success": ft.ButtonStyle(bgcolor="#4caf50", color="#ffffff"),
        "info": ft.ButtonStyle(bgcolor="#03a9f4", color="#ffffff"),
        "warning": ft.ButtonStyle(bgcolor="#ff9800", color="#ffffff"),
        "danger": ft.ButtonStyle(bgcolor="#f44336", color="#ffffff"),
        "secondary": ft.ButtonStyle(bgcolor="#bdbdbd", color="#ffffff"),
        "light": ft.ButtonStyle(bgcolor="#eeeeee", color="#000000"),
    }
    
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        style=style_map.get(style, style_map["primary"]),
        width=150,
        height=60,
    )

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

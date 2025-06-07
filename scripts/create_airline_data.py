# scripts/create_airline_data.py

import json
import sqlite3
import os

def create_airline_json():
    """Create airline_data.json with sample airlines"""
    
    airlines_data = [
        {
            "id": 1,
            "name": "SkyLine Airways",
            "icao": "SKY",
            "iata": "SL",
            "country": "United States",
            "hub": "KJFK"
        },
        {
            "id": 2,
            "name": "Pacific Airlines",
            "icao": "PAC",
            "iata": "PA",
            "country": "United States", 
            "hub": "KLAX"
        },
        {
            "id": 3,
            "name": "Atlantic Express",
            "icao": "ATL",
            "iata": "AE",
            "country": "United States",
            "hub": "KATL"
        },
        {
            "id": 4,
            "name": "Continental Airways",
            "icao": "CON",
            "iata": "CO",
            "country": "United States",
            "hub": "KORD"
        },
        {
            "id": 5,
            "name": "Sunrise Airlines",
            "icao": "SUN",
            "iata": "SR",
            "country": "United States",
            "hub": "KMIA"
        },
        {
            "id": 6,
            "name": "Mountain Air",
            "icao": "MTN",
            "iata": "MA",
            "country": "United States",
            "hub": "KDEN"
        },
        {
            "id": 7,
            "name": "Coastal Airlines",
            "icao": "CST",
            "iata": "CS",
            "country": "United States",
            "hub": "KSEA"
        },
        {
            "id": 8,
            "name": "Desert Wings",
            "icao": "DST",
            "iata": "DW",
            "country": "United States",
            "hub": "KPHX"
        },
        {
            "id": 9,
            "name": "Northern Express",
            "icao": "NOR",
            "iata": "NE",
            "country": "United States",
            "hub": "KMSP"
        },
        {
            "id": 10,
            "name": "Golden State Air",
            "icao": "GSA",
            "iata": "GS",
            "country": "United States",
            "hub": "KSFO"
        }
    ]
    
    # Write to JSON file
    with open('airline_data.json', 'w') as f:
        json.dump(airlines_data, f, indent=2)
    
    print("✅ Created airline_data.json with 10 sample airlines")
    return airlines_data

def create_airline_database():
    """Create airline_data.db if needed"""
    
    if os.path.exists('airline_data.db'):
        print("✅ airline_data.db already exists")
        return
    
    conn = sqlite3.connect('airline_data.db')
    cursor = conn.cursor()
    
    # Create airlines table
    cursor.execute('''
        CREATE TABLE airlines (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            icao TEXT,
            iata TEXT,
            country TEXT,
            hub TEXT
        )
    ''')
    
    # Get airline data
    airlines_data = create_airline_json()
    
    # Insert airlines into database
    for airline in airlines_data:
        cursor.execute('''
            INSERT INTO airlines (id, name, icao, iata, country, hub)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            airline['id'],
            airline['name'],
            airline['icao'],
            airline['iata'],
            airline['country'],
            airline['hub']
        ))
    
    conn.commit()
    conn.close()
    
    print("✅ Created airline_data.db with 10 sample airlines")

def fix_utils_file():
    """Fix the utils.py file to handle missing airline data gracefully"""
    
    utils_file = "core/utils.py"
    
    if not os.path.exists(utils_file):
        print("⚠️ core/utils.py not found - creating a basic version")
        
        # Create core directory if it doesn't exist
        os.makedirs("core", exist_ok=True)
        
        utils_content = '''# core/utils.py

import json
import sqlite3
import os
import tkinter as tk
from tkinter import ttk
import threading
import time
from functools import wraps

def load_airlines_json():
    """Load airlines from JSON file or database"""
    
    # Try JSON file first
    if os.path.exists('airline_data.json'):
        try:
            with open('airline_data.json', 'r') as f:
                airlines = json.load(f)
                print(f"✅ Loaded {len(airlines)} airlines from JSON")
                return airlines
        except Exception as e:
            print(f"Error loading airline_data.json: {e}")
    
    # Try database
    if os.path.exists('airline_data.db'):
        try:
            conn = sqlite3.connect('airline_data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, icao, iata, country, hub FROM airlines")
            rows = cursor.fetchall()
            conn.close()
            
            airlines = []
            for row in rows:
                airlines.append({
                    'id': row[0],
                    'name': row[1],
                    'icao': row[2],
                    'iata': row[3],
                    'country': row[4],
                    'hub': row[5]
                })
            
            print(f"✅ Loaded {len(airlines)} airlines from database")
            return airlines
            
        except Exception as e:
            print(f"Error loading airline database: {e}")
    
    # Return default airlines if no data found
    print("⚠️ No airline data found, using defaults")
    return [
        {
            "id": 1,
            "name": "Default Airlines",
            "icao": "DEF",
            "iata": "DA", 
            "country": "United States",
            "hub": "KJFK"
        }
    ]

def create_button(parent, text, style, command, icon=None):
    """Create a button with optional icon"""
    if icon:
        btn = ttk.Button(parent, text=text, bootstyle=style, command=command, image=icon, compound='top')
    else:
        btn = ttk.Button(parent, text=text, bootstyle=style, command=command)
    
    return btn

def debounce(wait_time):
    """Decorator to debounce function calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def call_func():
                func(*args, **kwargs)
            
            # Cancel previous call if exists
            if hasattr(wrapper, '_timer'):
                wrapper._timer.cancel()
            
            # Schedule new call
            wrapper._timer = threading.Timer(wait_time / 1000.0, call_func)
            wrapper._timer.start()
        
        return wrapper
    return decorator
'''
        
        with open(utils_file, 'w') as f:
            f.write(utils_content)
        
        print("✅ Created core/utils.py")
    else:
        print("✅ core/utils.py already exists")

def main():
    """Main function to fix airline data issues"""
    print("🔧 Fixing airline data issues...")
    
    # Create necessary files
    create_airline_json()
    create_airline_database() 
    fix_utils_file()
    
    print("\n🎉 All airline data issues fixed!")
    print("\nFiles created:")
    print("• airline_data.json - JSON airline data")
    print("• airline_data.db - SQLite airline database") 
    print("• core/utils.py - Utility functions")
    
    print("\n📋 Now you can run: python main.py")

if __name__ == "__main__":
    main()
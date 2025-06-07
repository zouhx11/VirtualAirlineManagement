# scripts/debug_main.py

import sys
import os
import traceback

# Add current directory to path so we can import modules
sys.path.insert(0, '.')

def test_airline_loading():
    """Test airline data loading"""
    print("🧪 Testing airline data loading...")
    
    try:
        from core.utils import load_airlines_json
        airlines = load_airlines_json()
        
        print(f"✅ Loaded {len(airlines)} airlines")
        
        # Show first few airlines
        for i, airline in enumerate(airlines[:3]):
            print(f"   {i+1}. {airline}")
        
        return airlines
        
    except Exception as e:
        print(f"❌ Error loading airlines: {e}")
        traceback.print_exc()
        return None

def test_airline_selection_format():
    """Test the airline selection format that main.py expects"""
    print("\n🧪 Testing airline selection format...")
    
    try:
        airlines = test_airline_loading()
        if not airlines:
            return
        
        # Test the format that main.py creates
        formatted_airlines = [f"{airline['name']} (ID: {airline['id']})" for airline in airlines]
        
        print("📋 Formatted airline list:")
        for i, formatted in enumerate(formatted_airlines[:3]):
            print(f"   {i+1}. {formatted}")
        
        # Test parsing logic from main.py
        print("\n🔍 Testing parsing logic...")
        
        test_selection = formatted_airlines[0]
        print(f"Testing with: '{test_selection}'")
        
        # This is the parsing logic from main.py
        if "(ID: " in test_selection and ")" in test_selection:
            try:
                airline_id = int(test_selection.split("(ID: ")[1].split(")")[0])
                airline_name = test_selection.split(" (ID: ")[0]
                print(f"✅ Parsed successfully:")
                print(f"   ID: {airline_id}")
                print(f"   Name: {airline_name}")
            except (IndexError, ValueError) as e:
                print(f"❌ Parsing failed: {e}")
        else:
            print("❌ Invalid format - missing '(ID: ' and ')'")
            
    except Exception as e:
        print(f"❌ Error in format testing: {e}")
        traceback.print_exc()

def test_config_loading():
    """Test configuration loading"""
    print("\n🧪 Testing configuration loading...")
    
    try:
        from core.config_manager import ConfigManager
        config_manager = ConfigManager()
        
        # Test getting preferences
        theme = config_manager.get_preference('theme', 'flatly')
        selected_airline = config_manager.get_preference('selected_airline', '')
        
        print(f"✅ Config loaded successfully")
        print(f"   Theme: {theme}")
        print(f"   Selected airline: '{selected_airline}'")
        
        # Test database path
        db_path = config_manager.get_database_path('userdata')
        print(f"   Database path: {db_path}")
        print(f"   Database exists: {os.path.exists(db_path)}")
        
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        traceback.print_exc()

def test_database_connection():
    """Test database connection"""
    print("\n🧪 Testing database connection...")
    
    try:
        from core.database_utils import fetch_pilot_data
        from core.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        
        # Try to fetch pilot data (this might fail if no pilots exist)
        try:
            pilots = fetch_pilot_data(1)  # Test with airline ID 1
            print(f"✅ Database connection works")
            print(f"   Found {len(pilots) if pilots else 0} pilots for airline ID 1")
        except Exception as e:
            print(f"⚠️ Database query failed (this might be normal): {e}")
            
    except Exception as e:
        print(f"❌ Error testing database: {e}")
        traceback.print_exc()

def simulate_main_app_startup():
    """Simulate the main app startup to find where it fails"""
    print("\n🧪 Simulating main app startup...")
    
    try:
        import ttkbootstrap as ttk
        from core.config_manager import ConfigManager
        from core.utils import load_airlines_json
        
        print("✅ Imports successful")
        
        # Test ConfigManager
        config_manager = ConfigManager()
        print("✅ ConfigManager created")
        
        # Test airline loading
        airlines = load_airlines_json()
        print(f"✅ Airlines loaded: {len(airlines)}")
        
        # Test airline formatting
        all_airlines = [f"{airline['name']} (ID: {airline['id']})" for airline in airlines]
        print(f"✅ Airlines formatted: {len(all_airlines)}")
        
        # Test preferences loading
        selected_airline = config_manager.get_preference('selected_airline', '')
        print(f"✅ Selected airline from config: '{selected_airline}'")
        
        # Test the specific condition that might be causing the error
        if selected_airline and selected_airline.strip():
            print("🔍 Testing selected airline parsing...")
            
            # This is where the error might occur in ensure_pilot_exists()
            if "(ID: " in selected_airline and ")" in selected_airline:
                try:
                    airline_id = int(selected_airline.split("(ID: ")[1].split(")")[0])
                    airline_name = selected_airline.split(" (ID: ")[0]
                    print(f"✅ Selected airline parsed successfully:")
                    print(f"   ID: {airline_id}, Name: {airline_name}")
                except Exception as e:
                    print(f"❌ This is likely the error: {e}")
                    print(f"   Selected airline value: '{selected_airline}'")
            else:
                print(f"❌ Selected airline has invalid format: '{selected_airline}'")
        else:
            print("ℹ️ No airline selected in config (this is normal for first run)")
        
    except Exception as e:
        print(f"❌ Error in simulation: {e}")
        traceback.print_exc()

def check_files():
    """Check if all required files exist"""
    print("\n📁 Checking required files...")
    
    required_files = [
        'config.ini',
        'airline_data.json', 
        'core/utils.py',
        'core/config_manager.py',
        'core/database_utils.py',
        'main.py'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} ({size} bytes)")
        else:
            print(f"❌ {file_path} - MISSING")

def main():
    """Run all debug tests"""
    print("🔍 VIRTUAL AIRLINE MANAGEMENT - DEBUG ANALYSIS")
    print("=" * 60)
    
    check_files()
    test_airline_loading()
    test_airline_selection_format()
    test_config_loading()
    test_database_connection()
    simulate_main_app_startup()
    
    print("\n🎯 RECOMMENDATIONS:")
    print("1. Check the 'Selected airline from config' value above")
    print("2. If it shows an invalid format, edit config.ini and clear the selected_airline value")
    print("3. The error dialog should show the specific issue")

if __name__ == "__main__":
    main()
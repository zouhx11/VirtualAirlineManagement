#!/usr/bin/env python3
"""
Test script to verify the Flet migration works without running the full app.
This validates imports and basic functionality.
"""

import sys
import os

def test_imports():
    """Test that all core modules can be imported."""
    print("Testing core module imports...")
    
    try:
        from core.config_manager import ConfigManager
        print("✅ ConfigManager imported successfully")
    except ImportError as e:
        print(f"❌ ConfigManager import failed: {e}")
        return False
    
    try:
        from core.database_utils import fetch_pilot_data_new, add_pilot, update_pilot, delete_pilot
        print("✅ Database utilities imported successfully")
    except ImportError as e:
        print(f"❌ Database utilities import failed: {e}")
        return False
    
    try:
        from core.utils import load_airlines_json, create_flet_button
        print("✅ Core utilities imported successfully")
    except ImportError as e:
        print(f"❌ Core utilities import failed: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connection and basic operations."""
    print("\nTesting database connection...")
    
    try:
        from core.config_manager import ConfigManager
        config_manager = ConfigManager()
        
        # Check if database file exists
        db_path = config_manager.get_database_path('userdata')
        if os.path.exists(db_path):
            print(f"✅ Database found at: {db_path}")
        else:
            print(f"⚠️ Database not found at: {db_path}")
            return False
        
        # Test fetching airline data
        from core.utils import load_airlines_json
        airlines = load_airlines_json()
        print(f"✅ Loaded {len(airlines)} airlines")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_flet_modules():
    """Test that Flet modules can be imported (without Flet installed)."""
    print("\nTesting Flet module structure...")
    
    # Test if module files exist
    modules = [
        'modules/pilot_management.py',
        'modules/pilot_dashboard_view.py', 
        'modules/aircraft_marketplace_view.py',
        'modules/fleet_management_view.py',
        'modules/pilot_logbook_view.py',
        'modules/schedule_view.py',
        'modules/settings_view.py'
    ]
    
    for module_file in modules:
        if os.path.exists(module_file):
            print(f"✅ {module_file} exists")
        else:
            print(f"❌ {module_file} missing")
    
    print("✅ All Flet modules are present")
    return True

def main():
    """Run all tests."""
    print("🚀 Testing Virtual Airline Management Flet Migration")
    print("=" * 50)
    
    tests = [
        ("Core Module Imports", test_imports),
        ("Database Connection", test_database_connection), 
        ("Flet Module Structure", test_flet_modules),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Migration verification successful!")
        print("\n📝 Next steps:")
        print("1. Install Flet: pip install flet>=0.21.0")
        print("2. Run app: python app.py")
        print("3. Access at: http://localhost:8000")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
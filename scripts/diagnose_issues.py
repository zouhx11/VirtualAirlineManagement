# scripts/diagnose_issues.py

import os
import json
import sqlite3

def diagnose_files():
    """Diagnose file issues in the VirtualAirlineManagement directory"""
    
    print("🔍 VIRTUAL AIRLINE MANAGEMENT - FILE DIAGNOSTIC")
    print("=" * 60)
    
    # Check current directory
    current_dir = os.getcwd()
    print(f"📁 Current directory: {current_dir}")
    
    # List all files in current directory
    print(f"\n📋 Files in current directory:")
    try:
        files = os.listdir('.')
        for file in sorted(files):
            if os.path.isfile(file):
                size = os.path.getsize(file)
                print(f"   📄 {file} ({size} bytes)")
            elif os.path.isdir(file):
                print(f"   📁 {file}/")
    except Exception as e:
        print(f"   ❌ Error listing files: {e}")
    
    # Check specific files
    files_to_check = [
        'config.ini',
        'main.py', 
        'airline_data.json',
        'airline_data.db',
        'userdata.db'
    ]
    
    print(f"\n🔍 Checking specific files:")
    for filename in files_to_check:
        print(f"\n📄 {filename}:")
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"   ✅ Exists ({size} bytes)")
            
            # Check file content based on extension
            if filename.endswith('.json'):
                check_json_file(filename)
            elif filename.endswith('.db'):
                check_database_file(filename)
            elif filename.endswith('.ini'):
                check_ini_file(filename)
                
        else:
            print(f"   ❌ Does not exist")
    
    # Check directories
    dirs_to_check = ['core', 'modules', 'scripts', 'icons']
    print(f"\n📁 Checking directories:")
    for dirname in dirs_to_check:
        print(f"\n📁 {dirname}/:")
        if os.path.exists(dirname) and os.path.isdir(dirname):
            print(f"   ✅ Exists")
            try:
                files = os.listdir(dirname)
                for file in sorted(files):
                    print(f"   📄 {file}")
            except Exception as e:
                print(f"   ❌ Error listing contents: {e}")
        else:
            print(f"   ❌ Does not exist")

def check_json_file(filename):
    """Check JSON file validity"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Try to parse JSON
        data = json.loads(content)
        print(f"   ✅ Valid JSON ({len(data)} items)")
        
        # Show first few characters
        preview = content[:100].replace('\n', ' ')
        print(f"   📝 Preview: {preview}...")
        
    except json.JSONDecodeError as e:
        print(f"   ❌ Invalid JSON: {e}")
    except UnicodeDecodeError as e:
        print(f"   ❌ Encoding error: {e}")
        
        # Try to read with different encodings
        for encoding in ['latin-1', 'cp1252']:
            try:
                with open(filename, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"   ⚠️  Readable with {encoding} encoding")
                break
            except:
                continue
    except Exception as e:
        print(f"   ❌ Error reading: {e}")

def check_database_file(filename):
    """Check SQLite database file"""
    try:
        # Check if it's actually a SQLite file
        with open(filename, 'rb') as f:
            header = f.read(16)
            
        if header.startswith(b'SQLite format 3'):
            print(f"   ✅ Valid SQLite database")
            
            # Try to connect and list tables
            conn = sqlite3.connect(filename)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            print(f"   📊 Tables: {[table[0] for table in tables]}")
            
            # Check airlines table if it exists
            if any(table[0] == 'airlines' for table in tables):
                cursor.execute("SELECT COUNT(*) FROM airlines")
                count = cursor.fetchone()[0]
                print(f"   👥 Airlines: {count} records")
            
            conn.close()
            
        else:
            print(f"   ❌ Not a valid SQLite file")
            print(f"   📝 Header: {header}")
            
    except Exception as e:
        print(f"   ❌ Error checking database: {e}")

def check_ini_file(filename):
    """Check INI configuration file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"   ✅ Readable")
        
        # Show sections
        import configparser
        config = configparser.ConfigParser()
        config.read(filename)
        
        sections = config.sections()
        print(f"   📋 Sections: {sections}")
        
        # Show database path if exists
        if 'DATABASES' in sections:
            userdata = config.get('DATABASES', 'userdata', fallback='Not set')
            print(f"   🗄️  Database path: {userdata}")
            
    except Exception as e:
        print(f"   ❌ Error reading config: {e}")

def fix_common_issues():
    """Fix common issues automatically"""
    print(f"\n🔧 ATTEMPTING AUTOMATIC FIXES")
    print("=" * 40)
    
    # Fix 1: Create missing airline_data.json
    if not os.path.exists('airline_data.json'):
        print("🔨 Creating airline_data.json...")
        try:
            default_airlines = [
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
                }
            ]
            
            with open('airline_data.json', 'w', encoding='utf-8') as f:
                json.dump(default_airlines, f, indent=2, ensure_ascii=False)
            
            print("   ✅ Created airline_data.json")
            
        except Exception as e:
            print(f"   ❌ Failed to create airline_data.json: {e}")
    
    # Fix 2: Remove corrupted airline_data.db if it exists
    if os.path.exists('airline_data.db'):
        try:
            with open('airline_data.db', 'rb') as f:
                header = f.read(16)
            
            if not header.startswith(b'SQLite format 3'):
                print("🔨 Removing corrupted airline_data.db...")
                os.remove('airline_data.db')
                print("   ✅ Removed corrupted database")
        except Exception as e:
            print(f"   ⚠️  Could not check/remove airline_data.db: {e}")
    
    # Fix 3: Create core directory and utils.py if missing
    if not os.path.exists('core'):
        print("🔨 Creating core directory...")
        os.makedirs('core', exist_ok=True)
        print("   ✅ Created core directory")
    
    if not os.path.exists('core/utils.py'):
        print("🔨 Creating core/utils.py...")
        # This would be created by the previous utils fix script
        print("   ⚠️  Run: python scripts/create_airline_data.py to create utils.py")

def main():
    """Run complete diagnostic"""
    diagnose_files()
    fix_common_issues()
    
    print(f"\n💡 RECOMMENDATIONS:")
    print("1. Run: python scripts/create_airline_data.py")
    print("2. Run: python scripts/initial_setup.py") 
    print("3. Run: python main.py")
    print("\n🎯 If issues persist, share this diagnostic output!")

if __name__ == "__main__":
    main()
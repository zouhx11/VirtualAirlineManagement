import json
import os
from json import JSONDecodeError
from core.config_manager import ConfigManager

config_manager = ConfigManager("config.ini")

def load_airlines_json():
    """Load and parse the airlines JSON file derived from the airline_data.db path."""
    # Get the userdata database path and replace with airline_data.db
    userdata_db = config_manager.get_database_path('userdata')
    json_file_path = userdata_db.replace("userdata.db", "airline_data.db")

    if not os.path.exists(json_file_path):
        print(f"Airline data file not found: {json_file_path}")
        return []

    try:
        with open(json_file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except IOError as e:
        print(f"IOError while reading airline data from {json_file_path}: {e}")
    except ValueError as e:
        # ValueError can occur if the file is not valid JSON prior to Python 3.5
        print(f"ValueError: Invalid JSON format in {json_file_path}: {e}")
    except JSONDecodeError as e:
        # JSONDecodeError is more explicit if using Python 3.5+
        print(f"JSONDecodeError: Invalid JSON in {json_file_path}: {e}")

    return []

import json
from configparser import ConfigParser

# Load config to get the JSON file path
config = ConfigParser()
config.read("config.ini")
json_file_path = config.get("DATABASES", "userdata").replace("userdata.db", "airline_data.db")

def load_airlines_json():
    """Loads and parses the airlines JSON file."""
    try:
        with open(json_file_path, "r") as file:
            airlines_data = json.load(file)
        return airlines_data
    except Exception as e:
        print(f"Error loading airline data: {e}")
        return []

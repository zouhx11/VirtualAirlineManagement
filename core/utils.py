import json
import os
from json import JSONDecodeError
import ttkbootstrap as ttk
from ttkbootstrap.constants import LEFT
import functools
import threading
from core.config_manager import ConfigManager
import logging

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



def create_button(parent, text, style, command, icon):
    return ttk.Button(
        parent,
        text=text,
        image=icon,
        compound=LEFT,
        bootstyle=style,
        command=command
    )


def debounce(wait_time):
    """Decorator to debounce a function using Tkinter's after method."""
    def decorator(fn):
        @functools.wraps(fn)
        def debounced(self, *args, **kwargs):
            if hasattr(self, '_debounce_id'):
                self.root.after_cancel(self._debounce_id)
            self._debounce_id = self.root.after(wait_time, lambda: fn(self, *args, **kwargs))
        return debounced
    return decorator

def convert_to_int(value):
    """Safely convert a value to int, return None if conversion fails."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        value = value.strip()
        if value.isdigit():
            return int(value)
        else:
            try:
                converted_value = int(float(value))
                logging.debug(f"convert_to_int: Converted string '{value}' to integer '{converted_value}'.")
                return converted_value
            except ValueError:
                logging.error(f"convert_to_int: Cannot convert value '{value}' to int.")
                return None
    if isinstance(value, float):
        return int(value)
    logging.error(f"convert_to_int: Unsupported type '{type(value)}' for value '{value}'.")
    return None

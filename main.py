import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import simpledialog
from configparser import ConfigParser
import os
import sqlite3
from PIL import Image, ImageTk
from modules.pilot_management_gui import PilotManagementGUI
from modules.schedule import ScheduleViewer
from modules.fleet_management import FleetManagement
from modules.pilot_logbook import PilotLogbook
from modules.pilot_dashboard import create_dashboard
from core.settings import open_settings
from core.database_utils import fetch_pilot_data, add_pilot
from core.utils import load_airlines_json

# Load configuration
CONFIG_FILE = "config.ini"
config = ConfigParser()
config.read(CONFIG_FILE)

def clear_window(root):
    """Clears all widgets in the main window."""
    for widget in root.winfo_children():
        widget.destroy()

def check_pilot_existence():
    """Checks if at least one pilot exists in the database."""
    pilots = fetch_pilot_data()
    return len(pilots) > 0

def prompt_create_pilot():
    """Prompts the user to create a new pilot."""
    pilot_name = simpledialog.askstring("Create Pilot", "Enter the pilot's name:")
    if pilot_name:
        try:
            add_pilot(pilot_name, home_hub="Unknown", current_location="Unknown")
            Messagebox.show_info("Success", f"Pilot '{pilot_name}' created successfully!")
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to create pilot: {e}")
    else:
        Messagebox.show_warning("Warning", "Pilot creation canceled. The application requires at least one pilot to function.")

def load_icon(file_path):
    """Load and resize an icon image or return a placeholder if loading fails."""
    try:
        img = Image.open(file_path).resize((32, 32), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Error loading icon {file_path}: {e}")
        return None

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Airline Management")
        self.root.geometry("1024x768")
        self.selected_airline = ttk.StringVar()
        self.selected_location = ttk.StringVar()
        self.ensure_pilot_exists()
        self.load_airline_from_config()
        self.load_location_from_config()
        self.show_main_menu()

    def ensure_pilot_exists(self):
        """Ensures at least one pilot exists in the database."""
        if not check_pilot_existence():
            Messagebox.show_info("Pilot Required", "No pilots found. Let's create one!")
            prompt_create_pilot()
            if not check_pilot_existence():
                Messagebox.show_error("Error", "No pilot created. The application will close.")
                self.root.quit()

    def load_airline_from_config(self):
        """Load the previously selected airline from the configuration file."""
        saved_airline = config['PREFERENCES'].get('selected_airline', None)
        if saved_airline:
            self.selected_airline.set(saved_airline)
    
    def load_location_from_config(self):
        """Load the previously selected location from the configuration file."""
        saved_location = config['PREFERENCES'].get('current_location', None)
        if saved_location:
            self.selected_location.set(saved_location)

    def save_airline_to_config(self, airline):
        """Save the selected airline to the configuration file."""
        config['PREFERENCES']['selected_airline'] = airline
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)

    def show_main_menu(self):
        """Displays the main menu with a grid layout for improved aesthetics."""
        clear_window(self.root)

        title_label = ttk.Label(self.root, text="Virtual Airline Management", font=("Arial", 24, "bold"))
        title_label.pack(pady=20)

        # Airline Selection Dropdown
        airlines = load_airlines_json()
        if not airlines:
            Messagebox.show_warning("Warning", "No airline data available. Please check the JSON file.")
            return

        ttk.Label(self.root, text="Select Airline:", font=("Arial", 14)).pack(pady=10)
        airline_dropdown = ttk.Combobox(
            self.root,
            textvariable=self.selected_airline,
            values=[f"{airline['name']} (ID: {airline['id']})" for airline in airlines],
            state="normal"
        )
        airline_dropdown.pack(pady=10)

        # Make Combobox searchable
        def filter_dropdown(event):
            """Filter the dropdown dynamically while keeping it open."""
            value = airline_dropdown.get().lower()
            filtered = [f"{airline['name']} (ID: {airline['id']})" for airline in airlines if value in airline['name'].lower()]

            # Temporarily disable the event to prevent recursion
            #airline_dropdown.unbind("<KeyRelease>")
            
            # Update the dropdown values
            airline_dropdown['values'] = filtered
            
            # Keep focus on the dropdown input and cursor position
            airline_dropdown.focus_set()
            airline_dropdown.icursor(len(value))  # Set cursor to the end of the input
            
            

            # Force the dropdown to stay open
            #airline_dropdown.event_generate('<Down>')
        # Re-bind the event after updating
        airline_dropdown.bind("<KeyRelease>", filter_dropdown)

        confirm_button = ttk.Button(self.root, text="Confirm Airline", bootstyle=SUCCESS, command=self.confirm_airline)
        confirm_button.pack(pady=10)

        grid_frame = ttk.Frame(self.root, padding=20)
        grid_frame.pack(fill=BOTH, expand=True)
        
        self.icons = {
            "Pilot Management": load_icon("icons/pilot.png"),
            "Flight Schedules": load_icon("icons/schedule.png"),
            "Fleet Management": load_icon("icons/fleet.png"),
            "Pilot Logbook": load_icon("icons/logbook.png"),
            "Pilot Dashboard": load_icon("icons/dashboard.png"),
            "Settings": load_icon("icons/settings.png"),
            "Exit": load_icon("icons/exit.png")
        }

        buttons = [
            ("Pilot Management", SUCCESS, self.open_pilot_management),
            ("Flight Schedules", PRIMARY, self.open_flight_schedule),
            ("Fleet Management", INFO, self.open_fleet_management),
            ("Pilot Logbook", WARNING, self.open_pilot_logbook),
            ("Pilot Dashboard", SECONDARY, self.open_pilot_dashboard),
            ("Settings", LIGHT, self.open_settings_window),
            ("Exit", DANGER, self.root.quit)
        ]

        for idx, (text, style, command) in enumerate(buttons):
            ttk.Button(
                grid_frame, text=text, image=self.icons[text], compound=LEFT, bootstyle=style, command=command
            ).grid(row=idx // 2, column=idx % 2, padx=10, pady=10, sticky=NSEW)

        for i in range((len(buttons) + 1) // 2):
            grid_frame.rowconfigure(i, weight=1)
        for j in range(2):
            grid_frame.columnconfigure(j, weight=1)

    def confirm_airline(self):
        """Confirm the selected airline and associate it with the pilot in the database."""
        selected_airline = self.selected_airline.get()
        if not selected_airline or selected_airline == "Select an Airline":
            Messagebox.show_warning("Warning", "Please select an airline!")
            return
        
        try:
            # Extract airline ID and name
            airline_id = int(selected_airline.split("(ID: ")[1].split(")")[0])
            airline_name = selected_airline.split(" (ID: ")[0]
            
            # Update the pilot's associated airline in the database
            conn = sqlite3.connect(config.get("DATABASES", "userdata"))
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE pilots
                SET airline_id = ?
                WHERE id = 1
                """,
                (airline_id,)
            )
            conn.commit()
            conn.close()
            
            # Update config and notify the user
            self.save_airline_to_config(selected_airline)
            Messagebox.show_info("Airline Selected", f"Airline '{airline_name}' (ID: {airline_id}) has been associated with the pilot.")
        
        except sqlite3.Error as e:
            Messagebox.show_error("Error", f"Failed to associate airline with pilot: {e}")
        except Exception as e:
            Messagebox.show_error("Error", f"Unexpected error: {e}")

    def open_pilot_management(self):
        try:
            config.read(CONFIG_FILE)  # Reload the config file to get the latest values
            airline_info = self.selected_airline.get()  # Example: "Qantas (ID: 123)"
            airline_id = int(airline_info.split("(ID: ")[1].split(")")[0])
            airline_name = airline_info.split(" (ID: ")[0]
            PilotManagementGUI(ttk.Toplevel(self.root), airline_id, airline_name)
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to open Pilot Management: {e}")

    def open_flight_schedule(self):
        try:
            config.read(CONFIG_FILE)  # Reload the config file to get the latest values
            self.load_location_from_config()
            current_location = self.selected_location.get()
            selected_airline = int(self.selected_airline.get().split("(ID: ")[1].split(")")[0])

            if not current_location or not selected_airline:
                Messagebox.show_error("Error", "Current location or selected airline is not set.")
                return

            airline_id = selected_airline  # Extract airline ID
            ScheduleViewer(ttk.Toplevel(self.root), current_location, airline_id)
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to open Flight Schedules: {e}")
    


    def open_fleet_management(self):
        try:
            config.read(CONFIG_FILE)  # Reload the config file to get the latest values
            self.load_location_from_config()
            print(f"Opening Fleet Management for airline: {self.selected_airline.get()}")
            airline_id = int(self.selected_airline.get().split("(ID: ")[1].split(")")[0])
            current_location = self.selected_location.get()  # Extract string value
            print(f"Current Location: {current_location}")
            FleetManagement(ttk.Toplevel(self.root), airline_id, current_location)
        except Exception as e:
            print(f"Error initializing Fleet Management: {e}")
            Messagebox.show_error("Error", f"Failed to open Fleet Management: {e}")



    def open_pilot_logbook(self):
        try:
            PilotLogbook(ttk.Toplevel(self.root))
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to open Pilot Logbook: {e}")

    def open_pilot_dashboard(self):
        try:
            config.read(CONFIG_FILE)  # Reload the config file to get the latest values
            self.load_location_from_config()
            print(f"Opening Fleet Management for airline: {self.selected_airline.get()}")
            airline_id = int(self.selected_airline.get().split("(ID: ")[1].split(")")[0])
            dashboard_window = ttk.Toplevel(self.root)
            create_dashboard(dashboard_window, dashboard_window.destroy, airline_id)
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to open Pilot Dashboard: {e}")

    def open_settings_window(self):
        try:
            open_settings(self.root)
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to open Settings: {e}")

if __name__ == "__main__":
    theme = config['PREFERENCES'].get('theme', 'flatly')
    root = ttk.Window(themename=theme)
    app = MainApp(root)
    root.mainloop()

# main.py

import logging
import sqlite3
from tkinter import simpledialog, BOTH
from typing import Optional

# Third-party imports
import ttkbootstrap as ttk
from ttkbootstrap.constants import SUCCESS, INFO, WARNING, PRIMARY, SECONDARY, LIGHT, DANGER, LEFT
from ttkbootstrap.dialogs import Messagebox
from PIL import Image, ImageTk

# Local application imports
from modules.pilot_management_gui import PilotManagementGUI
from modules.schedule import ScheduleViewer
from modules.fleet_management import FleetManagement
from modules.pilot_logbook import PilotLogbook
from modules.pilot_dashboard import create_dashboard
from core.settings import open_settings
from core.database_utils import fetch_pilot_data, add_pilot
from core.utils import load_airlines_json, create_button, debounce
from core.config_manager import ConfigManager

def clear_window(root):
    """Clear all widgets in the main window."""
    for widget in root.winfo_children():
        widget.destroy()

class MainApp:
    def __init__(self, root):
        """Initialize the main application."""
        self.root = root
        self.config_manager = ConfigManager()

        # Load and apply theme
        self.apply_theme()

        self.selected_airline = ttk.StringVar()
        self.selected_location = ttk.StringVar()

        # Load user preferences from config
        self.load_preferences()

        # Ensure at least one pilot exists before proceeding
        self.ensure_pilot_exists()

        # Load icons once
        self.icons = self.load_icons()

        self.root.title("Virtual Airline Management")
        self.root.geometry("1024x768")
        self.show_main_menu()

    def apply_theme(self, theme: Optional[str] = None):
        theme = theme or self.config_manager.get_preference('theme', 'flatly')
        self.root.style.theme_use(theme)

    def ensure_pilot_exists(self):
        """Ensures that at least one pilot exists in the database."""
        selected_airline = self.selected_airline.get()
        if not selected_airline:
            Messagebox.show_warning("Warning", "No airline selected. Please select an airline first.")
            return  # Optionally, you might want to quit the application here

        try:
            airline_id, _ = self.parse_airline_selection(selected_airline)
            if not fetch_pilot_data(airline_id):
                Messagebox.show_info("Pilot Required", "No pilots found. Let's create one!")
                pilot_name = simpledialog.askstring("Create Pilot", "Enter the pilot's name:")
                if pilot_name:
                    try:
                        add_pilot(pilot_name, home_hub="Unknown", current_location="Unknown")
                        Messagebox.show_info("Success", f"Pilot '{pilot_name}' created successfully!")
                    except Exception as e:
                        Messagebox.show_error("Error", f"Failed to create pilot: {e}")
                        self.root.quit()
                else:
                    Messagebox.show_error("Error", "No pilot created. The application will close.")
                    self.root.quit()
        except ValueError as e:
            Messagebox.show_error("Error", f"Invalid airline selection: {e}")
            self.root.quit()

    def load_preferences(self):
        """Load previously saved preferences from the config file."""
        saved_airline = self.config_manager.get_preference('selected_airline', '')
        self.selected_airline.set(saved_airline)

        saved_location = self.config_manager.get_preference('current_location', '')
        self.selected_location.set(saved_location)

    def load_icons(self):
        """Load icon images once and store them in a dictionary."""
        def load_icon(file_path):
            try:
                img = Image.open(file_path).resize((32, 32), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error loading icon {file_path}: {e}")
                return None

        icons_map = {
            "Pilot Management": "icons/pilot.png",
            "Flight Schedules": "icons/schedule.png",
            "Fleet Management": "icons/fleet.png",
            "Pilot Logbook": "icons/logbook.png",
            "Pilot Dashboard": "icons/dashboard.png",
            "Settings": "icons/settings.png",
            "Exit": "icons/exit.png"
        }
        return {key: load_icon(path) for key, path in icons_map.items()}

    def show_main_menu(self):
        """Displays the main menu."""
        clear_window(self.root)

        title_label = ttk.Label(self.root, text="Virtual Airline Management", font=("Arial", 24, "bold"))
        title_label.pack(pady=20)

        # Airline Selection Dropdown
        airlines = load_airlines_json()
        if not airlines:
            Messagebox.show_warning("Warning", "No airline data available. Please check the JSON file.")
            return

        ttk.Label(self.root, text="Select Airline:", font=("Arial", 14)).pack(pady=10)

        all_airlines = [f"{airline['name']} (ID: {airline['id']})" for airline in airlines]
        airline_dropdown = ttk.Combobox(self.root, textvariable=self.selected_airline, values=all_airlines, state="normal")
        airline_dropdown.pack(pady=10)

        # Filter function for the combobox
        self.setup_dropdown(airline_dropdown, all_airlines)

        confirm_button = ttk.Button(self.root, text="Confirm Airline", bootstyle=SUCCESS, command=self.confirm_airline)
        confirm_button.pack(pady=10)

        grid_frame = ttk.Frame(self.root, padding=20)
        grid_frame.pack(fill=BOTH, expand=True)

        self.setup_buttons(grid_frame)

    def setup_buttons(self, grid_frame):
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
            btn = create_button(grid_frame, text, style, command, self.icons[text])
            btn.grid(row=idx // 2, column=idx % 2, padx=10, pady=10, sticky="NSEW")

        for i in range((len(buttons) + 1) // 2):
            grid_frame.rowconfigure(i, weight=1)
        for j in range(2):
            grid_frame.columnconfigure(j, weight=1)

    @debounce(300)  # 300 milliseconds debounce delay
    def filter_dropdown(self, _event, combobox, all_values):
        """Filter the dropdown dynamically based on user input."""
        value = combobox.get().lower()
        filtered = [val for val in all_values if value in val.lower()]
        combobox['values'] = filtered
        # Keep focus and cursor at the end
        combobox.focus_set()
        combobox.icursor(len(value))

    def parse_airline_selection(self, selection: str) -> tuple[int, str]:
        if "(ID: " in selection and ")" in selection:
            try:
                airline_id = int(selection.split("(ID: ")[1].split(")")[0])
                airline_name = selection.split(" (ID: ")[0]
                return airline_id, airline_name
            except (IndexError, ValueError) as e:
                raise ValueError(f"Error parsing airline selection: {e}")
        else:
            raise ValueError("Invalid airline selection format.")

    def confirm_airline(self):
        """Confirm and save the selected airline."""
        selected = self.selected_airline.get()
        if not selected:
            Messagebox.show_warning("Warning", "Please select an airline!")
            return

        try:
            airline_id, airline_name = self.parse_airline_selection(selected)
            user_db = self.config_manager.get_database_path('userdata')

            # Update the pilot's associated airline in the database
            with sqlite3.connect(user_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE pilots SET airline_id = ? WHERE id = 1",
                    (airline_id,)
                )
                conn.commit()

            # Update config and notify the user
            self.config_manager.set_preference('selected_airline', selected)
            Messagebox.show_info("Airline Selected", f"Airline '{airline_name}' (ID: {airline_id}) has been associated with the pilot.")
        except sqlite3.Error as e:
            Messagebox.show_error("Error", f"Failed to associate airline with pilot: {e}")
        except Exception as e:
            Messagebox.show_error("Error", f"Unexpected error: {e}")

    def open_pilot_management(self):
        try:
            airline_id, airline_name = self.parse_airline_selection(self.selected_airline.get())
            PilotManagementGUI(ttk.Toplevel(self.root), airline_id, airline_name)
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to open Pilot Management: {e}")

    def open_flight_schedule(self):
        try:
            airline_id, _ = self.parse_airline_selection(self.selected_airline.get())
            current_location = self.config_manager.get_preference('current_location', '')
            if not current_location or not airline_id:
                Messagebox.show_error("Error", "Current location or selected airline is not set.")
                return
            ScheduleViewer(ttk.Toplevel(self.root), current_location, airline_id)
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to open Flight Schedules: {e}")

    def open_fleet_management(self):
        try:
            airline_id, _ = self.parse_airline_selection(self.selected_airline.get())
            current_location = self.selected_location.get()
            FleetManagement(ttk.Toplevel(self.root), airline_id, current_location)
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to open Fleet Management: {e}")

    def open_pilot_logbook(self):
        try:
            PilotLogbook(ttk.Toplevel(self.root))  # Removed airline_id
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to open Pilot Logbook: {e}")

    def open_pilot_dashboard(self):
        try:
            airline_id, airline_name = self.parse_airline_selection(self.selected_airline.get())
            dashboard_window = ttk.Toplevel(self.root)
            create_dashboard(dashboard_window, dashboard_window.destroy, airline_id, airline_name)
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to open Pilot Dashboard: {e}")

    def open_settings_window(self):
        try:
            open_settings(self.root)
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to open Settings: {e}")

    def setup_dropdown(self, combobox, all_values):
        combobox.bind("<KeyRelease>", lambda event: self.filter_dropdown(event, combobox, all_values))

if __name__ == "__main__":
    # Initialize with a base theme (overridden by config in __init__)
    root = ttk.Window(themename="flatly")
    app = MainApp(root)
    root.mainloop()

import sqlite3
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import StringVar
from core.config_manager import ConfigManager
from core.database_utils import (
    update_pilot_property,
    fetch_pilot_data,
    calculate_total_hours,
    calculate_rank_and_achievements
)
import os

CONFIG_FILE = "config.ini"

class PilotManagementGUI:
    def __init__(self, root, airline_id, airline_name):
        self.root = root
        self.airline_id = airline_id
        self.airline_name = airline_name

        # Initialize configuration manager
        self.config_manager = ConfigManager(CONFIG_FILE)
        
        # Widgets variables
        self.home_hub_var = StringVar()
        self.new_location_var = StringVar()

        self.setup_window()
        self.create_widgets()
        self.load_pilot_data()

    def setup_window(self):
        """Configure the main window."""
        self.root.title(f"Pilot Management - {self.airline_name} (ID: {self.airline_id})")

    def create_widgets(self):
        """Create and layout all GUI elements."""
        form_frame = ttk.Frame(self.root, padding=10)
        form_frame.pack(pady=20, padx=20, fill=X)

        ttk.Label(form_frame, text="Home Hub:", font=("Arial", 12)).grid(row=0, column=0, sticky="e", padx=(0, 5))
        home_hub_entry = ttk.Entry(form_frame, textvariable=self.home_hub_var, width=20)
        home_hub_entry.grid(row=0, column=1, padx=10)

        ttk.Label(form_frame, text="New Location:", font=("Arial", 12)).grid(row=1, column=0, sticky="e", padx=(0, 5))
        new_location_entry = ttk.Entry(form_frame, textvariable=self.new_location_var, width=20)
        new_location_entry.grid(row=1, column=1, padx=10)

        # Buttons for updating home hub and jumpseat
        update_button = ttk.Button(form_frame, text="Update Home Hub", bootstyle=INFO, command=self.update_home_hub)
        update_button.grid(row=2, column=0, columnspan=2, pady=10, sticky=EW)

        jumpseat_button = ttk.Button(form_frame, text="Jumpseat", bootstyle=PRIMARY, command=self.jumpseat_pilot)
        jumpseat_button.grid(row=3, column=0, columnspan=2, pady=10, sticky=EW)

        # Label to display selected airline
        ttk.Label(self.root, text=f"Airline: {self.airline_name} (ID: {self.airline_id})", 
                  font=("Arial", 14, "bold")).pack(pady=5)

        # Treeview for pilot data
        self.pilot_table = ttk.Treeview(self.root, columns=("ID", "Name", "Home Hub", "Current Location", "Rank"), show="headings")
        self.pilot_table.heading("ID", text="ID")
        self.pilot_table.heading("Name", text="Name")
        self.pilot_table.heading("Home Hub", text="Home Hub")
        self.pilot_table.heading("Current Location", text="Current Location")
        self.pilot_table.heading("Rank", text="Rank")
        self.pilot_table.pack(pady=10, fill="both", expand=True)

        self.total_hours_label = ttk.Label(self.root, text="Total Flight Hours: 0.00 hours", font=("Arial", 12))
        self.total_hours_label.pack(pady=10)

    def get_user_db_path(self):
        """Retrieve user database path from the configuration manager."""
        return self.config_manager.get_database_path('userdata')

    def update_home_hub(self):
        """Update the pilot's home hub using the centralized database utilities."""
        new_home_hub = self.home_hub_var.get().strip()
        if not new_home_hub:
            Messagebox.show_error("Home Hub cannot be empty.", "Error")
            return
        if update_pilot_property(self.airline_id, "homeHub", new_home_hub):
            Messagebox.show_info("Home Hub updated successfully!", "Success")
            self.load_pilot_data()

    def jumpseat_pilot(self):
        """Change the pilot's current location using the centralized database utilities."""
        new_location = self.new_location_var.get().strip()
        if not new_location:
            Messagebox.show_error("New location must be provided.", "Error")
            return
        if update_pilot_property(self.airline_id, "currentLocation", new_location):
            self.config_manager.set_preference("current_location", new_location)
            Messagebox.show_info(f"Jumpseat successful! New location: {new_location}", "Success")
            self.load_pilot_data()

    def load_pilot_data(self):
        """Load pilot data using the centralized database utilities."""
        rows = fetch_pilot_data(self.airline_id)
        # Clear the treeview
        for item in self.pilot_table.get_children():
            self.pilot_table.delete(item)
        if not rows:
            Messagebox.show_warning("No pilots found for this airline.", "No Data")
        # Update total hours and label
        total_hours = calculate_total_hours(self.airline_id)
        self.total_hours_label.config(text=f"Total Flight Hours: {total_hours:.2f} hours")
        # Populate the treeview with updated data
        for row in rows:
            pilot_id, name, home_hub, current_location, rank, _ = row
            computed_rank, _ = calculate_rank_and_achievements(pilot_id, self.airline_id)
            self.pilot_table.insert("", "end", values=(pilot_id, name, home_hub, current_location, computed_rank))

if __name__ == "__main__":
    root = ttk.Window(themename="flatly")  # Adjust theme as needed
    airline_id = 1  # Placeholder for testing
    airline_name = "Test Airline"  # Placeholder for testing
    gui = PilotManagementGUI(root, airline_id, airline_name)
    root.mainloop()

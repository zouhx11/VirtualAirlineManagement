import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from core.database_utils import fetch_fleet_data, update_aircraft_location
from configparser import ConfigParser
import tkinter as tk

class FleetManagement:
    def __init__(self, root, selected_airline_id, selected_current_location):
        self.root = root
        self.root.title("Fleet Management")
        self.root.geometry("1000x600")
        self.selected_airline_id = selected_airline_id
        self.selected_current_location = selected_current_location
        self.fleet_data = []

        # Top title
        title_label = ttk.Label(self.root, text="Fleet Management", font=("Helvetica", 20, "bold"))
        title_label.pack(pady=(20,10))

        # Control Frame for search, refresh, transfer
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(side=TOP, fill=X)

        # Search label and entry
        ttk.Label(control_frame, text="Search:", font=("Helvetica", 12)).pack(side=LEFT, padx=(0,5))
        self.search_var = ttk.StringVar()
        self.search_var.trace_add("write", self.update_filter)
        search_entry = ttk.Entry(control_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=LEFT, padx=(0,10))

        # Refresh button
        refresh_button = ttk.Button(control_frame, text="Refresh", bootstyle=INFO, command=self.load_fleet)
        refresh_button.pack(side=LEFT, padx=5)

        # Transfer button
        self.transfer_button = ttk.Button(control_frame, text="Transfer Selected Aircraft", bootstyle=PRIMARY, command=self.transfer_selected_aircraft)
        self.transfer_button.pack(side=LEFT, padx=5)

        # Frame for the fleet table
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=BOTH, expand=True)

        # Columns for the Treeview
        self.columns = ("id", "registration", "airframeIcao", "logHours", "logLocation")
        self.tree = ttk.Treeview(frame, columns=self.columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("registration", text="Registration")
        self.tree.heading("airframeIcao", text="ICAO")
        self.tree.heading("logHours", text="Logged Hours")
        self.tree.heading("logLocation", text="Location")

        self.tree.column("id", width=40, anchor=CENTER)
        self.tree.column("registration", width=150, anchor=W)
        self.tree.column("airframeIcao", width=100, anchor=CENTER)
        self.tree.column("logHours", width=120, anchor=E)
        self.tree.column("logLocation", width=100, anchor=CENTER)

        self.tree.pack(fill=BOTH, expand=True)

        # Scrollbar for the treeview
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Load fleet data
        self.load_fleet()

    def load_fleet(self):
        """Load full fleet data from the database filtered by the selected airline ID."""
        try:
            self.fleet_data = fetch_fleet_data(self.selected_airline_id)
            self.populate_tree(self.fleet_data)
        except Exception as e:
            print(f"Error loading fleet data: {e}")
            Messagebox.show_error(f"Error loading fleet data: {e}", "Database Error")

    def populate_tree(self, data):
        """Populate the treeview with the given fleet data."""
        # Clear existing data in the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new rows into the treeview
        for row in data:
            # row expected format: (id, registration, airframeIcao, logHours, logLocation)
            self.tree.insert("", tk.END, values=row)

    def update_filter(self, *args):
        """
        Filter the displayed fleet based on the search query.
        Matches if the query is found in registration, airframeIcao, or logLocation.
        """
        query = self.search_var.get().strip().lower()
        if query == "":
            # No filter, show all data
            self.populate_tree(self.fleet_data)
            return

        filtered = []
        for row in self.fleet_data:
            # row: (id, reg, icao, hours, location)
            # Convert to lower for case-insensitive match
            reg = str(row[1]).lower()
            icao = str(row[2]).lower()
            loc = str(row[4]).lower()

            if query in reg or query in icao or query in loc:
                filtered.append(row)

        self.populate_tree(filtered)

    def transfer_selected_aircraft(self):
        """
        Transfer the selected aircraft to the pilot's current location.
        """
        selected = self.tree.selection()
        if not selected:
            Messagebox.show_warning("Please select an aircraft to transfer.", "No aircraft selected")
            return

        selected_item = self.tree.item(selected[0])
        values = selected_item["values"]
        aircraft_id = values[0]

        confirm = Messagebox.yesno(
            title="Confirm Transfer",
            message=(f"Are you sure you want to transfer aircraft {values[1]} "
                     f"from {values[4]} to {self.selected_current_location}?")
        )
        if not confirm:
            return

        success = update_aircraft_location(aircraft_id, self.selected_current_location)
        if success:
            Messagebox.show_info(f"Aircraft {values[1]} transferred to {self.selected_current_location}.", "Success")
            self.load_fleet()  # Refresh the table to reflect changes
        else:
            Messagebox.show_error("Failed to transfer aircraft. Check logs for details.", "Error")


if __name__ == "__main__":
    config = ConfigParser()
    config.read("config.ini")
    selected_airline = config['PREFERENCES'].get('selected_airline', None)
    current_location = config['PREFERENCES'].get('current_location', None)
    if selected_airline:
        selected_airline_id = int(selected_airline.split("(ID: ")[1].split(")")[0])
    else:
        selected_airline_id = None

    root = ttk.Window(themename=config['PREFERENCES'].get('theme', 'flatly'))
    app = FleetManagement(root, selected_airline_id, current_location)
    root.mainloop()

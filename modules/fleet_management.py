import tkinter as tk
from tkinter import ttk, messagebox
from core.database_utils import fetch_fleet_data
from configparser import ConfigParser

class FleetManagement:
    def __init__(self, root, selected_airline_id, selected_current_location):
        print(f"Initializing FleetManagement with airline ID: {selected_airline_id}")
        print(f"Initializing FleetManagement with current location: {selected_current_location}")
        self.root = root
        self.root.title("Fleet Management")
        self.root.geometry("800x600")
        self.selected_airline_id = selected_airline_id
        self.selected_current_location = selected_current_location

        # Frame for the fleet table
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Treeview widget for displaying fleet
        self.tree = ttk.Treeview(frame, columns=("registration", "airframeIcao", "logHours"), show="headings")
        self.tree.heading("registration", text="Registration")
        self.tree.heading("airframeIcao", text="Aircraft Type (ICAO)")
        self.tree.heading("logHours", text="Logged Hours")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Scrollbar for the treeview
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Load fleet data
        self.load_fleet()
    
    def load_fleet(self):
        """Load fleet data from the database filtered by the selected airline ID."""
        try:
            """Load the previously selected airline from the configuration file."""
            
            fleet_data = fetch_fleet_data(self.selected_airline_id, self.selected_current_location)
            print(f"Fetched fleet data: {fleet_data}")
            # Clear existing data in the treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Insert new rows into the treeview
            for row in fleet_data:
                self.tree.insert("", tk.END, values=row)

        except Exception as e:
            print(f"Error loading fleet data: {e}")
            messagebox.showerror("Database Error", f"Error loading fleet data: {e}")


if __name__ == "__main__":
    config = ConfigParser()
    config.read("config.ini")
    selected_airline = config['PREFERENCES'].get('selected_airline', None)
    current_location = config['PREFERENCES'].get('current_location', None)
    if selected_airline:
        selected_airline_id = int(selected_airline.split("(ID: ")[1].split(")")[0])
    else:
        selected_airline_id = None

    root = tk.Tk()
    app = FleetManagement(root, selected_airline_id, selected_current_location)
    root.mainloop()

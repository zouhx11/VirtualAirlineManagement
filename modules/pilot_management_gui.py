import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from configparser import ConfigParser
from core.database_utils import calculate_rank_and_achievements

import os

# Configuration file
CONFIG_FILE = "config.ini"

# Load database paths
config = ConfigParser()
config.read(CONFIG_FILE)

data_paths = {
    "userdata": config.get("DATABASES", "userdata"),
}

class PilotManagementGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pilot Management")
        self.create_gui()
        self.load_pilot_data()

    def create_gui(self):
        """Create the GUI for pilot management."""
        self.frame = tk.Frame(self.root)
        self.frame.pack(pady=20, padx=20)

        tk.Label(self.frame, text="Home Hub:").grid(row=0, column=0, sticky="e")
        self.home_hub_entry = tk.Entry(self.frame)
        self.home_hub_entry.grid(row=0, column=1, padx=10)

        tk.Label(self.frame, text="New Location:").grid(row=1, column=0, sticky="e")
        self.new_location_entry = tk.Entry(self.frame)
        self.new_location_entry.grid(row=1, column=1, padx=10)

        update_button = tk.Button(self.frame, text="Update Home Hub", command=self.update_home_hub)
        update_button.grid(row=2, columnspan=2, pady=10)

        jumpseat_button = tk.Button(self.frame, text="Jumpseat", command=self.jumpseat_pilot)
        jumpseat_button.grid(row=3, columnspan=2, pady=10)

        # Treeview for displaying pilot data
        self.pilot_table = ttk.Treeview(self.root, columns=("ID", "Name", "Home Hub", "Current Location", "Rank"), show="headings")
        self.pilot_table.heading("ID", text="ID")
        self.pilot_table.heading("Name", text="Name")
        self.pilot_table.heading("Home Hub", text="Home Hub")
        self.pilot_table.heading("Current Location", text="Current Location")
        self.pilot_table.heading("Rank", text="Rank")
        self.pilot_table.pack(pady=10, fill=tk.BOTH, expand=True)

        # Label to display total flight hours
        self.total_hours_label = tk.Label(self.root, text="Total Flight Hours: 0.00 hours")
        self.total_hours_label.pack(pady=10)

    def update_home_hub(self):
        """Update pilot's home hub in the database."""
        try:
            new_home_hub = self.home_hub_entry.get().strip()

            if not new_home_hub:
                messagebox.showerror("Error", "Home Hub cannot be empty.")
                return

            conn = sqlite3.connect(data_paths["userdata"])
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE pilots
                SET homeHub = ?
                WHERE id = 1
                """,
                (new_home_hub,),
            )

            if cursor.rowcount == 0:
                messagebox.showerror("Error", "Failed to update Home Hub.")
            else:
                conn.commit()
                messagebox.showinfo("Success", "Home Hub updated successfully.")
                self.root.destroy()

            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))

    def jumpseat_pilot(self):
        """Change the current location of the pilot."""
        try:
            new_location = self.new_location_entry.get().strip()

            if not new_location:
                messagebox.showerror("Error", "New location must be provided.")
                return

            conn = sqlite3.connect(data_paths["userdata"])
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE pilots
                SET currentLocation = ?
                WHERE id = 1
                """,
                (new_location,),
            )

            if cursor.rowcount == 0:
                messagebox.showerror("Error", "Failed to update current location.")
            else:
                conn.commit()
                config.set("PREFERENCES", "current_location", new_location)
                with open(CONFIG_FILE, "w") as configfile:
                    config.write(configfile)
                messagebox.showinfo("Success", f"Jumpseat successful! New location: {new_location}")
                self.root.destroy()

            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))

    def calculate_total_hours(self):
        """Calculate total flight hours from the logbook."""
        try:
            conn = sqlite3.connect(data_paths["userdata"])
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT actualDep, actualArr FROM logbook
                """
            )
            rows = cursor.fetchall()

            total_minutes = 0
            for dep, arr in rows:
                if dep and arr:
                    try:
                        dep_minutes = int(dep)
                        arr_minutes = int(arr)
                        total_minutes += (arr_minutes - dep_minutes) // 60
                    except ValueError:
                        continue

            total_hours = total_minutes / 60
            conn.close()
            return total_hours
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))
            return 0

    def load_pilot_data(self):
        """Load pilot data from the database and update the GUI."""
        try:
            conn = sqlite3.connect(data_paths["userdata"])
            cursor = conn.cursor()

            # Fetch pilot data
            cursor.execute("SELECT id, name, homeHub, currentLocation, rank FROM pilots WHERE id = 1")
            rows = cursor.fetchall()

            # Clear the treeview
            for item in self.pilot_table.get_children():
                self.pilot_table.delete(item)

            # Populate the treeview with updated data
            for row in rows:
                pilot_id = row[0]  # Assuming ID is the first column
                airline_id = 1  # Replace with logic to get airline_id dynamically
                rank, achievements = calculate_rank_and_achievements(pilot_id, airline_id)
                updated_row = (*row[:-1], rank)  # Update rank in row data
                self.pilot_table.insert("", "end", values=updated_row)

            # Update total flight hours label
            total_hours = self.calculate_total_hours()
            self.total_hours_label.config(text=f"Total Flight Hours: {total_hours:.2f} hours")

            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    gui = PilotManagementGUI(root)
    root.mainloop()

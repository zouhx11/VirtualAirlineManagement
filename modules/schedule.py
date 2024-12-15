import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from core.database_utils import fetch_schedules_by_location_and_airline
from configparser import ConfigParser

class ScheduleViewer:
    def __init__(self, root, current_location, airline_id):
        self.root = root
        self.current_location = current_location
        self.airline_id = airline_id
        self.root.title("Flight Schedules")

        # Frame for the schedule table
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Treeview widget for displaying schedules
        self.tree = ttk.Treeview(frame, columns=("Flight", "Departure", "Arrival", "Fleet"), show="headings")
        self.tree.heading("Flight", text="Flight")
        self.tree.heading("Departure", text="Departure")
        self.tree.heading("Arrival", text="Arrival")
        self.tree.heading("Fleet", text="Fleet")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Scrollbar for the treeview
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Load schedule data
        self.load_schedules()

    def load_schedules(self):
        """Load schedules from the database filtered by current location and airline."""
        if not self.current_location or not self.airline_id:
            messagebox.showerror("Error", "Current location or airline ID is not set.")
            return

        schedules = fetch_schedules_by_location_and_airline(self.current_location, self.airline_id)

        # Clear existing data in the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new rows into the treeview
        for row in schedules:
            self.tree.insert("", tk.END, values=row)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScheduleViewer(root)
    root.mainloop()

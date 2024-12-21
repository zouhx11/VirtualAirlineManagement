import logging
from datetime import datetime, timedelta
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from core.config_manager import ConfigManager
from core.database_utils import (
    fetch_pilot_data,
    fetch_logbook_data
)
import sqlite3  # Ensure sqlite3 is imported for database operations
import tkinter as tk
from tkinter import ttk

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pilot_logbook.log"),
        logging.StreamHandler()
    ]
)

class PilotLogbook:
    def __init__(self, root):
        logging.debug("Initializing PilotLogbook")
        self.root = root
        self.root.title("Pilot Logbook")
        try:
            self.root.geometry("1000x600")

            # Initialize ConfigManager
            self.config_manager = ConfigManager("config.ini")

            self.pilot_rank = None
            self.airline_hours = None

            # Current full dataset and filtered dataset
            self.full_flight_data = []
            self.filtered_flight_data = []

            self.flights_per_page = 50  # Number of rows per page
            self.current_page_number = 0
            logging.debug("Creating widgets")
            self.create_widgets()
            logging.debug("Loading data")
            self.load_data()
            logging.debug("Updating status bar")
            self.update_status_bar()
        except Exception as e:
            logging.exception("An error occurred during Pilot Logbook initialization.")
            Messagebox.show_error("Initialization Error", f"An unexpected error occurred: {e}")
            self.root.destroy()
            return

    def create_widgets(self):
        logging.debug("Creating widgets for Pilot Logbook")
        try:
            # Search bar
            self.search_var = tk.StringVar()
            self.search_var.trace("w", self.apply_filter)
            search_entry = ttk.Entry(self.root, textvariable=self.search_var)
            search_entry.grid(row=0, column=0, padx=10, pady=10, sticky='ew')

            # Treeview with Scrollbars
            self.tree = ttk.Treeview(self.root, columns=("Flight Number", "Origin", "Destination", "Start Time", "End Time", "Status", "Duration"), show='headings')
            for col in self.tree["columns"]:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100, anchor='center')

            # Vertical Scrollbar
            self.v_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=self.v_scrollbar.set)

            # Horizontal Scrollbar
            self.h_scrollbar = ttk.Scrollbar(self.root, orient="horizontal", command=self.tree.xview)
            self.tree.configure(xscrollcommand=self.h_scrollbar.set)

            # Position Treeview and Scrollbars
            self.tree.grid(row=1, column=0, sticky='nsew')
            self.v_scrollbar.grid(row=1, column=1, sticky='ns')
            self.h_scrollbar.grid(row=2, column=0, sticky='ew')

            # Configure grid weights
            self.root.grid_rowconfigure(1, weight=1)
            self.root.grid_columnconfigure(0, weight=1)

            # Pagination Controls
            self.pagination_frame = ttk.Frame(self.root)
            self.pagination_frame.grid(row=3, column=0, columnspan=2, pady=10)

            self.prev_button = ttk.Button(self.pagination_frame, text="Previous", command=self.prev_page)
            self.prev_button.grid(row=0, column=0, padx=5)

            self.page_label = ttk.Label(self.pagination_frame, text=f"Page {self.current_page_number + 1}")
            self.page_label.grid(row=0, column=1, padx=5)

            self.next_button = ttk.Button(self.pagination_frame, text="Next", command=self.next_page)
            self.next_button.grid(row=0, column=2, padx=5)

            # Status Bar
            self.status_bar = ttk.Label(self.root, text="Loading data...", anchor='w')
            self.status_bar.grid(row=4, column=0, columnspan=2, sticky='ew')

            # Load initial data
            self.load_data()

        except Exception as e:
            logging.exception("An error occurred while creating widgets.")
            Messagebox.show_error("Widget Creation Error", f"An error occurred while creating widgets: {e}")

    def get_pilot_id(self):
        """Get the pilot ID from the database. Assuming first pilot is the active one."""
        try:
            pilot_data = fetch_pilot_data(1)
            if pilot_data and len(pilot_data) > 0:
                # pilot_data is a list of tuples: (id, name, homeHub, currentLocation, ...)
                logging.info(f"Fetched {len(pilot_data)} pilots from the database.")
                return pilot_data[0][0]  # The pilot ID
            logging.warning("No pilot data found.")
            return None
        except Exception as e:
            logging.error(f"Error fetching pilot data: {e}", exc_info=True)
            Messagebox.show_error("Error", f"Failed to fetch pilot data: {e}")
            return None

    def refresh_data(self):
        """Refresh data from the database."""
        self.search_var.set("")  # Clear the search bar
        self.load_data()
        self.update_status_bar()

    def load_data(self):
        """Load pilot logbook data from the database."""
        logging.debug("Loading data from the database")
        try:
            rows = fetch_logbook_data()
            logging.debug(f"Fetched {len(rows)} rows from the database.")
            logging.debug(f"Fetched {rows}")

            if not rows:
                logging.warning("No pilot data found.")
                Messagebox.show_warning("No Data", "No pilot data found.")
                return

            formatted_data = self.format_data(rows)
            logging.debug(f"Fetched {formatted_data}")
            self.full_flight_data = formatted_data
            self.filtered_flight_data = formatted_data
            self.current_page_number = 0
            self.load_page()
        except Exception as e:
            logging.error(f"Error in load_data: {e}", exc_info=True)
            Messagebox.show_error("Data Load Error", f"An error occurred while loading data: {e}")

    def load_page(self):
        """Load a specific page of data."""
        logging.debug("Loading page")
        start_index = self.current_page_number * self.flights_per_page
        end_index = start_index + self.flights_per_page
        page_data = self.filtered_flight_data[start_index:end_index]
        formatted = page_data
        self.populate_tree(formatted)
        self.update_status_bar()
        self.page_label.config(text=f"Page {self.current_page_number + 1}")

    def populate_tree(self, formatted_data):
        """Populate the tree view with formatted data."""
        # Clear existing data
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insert new rows
        for row in formatted_data:
            self.tree.insert("", "end", values=row)

    def apply_filter(self, *args):
        """Filter the displayed flights based on the search query."""
        query = self.search_var.get().strip().lower()
        logging.debug(f"Applying filter with query: '{query}'")

        if query:
            self.filtered_flight_data = []
            for row in self.full_flight_data:
                # row format: (flightNumber, dep, arr, departureTime, arrivalTime, status, duration)
                if (query in str(row[0]).lower() or 
                    query in str(row[1]).lower() or 
                    query in str(row[2]).lower()):
                    self.filtered_flight_data.append(row)
        else:
            self.filtered_flight_data = self.full_flight_data.copy()

        logging.debug(f"Filtered data count: {len(self.filtered_flight_data)}")
        self.current_page_number = 0
        self.load_page()

    def update_status_bar(self):
        """Update status bar with flight count and optionally pilot rank and airline hours."""
        total_count = len(self.filtered_flight_data)
        page_count = (total_count + self.flights_per_page - 1) // self.flights_per_page
        status_text = f"Total Flights: {total_count} | Page {self.current_page_number + 1} of {page_count}"
        # If we have airline-specific rank and hours, display them
        if self.pilot_rank is not None and self.airline_hours is not None:
            status_text += f" | Rank: {self.pilot_rank} | Airline Hours: {self.airline_hours:.2f}"
        self.status_bar.config(text=status_text)
        logging.debug(f"Status Bar Updated: {status_text}")

    def format_data(self, rows):
        """Format raw data by converting timestamps to datetime strings and calculating duration."""
        formatted = []
        for row in rows:
            (
                flight_number,
                origin,
                destination,
                field4,
                timestamp1,
                field6,
                timestamp2,
                status,
                _field9,  # Added to ignore field9
            ) = row

            # Convert timestamp1 if it's not zero
            if timestamp1 != 0:
                datetime1 = datetime.fromtimestamp(timestamp1).strftime('%Y-%m-%d %H:%M:%S')
            else:
                datetime1 = ''

            # Convert timestamp2 if it's not zero
            if timestamp2 != 0:
                datetime2 = datetime.fromtimestamp(timestamp2).strftime('%Y-%m-%d %H:%M:%S')
            else:
                datetime2 = ''

            # Calculate duration if both timestamps are available
            if timestamp1 != 0 and timestamp2 != 0:
                duration_seconds = timestamp2 - timestamp1
                duration = str(timedelta(seconds=duration_seconds))
            else:
                duration = 'N/A'

            # Construct formatted row without field9
            formatted_row = [
                flight_number,
                origin,
                destination,
                datetime1,
                datetime2,
                status,          # Correctly include status
                duration,        # Added duration
            ]
            formatted.append(formatted_row)

        return formatted

    @staticmethod
    def format_unix_time(timestamp):
        """Convert a Unix timestamp to a readable format."""
        if timestamp is None:
            logging.error("Timestamp is None.")
            return "Invalid Timestamp"
        try:
            # Ensure the timestamp is an integer
            timestamp_int = int(timestamp)
            return datetime.utcfromtimestamp(timestamp_int).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError) as e:
            logging.error(f"Error formatting timestamp: {e}")
            return "Invalid Timestamp"

    def calculate_duration(self, actualDep, actualArr):
        """Calculate flight duration in hours."""
        if actualDep is None or actualArr is None:
            logging.warning("Scheduled or actual departure time is None.")
            return "N/A"
        try:
            duration_seconds = actualArr - actualDep
            duration_hours = duration_seconds / 3600
            logging.debug(f"Calculated duration: {duration_hours} hours")
            return f"{duration_hours:.2f}"
        except Exception as e:
            logging.error(f"Error calculating duration: {e}", exc_info=True)
            return "N/A"

    def next_page(self):
        """Go to the next page."""
        if (self.current_page_number + 1) * self.flights_per_page < len(self.filtered_flight_data):
            self.current_page_number += 1
            self.load_page()

    def prev_page(self):
        """Go to the previous page."""
        if self.current_page_number > 0:
            self.current_page_number -= 1
            self.load_page()

if __name__ == "__main__":
    app = ttk.Window(themename="flatly")
    PilotLogbook(app)  # Ensure no airline_id argument is passed
    app.mainloop()

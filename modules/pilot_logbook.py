import logging
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from core.config_manager import ConfigManager
from core.database_utils import (
    fetch_pilot_data,
    fetch_logbook_data
)
import sqlite3  # Ensure sqlite3 is imported for database operations

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
    def __init__(self, parent, airline_id):
        self.parent = parent
        self.parent.title("Pilot Logbook")
        self.parent.geometry("1000x600")

        # Initialize ConfigManager
        self.config_manager = ConfigManager("config.ini")

        # Attempt to determine pilot_id and airline_id
        self.pilot_id = self.get_pilot_id()
        self.airline_id = airline_id
        self.rank = None
        self.airline_hours = None

        # Current full dataset and filtered dataset
        self.full_data = []
        self.filtered_data = []

        self.page_size = 50  # Number of rows per page
        self.current_page = 0
        self.create_widgets()
        self.load_data()
        self.update_status_bar()

    def create_widgets(self):
        # Top frame for info, search and refresh controls
        top_frame = ttk.Frame(self.parent, padding=10)
        top_frame.pack(side=TOP, fill=X)

        # Informational Label
        info_label = ttk.Label(
            top_frame,
            text=("All completed flights are shown below.\n"
                  "Rank and airline-specific hours apply only to the selected airline."),
            font=("Helvetica", 10), 
            anchor=W, 
            justify=LEFT
        )
        info_label.pack(side=LEFT, padx=(0,20))

        # Frame for search and refresh
        control_frame = ttk.Frame(self.parent, padding=10)
        control_frame.pack(side=TOP, fill=X)

        # Search Label and Entry
        ttk.Label(control_frame, text="Search (Flight #, Dep, Arr):", font=("Helvetica", 12)).pack(side=LEFT, padx=(0, 5))
        self.search_var = ttk.StringVar()
        self.search_var.trace_add("write", self.apply_filter)
        search_entry = ttk.Entry(control_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=LEFT, padx=(0, 10))

        # Refresh Button
        refresh_button = ttk.Button(control_frame, text="Refresh", bootstyle=INFO, command=self.refresh_data)
        refresh_button.pack(side=LEFT, padx=5)

        # Frame for the Treeview
        tree_frame = ttk.Frame(self.parent, padding=10)
        tree_frame.pack(fill=BOTH, expand=True)

        # Updated columns to match fetched data (7 columns)
        columns = ("flightNumber", "dep", "arr", "departureTime", "arrivalTime", "status", "duration")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings"
        )
        self.tree.heading("flightNumber", text="Flight #")
        self.tree.heading("dep", text="Departure")
        self.tree.heading("arr", text="Arrival")
        self.tree.heading("departureTime", text="Departure Time")
        self.tree.heading("arrivalTime", text="Arrival Time")
        self.tree.heading("status", text="Status")
        self.tree.heading("duration", text="Duration (Hrs)")

        # Set column widths and alignment
        self.tree.column("flightNumber", width=100, anchor=W)
        self.tree.column("dep", width=80, anchor=CENTER)
        self.tree.column("arr", width=80, anchor=CENTER)
        self.tree.column("departureTime", width=150, anchor=W)
        self.tree.column("arrivalTime", width=150, anchor=W)
        self.tree.column("status", width=80, anchor=CENTER)
        self.tree.column("duration", width=100, anchor=E)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Pagination controls
        pagination_frame = ttk.Frame(self.parent, padding=10)
        pagination_frame.pack(side=BOTTOM, fill=X)

        self.prev_button = ttk.Button(pagination_frame, text="Previous", command=self.prev_page)
        self.prev_button.pack(side=LEFT, padx=5)

        self.next_button = ttk.Button(pagination_frame, text="Next", command=self.next_page)
        self.next_button.pack(side=LEFT, padx=5)

        # Status bar at the bottom
        self.status_bar = ttk.Label(self.parent, text="", anchor=W, font=("Helvetica", 10))
        self.status_bar.pack(side=BOTTOM, fill=X, padx=10, pady=5)

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
        """Fetch and display logbook data for the specified airline."""
        try:
            rows = fetch_logbook_data(self.airline_id)  # Ensure this function retrieves data
            logging.debug(f"Fetched {len(rows)} rows from the database.")
            self.full_data = rows  # Set full_data for filtering
            self.filtered_data = rows
            formatted = self.format_data(rows)
            self.populate_tree(formatted)
            self.update_status_bar()
        except Exception as e:
            logging.error(f"Error in load_data: {e}", exc_info=True)
            Messagebox.show_error("Error", f"Failed to load logbook data: {e}")

    def load_page(self):
        """Load a specific page of data."""
        start_index = self.current_page * self.page_size
        end_index = start_index + self.page_size
        page_data = self.filtered_data[start_index:end_index]
        formatted = self.format_data(page_data)
        self.populate_tree(formatted)
        self.update_status_bar()

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
            self.filtered_data = []
            for row in self.full_data:
                # row format: (flightNumber, dep, arr, departureTime, arrivalTime, status, duration)
                if (query in str(row[0]).lower() or 
                    query in str(row[1]).lower() or 
                    query in str(row[2]).lower()):
                    self.filtered_data.append(row)
        else:
            self.filtered_data = self.full_data.copy()

        logging.debug(f"Filtered data count: {len(self.filtered_data)}")
        self.current_page = 0
        self.load_page()

    def update_status_bar(self):
        """Update status bar with flight count and optionally pilot rank and airline hours."""
        total_count = len(self.filtered_data)
        page_count = (total_count + self.page_size - 1) // self.page_size
        status_text = f"Total Flights: {total_count} | Page {self.current_page + 1} of {page_count}"
        # If we have airline-specific rank and hours, display them
        if self.rank is not None and self.airline_hours is not None:
            status_text += f" | Rank: {self.rank} | Airline Hours: {self.airline_hours:.2f}"
        self.status_bar.config(text=status_text)
        logging.debug(f"Status Bar Updated: {status_text}")

    def format_data(self, rows):
        """Format raw rows into readable table data."""
        formatted = []
        for row in rows:
            formatted_row = [
                row[0],  # flightNumber
                row[1],  # dep
                row[2],  # arr
                self.format_unix_time(row[3]),  # departureTime
                self.format_unix_time(row[4]),  # arrivalTime
                row[5],  # status
                row[6],  # duration
            ]
            formatted.append(formatted_row)
        logging.debug(f"Formatted {len(formatted)} rows for display.")
        return formatted

    @staticmethod
    def format_unix_time(timestamp):
        """Convert a Unix timestamp to a readable format."""
        if not timestamp:
            return "-"
        try:
            return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logging.error(f"Error formatting timestamp: {e}", exc_info=True)
            return "-"

    def next_page(self):
        """Go to the next page."""
        if (self.current_page + 1) * self.page_size < len(self.filtered_data):
            self.current_page += 1
            self.load_page()

    def prev_page(self):
        """Go to the previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page()

if __name__ == "__main__":
    app = ttk.Window(themename="flatly")
    PilotLogbook(app, airline_id=1)  # Pass the airline_id as an argument
    app.mainloop()

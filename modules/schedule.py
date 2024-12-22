import tkinter as tk
from tkinter import ttk
import sqlite3
import random
import time
from datetime import datetime
from ttkbootstrap.dialogs import Messagebox
from core.database_utils import fetch_schedules_by_location_and_airline, fetch_fleet_data, update_aircraft_location, fetch_latest_location
from core.config_manager import ConfigManager
from core.utils import load_airlines_json
from datetime import timedelta
import requests  # Add this import at the top

class ScheduleViewer:
    def __init__(self, root, current_location, airline_id):
        self.root = root
        self.current_location = current_location
        self.airline_id = airline_id
        self.root.title("Flight Schedules")

        self.config_manager = ConfigManager("config.ini")
        self.target_airline = None
        self.airline_iata = "XX"  # fallback if not found
        self.airline_icao = "ZZZ" # fallback if not found
        self.fleet = []  # (id, registration, airframeIcao, logHours, logLocation)
        self.selected_aircraft_id = None
        self.selected_aircraft_location = None
        self.api_key = self.config_manager.get_aeroapi_credentials('api_key', '')

        # Top-level frames
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        load_db_button = ttk.Button(control_frame, text="Load DB Schedules", command=self.load_db_schedules, bootstyle="info")
        load_db_button.pack(side=tk.LEFT, padx=5)

        load_json_button = ttk.Button(control_frame, text="Load JSON Routes", command=self.load_json_routes, bootstyle="info")
        load_json_button.pack(side=tk.LEFT, padx=5)

        aeroapi_button = ttk.Button(control_frame, text="Load AeroAPI Schedules", command=self.load_aeroapi_schedules, bootstyle="info")
        aeroapi_button.pack(side=tk.LEFT, padx=5)

        # Aircraft selection frame
        aircraft_frame = ttk.Frame(self.root, padding=10)
        aircraft_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(aircraft_frame, text="Select Aircraft:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(0,5))
        self.aircraft_var = tk.StringVar()
        self.aircraft_combobox = ttk.Combobox(aircraft_frame, textvariable=self.aircraft_var, state="readonly")
        self.aircraft_combobox.pack(side=tk.LEFT, padx=(0,10))

        schedule_button = ttk.Button(aircraft_frame, text="Schedule Selected Flight", command=self.schedule_selected_flight, bootstyle="success")
        schedule_button.pack(side=tk.LEFT, padx=5)

        # Frame for the schedule table
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Update Treeview columns to include Route, Altitude, Distance
        self.tree = ttk.Treeview(frame, columns=("Flight", "Callsign", "Departure", "Arrival", "Route", "Altitude", "Distance", "Fleet"), show="headings")
        self.tree.heading("Flight", text="Flight")
        self.tree.heading("Callsign", text="Callsign")
        self.tree.heading("Departure", text="Departure")
        self.tree.heading("Arrival", text="Arrival")
        self.tree.heading("Route", text="Route")
        self.tree.heading("Altitude", text="Altitude (FL)")
        self.tree.heading("Distance", text="Distance (nm)")
        self.tree.heading("Fleet", text="Fleet")

        self.tree.column("Flight", width=100, anchor=tk.CENTER)
        self.tree.column("Callsign", width=100, anchor=tk.CENTER)
        self.tree.column("Departure", width=80, anchor=tk.CENTER)
        self.tree.column("Arrival", width=80, anchor=tk.CENTER)
        self.tree.column("Route", width=200, anchor=tk.W)
        self.tree.column("Altitude", width=100, anchor=tk.CENTER)
        self.tree.column("Distance", width=100, anchor=tk.CENTER)
        self.tree.column("Fleet", width=100, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        if self.current_location and self.airline_id:
            self.load_db_schedules()

        self.load_fleet_data()
        self.load_airline_info()
        self.update_location()

    def clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def load_db_schedules(self):
        if not self.current_location or not self.airline_id:
            Messagebox.show_error("Current location or airline ID is not set.", "Error")
            return

        # Debug print to check values
        print(f"DEBUG: Loading DB schedules for location={self.current_location}, airline_id={self.airline_id}")

        schedules = fetch_schedules_by_location_and_airline(self.current_location, self.airline_id)

        # Debug print the fetched data
        print("DEBUG: Schedules fetched from DB:", schedules)

        self.clear_tree()
        if not schedules:
            Messagebox.show_warning("No DB schedules found for this location and airline.", "No Data")
            return

        for row in schedules:
            # row should be (flight_number, callsign, departure, arrival, route, altitude, distance, fleet)
            
            print("DEBUG: Inserting row into Treeview:", row)
            self.tree.insert("", tk.END, values=(row[0], row[1], row[2], row[3],'','','', row[4]))

    def load_json_routes(self):
        if not self.current_location or not self.airline_id:
            Messagebox.show_error("Current location or airline ID is not set.", "Error")
            return

        try:
            airlines_data = load_airlines_json()
        except Exception as e:
            Messagebox.show_error(f"Failed to load airline data from JSON: {e}", "Error")
            return

        target_airline = self.find_target_airline(airlines_data)
        if target_airline is None:
            Messagebox.show_warning("No matching airline found in JSON for the selected airline ID.", "No Data")
            return

        self.clear_tree()

        if "Routes" not in target_airline:
            Messagebox.show_warning("No routes found for this airline in JSON.", "No Data")
            return

        iata_code = target_airline.get("iata", "XX")
        icao_code = target_airline.get("icao", "ZZZ")  # fallback if not found

        routes = target_airline["Routes"]
        found_route = False
        for route_obj in routes:
            route_str = route_obj.get("route", "")
            if " > " in route_str:
                dep, arr = route_str.split(" > ", 1)
                dep = dep.strip().upper()
                arr = arr.strip().upper()
                if dep == self.current_location.upper():
                    random_num = random.randint(1, 9999)
                    flight_number = f"{iata_code}{random_num}"
                    flight_callsign = f"{icao_code}{random_num}"
                    fleet = route_obj.get("ac", "N/A")
                    self.tree.insert("", tk.END, values=(flight_number, flight_callsign, dep, arr, 'N/A', 'N/A', 'N/A', fleet))
                    found_route = True

        if not found_route:
            Messagebox.show_warning("No routes start from your current location.", "No Data")

    def schedule_selected_flight(self):
        selected = self.tree.selection()
        if not selected:
            Messagebox.show_warning("Please select a flight to schedule.", "No Selection")
            return

        values = self.tree.item(selected[0])["values"]
        # values = (flightNumber, flightCallsign, dep, arr, fleet)
        flightNumber, flightCallsign, dep, arr, fleet = values[:5]

        if not self.aircraft_var.get():
            Messagebox.show_warning("Please select an aircraft from the dropdown.", "No Aircraft Selected")
            return

        selected_reg = self.aircraft_var.get().split(" - ")[0]
        aircraft_type = self.aircraft_var.get().split(" - ")[2]
        aircraft_info = next((a for a in self.fleet if a[1] == selected_reg), None)
        if not aircraft_info:
            Messagebox.show_error("Selected aircraft not found in fleet data.", "Error")
            return

        aircraft_id, aircraft_reg, aircraft_icao, aircraft_hours, aircraft_location = aircraft_info
        self.selected_aircraft_id = aircraft_id
        self.selected_aircraft_location = aircraft_location

        # If aircraft not at current_location, transport it first
        if self.selected_aircraft_location.upper() != self.current_location.upper():
            confirm = Messagebox.yesno(
                "Transport Aircraft",
                f"This aircraft ({aircraft_reg}) is currently at {aircraft_location}. Transport it to {self.current_location}?"
            )
            if not confirm:
                return
            if not update_aircraft_location(aircraft_id, self.current_location):
                Messagebox.show_error("Failed to transport aircraft.", "Error")
                return
            self.selected_aircraft_location = self.current_location

        db_path = self.config_manager.get_database_path('userdata')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            scheduledDep = int(datetime.utcnow().timestamp())
            scheduledArr = scheduledDep + 3600  # placeholder for 1h flight

            # Include fleetId in the insert
            cursor.execute("""
                INSERT INTO logbook (flightNumber, flightCallsign, dep, arr, status, scheduledDep, scheduledArr, fleetReg, fleetId)
                VALUES (?, ?, ?, ?, 'SCHEDULED', ?, ?, ?, ?)
            """, (flightNumber, flightCallsign, dep, arr, scheduledDep, scheduledArr, aircraft_reg+'/'+aircraft_type, aircraft_id))

            conn.commit()
            conn.close()

            Messagebox.show_info(f"Flight {flightNumber} with ATC Callsign {flightCallsign} scheduled successfully with aircraft {aircraft_reg}!", "Success")

        except sqlite3.Error as e:
            Messagebox.show_error(f"Database error: {e}", "Error")

    def load_fleet_data(self):
        if not self.airline_id:
            return
        try:
            self.fleet = fetch_fleet_data(self.airline_id)
            if self.fleet:
                # Include aircraft ICAO (assuming it's at index 2)
                aircraft_strings = [f"{f[1]} - {f[4]} - {f[2]}" for f in self.fleet]
                self.aircraft_combobox["values"] = aircraft_strings
            else:
                self.aircraft_combobox["values"] = []
        except Exception as e:
            print("Error loading fleet data:", e)
            self.aircraft_combobox["values"] = []

    def load_airline_info(self):
        if not self.airline_id:
            return
        try:
            airlines_data = load_airlines_json()
            self.target_airline = self.find_target_airline(airlines_data)
            if self.target_airline:
                self.airline_iata = self.target_airline.get("iata")
                self.airline_icao = self.target_airline.get("icao")
        except Exception as e:
            print("Error loading airline info:", e)

    def find_target_airline(self, airlines_data):
        for airline in airlines_data:
            try:
                aid = int(airline.get("id"))
                if aid == self.airline_id:
                    return airline
            except (ValueError, TypeError):
                continue
        return None

    def update_location(self):
        try:
            # Fetch the latest location from the database or source
            self.current_location = fetch_latest_location(1)
            # Update the UI elements accordingly
            
            self.update_location_display()
        except Exception as e:
            print("Error updating location:", e)

    def update_location_display(self):
        # Update the UI with the new location
        location_label = ttk.Label(self.root, text=f"Location: {self.current_location}")
        location_label.pack()

    def fetch_aeroapi_schedules(self):
        """Fetch flight schedules from FlightAware AeroAPI."""
        start_time = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        url = f"https://aeroapi.flightaware.com/aeroapi/airports/{self.current_location}/flights/departures?airline={self.airline_icao}&start={start_time}&end={end_time}"
        headers = {
            "x-apikey": self.api_key,
            "Accept": "application/json"
        }
        retries = 3
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                print("DEBUG: AeroAPI response:", data)
                return data.get('departures', [])
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2)  # Wait before retrying
                else:
                    Messagebox.show_error(f"Failed to fetch schedules after {retries} attempts: {e}", "API Error")
                    return []

    def filter_schedules_by_airline(self, schedules, icao_code):
        """Filter schedules based on the airline's ICAO code."""
        filtered = [flight for flight in schedules if flight.get('operator_icao') == icao_code]
        print(f"DEBUG: Filtered {len(filtered)} schedules for airline ICAO {icao_code}")
        return filtered

    def load_aeroapi_schedules(self):
        """Load schedules from AeroAPI and populate the Treeview."""
        if not self.current_location or not self.airline_id:
            Messagebox.show_error("Current location or airline ID is not set.", "Error")
            return

        try:
            airlines_data = load_airlines_json()
        except Exception as e:
            Messagebox.show_error(f"Failed to load airline data from JSON: {e}", "Error")
            return

        target_airline = self.find_target_airline(airlines_data)
        if target_airline is None:
            Messagebox.show_warning("No matching airline found in JSON for the selected airline ID.", "No Data")
            return

        self.clear_tree()

        if "Routes" not in target_airline:
            Messagebox.show_warning("No routes found for this airline in JSON.", "No Data")
            return

        iata_code = target_airline.get("iata", "XX")
        icao_code = target_airline.get("icao", "ZZZ")  # fallback if not found
        print("DEBUG: Selected airline ICAO:", icao_code)

        schedules = self.fetch_aeroapi_schedules()
        print(f"DEBUG: Fetched {len(schedules)} schedules from API")

        if not schedules:
            Messagebox.show_warning("No schedules fetched from API.", "No Data")
            return

        filtered_schedules = self.filter_schedules_by_airline(schedules, icao_code)
        print("DEBUG: Number of filtered schedules:", len(filtered_schedules))

        if not filtered_schedules:
            Messagebox.show_warning("No schedules match the selected airline.", "No Data")
            return

        self.clear_tree()
        for flight in filtered_schedules:
            flight_number = flight.get('ident_iata', 'N/A')
            callsign = flight.get('ident_icao', 'N/A')
            departure = flight.get('origin', {}).get('code', 'N/A')
            arrival = flight.get('destination', {}).get('code', 'N/A')
            route = flight.get('route', 'N/A')
            altitude = flight.get('filed_altitude', 'N/A')
            distance = flight.get('route_distance', 'N/A')
            fleet = flight.get('aircraft_type', 'N/A')

            self.tree.insert("", tk.END, values=(flight_number, callsign, departure, arrival, route, altitude, distance, fleet))


if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    # Adjust current_location and airline_id as needed
    app = ScheduleViewer(root, current_location="KATL", airline_id=20)
    root.mainloop()

from typing import Callable, Optional
from tkinter import Tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from core.database_utils import (
    calculate_pilot_statistics,
    fetch_flight_log,
    fetch_pilot_data,
    calculate_rank_and_achievements,
    calculate_pilot_analytics
)

class PilotDashboard:
    def __init__(
        self,
        parent_window: ttk.Window,
        on_close_callback: Callable,
        airline_id: int,
        airline_name: str
    ):
        self.parent_window = parent_window
        self.on_close_callback = on_close_callback
        self.airline_id = airline_id
        self.airline_name = airline_name
        self.pilot = self.get_pilot_data()

        self.setup_window()
        self.create_tabs()

    def get_pilot_data(self) -> Optional[tuple]:
        pilot_data = fetch_pilot_data(self.airline_id)
        if pilot_data:
            return pilot_data[0]
        return None

    def setup_window(self):
        self.parent_window.title("Pilot Dashboard")
        self.parent_window.geometry("800x600")
        self.parent_window.protocol("WM_DELETE_WINDOW", self.on_close_callback)

        self.notebook = ttk.Notebook(self.parent_window, padding=10)
        self.notebook.pack(fill="both", expand=True)

    def create_tabs(self):
        if self.pilot:
            pilot_id = self.pilot[0]
            self.create_overview_tab(pilot_id)
            self.create_flight_log_tab(pilot_id)
            self.create_achievements_tab(pilot_id)
            self.create_analytics_tab(pilot_id)
        else:
            Messagebox.show_error("Error", "No pilot data available.")

    def create_overview_tab(self, pilot_id: int):
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="Overview")
        frame = overview_frame
        if self.pilot is None:
            # No pilot data
            ttk.Label(frame, text="No pilot data available.", font=("Helvetica", 14)).grid(row=0, column=0, sticky="w")
            return frame

        _, pilot_name, home_hub, current_location = self.pilot[:4]

        try:
            rank, updated_achievements = calculate_rank_and_achievements(pilot_id, self.airline_id)
            total_flights, total_hours = calculate_pilot_statistics(pilot_id, self.airline_id)
        except Exception as e:
            Messagebox.show_error(f"Error loading pilot overview: {e}", "Error")
            print(f"Error in overview tab: {e}")
            rank = "Student Pilot"
            total_hours = 0.0
            total_flights = 0

        # Overview labels
        ttk.Label(frame, text=f"Airline: {self.airline_name}", font=("Helvetica", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(frame, text=f"Pilot Name: {pilot_name}", font=("Helvetica", 12)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(frame, text=f"Rank: {rank}", font=("Helvetica", 12)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(frame, text=f"Total Hours (Airline): {total_hours:.2f}", font=("Helvetica", 12)).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(frame, text=f"Home Hub: {home_hub}", font=("Helvetica", 12)).grid(row=4, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(frame, text=f"Current Location: {current_location}", font=("Helvetica", 12)).grid(row=5, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(frame, text=f"Total Flights (Airline): {total_flights}", font=("Helvetica", 12)).grid(row=6, column=0, sticky="w", padx=10, pady=5)

    def create_flight_log_tab(self, pilot_id: int):
        flight_log_frame = ttk.Frame(self.notebook)
        self.notebook.add(flight_log_frame, text="Flight Log")
        frame = flight_log_frame

        columns = ("flightCallsign", "Dep", "Arr", "actualDep", "actualArr")
        flight_log_tree = ttk.Treeview(frame, columns=columns, show="headings")
        flight_log_tree.heading("flightCallsign", text="Callsign")
        flight_log_tree.heading("Dep", text="Departure")
        flight_log_tree.heading("Arr", text="Arrival")
        flight_log_tree.heading("actualDep", text="Departure Time")
        flight_log_tree.heading("actualArr", text="Arrival Time")

        flight_log_tree.column("flightCallsign", width=120, anchor=W)
        flight_log_tree.column("Dep", width=80, anchor=CENTER)
        flight_log_tree.column("Arr", width=80, anchor=CENTER)
        flight_log_tree.column("actualDep", width=150, anchor=W)
        flight_log_tree.column("actualArr", width=150, anchor=W)

        flight_log_tree.pack(fill="both", expand=True)

        if pilot_id is None:
            return frame

        try:
            logs = fetch_flight_log(pilot_id, self.airline_id)
            for log in logs:
                flight_log_tree.insert("", "end", values=log)
        except Exception as e:
            Messagebox.show_error(f"Error loading flight log: {e}", "Error")
            print(f"Error in flight log tab: {e}")

    def create_achievements_tab(self, pilot_id: int):
        achievements_frame = ttk.Frame(self.notebook)
        self.notebook.add(achievements_frame, text="Achievements")
        frame = achievements_frame

        columns = ("achievement", "date_earned")
        achievements_tree = ttk.Treeview(frame, columns=columns, show="headings")
        achievements_tree.heading("achievement", text="Achievement")
        achievements_tree.heading("date_earned", text="Date Earned")

        achievements_tree.column("achievement", width=200, anchor=W)
        achievements_tree.column("date_earned", width=100, anchor=CENTER)

        achievements_tree.pack(fill="both", expand=True)

        if pilot_id is None:
            return frame

        try:
            _, updated_achievements = calculate_rank_and_achievements(pilot_id, self.airline_id)
            for achievement, date_earned in updated_achievements:
                achievements_tree.insert("", "end", values=(achievement, date_earned))
        except Exception as e:
            Messagebox.show_error(f"Error loading achievements: {e}", "Error")
            print(f"Error in achievements tab: {e}")

    def create_analytics_tab(self, pilot_id: int):
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text="Analytics")
        frame = analytics_frame

        if pilot_id is None:
            ttk.Label(frame, text="No pilot data available for analytics.", font=("Helvetica", 14)).pack(anchor="w", pady=10)
            return frame

        try:
            analytics = calculate_pilot_analytics(pilot_id, self.airline_id)
            total_landings = analytics["total_landings"]
            avg_vs = analytics["avg_vs"]  # Average Vertical Speed on touchdown
            avg_gf = analytics["avg_gf"]  # Average g-force on touchdown

            ttk.Label(frame, text="Analytics", font=("Helvetica", 16, "bold")).pack(anchor="w", pady=(0, 10))
            ttk.Label(frame, text=f"Total Landings: {total_landings}", font=("Helvetica", 12)).pack(anchor="w", pady=5)
            ttk.Label(frame, text=f"Average Touchdown V/S: {avg_vs:.2f} fpm", font=("Helvetica", 12)).pack(anchor="w", pady=5)
            ttk.Label(frame, text=f"Average Touchdown G-Force: {avg_gf:.2f}g", font=("Helvetica", 12)).pack(anchor="w", pady=5)

        except Exception as e:
            Messagebox.show_error(f"Error loading analytics: {e}", "Error")
            print(f"Error in analytics tab: {e}")

def create_dashboard(parent_window: ttk.Window, on_close_callback: Callable, airline_id: int, airline_name: str):
    PilotDashboard(parent_window, on_close_callback, airline_id, airline_name)

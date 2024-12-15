import sqlite3
from tkinter import ttk, messagebox
from configparser import ConfigParser
from core.database_utils import calculate_pilot_statistics, fetch_flight_log, fetch_achievements, fetch_pilot_data, calculate_rank_and_achievements

def create_dashboard(parent_window, on_close_callback, airline_id):
    parent_window.title("Pilot Dashboard")
    parent_window.geometry("800x600")

    notebook = ttk.Notebook(parent_window)
    notebook.pack(fill="both", expand=True)

    # Overview Tab
    overview_frame = ttk.Frame(notebook)
    notebook.add(overview_frame, text="Overview")

    pilot_data = fetch_pilot_data()

    if pilot_data:
        try:
            pilot = pilot_data[0]
            pilot_id = pilot[0]

            # Default values in case of errors
            rank = "Student Pilot"
            updated_achievements = []

            # Calculate rank and achievements
            rank, updated_achievements = calculate_rank_and_achievements(pilot_id, airline_id)

            # Calculate statistics
            total_flights, total_hours = calculate_pilot_statistics(pilot_id, airline_id)

            ttk.Label(overview_frame, text=f"Pilot Name: {pilot[1]}").grid(row=0, column=0, sticky="w", padx=10, pady=5)
            ttk.Label(overview_frame, text=f"Rank: {rank}").grid(row=1, column=0, sticky="w", padx=10, pady=5)
            ttk.Label(overview_frame, text=f"Total Hours for Airline: {total_hours:.2f}").grid(row=2, column=0, sticky="w", padx=10, pady=5)
            ttk.Label(overview_frame, text=f"Home Hub: {pilot[2]}").grid(row=3, column=0, sticky="w", padx=10, pady=5)
            ttk.Label(overview_frame, text=f"Current Location: {pilot[3]}").grid(row=4, column=0, sticky="w", padx=10, pady=5)
            ttk.Label(overview_frame, text=f"Total Flights for Airline: {total_flights}").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        except Exception as e:
            messagebox.showerror("Error", f"Error loading pilot overview: {e}")
            print(f"Error in overview tab: {e}")
    else:
        ttk.Label(overview_frame, text="No pilot data available.").grid(row=0, column=0, sticky="w", padx=10, pady=5)

    # Flight Log Tab
    flight_log_frame = ttk.Frame(notebook)
    notebook.add(flight_log_frame, text="Flight Log")

    try:
        flight_log_tree = ttk.Treeview(flight_log_frame, columns=("flightCallsign", "Dep", "Arr", "actualDep", "actualArr"), show="headings")
        flight_log_tree.heading("flightCallsign", text="Callsign")
        flight_log_tree.heading("Dep", text="Departure")
        flight_log_tree.heading("Arr", text="Arrival")
        flight_log_tree.heading("actualDep", text="Departure Time")
        flight_log_tree.heading("actualArr", text="Arrival Time")
        flight_log_tree.pack(fill="both", expand=True)

        for log in fetch_flight_log(pilot_id, airline_id):
            flight_log_tree.insert("", "end", values=log)
    except Exception as e:
        messagebox.showerror("Error", f"Error loading flight log: {e}")
        print(f"Error in flight log tab: {e}")

    # Achievements Tab
    achievements_frame = ttk.Frame(notebook)
    notebook.add(achievements_frame, text="Achievements")

    try:
        achievements_tree = ttk.Treeview(achievements_frame, columns=("achievement", "date_earned"), show="headings")
        achievements_tree.heading("achievement", text="Achievement")
        achievements_tree.heading("date_earned", text="Date Earned")
        achievements_tree.pack(fill="both", expand=True)

        for achievement, date_earned in updated_achievements:
            achievements_tree.insert("", "end", values=(achievement, date_earned))
    except Exception as e:
        messagebox.showerror("Error", f"Error loading achievements: {e}")
        print(f"Error in achievements tab: {e}")

    parent_window.protocol("WM_DELETE_WINDOW", on_close_callback)

import sqlite3
from tkinter import Tk, Toplevel, Label, ttk
from .pilot_ranking_achievements import update_pilot_rank_and_achievements

class PilotLogbook:
    def __init__(self, root):
        self.root = root
        self.root.title("Pilot Logbook")

        # Create Treeview
        self.tree = ttk.Treeview(
            self.root,
            columns=("flightNumber", "dep", "arr", "scheduledDep", "actualDep", "scheduledArr", "actualArr", "status", "duration"),
            show="headings",
        )
        self.tree.heading("flightNumber", text="Flight Number")
        self.tree.heading("dep", text="Departure")
        self.tree.heading("arr", text="Arrival")
        self.tree.heading("scheduledDep", text="Scheduled Depart")
        self.tree.heading("actualDep", text="Actual Departure")
        self.tree.heading("scheduledArr", text="Scheduled Arrival")
        self.tree.heading("actualArr", text="Actual Arrival")
        self.tree.heading("status", text="Status")
        self.tree.heading("duration", text="Duration (Hrs)")

        self.tree.pack(fill="both", expand=True)

        # Error label
        self.error_label = Label(self.root, text="", fg="red")
        self.error_label.pack()

        # Load logbook data
        self.load_logbook_data()

    def load_logbook_data(self):
        try:
            # Update pilot ranks and achievements before displaying the logbook
            update_pilot_rank_and_achievements()

            conn = sqlite3.connect("/home/phil/Documents/SimToolkitPro/userdata.db")
            cursor = conn.cursor()

            # Query the logbook table
            query = """
                SELECT
                    flightNumber,
                    dep,
                    arr,
                    scheduledDep,
                    actualDep,
                    scheduledArr,
                    actualArr,
                    status,
                    ROUND((actualArr - actualDep) / 3600.0, 2) AS duration
                FROM logbook
                WHERE status = 'COMPLETED'
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            # Clear existing data in Treeview
            for row in self.tree.get_children():
                self.tree.delete(row)

            # Insert data into Treeview
            for row in rows:
                formatted_row = [
                    row[0],
                    row[1],
                    row[2],
                    self.format_unix_time(row[3]),
                    self.format_unix_time(row[4]),
                    self.format_unix_time(row[5]),
                    self.format_unix_time(row[6]),
                    row[7],
                    row[8],
                ]
                self.tree.insert("", "end", values=formatted_row)

            conn.close()
        except sqlite3.Error as e:
            self.error_label.config(text=f"Database Error: {e}")

    @staticmethod
    def format_unix_time(timestamp):
        """Convert a Unix timestamp to a readable format."""
        if not timestamp:
            return "-"
        try:
            from datetime import datetime
            return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return "-"

if __name__ == "__main__":
    root = Tk()
    root.withdraw()  # Hide the root window
    PilotLogbook(root)
    root.mainloop()

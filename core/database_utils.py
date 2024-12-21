from typing import Optional, List, Tuple
import sqlite3
import logging
from datetime import datetime, timezone
from core.config_manager import ConfigManager
from core.utils import convert_to_int  # Import the helper function

# Singleton ConfigManager instance
config_manager = ConfigManager()
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("Database_Utils.log"),
        logging.StreamHandler()
    ]
)

def connect_to_database() -> Optional[sqlite3.Connection]:
    """
    Create and return a new database connection using the userdata database path
    from the configuration manager.
    """
    user_db_path = config_manager.get_database_path('userdata')
    try:
        connection = sqlite3.connect(user_db_path)
        return connection
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def get_airline_id_from_fleet(fleet_id: int) -> Optional[str]:
    """Fetch airline ID based on fleet ID."""
    conn = connect_to_database()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT airlineCode FROM fleet WHERE id = ?", (fleet_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return None
    finally:
        conn.close()

def calculate_rank_and_achievements(pilot_id: int, airline_id: str) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Calculate the rank and achievements for a pilot based on their flight hours for a specific airline.
    Returns a tuple: (rank, list_of_achievements).
    """
    conn = connect_to_database()
    if conn is None:
        print("Database connection failed.")
        return "Student Pilot", []

    try:
        cursor = conn.cursor()

        # Calculate total hours for the given airline
        cursor.execute("""
            SELECT SUM((actualArr - actualDep) / 3600.0) AS total_hours
            FROM logbook
            WHERE status = 'COMPLETED' AND fleetId IN (
                SELECT id FROM fleet WHERE airlineCode = ?
            )
        """, (airline_id,))
        result = cursor.fetchone()
        total_hours = result[0] if result and result[0] is not None else 0.0

        # Determine rank based on total hours
        rank_thresholds = [
            (0, "Student Pilot"),
            (10, "First Officer"),
            (50, "Captain"),
            (100, "Chief Captain"),
        ]
        rank = "Student Pilot"
        for hours, r in rank_thresholds:
            if total_hours >= hours:
                rank = r

        # Calculate unique destinations
        cursor.execute("""
            SELECT DISTINCT arr
            FROM logbook
            WHERE status = 'COMPLETED' AND fleetId IN (
                SELECT id FROM fleet WHERE airlineCode = ?
            )
        """, (airline_id,))
        destinations = cursor.fetchall()
        unique_destinations = len(destinations) if destinations else 0

        # Calculate hours per aircraft
        cursor.execute("""
            SELECT airframeIcao, SUM((actualArr - actualDep) / 3600.0) AS total_hours
            FROM logbook
            JOIN fleet ON logbook.fleetId = fleet.id
            WHERE logbook.status = 'COMPLETED' AND fleet.airlineCode = ?
            GROUP BY airframeIcao
        """, (airline_id,))
        aircraft_hours = cursor.fetchall() or []

        # Fetch existing achievements
        cursor.execute("""
            SELECT achievement
            FROM achievements
            WHERE pilot_id = ? AND airlineId = ?
        """, (pilot_id, airline_id))
        existing_achievements = {row[0] for row in cursor.fetchall()}

        # Count total flights for achievements
        cursor.execute("""
            SELECT COUNT(*)
            FROM logbook
            WHERE status = 'COMPLETED' AND fleetId IN (
                SELECT id FROM fleet WHERE airlineCode = ?
            )
        """, (airline_id,))
        flight_result = cursor.fetchone()
        flight_count = flight_result[0] if flight_result and flight_result[0] is not None else 0

        # Determine new achievements to add
        achievements_to_add = []

        # First Flight Achievement
        if flight_count >= 1 and "First Flight" not in existing_achievements:
            achievements_to_add.append(("First Flight", "now"))

        # Hours-based Achievements for each aircraft
        for aircraft, hours in aircraft_hours:
            if hours >= 10 and f"First Officer ({aircraft})" not in existing_achievements:
                achievements_to_add.append((f"First Officer ({aircraft})", "now"))
            if hours >= 20 and f"Captain ({aircraft})" not in existing_achievements:
                achievements_to_add.append((f"Captain ({aircraft})", "now"))

        # Unique Destination Achievements
        if unique_destinations >= 20 and "20 Unique Destinations" not in existing_achievements:
            achievements_to_add.append(("20 Unique Destinations", "now"))
        if unique_destinations >= 50 and "50 Unique Destinations" not in existing_achievements:
            achievements_to_add.append(("50 Unique Destinations", "now"))

        # Add new achievements to the database
        for achievement, date_earned in achievements_to_add:
            cursor.execute("""
                INSERT INTO achievements (pilot_id, airlineId, achievement, date_earned)
                VALUES (?, ?, ?, DATE(?))
            """, (pilot_id, airline_id, achievement, date_earned))

        conn.commit()

        # Fetch updated achievements
        cursor.execute("""
            SELECT achievement, date_earned
            FROM achievements
            WHERE pilot_id = ? AND airlineId = ?
        """, (pilot_id, airline_id))
        updated_achievements = cursor.fetchall() or []

        return rank, updated_achievements
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Student Pilot", []
    finally:
        conn.close()

def add_pilot(name: str, home_hub: str = "Unknown", current_location: str = "Unknown", connection: Optional[sqlite3.Connection] = None) -> None:
    """Add a new pilot to the database."""
    conn = connection or connect_to_database()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pilots (name, homeHub, currentLocation) VALUES (?, ?, ?)",
            (name, home_hub, current_location),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error while adding pilot: {e}")
    finally:
        if connection is None:
            conn.close()

def fetch_pilot_data(connection: Optional[sqlite3.Connection] = None) -> List[Tuple]:
    """Fetch all pilot data from the database."""
    conn = connection or connect_to_database()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pilots")
        data = cursor.fetchall()

        # Convert timestamp fields from strings to integers if necessary and handle None
        processed_data = []
        for row in data:
            *pilot_info, created_at = row
            created_at = int(created_at) if created_at and str(created_at).isdigit() else None
            processed_data.append((*pilot_info, created_at))

        return processed_data
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return []
    finally:
        if connection is None:
            conn.close()

def calculate_pilot_statistics(pilot_id: int, airline_id: str) -> Tuple[int, float]:
    """
    Calculate total flights and total hours for a given pilot and airline.
    Returns a tuple (total_flights, total_hours).
    """
    conn = connect_to_database()
    if conn is None:
        return 0, 0.0

    try:
        cursor = conn.cursor()

        # Total hours
        cursor.execute("""
            SELECT SUM((actualArr - actualDep) / 3600.0) AS total_hours
            FROM logbook
            WHERE status = 'COMPLETED' AND fleetId IN (
                SELECT id FROM fleet WHERE airlineCode = ?
            )
        """, (airline_id,))
        hours_result = cursor.fetchone()
        total_hours = hours_result[0] if hours_result and hours_result[0] else 0.0

        # Total flights
        cursor.execute("""
            SELECT COUNT(*) AS total_flights
            FROM logbook
            WHERE status = 'COMPLETED' AND fleetId IN (
                SELECT id FROM fleet WHERE airlineCode = ?
            )
        """, (airline_id,))
        flights_result = cursor.fetchone()
        total_flights = flights_result[0] if flights_result and flights_result[0] else 0

        return total_flights, total_hours
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return 0, 0.0
    finally:
        conn.close()

def fetch_flight_log(pilot_id: int, airline_id: str) -> List[Tuple[str, str, str, str, str]]:
    """
    Fetch the flight log for a given pilot and airline, including flight callsign, departure,
    arrival, and actual departure/arrival times.
    """
    conn = connect_to_database()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT flightCallsign, Dep, Arr, actualDep, actualArr
            FROM logbook
            WHERE status = 'COMPLETED' AND fleetId IN (
                SELECT id FROM fleet WHERE airlineCode = ?
            )
        """, (airline_id,))
        rows = cursor.fetchall()
        return [
            (
                row[0],
                row[1],
                row[2],
                datetime.utcfromtimestamp(row[3]).strftime('%Y-%m-%d %H:%M:%S') if row[3] else '-',
                datetime.utcfromtimestamp(row[4]).strftime('%Y-%m-%d %H:%M:%S') if row[4] else '-'
            )
            for row in rows
        ]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def fetch_achievements(pilot_id: int, airline_id: str) -> List[Tuple[str, str]]:
    """Fetch achievements for a given pilot and airline."""
    conn = connect_to_database()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT achievement, date_earned
            FROM achievements
            WHERE pilot_id = ? AND airlineId = ?
        """, (pilot_id, airline_id))
        data = cursor.fetchall()
        return data
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def fetch_achievements_general(pilot_id: int) -> List[Tuple[str, str]]:
    """Fetch achievements for a given pilot across all airlines."""
    conn = connect_to_database()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT achievement, date_earned FROM achievements WHERE pilot_id = ?", (pilot_id,))
        data = cursor.fetchall()
        return data
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def fetch_fleet_data(selected_airline_code: Optional[str] = None, pilot_location: Optional[str] = None) -> List[Tuple[int, str, str, float, str]]:
    """
    Fetch fleet data, optionally filtered by airline code and pilot location.
    Returns tuples of (id, registration, airframeIcao, logHours, logLocation).
    """
    conn = connect_to_database()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        query = "SELECT id, registration, airframeIcao, logHours, logLocation FROM fleet"
        filters = []
        params = []

        if selected_airline_code is not None:
            # Extract airline_id from the string if needed
            if isinstance(selected_airline_code, str) and "(ID: " in selected_airline_code:
                airline_id = int(selected_airline_code.split("(ID: ")[1].split(")")[0])
            else:
                airline_id = selected_airline_code
            filters.append("airlineCode = ?")
            params.append(airline_id)

        # If we do NOT want to limit by pilot_location initially, comment the next lines.
        # if pilot_location is not None and isinstance(pilot_location, str):
        #     filters.append("logLocation = ?")
        #     params.append(pilot_location)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        cursor.execute(query, tuple(params))
        data = cursor.fetchall()
        return data  # Each row: (id, registration, airframeIcao, logHours, logLocation)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def update_aircraft_location(aircraft_id: int, new_location: str) -> bool:
    """
    Update the logLocation of a specific aircraft by its ID.
    """
    conn = connect_to_database()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE fleet
            SET logLocation = ?
            WHERE id = ?
        """, (new_location, aircraft_id))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()


def fetch_schedules_by_location_and_airline(current_location: str, airline_id: str) -> List[Tuple[str, str, str, str]]:
    """
    Fetch scheduled flights for a given location and airline ID.
    Returns a list of tuples with (flightNumber, dep, arr, fleetReg).
    """
    conn = connect_to_database()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        query = """
            SELECT flightNumber, dep, arr, fleetReg
            FROM logbook
            WHERE status = 'SCHEDULED'
            AND dep = ?
            AND fleetId IN (
                SELECT id
                FROM fleet
                WHERE airlineCode = ?
            )
        """
        cursor.execute(query, (current_location, airline_id))
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def calculate_pilot_analytics(pilot_id: int, airline_id: str) -> dict:
    """
    Calculate analytics for the pilot's airline:
    - Total landings
    - Average touchdown vertical speed (fpm)
    - Average touchdown g-force
    This assumes all flights under the given airline_id are associated with this pilot.
    """

    conn = connect_to_database()
    if conn is None:
        return {"total_landings": 0, "avg_vs": 0.0, "avg_gf": 0.0}

    try:
        cursor = conn.cursor()
        # Join landings with logbook and fleet to filter by airline_id
        # Only consider completed flights
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_landings,
                AVG(touchdownVerticalSpeed) AS avg_vs,
                AVG(touchdownGforce) AS avg_gf
            FROM landings
            JOIN logbook ON landings.flightId = logbook.id
            JOIN fleet ON logbook.fleetId = fleet.id
            WHERE logbook.status = 'COMPLETED'
              AND fleet.airlineCode = ?
        """, (airline_id,))

        row = cursor.fetchone()
        if row:
            total_landings = row[0] if row[0] is not None else 0
            avg_vs = row[1] if row[1] is not None else 0.0
            avg_gf = row[2] if row[2] is not None else 0.0
        else:
            total_landings = 0
            avg_vs = 0.0
            avg_gf = 0.0

        return {
            "total_landings": total_landings,
            "avg_vs": avg_vs,
            "avg_gf": avg_gf
        }
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return {"total_landings": 0, "avg_vs": 0.0, "avg_gf": 0.0}
    finally:
        conn.close()

def update_pilot_property(airline_id, property_name, value):
    """Update a property of the pilot associated with the given airline."""
    conn = connect_to_database()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE pilots
            SET {property_name} = ?
            WHERE airline_id = ? AND id = (
                SELECT id FROM pilots WHERE airline_id = ? LIMIT 1
            )
        """, (value, airline_id, airline_id))
        if cursor.rowcount == 0:
            print(f"Failed to update {property_name}.")
            return False
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database Error: {e}")
        return False
    finally:
        conn.close()

def fetch_pilot_data(airline_id):
    """Fetch pilot data for the specified airline."""
    conn = connect_to_database()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, homeHub, currentLocation, rank, total_hours
            FROM pilots
            WHERE airline_id = ?
        """, (airline_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database Error: {e}")
        return []
    finally:
        conn.close()

def fetch_latest_location(airline_id: int) -> Optional[str]:
    """Fetch the latest location for the given airline_id."""
    conn = connect_to_database()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT current_location FROM airlines WHERE id = ?", (airline_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def calculate_total_hours(airline_id):
    """Calculate total flight hours for the specified airline."""
    
    total_hours = 0.0
    conn = connect_to_database()
    if conn is None:
        return 0.0
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM((actualArr - actualDep) / 3600.0) AS total_hours
            FROM logbook
            WHERE fleetId IN (
                SELECT id FROM fleet WHERE airlineCode = ?
            )
        """, (airline_id,))
        result = cursor.fetchone()
        total_hours = result[0] if result and result[0] is not None else 0.0
        cursor.execute("""
            UPDATE pilots
            SET total_hours = ?
            WHERE airline_id = ?
        """, (total_hours, airline_id))
        conn.commit()
        return total_hours
    except sqlite3.Error as e:
        print(f"Database Error: {e}")
        return 0.0
    finally:
        conn.close()

def fetch_latest_location(pilot_id: int) -> Optional[str]:
    """Fetch the latest location for the given pilot_id."""
    conn = connect_to_database()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT currentLocation FROM pilots WHERE id = ?", (pilot_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def fetch_logbook_data() -> List[Tuple]:
    """
    Fetch all logbook entries with status 'COMPLETED'.
    """
    conn = connect_to_database()
    if conn is None:
        logging.warning("Failed to establish database connection.")
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT flightNumber, dep, arr, scheduledDep, actualDep, scheduledArr, actualArr, status, fleetId
            FROM logbook
            WHERE status = 'COMPLETED'
        """)
        rows = cursor.fetchall()

        logging.debug(f"Fetched {len(rows)} rows from the database.")

        # Convert timestamp fields from integers and handle None
        processed_rows = []
        for row in rows:
            flightNumber, dep, arr, scheduledDep, actualDep, scheduledArr, actualArr, status, fleetId = row
            scheduledDep = convert_to_int(scheduledDep)
            actualDep = convert_to_int(actualDep)
            scheduledArr = convert_to_int(scheduledArr)
            actualArr = convert_to_int(actualArr)
            processed_rows.append((flightNumber, dep, arr, scheduledDep, actualDep, scheduledArr, actualArr, status, fleetId))

            # Log the converted values
            logging.debug(f"Processed Row: flightNumber={flightNumber}, dep={dep}, arr={arr}, "
                          f"scheduledDep={scheduledDep}, actualDep={actualDep}, "
                          f"scheduledArr={scheduledArr}, actualArr={actualArr}, status={status}, fleetId={fleetId}")

        logging.debug(f"Processed {len(processed_rows)} rows for display.")
        return processed_rows
    except sqlite3.Error as e:
        logging.error(f"Database error in fetch_logbook_data: {e}")
        return []
    finally:
        conn.close()

def get_logbook_table_columns():
    conn = connect_to_database()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(logbook);")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        return column_names
    except sqlite3.Error as e:
        logging.error(f"Error fetching table info: {e}")
        return []
    finally:
        conn.close()

# Example usage:
if __name__ == "__main__":
    columns = get_logbook_table_columns()
    print("Logbook table columns:", columns)

import sqlite3
from configparser import ConfigParser
from datetime import datetime

def get_database_config():
    config = ConfigParser()
    config.read("config.ini")
    return {
        "userdata": config.get("DATABASES", "userdata")
    }

# Configuration for the database
DATABASE_PATH = get_database_config()["userdata"]  # Fixing the database path key

def connect_to_database():
    print(f"Connecting to database at: {DATABASE_PATH}")
    connection = sqlite3.connect(DATABASE_PATH)
    print(f"Connection: {connection}")
    return connection

def get_airline_id_from_fleet(fleet_id):
    """Fetch airline ID based on fleet ID."""
    connection = connect_to_database()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT airlineCode FROM fleet WHERE id = ?", (fleet_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        connection.close()

def calculate_rank_and_achievements(pilot_id, airline_id):
    """
    Calculate the rank and achievements for a pilot based on their flight hours for a specific airline.
    """
    connection = connect_to_database()
    if not connection:
        print("Database connection failed.")
        return "Student Pilot", []

    try:
        cursor = connection.cursor()

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
        print(f"Total Hours: {total_hours}")

        # Determine rank
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
        unique_destinations = len(cursor.fetchall()) if cursor.fetchall() else 0
        print(f"Unique Destinations: {unique_destinations}")

        # Calculate hours per aircraft
        cursor.execute("""
            SELECT airframeIcao, SUM((actualArr - actualDep) / 3600.0) AS total_hours
            FROM logbook
            JOIN fleet ON logbook.fleetId = fleet.id
            WHERE logbook.status = 'COMPLETED' AND fleet.airlineCode = ?
            GROUP BY airframeIcao
        """, (airline_id,))
        aircraft_hours = cursor.fetchall() or []
        print(f"Aircraft Hours: {aircraft_hours}")

        # Fetch existing achievements
        cursor.execute("""
            SELECT achievement
            FROM achievements
            WHERE pilot_id = ? AND airlineId = ?
        """, (pilot_id, airline_id))
        existing_achievements = {row[0] for row in cursor.fetchall()}
        print(f"Existing Achievements: {existing_achievements}")

        # Achievements to add
        achievements_to_add = []

        # First Flight Achievement
        cursor.execute("""
            SELECT COUNT(*)
            FROM logbook
            WHERE status = 'COMPLETED' AND fleetId IN (
                SELECT id FROM fleet WHERE airlineCode = ?
            )
        """, (airline_id,))
        result = cursor.fetchone()
        flight_count = result[0] if result and result[0] is not None else 0
        print(f"Flight Count: {flight_count}")
        if flight_count >= 1 and "First Flight" not in existing_achievements:
            achievements_to_add.append(("First Flight", "now"))

        # Hours-based Achievements for Specific Aircraft
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

        connection.commit()

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
        connection.close()


def add_pilot(name, home_hub="Unknown", current_location="Unknown", connection=None):
    conn = connection or connect_to_database()
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

def fetch_pilot_data(connection=None):
    conn = connection or connect_to_database()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pilots")
        data = cursor.fetchall()
        return data
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if connection is None:
            conn.close()

# Calculate pilot statistics
def calculate_pilot_statistics(pilot_id, airline_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Calculate total flight hours for the specific airline
            cursor.execute("""
                SELECT SUM((actualArr - actualDep) / 3600.0) AS total_hours
                FROM logbook
                WHERE status = 'COMPLETED' AND fleetId IN (
                    SELECT id FROM fleet WHERE airlineCode = ?
                )
            """, (airline_id,))
            result = cursor.fetchone()
            total_hours = result[0] if result[0] else 0.0
            
            # Calculate total flights for the specific airline
            cursor.execute("""
                SELECT COUNT(*) AS total_flights
                FROM logbook
                WHERE status = 'COMPLETED' AND fleetId IN (
                    SELECT id FROM fleet WHERE airlineCode = ?
                )
            """, (airline_id,))
            result = cursor.fetchone()
            total_flights = result[0] if result[0] else 0
            
            connection.close()
            return total_flights, total_hours
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return 0, 0.0

def fetch_flight_log(pilot_id, airline_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT flightCallsign, Dep, Arr, 
                       actualDep, actualArr 
                FROM logbook 
                WHERE status = 'COMPLETED' AND fleetId IN (
                    SELECT id FROM fleet WHERE airlineCode = ?
                )
            """, (airline_id,))
            rows = cursor.fetchall()
            connection.close()
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

def fetch_achievements(pilot_id, airline_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT achievement, date_earned 
                FROM achievements 
                WHERE pilot_id = ? AND airlineId = ?
            """, (pilot_id, airline_id))
            data = cursor.fetchall()
            connection.close()
            return data
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

# Keep this function for non-airline-specific achievement queries
def fetch_achievements_general(pilot_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT achievement, date_earned FROM achievements WHERE pilot_id = ?", (pilot_id,))
            data = cursor.fetchall()
            connection.close()
            return data
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

# Fetch fleet data with filtering
def fetch_fleet_data(selected_airline_code=None, pilot_location=None):
    connection = connect_to_database()
    try:
        cursor = connection.cursor()
        query = """
            SELECT registration, airframeIcao, logHours, logLocation
            FROM fleet
        """
        filters = []
        params = []

        if selected_airline_code is not None:
            airline_id = selected_airline_code if isinstance(selected_airline_code, int) else int(selected_airline_code.split("(ID: ")[1].split(")")[0])
            filters.append("airlineCode = ?")
            params.append(airline_id)

        if pilot_location is not None and isinstance(pilot_location, str):
            filters.append("logLocation = ?")
            params.append(pilot_location)
        else:
            print(f"Invalid pilot_location provided: {pilot_location}")

        if filters:
            query += " WHERE " + " AND ".join(filters)

        print(f"Executing query: {query} with params={params}")
        cursor.execute(query, tuple(params))

        data = cursor.fetchall()
        print(f"Query result: {data}")
        connection.close()
        return data
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []

# Fetch Schedules by location and airline
def fetch_schedules_by_location_and_airline(current_location, airline_id):
    """
    Fetch schedules filtered by current location and valid airline using fleetId.
    """
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
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
            connection.close()
            return rows
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

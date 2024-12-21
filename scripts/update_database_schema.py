import sqlite3
import logging
from configparser import ConfigParser
import os
from datetime import datetime

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_database_path():
    config = ConfigParser()
    # Use the parent directory to locate the config file
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.ini")
    config.read(config_path)
    return config.get("DATABASES", "userdata")

def ensure_table_exists(cursor, table_name, columns):
    """
    Ensure the specified table exists in the database.
    If the table does not exist, it will be created with the provided columns.
    """
    logging.info(f"Ensuring table '{table_name}' exists...")
    column_definitions = ", ".join(f"{col} {defn}" for col, defn in columns.items())
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({column_definitions})")
    logging.info(f"Table '{table_name}' exists or was created successfully.")

def ensure_columns_exist(cursor, table_name, columns):
    """
    Ensure the specified columns exist in the database table.
    If a column does not exist, it will be added.
    """
    logging.info(f"Checking columns for table '{table_name}'...")
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cursor.fetchall()}

    for column_name, column_definition in columns.items():
        if column_name not in existing_columns:
            logging.info(f"Adding column '{column_name}' to table '{table_name}'...")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
            logging.info(f"Column '{column_name}' added successfully.")

def verify_schema():
    db_path = get_database_path()
    if not os.path.exists(db_path):
        logging.error(f"Database file not found at {db_path}")
        return

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        # Define the expected schema
        tables = {
            "logbook": {
                "flightNumber": "TEXT PRIMARY KEY",
                "dep": "TEXT NOT NULL",
                "arr": "TEXT NOT NULL",
                "scheduledDep": "INTEGER",
                "actualDep": "INTEGER",
                "scheduledArr": "INTEGER",
                "actualArr": "INTEGER",
                "status": "TEXT NOT NULL",
                "fleetId": "INTEGER"
            },
            "fleet": {
                "id": "INTEGER PRIMARY KEY",
                "airlineCode": "TEXT NOT NULL",
                "registration": "TEXT",
                "airframeIcao": "TEXT",
                "logHours": "REAL"
            },
            "achievements": {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "pilot_id": "INTEGER",
                "airlineId": "INTEGER",
                "achievement": "TEXT NOT NULL",
                "date_earned": "TEXT NOT NULL"
            },
            "pilots": {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "name": "TEXT NOT NULL",
                "homeHub": "TEXT",
                "currentLocation": "TEXT",
                "rank": "TEXT DEFAULT 'Student Pilot'",
                "airline_id": "INTEGER DEFAULT NULL",
                "total_hours": "REAL DEFAULT 0.0"
            },
        }

        # Ensure tables and columns exist
        for table_name, columns in tables.items():
            ensure_table_exists(cursor, table_name, columns)
            ensure_columns_exist(cursor, table_name, columns)

        connection.commit()
        logging.info("Schema verification and updates completed successfully.")

    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")

    finally:
        connection.close()
        logging.info("Database connection closed.")

def update_null_timestamps():
    db_path = get_database_path()
    if not os.path.exists(db_path):
        logging.error(f"Database file not found at {db_path}")
        return

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        # Update NULL timestamps to the current Unix timestamp
        current_timestamp = int(datetime.utcnow().timestamp())
        cursor.execute("""
            UPDATE logbook
            SET scheduledDep = ?, actualDep = ?, scheduledArr = ?, actualArr = ?
            WHERE scheduledDep IS NULL OR actualDep IS NULL OR scheduledArr IS NULL OR actualArr IS NULL
        """, (current_timestamp, current_timestamp, current_timestamp, current_timestamp))
        connection.commit()
        logging.info("Updated NULL timestamps with current Unix timestamp.")
    except sqlite3.Error as e:
        logging.error(f"Error updating timestamps: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    verify_schema()
    update_null_timestamps()

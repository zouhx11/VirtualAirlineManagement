import sqlite3
import logging
from configparser import ConfigParser

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_database_path():
    config = ConfigParser()
    config.read("../config.ini")
    return config.get("DATABASES", "userdata")

def ensure_table_and_columns(cursor, table_name, columns):
    """
    Ensure the specified table and columns exist in the database.
    """
    logging.info(f"Ensuring table '{table_name}' exists...")
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # Add missing columns
    for column_name, column_definition in columns.items():
        if column_name not in existing_columns:
            logging.info(f"Adding column '{column_name}' to table '{table_name}'...")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
            logging.info(f"Column '{column_name}' added successfully.")

def verify_schema():
    db_path = get_database_path()
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
                "id": "INTEGER PRIMARY KEY",
                "name": "TEXT NOT NULL",
                "homeHub": "TEXT",
                "currentLocation": "TEXT",
                "rank": "TEXT DEFAULT 'Student Pilot'",
                "total_hours": "REAL DEFAULT 0.0"
            },
        }

        # Verify tables and columns
        for table_name, columns in tables.items():
            ensure_table_and_columns(cursor, table_name, columns)

        connection.commit()
        logging.info("Schema verification and updates completed successfully.")

    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")

    finally:
        connection.close()
        logging.info("Database connection closed.")

if __name__ == "__main__":
    verify_schema()

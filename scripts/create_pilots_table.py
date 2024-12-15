import sqlite3
import configparser
import os
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("create_pilots_table.log"),
            logging.StreamHandler()
        ]
    )

def get_database_path():
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config.get("DATABASES", "userdata")

def ensure_table_exists(cursor):
    logging.info("Ensuring 'pilots' table exists...")
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS pilots (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            homeHub TEXT DEFAULT 'Unknown',
            currentLocation TEXT DEFAULT 'Unknown',
            total_hours REAL DEFAULT 0.0
        )'''
    )
    logging.info("'pilots' table verified or created successfully.")

def add_column_if_missing(cursor, table_name, column_name, column_definition):
    logging.info(f"Checking if column '{column_name}' exists in table '{table_name}'...")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]

    if column_name not in columns:
        logging.info(f"Column '{column_name}' is missing. Adding it...")
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
        logging.info(f"Column '{column_name}' added successfully.")
    else:
        logging.info(f"Column '{column_name}' already exists. No changes needed.")

def main():
    setup_logging()
    logging.info("Starting 'create_pilots_table' script...")

    db_path = get_database_path()
    logging.info(f"Using database path: {db_path}")

    if not os.path.exists(db_path):
        logging.error(f"Database file not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        ensure_table_exists(cursor)

        # Ensure necessary columns exist
        add_column_if_missing(cursor, "pilots", "homeHub", "TEXT DEFAULT 'Unknown'")
        add_column_if_missing(cursor, "pilots", "currentLocation", "TEXT DEFAULT 'Unknown'")

        conn.commit()
        logging.info("Database schema is up to date.")

    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")

    finally:
        conn.close()
        logging.info("Database connection closed.")

if __name__ == "__main__":
    main()

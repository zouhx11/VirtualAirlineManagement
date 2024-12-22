import sqlite3
import configparser
import os
import logging
from core.database_utils import connect_to_database

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

def setup_achievements_table(cursor):
    logging.info("Ensuring 'achievements' table exists...")
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pilot_id INTEGER,
        airlineId INTEGER, 
        achievement TEXT NOT NULL, 
        date_earned TEXT NOT NULL)
        '''
    )
    logging.info("'achievements' table verified or created successfully.")


def setup_fleet_table(cursor):
    logging.info("Ensuring 'fleet' table exists...")
    cursor.execute (
        '''CREATE TABLE IF NOT EXISTS fleet (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        airframeIcao TEXT,
        airlineCode	TEXT,
        registration TEXT,
        simbriefProfileId	TEXT,
        simbriefAcData	NUMERIC,
        logHours	REAL DEFAULT 0,
        logLocation	TEXT,
        logDistance	INTEGER DEFAULT 0,
        logFuelBurned	REAL DEFAULT 0,
        logFlightCount	INTEGER DEFAULT 0,
        associatedLivery	TEXT,
        image	TEXT,
        notes	TEXT,
        deleted	INTEGER DEFAULT 0, 
        lastupdated NUMBER DEFAULT 0)
    ''')

def ensure_table_exists(cursor):
    logging.info("Ensuring 'pilots' table exists...")
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS pilots (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            homeHub TEXT DEFAULT 'Unknown',
            currentLocation TEXT DEFAULT 'Unknown',
            total_hours REAL DEFAULT 0.0,
            created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))  -- Unix timestamp
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

    conn = connect_to_database()
    if conn:
        try:
            cursor = conn.cursor()
            ensure_table_exists(cursor)
            conn.commit()
            logging.info("Database schema is up to date.")
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
        finally:
            conn.close()
            logging.info("Database connection closed.")

if __name__ == "__main__":
    main()

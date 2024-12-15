import sqlite3
import pytest
from unittest.mock import patch
from modules.pilot_ranking_achievements import update_pilot_rank_and_achievements

@pytest.fixture
def in_memory_db():
    connection = sqlite3.connect(':memory:')

    connection.execute('''
        CREATE TABLE pilots (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            homeHub TEXT DEFAULT 'Unknown',
            currentLocation TEXT DEFAULT 'Unknown',
            total_hours REAL DEFAULT 0.0,
            rank TEXT DEFAULT 'Student Pilot'
        )
    ''')

    connection.execute('''
        CREATE TABLE logbook (
            flightNumber TEXT PRIMARY KEY,
            dep TEXT NOT NULL,
            arr TEXT NOT NULL,
            scheduledDep INTEGER,
            actualDep INTEGER,
            scheduledArr INTEGER,
            actualArr INTEGER,
            status TEXT NOT NULL
        )
    ''')

    connection.execute('''
        CREATE TABLE achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pilot_id INTEGER,
            achievement TEXT NOT NULL,
            date_earned TEXT NOT NULL,
            FOREIGN KEY (pilot_id) REFERENCES pilots(id)
        )
    ''')

    connection.commit()
    yield connection
    connection.close()

def test_update_pilot_rank_and_achievements(in_memory_db):
    in_memory_db.execute("INSERT INTO pilots (id, name) VALUES (1, 'John Doe')")
    in_memory_db.execute("INSERT INTO logbook (flightNumber, dep, arr, actualDep, actualArr, status) VALUES ('FL123', 'KATL', 'KLAX', 1638902400, 1638913200, 'COMPLETED')")
    in_memory_db.commit()

    update_pilot_rank_and_achievements(connection=in_memory_db)

    cursor = in_memory_db.cursor()
    cursor.execute("SELECT rank, total_hours FROM pilots WHERE id = 1")
    pilot = cursor.fetchone()
    assert pilot[0] == 'Student Pilot'
    assert pytest.approx(pilot[1], 0.01) == 3.0

    cursor.execute("SELECT achievement FROM achievements WHERE pilot_id = 1")
    achievements = cursor.fetchall()
    assert len(achievements) == 1
    assert achievements[0][0] == 'First Flight'

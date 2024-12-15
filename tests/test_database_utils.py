import unittest
import sqlite3
from unittest.mock import patch
from core.database_utils import add_pilot, fetch_pilot_data

class TestDatabaseUtils(unittest.TestCase):

    def setUp(self):
        # Create an in-memory database connection
        self.test_conn = sqlite3.connect(":memory:")

        # Patch `connect_to_database` to return the same connection
        self.patcher = patch('core.database_utils.connect_to_database', return_value=self.test_conn)
        self.patcher.start()

        # Initialize the database schema
        with self.test_conn:
            self.test_conn.execute("""
                CREATE TABLE pilots (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    homeHub TEXT,
                    currentLocation TEXT
                )
            """)

    def tearDown(self):
        # Stop the patch and close the database connection
        self.patcher.stop()
        self.test_conn.close()

    def test_add_pilot(self):
        # Add a pilot and verify it was added
        add_pilot("John Doe", "KATL", "KJFK", connection=self.test_conn)
        pilots = fetch_pilot_data(connection=self.test_conn)
        self.assertEqual(len(pilots), 1)
        self.assertEqual(pilots[0][1], "John Doe")

    def test_fetch_empty_pilot_data(self):
        # Verify no pilots exist initially
        pilots = fetch_pilot_data(connection=self.test_conn)
        self.assertEqual(pilots, [])

if __name__ == "__main__":
    unittest.main()

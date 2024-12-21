# scripts/test_fetch_logbook_data.py

from core.database_utils import fetch_logbook_data

def test_fetch():
    data = fetch_logbook_data()
    print(f"Fetched {len(data)} logbook entries.")
    for entry in data:
        print(entry)

if __name__ == "__main__":
    test_fetch()
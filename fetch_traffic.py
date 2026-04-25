import requests
import sqlite3
import datetime
import os

# API URL
API_URL = "https://api.ibb.gov.tr/tkmservices/api/TrafficData/v1/TrafficIndexHistory/1/5M"
DB_NAME = "traffic_data.db"

def setup_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS traffic_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            traffic_index INTEGER,
            traffic_index_date TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

def fetch_and_save():
    try:
        print(f"Fetching data from {API_URL}...")
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()

        if not data:
            print("No data received from API.")
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        new_records = 0
        for item in data:
            idx = item.get("TrafficIndex")
            date_str = item.get("TrafficIndexDate")
            
            # API returns dates like "2026-04-24T18:58:19.4738242+03:00"
            # We store it as is, or can normalize if needed.
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO traffic_index (traffic_index, traffic_index_date) VALUES (?, ?)",
                    (idx, date_str)
                )
                if cursor.rowcount > 0:
                    new_records += 1
            except Exception as e:
                print(f"Error inserting record: {e}")

        conn.commit()
        conn.close()
        print(f"Success: {new_records} new records added.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_db()
    fetch_and_save()

import sqlite3
import requests
from datetime import datetime

DB_NAME = "traffic_locations.db"
API_URL = "https://ulasav.csb.gov.tr/api/3/action/datastore_search?resource_id=70ecde5b-95ff-4168-b650-d726923408e8&limit=5000&sort=DATE_TIME%20desc"

def setup_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS traffic_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_time TEXT,
            latitude TEXT,
            longitude TEXT,
            minimum_speed INTEGER,
            maximum_speed INTEGER,
            average_speed INTEGER,
            number_of_vehicles INTEGER,
            UNIQUE(date_time, latitude, longitude)
        )
    ''')
    conn.commit()
    return conn

def get_latest_date(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(date_time) FROM traffic_locations")
    result = cursor.fetchone()
    return result[0] if result[0] else None

def fetch_and_save():
    print(f"[{datetime.now()}] Fetching location data from IBB API...")
    conn = setup_db()
    latest_date = get_latest_date(conn)
    print(f"Latest date in DB: {latest_date}")
    
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        
        records = data.get('result', {}).get('records', [])
        if not records:
            print("No location records found in API response.")
            return
            
        cursor = conn.cursor()
        new_records = 0
        
        for item in records:
            dt = item.get("DATE_TIME")
            
            # If we have a latest_date and the record is older or equal, we can skip
            # since we sort by DATE_TIME desc, but we'll try to insert anyway with IGNORE
            # to be safe against unordered data chunks
            
            try:
                cursor.execute(
                    '''INSERT OR IGNORE INTO traffic_locations 
                       (date_time, latitude, longitude, minimum_speed, maximum_speed, average_speed, number_of_vehicles) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (
                        dt,
                        item.get("LATITUDE"),
                        item.get("LONGITUDE"),
                        item.get("MINIMUM_SPEED"),
                        item.get("MAXIMUM_SPEED"),
                        item.get("AVERAGE_SPEED"),
                        item.get("NUMBER_OF_VEHICLES")
                    )
                )
                if cursor.rowcount > 0:
                    new_records += 1
            except Exception as e:
                print(f"Error inserting record: {e}")
                
        conn.commit()
        print(f"Successfully added {new_records} new location records.")
        
    except Exception as e:
        print(f"Error fetching/saving data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fetch_and_save()

import requests
import sqlite3
from datetime import datetime
import os

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

def get_missing_days():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(traffic_index_date) FROM traffic_index")
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        return 30 # Veritabanı boşsa son 30 günü çek
    
    last_date_str = row[0]
    # Örnek tarih formatı: "2026-04-24T18:58:19.4738242+03:00"
    # Sadece ilk 19 karakteri (YYYY-MM-DDTHH:MM:SS) alıyoruz
    try:
        last_date = datetime.strptime(last_date_str[:19], "%Y-%m-%dT%H:%M:%S")
        now = datetime.now()
        diff = now - last_date
        days = diff.days + 1 # En az 1 günlük çek, eksikse daha fazla
        
        if days < 1:
            days = 1
        elif days > 30:
            days = 30 # API'yi yormamak için maksimum 30 gün
            
        return days
    except Exception as e:
        print(f"Tarih ayrıştırma hatası: {e}. Varsayılan 1 gün çekiliyor.")
        return 1

def fetch_and_save():
    days_to_fetch = get_missing_days()
    api_url = f"https://api.ibb.gov.tr/tkmservices/api/TrafficData/v1/TrafficIndexHistory/{days_to_fetch}/5M"
    
    try:
        print(f"Son kayıttan bu yana geçen/eksik süre kontrol edildi. {days_to_fetch} günlük veri çekiliyor: {api_url}")
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        if not data:
            print("API'den veri alınamadı.")
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        new_records = 0
        for item in data:
            idx = item.get("TrafficIndex")
            date_str = item.get("TrafficIndexDate")
            
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO traffic_index (traffic_index, traffic_index_date) VALUES (?, ?)",
                    (idx, date_str)
                )
                if cursor.rowcount > 0:
                    new_records += 1
            except Exception as e:
                print(f"Kayıt hatası: {e}")

        conn.commit()
        conn.close()
        print(f"Başarılı: {new_records} yeni kayıt eklendi.")

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    setup_db()
    fetch_and_save()

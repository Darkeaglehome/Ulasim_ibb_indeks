from flask import Flask, jsonify, request, send_from_directory, make_response
import sqlite3
import os
import csv
import requests
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='')

# Disable caching for development
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

DB_NAME = "traffic_data.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/latest-dates')
def latest_dates():
    conn_idx = get_db_connection()
    idx_row = conn_idx.execute("SELECT MAX(traffic_index_date) as max_date FROM traffic_index").fetchone()
    idx_date = idx_row['max_date'] if idx_row else None
    conn_idx.close()
    
    return jsonify({
        "traffic_index": idx_date
    })

@app.route('/api/traffic')
def get_traffic_data():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    conn = get_db_connection()
    query = "SELECT traffic_index, traffic_index_date FROM traffic_index"
    params = []
    
    if start_date and end_date:
        query += " WHERE traffic_index_date BETWEEN ? AND ?"
        params = [start_date, end_date]
    elif start_date:
        query += " WHERE traffic_index_date >= ?"
        params = [start_date]
    
    query += " ORDER BY traffic_index_date ASC"
    
    data = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in data])

@app.route('/api/fetch-history')
def fetch_history():
    days = request.args.get('days', default='7', type=str)
    
    # Simple validation to ensure it's a number
    if not days.isdigit():
        return jsonify({"success": False, "message": "Geçersiz gün sayısı."}), 400
        
    api_url = f"https://api.ibb.gov.tr/tkmservices/api/TrafficData/v1/TrafficIndexHistory/{days}/5M"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        
        if not data:
             return jsonify({"success": False, "message": "API'den veri alınamadı."}), 404
             
        conn = get_db_connection()
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
                pass # Ignore individual insert errors
                
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": f"{days} günlük veri çekildi. {new_records} yeni kayıt eklendi."})
    except Exception as e:
         return jsonify({"success": False, "message": f"Veri çekilirken hata oluştu: {str(e)}"}), 500

@app.route('/api/export-csv')
def export_csv():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    conn = get_db_connection()
    query = "SELECT traffic_index, traffic_index_date FROM traffic_index"
    params = []
    
    if start_date and end_date:
        query += " WHERE traffic_index_date BETWEEN ? AND ?"
        params = [start_date, end_date]
    elif start_date:
        query += " WHERE traffic_index_date >= ?"
        params = [start_date]
    
    query += " ORDER BY traffic_index_date ASC"
    
    data = conn.execute(query, params).fetchall()
    conn.close()
    
    if not data:
        return jsonify({"success": False, "message": "Dışa aktarılacak veri bulunamadı."}), 400

    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    filename = f"trafik_verisi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(desktop, filename)
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Tarih', 'Trafik İndeksi'])
            for row in data:
                writer.writerow([row['traffic_index_date'], row['traffic_index']])
        
        return jsonify({"success": True, "message": f"Veri başarıyla dışa aktarildi: {filename}"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Hata: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)

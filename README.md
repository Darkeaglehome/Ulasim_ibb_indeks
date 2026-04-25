# İBB Trafik Analizi & Harita

Bu proje, İstanbul Büyükşehir Belediyesi'nin trafik verilerini çekerek, analiz etmenizi ve grafikler üzerinden görselleştirmenizi sağlayan bir web uygulamasıdır.

https://darkeaglehome.github.io/Ulasim_ibb_indeks/ yüklenmiş olup localde çalıştırılması tavsiye edilir...

## Özellikler

- **Trafik İndeksi Grafiği:** Belirli tarih aralıklarındaki trafik yoğunluğunu görselleştirir.
- **Tarihsel Veri Çekme:** Geçmişe dönük trafik verilerini API üzerinden çekip yerel veritabanına kaydeder.
- **CSV Dışa Aktarma:** Analiz edilen verileri CSV formatında indirmenize olanak tanır.
- **İstatistikler:** Seçilen tarih aralığındaki en yüksek, en düşük ve ortalama trafik indeksini hesaplar.
- **Modern Arayüz:** Kullanıcı dostu ve modern bir arayüz sunar.

## Kullanılan Teknolojiler

- **Backend:** Python, Flask (veya FastAPI) (`app.py`), SQLite (`traffic_data.db`)
- **Frontend:** HTML, CSS, JavaScript (Chart.js, Luxon)

## Çalıştırma

Projeyi yerel ortamınızda çalıştırmak için:
1. Python bağımlılıklarını kurun.
2. `python app.py` komutuyla sunucuyu başlatın.
3. Tarayıcınızda uygulamanın çalıştığı adrese (örn: http://localhost:8080) gidin.

## GitHub Pages Hakkında Önemli Not
Bu proje bir Python arka ucu (backend) ve veritabanı (SQLite) kullandığı için, GitHub Pages (`.github.io`) gibi sadece statik dosya (HTML/CSS/JS) barındıran platformlarda API istekleri (veri çekme) çalışmayacaktır. Arayüz görünecektir, ancak veriler gelmeyecektir. Projeyi tam özellikleriyle internette yayınlamak için Render, Heroku veya PythonAnywhere gibi bir sunucu barındırma hizmeti kullanmanız gerekir.

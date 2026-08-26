# 🗺️ Sistem Maklumat Geografi (GIS) & Dashboard Analisis Poligon

Aplikasi web berasaskan Python dan **Streamlit** untuk memuat naik data koordinat (Easting, Northing), memetakan poligon 2D (CAD), melakukan overlay peta satelit interaktif, serta mengeksport data ke format **GeoJSON** dan **DXF (AutoCAD)**.

---

## 🌟 Ciri-Ciri Utama

- **🔒 Sistem Log Masuk:** Halaman pengesahan pengguna secara selamat.
- **📊 Pengiraan Luas & Geometri:** Mengira luas poligon ($m^2$ dan Hektar), bearing, serta jarak antara stesen secara automatik.
- **📐 Visualisasi 2D CAD:** Plot garisan sempadan, stesen (STN), bearing, dan jarak menggunakan `matplotlib`.
- **🌍 Overlay Peta Satelit Interaktif:** Integrasi peta interaktif (Google Satellite, Google Hybrid, Google Roadmap, OpenStreetMap) menggunakan `folium` dan penukaran unjuran koordinat (CRS/EPSG) secara dinamik.
- **📥 Eksport Data:**
  - **GeoJSON (WGS84)** untuk kegunaan perisian GIS (QGIS/ArcGIS).
  - **DXF** untuk perisian CAD/AutoCAD (termasuk *layer* POLYGON, POINTS, dan TEXT).

---

## 📁 Format Fail Input CSV

Aplikasi ini memerlukan fail CSV yang mempunyai sekurang-kurangnya lajur **`E`** (Easting) dan **`N`** (Northing). Lajur **`STN`** (Nombor Stesen) adalah pilihan (*optional*).

Contoh format `data_ukuran.csv`:

```csv
STN,E,N
1,438210.50,345120.20
2,438300.10,345150.80
3,438280.40,345000.10
4,438190.00,345020.50
```

---

## 🛠️ Kebergantungan Pakej (Dependencies)

Projek ini memerlukan modul-modul Python berikut. Anda boleh menyenaraikannya di dalam fail `requirements.txt`:

```text
streamlit
pandas
matplotlib
numpy
folium
streamlit-folium
ezdxf
pyproj
```

---

## 🚀 Cara Menjalankan Aplikasi Secara Tempatan (Local Setup)

### 1. Klonavan Repositori
```bash
git clone [https://github.com/nama-username/nama-repositori.git](https://github.com/nama-username/nama-repositori.git)
cd nama-repositori
```

### 2. Cipta Virtual Environment (Pilihan tetapi digalakkan)
```bash
python -m venv venv
# Bagi Windows:
venv\Scripts\activate
# Bagi macOS/Linux:
source venv/bin/activate
```

### 3. Pasang Semua Kebergantungan
```bash
pip install -r requirements.txt
```

### 4. Jalankan Aplikasi Streamlit
```bash
streamlit run app.py
```
*(Gantikan `app.py` dengan nama fail utama Python anda jika berbeza).*

---

## 🔑 Maklumat Log Masuk Lalai (Default Login)

- **Nama Pengguna / Emel:** `admin`
- **Kata Laluan:** `1234`

---

## 📸 Paparan Antaramuka (Screenshots)

| Plot CAD 2D | Overlay Peta Satelit |
| :---: | :---: |
| *Sertakan imej plot CAD di sini* | *Sertakan imej peta satelit di sini* |

---

## 📝 Lesen & Penghargaan
Dibangunkan untuk kemudahan visualisasi dan pemprosesan data ruang geospatial.

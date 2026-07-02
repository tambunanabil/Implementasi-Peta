# iLahan — Sistem Pengecekan Kesesuaian Lahan Kentang

Aplikasi berbasis Streamlit untuk menganalisis kesesuaian lahan pertanian kentang menggunakan model ANN (Artificial Neural Network) dan data spasial GIS.

**Live:** https://ilahan.gradien.my.id/

---

## Struktur Proyek

```
Implementasi-Peta/
├── app.py                          # Aplikasi utama Streamlit
├── requirements.txt                # Dependensi Python
├── migrate_sqlite_to_mysql.py      # Script migrasi data (jalankan sekali)
├── setup_mysql.sql                 # Script setup tabel MySQL (jalankan sekali)
├── .gitignore                      # File yang diabaikan Git
├── README.md                       # Dokumentasi ini
│
├── .streamlit/
│   └── secrets.toml                # ⚠️ JANGAN DI-COMMIT — kredensial DB
│
└── [file model — tidak di-commit, upload manual]
    ├── model_kesesuaian.keras
    ├── scaler_kesesuaian.save
    ├── model_ann.keras
    ├── scaler_X.pkl
    └── scaler_y.pkl
```

---

## Setup Awal (Lakukan Sekali)

### 1. Clone repo
```bash
git clone https://github.com/tambunanabil/Implementasi-Peta.git
cd Implementasi-Peta
```

### 2. Buat virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependensi
```bash
pip install -r requirements.txt
```

### 4. Buat file secrets (untuk development lokal)
Buat file `.streamlit/secrets.toml` (sudah ada templatenya di folder `.streamlit/`):
```toml
[mysql]
host     = "153.92.15.9"
port     = 3306
database = "u160973994_ilahan"
user     = "u160973994_ilahan"
password = "xxx"
```
> Minta password ke pengelola proyek. Jangan pernah commit file ini.

### 5. Setup tabel MySQL (sekali saja)
Buka database manager (TablePlus / DBeaver / phpMyAdmin) lalu jalankan:
```
setup_mysql.sql
```

### 6. Migrasi data dari SQLite ke MySQL (sekali saja)
Pastikan file `database_lahan.db` ada di folder proyek, lalu:
```bash
python migrate_sqlite_to_mysql.py
```

### 7. Upload file model
File model **tidak disimpan di GitHub** karena ukurannya besar.
Upload manual ke Streamlit Cloud melalui:
- Streamlit Cloud → App Settings → **Secrets** (untuk secrets)
- File model → upload ke **GitHub** dengan Git LFS, atau simpan di folder proyek lokal

### 8. Jalankan lokal
```bash
streamlit run app.py
```
Buka browser: http://localhost:8501

---

## Deploy ke Streamlit Cloud

1. Push semua perubahan ke GitHub
2. Buka https://share.streamlit.io
3. Klik **New app** → pilih repo `tambunanabil/Implementasi-Peta`
4. Main file: `app.py`
5. Klik **Advanced settings** → **Secrets** → paste isi `secrets.toml`
6. Klik **Deploy**

### Custom Domain
Setelah deploy, hubungkan domain:
1. Di Streamlit Cloud → App → **Settings** → **Custom domain** → isi `ilahan.gradien.my.id`
2. Di DNS hosting, tambahkan record:
   ```
   Type  : CNAME
   Name  : ilahan
   Value : cname.streamlit.app
   TTL   : 3600
   ```

---

## Alur Pengembangan (untuk Kontributor)

```
1. git pull origin main          ← ambil update terbaru
2. [edit kode]
3. streamlit run app.py          ← test lokal
4. git add .
5. git commit -m "deskripsi perubahan"
6. git push origin main          ← otomatis update di Streamlit Cloud
```

> ⚠️ Jangan pernah commit file `.streamlit/secrets.toml`, file `*.keras`, `*.pkl`, `*.save`, atau `database_lahan.db`.

---

## Database

- **Host:** 153.92.15.9 (MySQL remote)
- **Database:** u160973994_ilahan
- **Tabel utama:** `titik_acuan`
- Koneksi menggunakan Streamlit Secrets (lihat `secrets.toml`)
- Fallback otomatis ke SQLite lokal jika MySQL tidak tersedia (untuk development)

---

## Teknologi

| Komponen | Library |
|---|---|
| UI / Web | Streamlit |
| Peta | Folium + streamlit-folium |
| Model AI | TensorFlow / Keras |
| Data | Pandas, NumPy |
| Database | MySQL (mysql-connector-python) |
| Kalibrasi Sensor | Scikit-learn, Joblib |

---

## Kontak
Dibuat oleh Tim Penelitian — untuk pertanyaan teknis hubungi pengelola repo.

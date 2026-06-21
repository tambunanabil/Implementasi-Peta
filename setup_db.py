import sqlite3
import pandas as pd

print("Memulai proses perbaikan dan migrasi data...")
try:
    conn = sqlite3.connect('database_lahan.db')

    # 1. Baca file Excel
    df = pd.read_excel('Data_Kesesuaian.xlsx')

    # 2. SOLUSI MERGED CELLS: Menarik data koordinat ke baris kosong di bawahnya
    df['Latitude'] = df['Latitude'].ffill()
    df['Longitude'] = df['Longitude'].ffill()

    # 3. Masukkan ke tabel SQL
    df.to_sql('titik_acuan', conn, if_exists='replace', index=False)
    
    print("✅ Berhasil! Database telah diperbarui dan masalah Merged Cells sudah teratasi.")
except Exception as e:
    print(f"❌ Terjadi kesalahan: {e}")
finally:
    conn.close()
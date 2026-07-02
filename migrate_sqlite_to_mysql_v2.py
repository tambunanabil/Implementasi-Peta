"""
Script migrasi data SQLite -> MySQL (v2 - fix NaN & kolom aktual)
Jalankan: python migrate_sqlite_to_mysql_v2.py
"""

import sqlite3
import mysql.connector
import pandas as pd
import numpy as np
import math

SQLITE_FILE   = 'database_lahan.db'
SQLITE_TABLE  = 'titik_acuan'

MYSQL_HOST     = '153.92.15.9'
MYSQL_PORT     = 3306
MYSQL_DATABASE = 'u160973994_ilahan'
MYSQL_USER     = 'u160973994_ilahan'
MYSQL_PASSWORD = 'R@5aOtCck'

def safe_val(v):
    """Konversi NaN/inf ke None agar MySQL tidak error."""
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    # pandas NA
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v

def migrate():
    # 1. Baca SQLite
    print(f'Membaca {SQLITE_FILE}...')
    conn_s = sqlite3.connect(SQLITE_FILE)
    df = pd.read_sql_query(f'SELECT * FROM {SQLITE_TABLE}', conn_s)
    conn_s.close()
    print(f'  -> {len(df)} baris, kolom: {list(df.columns)}')

    # 2. Normalisasi kolom
    df.columns = df.columns.str.strip()
    df.rename(columns={
        'Latitude':  'Lat',
        'latitude':  'Lat',
        'lat':       'Lat',
        'Longitude': 'Lon',
        'longitude': 'Lon',
        'lon':       'Lon',
        'Kecocokan': 'Status',
        'kecocokan': 'Status',
        'EC_S1':     'EC_S',
        'N_S1':      'N_S',
        'P_S1':      'P_S',
        'K_S1':      'K_S',
        'Moist_S1':  'Moist_S',
        'Temp_D_S1': 'Temp_D_S',
    }, inplace=True)
    print(f'  -> Kolom setelah rename: {list(df.columns)}')

    # 3. Koneksi MySQL
    print(f'\nMenghubungkan ke MySQL {MYSQL_HOST}...')
    conn_m = mysql.connector.connect(
        host=MYSQL_HOST, port=MYSQL_PORT,
        database=MYSQL_DATABASE,
        user=MYSQL_USER, password=MYSQL_PASSWORD,
        connect_timeout=15
    )
    cursor = conn_m.cursor()
    print('  -> Terhubung!')

    # 4. Drop & recreate tabel sesuai kolom aktual
    print('Membuat ulang tabel titik_acuan...')
    cursor.execute('DROP TABLE IF EXISTS titik_acuan')

    # Bangun CREATE TABLE dari kolom df
    col_defs = ['id INT AUTO_INCREMENT PRIMARY KEY']
    type_map = {
        'Kabupaten': 'VARCHAR(150)',
        'Desa':      'VARCHAR(150)',
        'Jenis_Tanah': 'VARCHAR(150)',
        'Status':    'VARCHAR(50)',
    }
    for col in df.columns:
        sql_type = type_map.get(col, 'DOUBLE')
        col_defs.append(f'`{col}` {sql_type}')
    col_defs.append('created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')

    create_sql = 'CREATE TABLE titik_acuan (\n  ' + ',\n  '.join(col_defs) + '\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4'
    cursor.execute(create_sql)
    conn_m.commit()
    print('  -> Tabel dibuat!')

    # 5. Insert data
    cols        = list(df.columns)
    col_names   = ', '.join([f'`{c}`' for c in cols])
    placeholders = ', '.join(['%s'] * len(cols))
    insert_sql   = f'INSERT INTO titik_acuan ({col_names}) VALUES ({placeholders})'

    rows = []
    for _, row in df.iterrows():
        rows.append(tuple(safe_val(row[c]) for c in cols))

    print(f'Menginsert {len(rows)} baris...')
    batch_size = 50
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        cursor.executemany(insert_sql, batch)
        conn_m.commit()
        print(f'  -> {min(i+batch_size, len(rows))}/{len(rows)} baris')

    cursor.close()
    conn_m.close()
    print(f'\nMigrasi selesai! {len(rows)} baris berhasil masuk ke MySQL.')

if __name__ == '__main__':
    migrate()

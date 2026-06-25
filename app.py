import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import numpy as np
import sqlite3
import joblib
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

try:
    from tensorflow import keras
    HAS_TF = True
except ImportError:
    HAS_TF = False

# ==========================================
# 1. PENGATURAN HALAMAN DASAR & SESSION STATE
# ==========================================
st.set_page_config(page_title="AgriGIS | Lahan Kentang", layout="wide", initial_sidebar_state="collapsed")

if 'page' not in st.session_state:
    st.session_state.page = 'beranda'
if 'clicked_lat' not in st.session_state:
    st.session_state.clicked_lat = None
if 'clicked_lon' not in st.session_state:
    st.session_state.clicked_lon = None
if 'show_kes_form' not in st.session_state:
    st.session_state.show_kes_form = False
if 'elevasi_terklik' not in st.session_state:
    st.session_state.elevasi_terklik = None
if 'mode_luar_jangkauan' not in st.session_state:
    st.session_state.mode_luar_jangkauan = None  # None | 'prediksi' | 'skrining'
if 'sumber_data_npk' not in st.session_state:
    st.session_state.sumber_data_npk = None      # None | 'sensor' | 'lab'
if 'kalibrasi_selesai' not in st.session_state:
    st.session_state.kalibrasi_selesai = False
if 'kalibrasi_n' not in st.session_state:
    st.session_state.kalibrasi_n = 0.0
if 'kalibrasi_p' not in st.session_state:
    st.session_state.kalibrasi_p = 0.0
if 'kalibrasi_k' not in st.session_state:
    st.session_state.kalibrasi_k = 0.0
if 'kalibrasi_ec' not in st.session_state:
    st.session_state.kalibrasi_ec = 0.0
if 'kalibrasi_ph' not in st.session_state:
    st.session_state.kalibrasi_ph = 7.0
if 'kalibrasi_moist' not in st.session_state:
    st.session_state.kalibrasi_moist = 0.0
if 'kalibrasi_suhu' not in st.session_state:
    st.session_state.kalibrasi_suhu = 20.0

# ==========================================
# 2. CSS: GLASSMORPHISM & TATA LETAK TERPUSAT
# ==========================================
st.markdown("""
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"], header { display: none !important; }

.stApp {
    background-image: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.6)), url("https://images.unsplash.com/photo-1590165482129-1b8b27698780?q=80&w=1600&auto=format&fit=crop");
    background-size: cover;
    background-attachment: fixed;
    background-position: center;
}

.block-container {
    background-color: rgba(20, 32, 20, 0.65) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 16px;
    padding: 40px 50px !important;
    max-width: 1140px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    margin-top: 10vh !important;
    margin-bottom: 10vh !important;
    box-shadow: 0 15px 35px rgba(0,0,0,0.4);
}

.stMarkdown, .stText, label, .stMarkdown p, h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}
[data-testid="stMetricValue"] { color: #ffffff !important; }
[data-testid="stMetricLabel"] { color: #cccccc !important; }

.stButton>button {
    background-color: rgba(45, 106, 79, 0.95);
    color: white !important;
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: 600;
    transition: 0.2s;
    width: 100%;
}
.stButton>button:hover {
    background-color: rgba(27, 67, 50, 1);
    border-color: white;
}

/* ── Kotak Hasil Evaluasi (tidak mirip tombol hijau) ── */
.box-cocok {
    background-color: rgba(0, 80, 140, 0.30);
    border-left: 4px solid #4da6e0;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0;
    color: #d0eeff;
    font-weight: 500;
    letter-spacing: 0.01em;
}
.box-netral {
    background-color: rgba(140, 100, 0, 0.30);
    border-left: 4px solid #e0b84d;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0;
    color: #fff3cc;
    font-weight: 500;
    letter-spacing: 0.01em;
}
.box-tidak {
    background-color: rgba(140, 30, 0, 0.30);
    border-left: 4px solid #e05c4d;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0;
    color: #ffe0dd;
    font-weight: 500;
    letter-spacing: 0.01em;
}
.box-info {
    background-color: rgba(20, 50, 90, 0.40);
    border-left: 4px solid #5b8dd9;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0;
    color: #ccdcf5;
    font-size: 0.95em;
    line-height: 1.6;
}
.box-notice {
    background-color: rgba(80, 60, 0, 0.35);
    border-left: 4px solid #c9952a;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0;
    color: #fde9b5;
    font-size: 0.95em;
}
.box-success {
    background-color: rgba(0, 80, 40, 0.35);
    border-left: 4px solid #2ecc71;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0;
    color: #b8f5d0;
    font-size: 0.95em;
}
.box-warn {
    background-color: rgba(120, 80, 0, 0.35);
    border-left: 4px solid #e0a020;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0;
    color: #fde8a0;
    font-size: 0.95em;
}
.box-error {
    background-color: rgba(100, 20, 0, 0.35);
    border-left: 4px solid #c94a3a;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0;
    color: #ffd5d0;
    font-size: 0.95em;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. FUNGSI LOGIKA SPASIAL (FITUR 1)
# ==========================================
@st.cache_data(ttl=600)
def load_data_peta():
    try:
        conn = sqlite3.connect('database_lahan.db')
        df = pd.read_sql_query("SELECT * FROM titik_acuan", conn)
        conn.close()
    except:
        try:
            df = pd.read_excel('Data_Kesesuaian.xlsx')
        except:
            return pd.DataFrame()

    if not df.empty:
        df.columns = df.columns.str.strip()
        if 'Latitude' in df.columns: df.rename(columns={'Latitude': 'Lat'}, inplace=True)
        elif 'lat' in df.columns: df.rename(columns={'lat': 'Lat'}, inplace=True)
        if 'Longitude' in df.columns: df.rename(columns={'Longitude': 'Lon'}, inplace=True)
        elif 'lon' in df.columns: df.rename(columns={'lon': 'Lon'}, inplace=True)
        if 'Kecocokan' in df.columns: df.rename(columns={'Kecocokan': 'Status'}, inplace=True)

        if 'Lat' in df.columns and 'Lon' in df.columns:
            df['Lat'] = pd.to_numeric(df['Lat'], errors='coerce')
            df['Lon'] = pd.to_numeric(df['Lon'], errors='coerce')
            df['Lat'] = df['Lat'].ffill()
            df['Lon'] = df['Lon'].ffill()
            df = df.dropna(subset=['Lat', 'Lon'])
            df = df.drop_duplicates(subset=['Lat', 'Lon'], keep='first')

    return df

def get_elevation(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        res = requests.get(url).json()
        return res["elevation"][0] if "elevation" in res else None
    except: return None

def hitung_jarak_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

# ==========================================
# 4. FUNGSI MODEL ANN PUPUK (FITUR 2)
# ==========================================
@st.cache_resource
def load_ann_model():
    if not HAS_TF: return None, None, None
    try:
        model = keras.models.load_model("model_ann.keras", compile=False)
        scaler_X = joblib.load("scaler_X.pkl")
        scaler_y = joblib.load("scaler_y.pkl")
        return model, scaler_X, scaler_y
    except:
        return None, None, None

# ==========================================
# 4B. FUNGSI MODEL ANN KESESUAIAN LAHAN (FALLBACK FITUR 1)
# ==========================================
@st.cache_resource
def load_kesesuaian_model():
    """Load model ANN kesesuaian lahan beserta scaler-nya."""
    if not HAS_TF: return None, None
    try:
        model_kes = keras.models.load_model("model_kesesuaian.keras", compile=False)
        scaler_kes = joblib.load("scaler_kesesuaian.save")
        return model_kes, scaler_kes
    except:
        return None, None

# Spearman weights iterasi ke-3 (digunakan saat training model kesesuaian)
_SPEARMAN_RAW = np.array([
    15.129147,  # EC
    11.488127,  # N
    5.098820,   # P
    10.377051,  # K
    2.214403,   # PH
    0.700232,   # Moist
    24.369542,  # T_D
    30.622679   # Elevasi
], dtype='float32')
SPEARMAN_KES_WEIGHTS = _SPEARMAN_RAW / _SPEARMAN_RAW.sum()

def prediksi_kesesuaian(ec, n, p, k, ph, moist, t_d, elevasi, model_kes, scaler_kes):
    """
    Jalankan model ANN kesesuaian lahan.
    Urutan input: EC, N, P, K, PH, Moist, T_D, Elevasi
    Output: (label_str, confidence_float, probs_array)
    """
    label_map = {0: 'Tidak Cocok', 1: 'Netral', 2: 'Cocok'}
    warna_map = {'Cocok': '#0072B2', 'Netral': '#E69F00', 'Tidak Cocok': '#D55E00'}

    input_arr = np.array([[ec, n, p, k, ph, moist, t_d, elevasi]], dtype='float32')
    X_scaled = scaler_kes.transform(input_arr)
    X_weighted = X_scaled * SPEARMAN_KES_WEIGHTS
    probs = model_kes.predict(X_weighted, verbose=0)
    pred_idx = int(np.argmax(probs, axis=1)[0])
    label = label_map[pred_idx]
    confidence = float(np.max(probs))
    warna = warna_map[label]
    return label, confidence, probs[0], warna

# ==========================================
# 5. FUNGSI KLASIFIKASI & REKOMENDASI PUPUK
# ==========================================
def klasifikasi_n(val):
    # Range data lab N: 595.8 - 7887 mg/100g, dibagi 5 kategori merata
    if val < 2054:   return 'Sangat Rendah'
    elif val < 3512: return 'Rendah'
    elif val < 4971: return 'Sedang'
    elif val < 6429: return 'Tinggi'
    else:            return 'Sangat Tinggi'

def klasifikasi_p(val):
    # Range data lab P: 0.38 - 875 mg/100g, dibagi 5 kategori merata
    if val < 175:  return 'Sangat Rendah'
    elif val < 350: return 'Rendah'
    elif val < 525: return 'Sedang'
    elif val < 700: return 'Tinggi'
    else:           return 'Sangat Tinggi'

def klasifikasi_k(val):
    # Range data lab K: 31.6 - 1403 mg/100g, dibagi 5 kategori merata
    if val < 306:   return 'Sangat Rendah'
    elif val < 580: return 'Rendah'
    elif val < 854: return 'Sedang'
    elif val < 1129: return 'Tinggi'
    else:            return 'Sangat Tinggi'

def saran_n(kat):
    if kat in ['Sangat Rendah', 'Rendah']: return 'Fase vegetatif terancam. Tanaman kentang akan kerdil.'
    elif kat == 'Sedang': return 'Kebutuhan N tercukupi untuk pertumbuhan daun.'
    else: return 'Kelebihan N. Tanaman akan terlalu rimbun daun namun pembentukan umbi terhambat.'

def langkah_n(kat):
    if kat in ['Sangat Rendah', 'Rendah']: return 'Berikan pupuk Urea/ZA dosis penuh pada fase awal tanam.'
    elif kat == 'Sedang': return 'Lakukan pemupukan N standar sesuai rekomendasi lokal.'
    else: return 'Kurangi dosis pupuk N. Fokuskan nutrisi untuk pembesaran umbi kentang.'

def saran_p(kat):
    if kat in ['Sangat Rendah', 'Rendah']: return 'Perakaran dan inisiasi umbi kentang akan sangat terhambat.'
    elif kat == 'Sedang': return 'Status P cukup, namun kentang butuh P tinggi untuk umbi.'
    else: return 'Kandungan Fosfor melimpah di dalam tanah.'

def langkah_p(kat):
    if kat in ['Sangat Rendah', 'Rendah']: return 'Wajib aplikasikan pupuk dasar SP-36/TSP dosis tinggi sebelum tanam.'
    elif kat == 'Sedang': return 'Tambahkan pupuk P dosis sedang untuk memaksimalkan jumlah umbi.'
    else: return 'Gunakan pupuk hayati (mikroba pelarut fosfat) untuk mencairkan P yang terikat di tanah.'

def saran_k(kat):
    if kat in ['Sangat Rendah', 'Rendah']: return 'Sangat kritis! Pembesaran umbi kentang akan gagal/kualitas rendah.'
    elif kat == 'Sedang': return 'Kentang adalah tanaman rakus Kalium. Status Sedang masih perlu tambahan.'
    else: return 'Ketersediaan Kalium optimal untuk sintesis pati dan pembesaran umbi.'

def langkah_k(kat):
    if kat in ['Sangat Rendah', 'Rendah']: return 'Segera aplikasikan pupuk KCl/ZK dosis tinggi pada fase pembentukan umbi.'
    elif kat == 'Sedang': return 'Berikan pupuk Kalium susulan pada fase pengisian umbi.'
    else: return 'Pemupukan Kalium kimia dapat dikurangi. Lakukan pemeliharaan standar.'

df_data = load_data_peta()

# ==========================================
# HALAMAN 0: BERANDA UTAMA
# ==========================================
if st.session_state.page == 'beranda':
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-weight: 800; text-shadow: 2px 2px 4px rgba(0,0,0,0.6);'>Sistem Informasi Spasial Lahan Kentang</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px; color: #e2e2e2;'>Platform Prediksi Kesesuaian Lahan Berbasis Agroklimat & Sebaran Hara</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.15); margin: 40px 0;'>", unsafe_allow_html=True)

    col_kiri, col_btn1, col_btn2, col_kanan = st.columns([1, 1.5, 1.5, 1])

    with col_btn1:
        if st.button("Peta Kesesuaian Lahan", use_container_width=True):
            st.session_state.page = 'fitur_peta'
            st.session_state.show_kes_form = False
            st.rerun()
    with col_btn2:
        if st.button("Rekomendasi Pemupukan", use_container_width=True):
            st.session_state.page = 'fitur_pupuk'
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

# ==========================================
# HALAMAN 1: PETA KESESUAIAN (FITUR 1)
# ==========================================
elif st.session_state.page == 'fitur_peta':

    col_judul, col_kembali = st.columns([4, 1])
    with col_judul:
        st.markdown("<h2 style='margin:0; font-weight: 700;'>Pemetaan Kesesuaian Lahan</h2>", unsafe_allow_html=True)
    with col_kembali:
        if st.button("Kembali ke Beranda"):
            st.session_state.page = 'beranda'
            st.session_state.show_kes_form = False
            st.session_state.clicked_lat = None
            st.session_state.clicked_lon = None
            st.rerun()

    st.markdown("<hr style='border-color: rgba(255,255,255,0.15); margin: 15px 0 25px 0;'>", unsafe_allow_html=True)

    col_input, col_peta = st.columns([1.2, 2.8])

    with col_input:
        st.markdown("<h4>Parameter Analisis</h4>", unsafe_allow_html=True)
        radius_km = st.slider("Radius Batas Toleransi (Km)", 1.0, 15.0, 3.0, 0.5)
        ph_manual = st.number_input("Input Data pH Lokal (Opsional)", 0.0, 14.0, 0.0, 0.1)

        st.markdown("<br>", unsafe_allow_html=True)
        if df_data.empty:
            st.markdown("<div class='box-error'>Data lahan tidak terdeteksi di server.</div>", unsafe_allow_html=True)

    with col_peta:
        m = folium.Map(
            location=[-7.2106, 109.8941],
            zoom_start=11,
            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attr='Google Maps Hybrid'
        )

        if not df_data.empty:
            for _, row in df_data.iterrows():
                kategori = str(row.get('Status', '')).strip().lower()

                if kategori == 'cocok': warna = '#0072B2'
                elif kategori == 'netral': warna = '#E69F00'
                else: warna = '#D55E00'

                ph_tanah = row.get('PH_S1', 'N/A')
                elev     = row.get('Elevasi', 'N/A')
                desa     = row.get('Desa', 'N/A')
                kabupaten = row.get('Kabupaten', 'N/A')

                popup_text = f"""
<div style='color: black; font-family: sans-serif; font-size: 12px; line-height: 1.5; min-width: 150px;'>
<b style='font-size: 13px; color: {warna};'>{kategori.upper()}</b><br>
<hr style='margin: 4px 0; border: 0; border-top: 1px solid #ccc;'>
<b>Desa:</b> {desa}<br>
<b>Kabupaten:</b> {kabupaten}<br>
<b>Elevasi:</b> {elev} mdpl<br>
<b>pH:</b> {ph_tanah}
</div>
"""
                folium.CircleMarker(
                    location=[row['Lat'], row['Lon']],
                    radius=6, color='white', weight=1.5, fill=True, fill_color=warna, fill_opacity=1.0,
                    popup=folium.Popup(popup_text, max_width=250)
                ).add_to(m)

        if st.session_state.clicked_lat is not None:
            folium.Marker(
                location=[st.session_state.clicked_lat, st.session_state.clicked_lon],
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)

        map_interaction = st_folium(m, use_container_width=True, height=450, returned_objects=["last_clicked"])

        if map_interaction and map_interaction.get("last_clicked"):
            lat_klik = map_interaction["last_clicked"]["lat"]
            lon_klik = map_interaction["last_clicked"]["lng"]

            if st.session_state.clicked_lat != lat_klik or st.session_state.clicked_lon != lon_klik:
                st.session_state.clicked_lat  = lat_klik
                st.session_state.clicked_lon  = lon_klik
                st.session_state.show_kes_form = False  # reset form saat titik baru diklik
                st.session_state.mode_luar_jangkauan = None
                st.session_state.sumber_data_npk = None
                st.session_state.kalibrasi_selesai = False
                st.rerun()

    # ─── BAGIAN HASIL EVALUASI ───────────────────────────────────
    if st.session_state.clicked_lat is not None:
        st.markdown("<hr style='border-color: rgba(255,255,255,0.15); margin: 30px 0 20px 0;'>", unsafe_allow_html=True)
        lat_eval = st.session_state.clicked_lat
        lon_eval = st.session_state.clicked_lon

        with st.spinner("Memproses analisis spasial wilayah..."):
            elevasi_satelit = get_elevation(lat_eval, lon_eval)

        if not df_data.empty and elevasi_satelit is not None:
            df_working = df_data.copy()
            df_working['Jarak_Km'] = df_working.apply(
                lambda r: hitung_jarak_haversine(lat_eval, lon_eval, r['Lat'], r['Lon']), axis=1
            )
            df_terfilter = df_working[df_working['Jarak_Km'] <= radius_km].copy()

            st.markdown("<h4>Hasil Evaluasi Lokasi</h4>", unsafe_allow_html=True)
            st.write(f"Koordinat Titik Uji: {lat_eval:.5f}, {lon_eval:.5f} | Ketinggian Tanah: {elevasi_satelit:.1f} mdpl")

            # ─── KONDISI: TITIK DI LUAR JANGKAUAN DATA ACUAN ───────
            if df_terfilter.empty:
                st.markdown(
                    f"<div class='box-notice'>Lokasi ini berada di luar jangkauan data acuan historis "
                    f"&mdash; tidak ada titik referensi dalam radius {radius_km} km.</div>",
                    unsafe_allow_html=True
                )

                st.session_state.elevasi_terklik = elevasi_satelit

                # ─── LANGKAH 1: TANYA APAKAH PUNYA DATA PENGUKURAN ───
                if st.session_state.mode_luar_jangkauan is None:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(
                        "<div class='box-info'>"
                        "<span style='font-size:15px; font-weight:700;'>Apakah Anda memiliki data pengukuran tanah?</span><br>"
                        "Jika Anda memiliki data hasil pengukuran sensor atau uji laboratorium (pH, N, P, K, "
                        "kelembapan, suhu, dll.), sistem dapat menjalankan <strong>model prediksi ANN</strong> "
                        "untuk hasil yang lebih akurat. Jika tidak, sistem akan memberikan "
                        "<strong>estimasi awal</strong> berdasarkan ketinggian dan pH lahan."
                        "</div>",
                        unsafe_allow_html=True
                    )
                    st.markdown("<br>", unsafe_allow_html=True)
                    col_punya, col_tidak = st.columns([1, 1])
                    with col_punya:
                        if st.button("Ya, Saya Punya Data — Lanjutkan Prediksi", use_container_width=True, key="btn_punya_data"):
                            st.session_state.mode_luar_jangkauan = 'prediksi'
                            st.session_state.show_kes_form = True
                            st.rerun()
                    with col_tidak:
                        if st.button("Tidak, Saya Tidak Punya Data", use_container_width=True, key="btn_tidak_data"):
                            st.session_state.mode_luar_jangkauan = 'skrining'
                            st.rerun()

                # ─── LANGKAH 2A: MODE PREDIKSI ANN ───────────────────
                elif st.session_state.mode_luar_jangkauan == 'prediksi':
                    st.markdown("<br>", unsafe_allow_html=True)

                    # Langkah 2A-i: pilih sumber data NPK
                    if st.session_state.sumber_data_npk is None:
                        st.markdown(
                            "<div class='box-info'>"
                            "<span style='font-size:15px; font-weight:700;'>Data N, P, K Anda dari mana?</span><br>"
                            "Nilai unsur hara tanah (Nitrogen, Fosfor, Kalium) bisa diperoleh dari dua sumber. "
                            "Pilih sesuai dengan yang Anda miliki:"
                            "</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown("<br>", unsafe_allow_html=True)
                        col_s, col_l = st.columns(2)
                        with col_s:
                            st.markdown(
                                "<div style='background:rgba(255,255,255,0.05); border-radius:10px; "
                                "padding:14px 16px; margin-bottom:10px; color:rgba(255,255,255,0.8); font-size:0.9em;'>"
                                "<strong>Dari Alat Sensor / Alat Ukur Tanah</strong><br>"
                                "Cocok jika Anda punya alat ukur tanah portabel yang biasa dipakai di ladang. "
                                "Sistem akan mengolah data sensor dulu sebelum menentukan kesesuaian lahan."
                                "</div>",
                                unsafe_allow_html=True
                            )
                            if st.button("Pakai Data Sensor", use_container_width=True, key="btn_npk_sensor"):
                                st.session_state.sumber_data_npk = 'sensor'
                                st.session_state.show_kes_form = True
                                st.rerun()
                        with col_l:
                            st.markdown(
                                "<div style='background:rgba(255,255,255,0.05); border-radius:10px; "
                                "padding:14px 16px; margin-bottom:10px; color:rgba(255,255,255,0.8); font-size:0.9em;'>"
                                "<strong>Dari Hasil Uji Laboratorium</strong><br>"
                                "Cocok jika Anda sudah punya hasil uji tanah dari laboratorium pertanian "
                                "atau instansi terkait. Data lab lebih presisi dan langsung bisa digunakan."
                                "</div>",
                                unsafe_allow_html=True
                            )
                            if st.button("Pakai Data Hasil Lab", use_container_width=True, key="btn_npk_lab"):
                                st.session_state.sumber_data_npk = 'lab'
                                st.session_state.show_kes_form = True
                                st.rerun()
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("← Kembali ke Pilihan Awal", key="btn_kembali_prediksi"):
                            st.session_state.mode_luar_jangkauan = None
                            st.session_state.show_kes_form = False
                            st.rerun()

                # ─── LANGKAH 2B: MODE SKRINING ELEVASI + pH ──────────
                elif st.session_state.mode_luar_jangkauan == 'skrining':
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<h5>Skrining Awal Berdasarkan Ketinggian Lahan</h5>", unsafe_allow_html=True)

                    if elevasi_satelit < 1000:
                        st.markdown(
                            f"<div class='box-error'>"
                            f"<span style='font-size:15px; font-weight:700;'>Ketinggian Terlalu Rendah</span><br>"
                            f"Lokasi ini berada pada ketinggian <strong>{elevasi_satelit:.0f} mdpl</strong> "
                            f"(di bawah 1.000 mdpl). Tanaman kentang umumnya membutuhkan ketinggian "
                            f"minimal 1.000 mdpl agar suhu dan kelembapan udara cukup mendukung. "
                            f"<strong>Lahan ini kemungkinan tidak cocok</strong> untuk budidaya kentang."
                            f"</div>",
                            unsafe_allow_html=True
                        )

                    elif 1000 <= elevasi_satelit <= 1500:
                        st.markdown(
                            f"<div class='box-notice'>"
                            f"<span style='font-size:15px; font-weight:700;'>Ketinggian Potensial — Perlu Cek pH</span><br>"
                            f"Lokasi ini berada pada ketinggian <strong>{elevasi_satelit:.0f} mdpl</strong> "
                            f"(rentang 1.000–1.500 mdpl). Ketinggian ini cukup menjanjikan, namun "
                            f"kesesuaian lahan bergantung pada pH tanah. "
                            f"Masukkan nilai pH tanah Anda untuk mendapatkan estimasi awal."
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        ph_input_rendah = st.number_input(
                            "Nilai pH Tanah (hasil uji lab / alat ukur)",
                            min_value=3.0, max_value=10.0, value=6.5, step=0.1,
                            key="ph_screen_rendah"
                        )
                        if ph_input_rendah > 7.0:
                            st.markdown(
                                f"<div class='box-success'>"
                                f"<span style='font-size:15px; font-weight:700;'>Berpotensi Cocok</span><br>"
                                f"Ketinggian <strong>{elevasi_satelit:.0f} mdpl</strong> dan pH "
                                f"<strong>{ph_input_rendah:.1f}</strong> (di atas 7,0) menunjukkan kondisi "
                                f"yang <strong>berpotensi cocok</strong> untuk budidaya kentang. "
                                f"Disarankan verifikasi lebih lanjut dengan uji parameter tanah lengkap."
                                f"</div>",
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f"<div class='box-warn'>"
                                f"<span style='font-size:15px; font-weight:700;'>Kurang Optimal</span><br>"
                                f"Ketinggian <strong>{elevasi_satelit:.0f} mdpl</strong> sudah memadai, namun "
                                f"pH <strong>{ph_input_rendah:.1f}</strong> (≤ 7,0) masih di bawah nilai ideal. "
                                f"Kentang tumbuh optimal pada pH di atas 7,0 pada rentang ketinggian ini. "
                                f"Pertimbangkan pengapuran untuk menaikkan pH tanah."
                                f"</div>",
                                unsafe_allow_html=True
                            )
                        # Panduan bagi petani yang belum tahu pH
                        st.markdown(
                            f"<div style='margin-top:14px; padding:12px 16px; border-radius:8px; "
                            f"background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); "
                            f"color:rgba(255,255,255,0.65); font-size:0.88em; line-height:1.6;'>"
                            f"<strong style='color:rgba(255,255,255,0.85);'>Belum tahu nilai pH tanah Anda?</strong><br>"
                            f"Lokasi ini berada pada ketinggian <strong>{elevasi_satelit:.0f} mdpl</strong> "
                            f"(rentang 1.000–1.500 mdpl). Pada rentang ini, kentang membutuhkan pH tanah "
                            f"yang sedikit basa agar unsur hara tersedia optimal. Berikut panduan singkatnya:<br><br>"
                            f"&bull;&nbsp; <strong>pH &gt; 7,0</strong> → Lahan <em>berpotensi cocok</em> "
                            f"untuk budidaya kentang.<br>"
                            f"&bull;&nbsp; <strong>pH 6,0–7,0</strong> → Lahan bersifat <em>marginal</em>, "
                            f"perlu tindakan pengapuran untuk menaikkan pH.<br>"
                            f"&bull;&nbsp; <strong>pH &lt; 6,0</strong> → Kondisi tanah <em>kurang mendukung</em>, "
                            f"diperlukan perbaikan intensif sebelum tanam.<br><br>"
                            f"Untuk mengetahui pH tanah, Anda dapat menggunakan <em>soil pH meter</em> "
                            f"yang tersedia di toko pertanian, atau mengirimkan sampel tanah ke laboratorium "
                            f"terdekat."
                            f"</div>",
                            unsafe_allow_html=True
                        )

                    else:  # elevasi > 1500
                        st.markdown(
                            f"<div class='box-notice'>"
                            f"<span style='font-size:15px; font-weight:700;'>Ketinggian Ideal — Perlu Cek pH</span><br>"
                            f"Lokasi ini berada pada ketinggian <strong>{elevasi_satelit:.0f} mdpl</strong> "
                            f"(di atas 1.500 mdpl) — rentang yang paling disukai tanaman kentang. "
                            f"Masukkan nilai pH tanah untuk konfirmasi kesesuaian."
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        ph_input_tinggi = st.number_input(
                            "Nilai pH Tanah (hasil uji lab / alat ukur)",
                            min_value=3.0, max_value=10.0, value=6.5, step=0.1,
                            key="ph_screen_tinggi"
                        )
                        if ph_input_tinggi > 6.5:
                            st.markdown(
                                f"<div class='box-success'>"
                                f"<span style='font-size:15px; font-weight:700;'>Kemungkinan Besar Cocok</span><br>"
                                f"Ketinggian <strong>{elevasi_satelit:.0f} mdpl</strong> dan pH "
                                f"<strong>{ph_input_tinggi:.1f}</strong> (di atas 6,5) menunjukkan bahwa "
                                f"kondisi dasar lahan Anda <strong>kemungkinan besar mendukung</strong> budidaya kentang. "
                                f"Lakukan analisis parameter tanah lengkap untuk hasil yang lebih akurat."
                                f"</div>",
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f"<div class='box-warn'>"
                                f"<span style='font-size:15px; font-weight:700;'>Perlu Perbaikan pH</span><br>"
                                f"Ketinggian <strong>{elevasi_satelit:.0f} mdpl</strong> sangat mendukung, namun "
                                f"pH <strong>{ph_input_tinggi:.1f}</strong> (≤ 6,5) masih di bawah ambang optimal. "
                                f"Lakukan pengapuran atau amandemen tanah untuk menaikkan pH sebelum memulai budidaya."
                                f"</div>",
                                unsafe_allow_html=True
                            )
                        # Panduan bagi petani yang belum tahu pH
                        st.markdown(
                            f"<div style='margin-top:14px; padding:12px 16px; border-radius:8px; "
                            f"background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); "
                            f"color:rgba(255,255,255,0.65); font-size:0.88em; line-height:1.6;'>"
                            f"<strong style='color:rgba(255,255,255,0.85);'>Belum tahu nilai pH tanah Anda?</strong><br>"
                            f"Lokasi ini berada pada ketinggian <strong>{elevasi_satelit:.0f} mdpl</strong> "
                            f"(di atas 1.500 mdpl) — rentang yang paling disukai tanaman kentang. "
                            f"Pada ketinggian ini, syarat pH tanah relatif lebih longgar. "
                            f"Berikut panduan singkatnya:<br><br>"
                            f"&bull;&nbsp; <strong>pH &gt; 6,5</strong> → Lahan <em>kemungkinan besar cocok</em> "
                            f"untuk budidaya kentang.<br>"
                            f"&bull;&nbsp; <strong>pH 5,5–6,5</strong> → Lahan bersifat <em>marginal</em>, "
                            f"masih dapat dioptimalkan dengan pengapuran ringan.<br>"
                            f"&bull;&nbsp; <strong>pH &lt; 5,5</strong> → Kondisi tanah <em>kurang mendukung</em>, "
                            f"diperlukan amandemen tanah sebelum mulai budidaya.<br><br>"
                            f"Untuk mengetahui pH tanah, gunakan <em>soil pH meter</em> dari toko pertanian "
                            f"atau kirimkan sampel tanah ke laboratorium analisis tanah terdekat."
                            f"</div>",
                            unsafe_allow_html=True
                        )

                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("← Kembali ke Pilihan Awal", key="btn_kembali_skrining"):
                        st.session_state.mode_luar_jangkauan = None
                        st.rerun()


                # ─── FORM INPUT: SENSOR ATAU LAB ────────────────
                if st.session_state.show_kes_form and st.session_state.sumber_data_npk is not None:
                    model_kes, scaler_kes = load_kesesuaian_model()

                    if model_kes is None:
                        st.markdown(
                            "<div class='box-error'>File model belum ditemukan di folder proyek. "
                            "Pastikan file <strong>model_kesesuaian.keras</strong> dan "
                            "<strong>scaler_kesesuaian.save</strong> sudah ada.</div>",
                            unsafe_allow_html=True
                        )

                    # ─── ALUR SENSOR ───────────────────────────────────
                    elif st.session_state.sumber_data_npk == 'sensor':
                        if not st.session_state.kalibrasi_selesai:
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown(
                                "<div class='box-info'>"
                                "<span style='font-size:15px; font-weight:700;'>Masukkan Hasil Bacaan Alat Ukur Tanah</span><br>"
                                "Isi angka yang muncul di layar alat ukur untuk masing-masing parameter. "
                                "Sistem akan mengolahnya terlebih dahulu sebelum menentukan kesesuaian lahan."
                                "</div>",
                                unsafe_allow_html=True
                            )
                            with st.form("form_kalibrasi_sensor"):
                                c1, c2, c3 = st.columns(3)
                                ec_s    = c1.number_input("Kelistrikan Tanah (EC)",       value=0.0,  step=0.1, format="%.2f")
                                n_s     = c2.number_input("Nitrogen – N (bacaan sensor)",  value=0.0,  step=0.1, format="%.2f")
                                p_s     = c3.number_input("Fosfor – P (bacaan sensor)",    value=0.0,  step=0.1, format="%.2f")
                                k_s     = c1.number_input("Kalium – K (bacaan sensor)",    value=0.0,  step=0.1, format="%.2f")
                                ph_s    = c2.number_input("Keasaman Tanah (pH)",           value=7.0,  step=0.1, format="%.2f")
                                moist_s = c3.number_input("Kelembaban Tanah (%)",          value=0.0,  step=0.1, format="%.2f")
                                suhu_s  = c1.number_input("Suhu Tanah (°C)",                value=20.0, step=0.1, format="%.2f")
                                submit_kal = st.form_submit_button("Proses Data Sensor")
                            if submit_kal:
                                model_kal, scaler_X, scaler_y = load_ann_model()
                                if model_kal is None:
                                    st.markdown(
                                        "<div class='box-error'>File model kalibrasi belum ditemukan. "
                                        "Pastikan <strong>model_ann.keras</strong>, <strong>scaler_X.pkl</strong>, "
                                        "dan <strong>scaler_y.pkl</strong> sudah ada di folder proyek.</div>",
                                        unsafe_allow_html=True
                                    )
                                else:
                                    with st.spinner("Sedang mengolah data sensor..."):
                                        input_df = pd.DataFrame(
                                            [[ec_s, n_s, p_s, k_s, ph_s, moist_s, suhu_s]],
                                            columns=["EC_S","N_S","P_S","K_S","PH_S","Moist_S","Temp_D_S"]
                                        ).astype('float32')
                                        X_log  = np.log1p(input_df)
                                        X_sc   = scaler_X.transform(X_log)
                                        y_pred = np.expm1(scaler_y.inverse_transform(model_kal.predict(X_sc)))[0]
                                    st.session_state.kalibrasi_n     = float(y_pred[0])
                                    st.session_state.kalibrasi_p     = float(y_pred[1])
                                    st.session_state.kalibrasi_k     = float(y_pred[2])
                                    st.session_state.kalibrasi_ec    = ec_s
                                    st.session_state.kalibrasi_ph    = ph_s
                                    st.session_state.kalibrasi_moist = moist_s
                                    st.session_state.kalibrasi_suhu  = suhu_s
                                    st.session_state.kalibrasi_selesai = True
                                    st.rerun()
                            if st.button("← Kembali ke Pilihan Sumber Data", key="btn_kembali_sumber"):
                                st.session_state.sumber_data_npk = None
                                st.session_state.show_kes_form   = False
                                st.rerun()
                        else:
                            raw_n = st.session_state.kalibrasi_n
                            raw_p = st.session_state.kalibrasi_p
                            raw_k = st.session_state.kalibrasi_k
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown(
                                "<div class='box-success'>"
                                "<span style='font-size:15px; font-weight:700;'>Hasil Pengolahan Data Sensor</span><br>"
                                f"Nitrogen (N): <strong>{raw_n:.1f} mg/100g</strong>&nbsp;|&nbsp;"
                                f"Fosfor (P): <strong>{raw_p:.1f} mg/100g</strong>&nbsp;|&nbsp;"
                                f"Kalium (K): <strong>{raw_k:.1f} mg/100g</strong><br>"
                                "Nilai-nilai ini sudah diolah dari bacaan sensor dan siap digunakan."
                                "</div>",
                                unsafe_allow_html=True
                            )
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown(
                                "<div class='box-info'>"
                                "<span style='font-size:15px; font-weight:700;'>Periksa dan Lengkapi Data</span><br>"
                                "Nilai N, P, K sudah terisi otomatis. Periksa nilai lainnya, "
                                "lalu klik 'Cek Kesesuaian Lahan'."
                                "</div>",
                                unsafe_allow_html=True
                            )
                            with st.form("form_kesesuaian_sensor"):
                                r1c1, r1c2, r1c3, r1c4 = st.columns(4)
                                ec_in    = r1c1.number_input("Kelistrikan Tanah (EC)", value=float(st.session_state.kalibrasi_ec),   step=0.1, format="%.2f")
                                n_in     = r1c2.number_input("Nitrogen – N (mg/100g)", value=float(st.session_state.kalibrasi_n),    step=0.1, format="%.2f")
                                p_in     = r1c3.number_input("Fosfor – P (mg/100g)",   value=float(st.session_state.kalibrasi_p),    step=0.1, format="%.2f")
                                k_in     = r1c4.number_input("Kalium – K (mg/100g)",   value=float(st.session_state.kalibrasi_k),    step=0.1, format="%.2f")
                                r2c1, r2c2, r2c3, r2c4 = st.columns(4)
                                ph_in    = r2c1.number_input("Keasaman Tanah (pH)",     value=float(st.session_state.kalibrasi_ph),   step=0.1, format="%.2f")
                                moist_in = r2c2.number_input("Kelembaban Tanah (%)",    value=float(st.session_state.kalibrasi_moist),step=0.1, format="%.2f")
                                td_in    = r2c3.number_input("Suhu Tanah (°C)",         value=float(st.session_state.kalibrasi_suhu), step=0.1, format="%.2f")
                                elev_in  = r2c4.number_input("Ketinggian Lahan (mdpl)", value=float(st.session_state.elevasi_terklik),step=1.0, format="%.1f")
                                submitted_kes = st.form_submit_button("Cek Kesesuaian Lahan")
                            if st.button("← Ulangi Pengisian Sensor (Reset ke Awal)", key="btn_ulang_sensor"):
                                st.session_state.kalibrasi_selesai = False
                                st.session_state.kalibrasi_n     = 0.0
                                st.session_state.kalibrasi_p     = 0.0
                                st.session_state.kalibrasi_k     = 0.0
                                st.session_state.kalibrasi_ec    = 0.0
                                st.session_state.kalibrasi_ph    = 7.0
                                st.session_state.kalibrasi_moist = 0.0
                                st.session_state.kalibrasi_suhu  = 20.0
                                st.rerun()

                        if submitted_kes:
                            with st.spinner("Sedang memeriksa kesesuaian lahan..."):
                                label, conf, probs_arr, warna_hasil = prediksi_kesesuaian(
                                    ec_in, n_in, p_in, k_in,
                                    ph_in, moist_in, td_in, elev_in,
                                    model_kes, scaler_kes
                                )
                            st.markdown("<hr style='border-color: rgba(255,255,255,0.15); margin: 20px 0;'>", unsafe_allow_html=True)
                            st.markdown("<h4>Hasil Pemeriksaan Kesesuaian Lahan</h4>", unsafe_allow_html=True)
                            if label == 'Cocok':
                                st.markdown(
                                    f"<div class='box-cocok'><strong>COCOK</strong><br>"
                                    f"Berdasarkan data yang dimasukkan, lahan ini kemungkinan cocok untuk budidaya kentang.</div>",
                                    unsafe_allow_html=True
                                )
                            elif label == 'Netral':
                                st.markdown(
                                    f"<div class='box-netral'><strong>PERLU PERBAIKAN</strong><br>"
                                    f"Lahan masih bisa digunakan, tapi butuh perbaikan kondisi tanah terlebih dahulu.</div>",
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown(
                                    f"<div class='box-tidak'><strong>KURANG COCOK</strong><br>"
                                    f"Kondisi lahan saat ini kurang mendukung untuk budidaya kentang.</div>",
                                    unsafe_allow_html=True
                                )
                            st.markdown("<br>", unsafe_allow_html=True)
                            col_conf1, col_conf2, col_conf3 = st.columns(3)
                            col_conf1.metric("Kemungkinan Tidak Cocok", f"{probs_arr[0]*100:.1f}%")
                            col_conf2.metric("Perlu Perbaikan",         f"{probs_arr[1]*100:.1f}%")
                            col_conf3.metric("Kemungkinan Cocok",       f"{probs_arr[2]*100:.1f}%")
                            st.caption(
                                f"Keyakinan model: **{conf*100:.1f}%** · "
                                f"Ketinggian: {elev_in:.1f} mdpl · "
                                f"Koordinat: {lat_eval:.5f}, {lon_eval:.5f}"
                            )
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("← Isi Ulang Data", key="btn_isi_ulang_hasil"):
                                st.session_state.kalibrasi_selesai = False
                                st.session_state.kalibrasi_n = 0.0; st.session_state.kalibrasi_p = 0.0
                                st.session_state.kalibrasi_k = 0.0; st.session_state.kalibrasi_ec = 0.0
                                st.session_state.kalibrasi_ph = 7.0; st.session_state.kalibrasi_moist = 0.0
                                st.session_state.kalibrasi_suhu = 20.0
                                st.session_state.sumber_data_npk = None
                                st.session_state.show_kes_form = False
                                st.rerun()

                    # ─── ALUR LAB ──────────────────────────────────────
                    elif st.session_state.sumber_data_npk == 'lab':
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(
                            "<div class='box-info'>"
                            "<span style='font-size:15px; font-weight:700;'>Masukkan Data Hasil Uji Laboratorium</span><br>"
                            "Isi angka-angka yang tertera pada lembar hasil uji tanah dari laboratorium. "
                            "Ketinggian lahan sudah terisi otomatis dari titik yang Anda pilih di peta."
                            "</div>",
                            unsafe_allow_html=True
                        )
                        with st.form("form_kesesuaian_lab"):
                            r1c1, r1c2, r1c3, r1c4 = st.columns(4)
                            ec_in    = r1c1.number_input("Kelistrikan Tanah (EC)", value=0.0,  step=0.1, format="%.2f")
                            n_in     = r1c2.number_input("Nitrogen – N (mg/100g)", value=0.0,  step=0.1, format="%.2f")
                            p_in     = r1c3.number_input("Fosfor – P (mg/100g)",   value=0.0,  step=0.1, format="%.2f")
                            k_in     = r1c4.number_input("Kalium – K (mg/100g)",   value=0.0,  step=0.1, format="%.2f")
                            r2c1, r2c2, r2c3, r2c4 = st.columns(4)
                            ph_in    = r2c1.number_input("Keasaman Tanah (pH)",     value=7.0,  step=0.1, format="%.2f")
                            moist_in = r2c2.number_input("Kelembaban Tanah (%)",    value=0.0,  step=0.1, format="%.2f")
                            td_in    = r2c3.number_input("Suhu Tanah (°C)",         value=20.0, step=0.1, format="%.2f")
                            elev_in  = r2c4.number_input("Ketinggian Lahan (mdpl)", value=float(st.session_state.elevasi_terklik) if st.session_state.elevasi_terklik else 0.0, step=1.0, format="%.1f")
                            submitted_kes = st.form_submit_button("Cek Kesesuaian Lahan")
                        if st.button("← Kembali ke Pilihan Sumber Data", key="btn_kembali_lab"):
                            st.session_state.sumber_data_npk = None
                            st.session_state.show_kes_form   = False
                            st.rerun()

                        if submitted_kes:
                            with st.spinner("Sedang memeriksa kesesuaian lahan..."):
                                label, conf, probs_arr, warna_hasil = prediksi_kesesuaian(
                                    ec_in, n_in, p_in, k_in,
                                    ph_in, moist_in, td_in, elev_in,
                                    model_kes, scaler_kes
                                )
                            st.markdown("<hr style='border-color: rgba(255,255,255,0.15); margin: 20px 0;'>", unsafe_allow_html=True)
                            st.markdown("<h4>Hasil Pemeriksaan Kesesuaian Lahan</h4>", unsafe_allow_html=True)
                            if label == 'Cocok':
                                st.markdown(
                                    f"<div class='box-cocok'><strong>COCOK</strong><br>"
                                    f"Berdasarkan data yang dimasukkan, lahan ini kemungkinan cocok untuk budidaya kentang.</div>",
                                    unsafe_allow_html=True
                                )
                            elif label == 'Netral':
                                st.markdown(
                                    f"<div class='box-netral'><strong>PERLU PERBAIKAN</strong><br>"
                                    f"Lahan masih bisa digunakan, tapi butuh perbaikan kondisi tanah terlebih dahulu.</div>",
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown(
                                    f"<div class='box-tidak'><strong>KURANG COCOK</strong><br>"
                                    f"Kondisi lahan saat ini kurang mendukung untuk budidaya kentang.</div>",
                                    unsafe_allow_html=True
                                )
                            st.markdown("<br>", unsafe_allow_html=True)
                            col_conf1, col_conf2, col_conf3 = st.columns(3)
                            col_conf1.metric("Kemungkinan Tidak Cocok", f"{probs_arr[0]*100:.1f}%")
                            col_conf2.metric("Perlu Perbaikan",         f"{probs_arr[1]*100:.1f}%")
                            col_conf3.metric("Kemungkinan Cocok",       f"{probs_arr[2]*100:.1f}%")
                            st.caption(
                                f"Keyakinan model: **{conf*100:.1f}%** · "
                                f"Ketinggian: {elev_in:.1f} mdpl · "
                                f"Koordinat: {lat_eval:.5f}, {lon_eval:.5f}"
                            )
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("← Isi Ulang Data", key="btn_isi_ulang_hasil"):
                                st.session_state.kalibrasi_selesai = False
                                st.session_state.kalibrasi_n = 0.0; st.session_state.kalibrasi_p = 0.0
                                st.session_state.kalibrasi_k = 0.0; st.session_state.kalibrasi_ec = 0.0
                                st.session_state.kalibrasi_ph = 7.0; st.session_state.kalibrasi_moist = 0.0
                                st.session_state.kalibrasi_suhu = 20.0
                                st.session_state.sumber_data_npk = None
                                st.session_state.show_kes_form = False
                                st.rerun()
            # ─── KONDISI: TITIK DALAM JANGKAUAN ────────────────────
            else:
                elev_min, elev_max = df_terfilter['Elevasi'].min(), df_terfilter['Elevasi'].max()

                if elevasi_satelit < (elev_min - 50.0) or elevasi_satelit > (elev_max + 50.0):
                    st.markdown(
                        f"<div class='box-tidak'><strong>TIDAK COCOK</strong><br>"
                        f"Ketinggian lokasi berada di luar batas toleransi wilayah terdekat "
                        f"(Rentang Acuan: {elev_min:.0f} &ndash; {elev_max:.0f} mdpl).</div>",
                        unsafe_allow_html=True
                    )
                else:
                    hitung_suara = df_terfilter['Status'].str.lower().value_counts()

                    if len(hitung_suara) > 1 and hitung_suara.iloc[0] == hitung_suara.iloc[1]:
                        st.markdown(
                            "<div class='box-netral'><strong>NETRAL</strong><br>"
                            "Karakteristik data referensi di sekitar titik uji memiliki rasio yang seimbang (50:50).</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        suara_dominan = hitung_suara.idxmax()
                        if suara_dominan == 'cocok':
                            st.markdown(
                                "<div class='box-cocok'><strong>COCOK</strong><br>"
                                "Mayoritas data observasi di sekitar lokasi ini menunjukkan kondisi lahan yang ideal.</div>",
                                unsafe_allow_html=True
                            )
                        elif suara_dominan == 'netral':
                            st.markdown(
                                "<div class='box-netral'><strong>NETRAL</strong><br>"
                                "Zonasi di sekitar lokasi didominasi oleh karakteristik lahan marginal.</div>",
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                "<div class='box-tidak'><strong>TIDAK COCOK</strong><br>"
                                "Mayoritas data observasi historis tidak merekomendasikan komoditas ini.</div>",
                                unsafe_allow_html=True
                            )

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"<h5>Data Ketinggian & pH dari Objek Acuan Terdekat (Radius {radius_km} Km)</h5>", unsafe_allow_html=True)

                df_tabel = df_terfilter[['Kabupaten', 'Desa', 'Elevasi', 'PH_S1', 'Status', 'Jarak_Km']].copy()
                df_tabel['Jarak_Km'] = df_tabel['Jarak_Km'].round(2)
                df_tabel.rename(columns={
                    'Elevasi': 'Ketinggian (mdpl)', 'PH_S1': 'pH Tanah',
                    'Status': 'Kategori Lahan', 'Jarak_Km': 'Jarak ke Lokasi Uji (Km)'
                }, inplace=True)
                st.dataframe(df_tabel, use_container_width=True, hide_index=True)

        else:
            st.markdown(
                "<div class='box-error'>Gagal terhubung dengan server koordinat satelit untuk menarik data elevasi.</div>",
                unsafe_allow_html=True
            )

# ==========================================
# HALAMAN 2: REKOMENDASI PEMUPUKAN (FITUR 2)
# ==========================================
elif st.session_state.page == 'fitur_pupuk':

    col_judul, col_kembali = st.columns([4, 1])
    with col_judul:
        st.markdown("<h2 style='margin:0; font-weight: 700;'>Dasbor Rekomendasi Pemupukan</h2>", unsafe_allow_html=True)
    with col_kembali:
        if st.button("Kembali ke Beranda"):
            st.session_state.page = 'beranda'
            st.rerun()

    st.markdown("<hr style='border-color: rgba(255,255,255,0.15); margin: 15px 0 25px 0;'>", unsafe_allow_html=True)

    model, scaler_X, scaler_y = load_ann_model()

    if model is None:
        st.warning("File model belum terbaca dengan sempurna. Pastikan model_ann.keras, scaler_X.pkl, dan scaler_y.pkl sudah berada di folder proyek VS Code Anda.")
    else:
        st.markdown("<h4>Input Parameter Sensor Lapangan</h4>", unsafe_allow_html=True)
        st.write("Silakan masukkan hasil pengukuran dari 7 parameter sensor tanah di bawah ini:")

        with st.form("form_prediksi_manual"):
            c1, c2, c3 = st.columns(3)
            ec    = c1.number_input("EC (Kelistrikan Tanah)",   value=0.0, step=0.1)
            n_s   = c2.number_input("N (Nilai Sensor)",          value=0.0, step=0.1)
            p_s   = c3.number_input("P (Nilai Sensor)",          value=0.0, step=0.1)

            k_s   = c1.number_input("K (Nilai Sensor)",          value=0.0, step=0.1)
            ph    = c2.number_input("pH Tanah Aktual",           value=7.0, step=0.1)
            moist = c3.number_input("Kelembaban (Moisture %)",   value=0.0, step=0.1)

            temp  = c1.number_input("Suhu Dalam Tanah (°C)",     value=20.0, step=0.1)

            submit_button = st.form_submit_button("Lakukan Model Kalibrasi")

        if submit_button:
            with st.spinner("Memproses Model Kalibrasi..."):
                input_df = pd.DataFrame(
                    [[ec, n_s, p_s, k_s, ph, moist, temp]],
                    columns=["EC_S", "N_S", "P_S", "K_S", "PH_S", "Moist_S", "Temp_D_S"]
                ).astype('float32')

                X_log    = np.log1p(input_df)
                X_scaled = scaler_X.transform(X_log)

                y_pred_scaled = model.predict(X_scaled)
                y_pred_log    = scaler_y.inverse_transform(y_pred_scaled)
                y_pred        = np.expm1(y_pred_log)[0]

                raw_n, raw_p, raw_k = y_pred[0], y_pred[1], y_pred[2]

            st.markdown("<hr style='border-color: rgba(255,255,255,0.15); margin: 25px 0;'>", unsafe_allow_html=True)
            st.markdown("<h4>Hasil Estimasi Kandungan Hara Laboratorium Kontinu</h4>", unsafe_allow_html=True)

            col_n, col_p, col_k = st.columns(3)
            col_n.metric("Estimasi N (Nitrogen)", f"{raw_n:.2f} mg/100g")
            col_p.metric("Estimasi P (Fosfor)",   f"{raw_p:.2f} mg/100g")
            col_k.metric("Estimasi K (Kalium)",   f"{raw_k:.2f} mg/100g")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h4>Analisis & Rekomendasi Pemupukan Kentang</h4>", unsafe_allow_html=True)

            kat_n = klasifikasi_n(raw_n)
            st.markdown(
                f"<div class='box-info'><strong>Nitrogen (N) &mdash; {kat_n.upper()}</strong><br>"
                f"{saran_n(kat_n)}<br><em>Tindakan:</em> {langkah_n(kat_n)}</div>",
                unsafe_allow_html=True
            )
            st.markdown("<br>", unsafe_allow_html=True)

            kat_p = klasifikasi_p(raw_p)
            st.markdown(
                f"<div class='box-info'><strong>Fosfor (P) &mdash; {kat_p.upper()}</strong><br>"
                f"{saran_p(kat_p)}<br><em>Tindakan:</em> {langkah_p(kat_p)}</div>",
                unsafe_allow_html=True
            )
            st.markdown("<br>", unsafe_allow_html=True)

            kat_k = klasifikasi_k(raw_k)
            st.markdown(
                f"<div class='box-info'><strong>Kalium (K) &mdash; {kat_k.upper()}</strong><br>"
                f"{saran_k(kat_k)}<br><em>Tindakan:</em> {langkah_k(kat_k)}</div>",
                unsafe_allow_html=True
            )
            st.markdown("<br>", unsafe_allow_html=True)

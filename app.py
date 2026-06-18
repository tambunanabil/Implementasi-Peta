import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import numpy as np

# --- 1. KONFIGURASI DAN NAVIGASI TOMBOL (TANPA TAB / SIDEBAR RAMAI) ---
st.set_page_config(page_title="Sistem Informasi Geografis Lahan Kentang", layout="wide", initial_sidebar_state="collapsed")

# Manajemen Sesi untuk Berpindah Halaman menggunakan Tombol Utama
if 'page' not in st.session_state:
    st.session_state.page = 'beranda'
if 'clicked_lat' not in st.session_state:
    st.session_state.clicked_lat = None
    st.session_state.clicked_lon = None

# --- 2. CUSTOM CSS: ANTARMUKA WEB SOLID & LATAR BELAKANG PERTANIAN REALISTIS ---
st.markdown("""
    <style>
    /* Hilangkan Komponen AI dan Sidebar */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header { visibility: hidden !important; }
    
    /* Latar Belakang Gambar Pertanian Realistis Skala Penuh */
    .stApp {
        background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.5)), url("https://images.unsplash.com/photo-1516253593875-bd7ba052fbc5?q=80&w=1600&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }

    /* Wadah Konten Utama Bersih dan Transparan Elegan */
    .block-container {
        max-width: 1100px;
        margin: auto;
        padding-top: 3rem !important;
    }

    /* Gaya Card / Panel Putih untuk Konten Menjadi Sangat Compact */
    .main-panel {
        background-color: rgba(255, 255, 255, 0.96);
        padding: 40px;
        border-radius: 8px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }

    /* Custom Tombol Menu Utama di Beranda */
    .stButton>button {
        background-color: #1e4620;
        color: white;
        border-radius: 4px;
        padding: 15px 20px;
        font-size: 16px;
        font-weight: bold;
        width: 100%;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #2d6a4f;
        color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Tombol Kembali yang Minimalis */
    .btn-back>div>button {
        background-color: #6c757d !important;
        padding: 8px 15px !important;
        font-size: 14px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE LOGIC SISTEM ---
@st.cache_data(ttl=600)
def query_database():
    try:
        conn = sqlite3.connect('database_lahan.db')
        df = pd.read_sql_query("SELECT * FROM titik_acuan", conn)
        conn.close()
        df = df.dropna(subset=['Lat', 'Lon']) # Sesuai dengan header file koordinat Anda (Lat, Lon)
        return df
    except Exception:
        return pd.DataFrame()

def get_elevation(lat, lon):
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
    try:
        res = requests.get(url).json()
        return res["elevation"][0] if "elevation" in res else None
    except: 
        return None

def hitung_jarak_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

df_data = query_database()

# ==========================================
# HALAMAN 1: BERANDA UTAMA (SIMPLE & COMPACT)
# ==========================================
if st.session_state.page == 'beranda':
    st.markdown('<div class="main-panel">', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #1e4620; font-family: sans-serif;'>Sistem Informasi Spasial Lahan Kentang</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555; font-size: 16px;'>Silakan pilih modul analitik di bawah ini untuk memulai pemetaan wilayah produksi Pulau Jawa.</p>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Grid 2 Kolom Tombol Fitur Utama
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Masuk ke Peta Kesesuaian Lahan"):
            st.session_state.page = 'fitur_peta'
            st.rerun()
    with col_btn2:
        if st.button("Masuk ke Rekomendasi Pemupukan"):
            st.session_state.page = 'fitur_pupuk'
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# HALAMAN 2: FITUR PETA KESESUAIAN LAHAN
# ==========================================
elif st.session_state.page == 'fitur_peta':
    st.markdown('<div class="main-panel">', unsafe_allow_html=True)
    
    # Header Navigasi Atas dan Tombol Kembali
    col_h, col_b = st.columns([4, 1])
    with col_h:
        st.markdown("<h2 style='color: #1e4620; margin:0;'>Model Prediksi Kesesuaian Lahan</h2>", unsafe_allow_html=True)
    with col_b:
        st.markdown('<div class="btn-back">', unsafe_allow_html=True)
        if st.button("Kembali ke Beranda"):
            st.session_state.page = 'beranda'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Pembagian Kerja Layout Fitur
    col_inputs, col_map_display = st.columns([1, 2.5])
    
    with col_inputs:
        st.markdown("#### Parameter")
        radius_km = st.slider("Radius Batas Analisis (Km)", 1.0, 15.0, 3.0, 0.5)
        ph_manual = st.number_input("Input pH Lokal (Opsional)", 0.0, 14.0, 0.0, 0.1)
        st.markdown("<br>", unsafe_allow_html=True)
        if not df_data.empty:
            st.caption(f"Sistem Terhubung: {len(df_data)} objek observasi.")
        else:
            st.caption("Koneksi basis data terputus.")

    with col_map_display:
        # PENGGUNAAN CITRA SATELIT GOOGLE MAPS SUNGGUHAN (Google Satellite Tiles)
        m = folium.Map(
            location=[-7.2106, 109.8941], 
            zoom_start=8, 
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
            attr='Google Maps Satellite'
        )
        
        # Plot Sebaran Titik Aktual dari Excel Berdasarkan Kolom 'Kecocokan'
        if not df_data.empty:
            for _, row in df_data.iterrows():
                # Membaca kolom 'Kecocokan' sesuai data Anda
                kategori_excel = str(row.get('Kecocokan', '')).strip().lower()
                
                if kategori_excel == 'cocok': 
                    warna_marker = '#00ff00' # Hijau Terang Kontras Tinggi untuk Citra Satelit
                elif kategori_excel == 'netral': 
                    warna_marker = '#ffff00' # Kuning Kontras
                else: 
                    warna_marker = '#ff0000' # Merah Kontras

                # Mengambil nilai PH_S1 asli Anda
                ph_tanah = row.get('PH_S1', 'N/A')
                
                popup_text = f"""
                <div style='font-family: sans-serif; font-size: 11px;'>
                    <b>Status Lahan:</b> {kategori_excel.upper()}<br>
                    <b>Elevasi Lahan:</b> {row.get('Elevasi', 'N/A')} mdpl<br>
                    <b>Nilai pH (S1):</b> {ph_tanah}
                </div>
                """
                
                folium.CircleMarker(
                    location=[row['Lat'], row['Lon']],
                    radius=6, color=warna_marker, fill=True, fill_color=warna_marker, fill_opacity=0.9,
                    popup=folium.Popup(popup_text, max_width=180)
                ).add_to(m)

        # Plot Pin Penanda Lokasi Klik Pengguna (Seketika Muncul Berwarna Biru)
        if st.session_state.clicked_lat is not None:
            folium.Marker(
                location=[st.session_state.clicked_lat, st.session_state.clicked_lon],
                icon=folium.Icon(color='blue', icon='cloud')
            ).add_to(m)
            
        # Tampilkan Peta Ke Layar Web
        map_interaction = st_folium(m, width=750, height=440, returned_objects=["last_clicked"])

    # Logika Interaktif Menangkap Titik Koordinat Klik dan Menempelkan Pin
    if map_interaction and map_interaction.get("last_clicked"):
        lat_klik = map_interaction["last_clicked"]["lat"]
        lon_klik = map_interaction["last_clicked"]["lng"]
        
        if st.session_state.clicked_lat != lat_klik or st.session_state.clicked_lon != lon_klik:
            st.session_state.clicked_lat = lat_klik
            st.session_state.clicked_lon = lon_klik
            st.rerun()

    # --- PANEL EVALUASI SPASIAL COMPACT (DI BAWAH MAP) ---
    if st.session_state.clicked_lat is not None:
        st.markdown("---")
        st.markdown("#### Hasil Analisis Titik Koordinat Pilihan")
        
        lat_eval = st.session_state.clicked_lat
        lon_eval = st.session_state.clicked_lon
        
        elevasi_satelit = get_elevation(lat_eval, lon_eval)
        
        if not df_data.empty and elevasi_satelit is not None:
            df_working = df_data.copy()
            df_working['Jarak_Km'] = df_working.apply(lambda r: hitung_jarak_haversine(lat_eval, lon_eval, r['Lat'], r['Lon']), axis=1)
            df_terfilter = df_working[df_working['Jarak_Km'] <= radius_km]
            
            if df_terfilter.empty:
                st.error(f"Hasil Evaluasi: Area di luar jangkauan pengamatan data (Tidak ada titik acuan dalam radius {radius_km} km).")
            else:
                elev_min, elev_max = df_terfilter['Elevasi'].min(), df_terfilter['Elevasi'].max()
                
                # Cek Rentang Batas Atas & Batas Bawah Elevasi
                if elevasi_satelit < (elev_min - 50.0) or elevasi_satelit > (elev_max + 50.0):
                    st.error(f"Hasil Evaluasi: TIDAK COCOK. Ketinggian lokasi ({elevasi_satelit:.1f} mdpl) di luar batas toleransi wilayah terdekat ({elev_min:.0f} - {elev_max:.0f} mdpl).")
                else:
                    # Penghitungan Suara Terbanyak (Majority Voting) Berdasarkan Kolom Kecocokan
                    hitung_suara = df_terfilter['Kecocokan'].str.lower().value_counts()
                    
                    if len(hitung_suara) > 1 and hitung_suara.iloc[0] == hitung_suara.iloc[1]:
                        st.warning(f"Hasil Evaluasi: NETRAL. Parameter data di sekitar titik uji memiliki kekuatan seimbang (50:50) dalam batas radius {radius_km} km.")
                    else:
                        suara_dominan = hitung_suara.idxmax()
                        if suara_dominan == 'cocok':
                            st.success(f"Hasil Evaluasi: COCOK. Lokasi ({lat_eval:.4f}, {lon_eval:.4f}) dengan ketinggian {elevasi_satelit:.1f} mdpl berada dalam rentang ideal budidaya.")
                        elif suara_dominan == 'netral':
                            st.warning(f"Hasil Evaluasi: NETRAL. Zonasi di sekitar lokasi didominasi karakteristik lahan marginal.")
                        else:
                            st.error(f"Hasil Evaluasi: TIDAK COCOK. Mayoritas observasi historis terdekat tidak merekomendasikan komoditas ini.")
        else:
            st.info("Sistem sedang menunggu respons server koordinat satelit...")

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# HALAMAN 3: FITUR REKOMENDASI PEMUPUKAN
# ==========================================
elif st.session_state.page == 'fitur_pupuk':
    st.markdown('<div class="main-panel">', unsafe_allow_html=True)
    
    col_h2, col_b2 = st.columns([4, 1])
    with col_h2:
        st.markdown("<h2 style='color: #1e4620; margin:0;'>Dasbor Optimasi Rekomendasi Pemupukan</h2>", unsafe_allow_html=True)
    with col_b2:
        if st.button("Kembali ke Beranda"):
            st.session_state.page = 'beranda'
            st.rerun()
            
    st.markdown("---")
    st.info("Modul kalkulasi nutrisi tanah berbasis algoritma matematika sedang dipersiapkan untuk diintegrasikan.")
    st.markdown('</div>', unsafe_allow_html=True)
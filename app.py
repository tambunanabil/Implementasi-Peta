import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import numpy as np
import sqlite3

# --- 1. PENGATURAN HALAMAN DASAR ---
st.set_page_config(page_title="AgriGIS | Lahan Kentang", layout="wide", initial_sidebar_state="collapsed")

if 'page' not in st.session_state:
    st.session_state.page = 'beranda'
if 'clicked_lat' not in st.session_state:
    st.session_state.clicked_lat = None
    st.session_state.clicked_lon = None

# --- 2. CSS: GLASSMORPHISM TOTAL SIMETRIS & SEIMBANG DI TENGAH ---
st.markdown("""
    <style>
    /* Sembunyikan elemen bawaan Streamlit */
    [data-testid="stSidebar"], [data-testid="collapsedControl"], header { display: none !important; }

    /* Latar Belakang Pertanian Realistis */
    .stApp {
        background-image: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.6)), url("https://images.unsplash.com/photo-1516253593875-bd7ba052fbc5?q=80&w=1600&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }

    /* WADAH UTAMA: Posisi panel kaca buram benar-benar berada di tengah (Center-Aligned) */
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
        /* PERBAIKAN: Mendorong panel lebih ke bawah agar persis di tengah layar */
        margin-top: 15vh !important; 
        margin-bottom: 10vh !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.4);
    }

    /* Memastikan semua komponen teks bawaan menjadi putih cerah */
    .stMarkdown, .stText, label, .stMarkdown p, h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }

    /* Menghapus warna teks hitam pada metric bawaan Streamlit */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }
    [data-testid="stMetricLabel"] {
        color: #cccccc !important;
    }

    /* Mempercantik Tombol Sesuai Karakter Web */
    .stButton>button {
        background-color: rgba(45, 106, 79, 0.95);
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 600;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: rgba(27, 67, 50, 1);
        border-color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI DATA ANTI-ERROR SPASIAL ---
@st.cache_data(ttl=600)
def load_data():
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
        # Normalisasi penamaan kolom agar fleksibel terhadap perubahan file
        df.columns = df.columns.str.strip()
        
        if 'Latitude' in df.columns: df.rename(columns={'Latitude': 'Lat'}, inplace=True)
        elif 'lat' in df.columns: df.rename(columns={'lat': 'Lat'}, inplace=True)
        
        if 'Longitude' in df.columns: df.rename(columns={'Longitude': 'Lon'}, inplace=True)
        elif 'lon' in df.columns: df.rename(columns={'lon': 'Lon'}, inplace=True)
        
        if 'Kecocokan' in df.columns: df.rename(columns={'Kecocokan': 'Status'}, inplace=True)

        if 'Lat' in df.columns and 'Lon' in df.columns:
            df['Lat'] = df['Lat'].ffill()
            df['Lon'] = df['Lon'].ffill()
            df = df.dropna(subset=['Lat', 'Lon'])
            
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

df_data = load_data()

# ==========================================
# HALAMAN 1: BERANDA UTAMA (GLASSMORPHISM)
# ==========================================
if st.session_state.page == 'beranda':
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-weight: 800; text-shadow: 2px 2px 4px rgba(0,0,0,0.6);'>Sistem Informasi Spasial Lahan Kentang</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px; color: #e2e2e2;'>Platform Prediksi Kesesuaian Lahan Berbasis Agroklimat & Sebaran Hara</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.15); margin: 40px 0;'>", unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Peta Kesesuaian Lahan", use_container_width=True):
            st.session_state.page = 'fitur_peta'
            st.rerun()
    with col_btn2:
        if st.button("Rekomendasi Pemupukan", use_container_width=True):
            st.session_state.page = 'fitur_pupuk'
            st.rerun()
    st.markdown("<br><br>", unsafe_allow_html=True)

# ==========================================
# HALAMAN 2: PETA KESESUAIAN
# ==========================================
elif st.session_state.page == 'fitur_peta':
    
    col_judul, col_kembali = st.columns([4, 1])
    with col_judul:
        st.markdown("<h2 style='margin:0; font-weight: 700;'>Pemetaan Kesesuaian Lahan</h2>", unsafe_allow_html=True)
    with col_kembali:
        if st.button("Kembali ke Beranda", use_container_width=True):
            st.session_state.page = 'beranda'
            st.rerun()
            
    st.markdown("<hr style='border-color: rgba(255,255,255,0.15); margin: 15px 0 25px 0;'>", unsafe_allow_html=True)

    col_input, col_peta = st.columns([1.2, 2.8])
    
    with col_input:
        st.markdown("<h4>Parameter Analisis</h4>", unsafe_allow_html=True)
        radius_km = st.slider("Radius Batas Toleransi (Km)", 1.0, 15.0, 3.0, 0.5)
        ph_manual = st.number_input("Input Data pH Lokal (Opsional)", 0.0, 14.0, 0.0, 0.1)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if not df_data.empty:
            st.success(f"Data Berhasil Dimuat: {len(df_data)} Titik Observasi")
        else:
            st.error("Data tidak terdeteksi di server.")
            
    with col_peta:
        m = folium.Map(
            location=[-7.2106, 109.8941], 
            zoom_start=9, 
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
            attr='Google Maps Satellite'
        )
        
        if not df_data.empty:
            for _, row in df_data.iterrows():
                kategori = str(row.get('Status', '')).strip().lower()
                
                # PALET WARNA BARU (RAMAH BUTA WARNA / COLORBLIND FRIENDLY)
                if kategori == 'cocok': 
                    warna = '#0072B2'       # Biru Cerah Kontras Tinggi
                elif kategori == 'netral': 
                    warna = '#E69F00'       # Oranye/Jingga Semburat Kuning
                else: 
                    warna = '#D55E00'       # Merah Bata / Cokelat Kemerahan

                ph_tanah = row.get('PH_S1', 'N/A')
                elev = row.get('Elevasi', 'N/A')
                desa = row.get('Desa', 'N/A')
                kabupaten = row.get('Kabupaten', 'N/A')
                
                # POP-UP: Menambahkan informasi Wilayah Desa dan Kabupaten
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
                    radius=6, 
                    color='white', 
                    weight=1.5, 
                    fill=True, 
                    fill_color=warna, 
                    fill_opacity=1.0,
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
            st.session_state.clicked_lat = lat_klik
            st.session_state.clicked_lon = lon_klik
            st.rerun()

    # --- PANEL HASIL PREDIKSI & DATA REFERENSI ---
    if st.session_state.clicked_lat is not None:
        st.markdown("<hr style='border-color: rgba(255,255,255,0.15); margin: 30px 0 20px 0;'>", unsafe_allow_html=True)
        
        lat_eval = st.session_state.clicked_lat
        lon_eval = st.session_state.clicked_lon
        
        with st.spinner("Memproses analisis spasial wilayah..."):
            elevasi_satelit = get_elevation(lat_eval, lon_eval)
            
            if not df_data.empty and elevasi_satelit is not None:
                df_working = df_data.copy()
                df_working['Jarak_Km'] = df_working.apply(lambda r: hitung_jarak_haversine(lat_eval, lon_eval, r['Lat'], r['Lon']), axis=1)
                
                df_terfilter = df_working[df_working['Jarak_Km'] <= radius_km].copy()
                
                st.markdown("<h4>Hasil Evaluasi Lokasi</h4>", unsafe_allow_html=True)
                st.write(f"Koordinat Titik Uji: {lat_eval:.5f}, {lon_eval:.5f} | Ketinggian Tanah: {elevasi_satelit:.1f} mdpl")
                
                if df_terfilter.empty:
                    st.error(f"EVALUASI: Di Luar Jangkauan. Tidak ditemukan titik data acuan historis dalam radius {radius_km} km.")
                else:
                    elev_min, elev_max = df_terfilter['Elevasi'].min(), df_terfilter['Elevasi'].max()
                    
                    if elevasi_satelit < (elev_min - 50.0) or elevasi_satelit > (elev_max + 50.0):
                        st.error(f"🟥 **TIDAK COCOK:** Ketinggian lokasi berada di luar batas toleransi wilayah terdekat (Rentang Ketinggian Acuan: {elev_min:.0f} - {elev_max:.0f} mdpl).")
                    else:
                        hitung_suara = df_terfilter['Status'].str.lower().value_counts()
                        
                        if len(hitung_suara) > 1 and hitung_suara.iloc[0] == hitung_suara.iloc[1]:
                            st.warning("🟨 **NETRAL:** Karakteristik data referensi di sekitar titik uji memiliki rasio yang seimbang (50:50).")
                        else:
                            suara_dominan = hitung_suara.idxmax()
                            if suara_dominan == 'cocok':
                                st.success("🟩 **COCOK:** Mayoritas objek data observasi di sekitar lokasi ini menunjukkan kondisi lahan yang ideal.")
                            elif suara_dominan == 'netral':
                                st.warning("🟨 **NETRAL:** Zonasi di sekitar lokasi didominasi oleh karakteristik lahan marginal.")
                            else:
                                st.error("🟥 **TIDAK COCOK:** Mayoritas objek data observasi historis tidak merekomendasikan komoditas ini.")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f"<h5>Data Ketinggian & pH dari Objek Acuan Terdekat (Radius {radius_km} Km)</h5>", unsafe_allow_html=True)
                    
                    df_tabel = df_terfilter[['Kabupaten', 'Desa', 'Elevasi', 'PH_S1', 'Status', 'Jarak_Km']].copy()
                    df_tabel['Jarak_Km'] = df_tabel['Jarak_Km'].round(2)
                    df_tabel.rename(columns={
                        'Elevasi': 'Ketinggian (mdpl)',
                        'PH_S1': 'pH Tanah',
                        'Status': 'Kategori Lahan',
                        'Jarak_Km': 'Jarak ke Lokasi Uji (Km)'
                    }, inplace=True)
                    
                    st.dataframe(df_tabel, use_container_width=True, hide_index=True)
            else:
                st.error("Gagal terhubung dengan server koordinat satelit untuk menarik data elevasi.")

# ==========================================
# HALAMAN 3: REKOMENDASI PEMUPUKAN
# ==========================================
elif st.session_state.page == 'fitur_pupuk':
    col_judul, col_kembali = st.columns([4, 1])
    with col_judul:
        st.markdown("<h2 style='margin:0;'>Rekomendasi Pemupukan</h2>", unsafe_allow_html=True)
    with col_kembali:
        if st.button("Kembali ke Beranda", use_container_width=True):
            st.session_state.page = 'beranda'
            st.rerun()
            
    st.markdown("<hr style='border-color: rgba(255,255,255,0.15); margin: 15px 0 25px 0;'>", unsafe_allow_html=True)
    st.info("Modul kalkulasi matematis untuk dosis nutrisi tanah sedang dalam tahap integrasi.")
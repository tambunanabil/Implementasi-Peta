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

# --- 2. CSS: EFEK GLASSMORPHISM (KACA BURAM ELEGAN) ---
st.markdown("""
    <style>
    /* Sembunyikan elemen bawaan yang tidak perlu */
    [data-testid="stSidebar"], [data-testid="collapsedControl"], header { display: none !important; }

    /* Latar Belakang Pertanian Realistis */
    .stApp {
        background-image: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.6)), url("https://images.unsplash.com/photo-1516253593875-bd7ba052fbc5?q=80&w=1600&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }

    /* WADAH KONTEN: Efek Kaca Buram (Tembus pandang tapi jelas) & Posisi lebih ke tengah */
    .block-container {
        background-color: rgba(20, 30, 20, 0.6) !important; /* Warna gelap transparan berbaur bg */
        backdrop-filter: blur(10px); /* Efek buram/blur elegan */
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2); /* Garis tepi (list) agar tidak menyatu total */
        border-radius: 15px;
        padding: 40px !important;
        margin-top: 8vh !important; /* Mendorong panel lebih ke tengah layar */
        margin-bottom: 8vh !important;
        max-width: 1100px !important;
    }

    /* Memastikan semua teks bawaan Streamlit menjadi putih agar terbaca di panel gelap */
    .stMarkdown, .stText, label, .stMarkdown p {
        color: #ffffff !important;
    }

    /* Mempercantik Tombol Navigasi */
    .stButton>button {
        background-color: rgba(45, 106, 79, 0.9);
        color: white !important;
        border: 1px solid rgba(255,255,255,0.4);
        border-radius: 8px;
        padding: 12px 20px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: rgba(27, 67, 50, 1);
        border-color: white;
        box-shadow: 0 0 10px rgba(255,255,255,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI DATA ANTI-ERROR ---
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
        # PEMBERSIHAN NAMA KOLOM OTOMATIS (Mencegah KeyError 'Lat')
        df.columns = df.columns.str.strip()
        
        if 'Latitude' in df.columns: df.rename(columns={'Latitude': 'Lat'}, inplace=True)
        elif 'lat' in df.columns: df.rename(columns={'lat': 'Lat'}, inplace=True)
        
        if 'Longitude' in df.columns: df.rename(columns={'Longitude': 'Lon'}, inplace=True)
        elif 'lon' in df.columns: df.rename(columns={'lon': 'Lon'}, inplace=True)
        
        if 'Kecocokan' in df.columns: df.rename(columns={'Kecocokan': 'Status'}, inplace=True)

        # Perbaiki sel yang digabung (merge cell) dan hapus yang kosong
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
# HALAMAN 1: BERANDA (TENGAH, ELEGAN, GLASSMORPHISM)
# ==========================================
if st.session_state.page == 'beranda':
    # Spacer untuk mendorong konten ke tengah panel
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: white; font-weight: 800; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>Sistem Informasi Spasial Lahan Kentang</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px; color: #e0e0e0;'>Platform Prediksi Kesesuaian Lahan Berbasis Agroklimat & Sebaran Hara</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.2); margin: 30px 0;'>", unsafe_allow_html=True)
    
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
        st.markdown("<h2 style='color: white; margin:0;'>Pemetaan Kesesuaian Lahan</h2>", unsafe_allow_html=True)
    with col_kembali:
        if st.button("Kembali ke Beranda", use_container_width=True):
            st.session_state.page = 'beranda'
            st.rerun()
            
    st.markdown("<hr style='border-color: rgba(255,255,255,0.2); margin: 15px 0 25px 0;'>", unsafe_allow_html=True)

    col_input, col_peta = st.columns([1.2, 2.8])
    
    with col_input:
        st.markdown("<h4 style='color: white;'>Parameter Analisis</h4>", unsafe_allow_html=True)
        radius_km = st.slider("Radius Batas Toleransi (Km)", 1.0, 15.0, 3.0, 0.5)
        ph_manual = st.number_input("Input pH (Opsional)", 0.0, 14.0, 0.0, 0.1)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if not df_data.empty:
            st.success(f"Data Siap: {len(df_data)} titik observasi")
        else:
            st.error("Data tidak ditemukan. Cek file Excel.")
            
    with col_peta:
        m = folium.Map(
            location=[-7.2106, 109.8941], 
            zoom_start=9, 
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
            attr='Google Maps'
        )
        
        if not df_data.empty:
            for _, row in df_data.iterrows():
                kategori = str(row.get('Status', '')).strip().lower()
                
                if kategori == 'cocok': warna = '#00FF00'
                elif kategori == 'netral': warna = '#FFFF00'
                else: warna = '#FF0000'

                ph_tanah = row.get('PH_S1', 'N/A')
                elev = row.get('Elevasi', 'N/A')
                
                # Teks popup warna hitam agar terbaca jelas
                popup_text = f"<div style='color: black;'><b>{kategori.upper()}</b><br>Elevasi: {elev} mdpl<br>pH: {ph_tanah}</div>"
                
                folium.CircleMarker(
                    location=[row['Lat'], row['Lon']],
                    radius=7, 
                    color='white', 
                    weight=1.5, 
                    fill=True, 
                    fill_color=warna, 
                    fill_opacity=1.0,
                    popup=folium.Popup(popup_text, max_width=200)
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

    # --- HASIL PREDIKSI ---
    if st.session_state.clicked_lat is not None:
        st.markdown("<hr style='border-color: rgba(255,255,255,0.2); margin: 25px 0;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: white;'>Hasil Evaluasi Lokasi</h4>", unsafe_allow_html=True)
        
        lat_eval = st.session_state.clicked_lat
        lon_eval = st.session_state.clicked_lon
        
        st.write(f"**Titik Terpilih:** {lat_eval:.5f}, {lon_eval:.5f}")
        
        with st.spinner("Menarik data satelit..."):
            elevasi_satelit = get_elevation(lat_eval, lon_eval)
            
            if not df_data.empty and elevasi_satelit is not None:
                st.write(f"**Elevasi Lokasi:** {elevasi_satelit:.1f} mdpl")
                
                df_working = df_data.copy()
                df_working['Jarak_Km'] = df_working.apply(lambda r: hitung_jarak_haversine(lat_eval, lon_eval, r['Lat'], r['Lon']), axis=1)
                df_terfilter = df_working[df_working['Jarak_Km'] <= radius_km]
                
                if df_terfilter.empty:
                    st.error(f"DI LUAR JANGKAUAN: Tidak ditemukan titik acuan dalam radius {radius_km} km.")
                else:
                    elev_min, elev_max = df_terfilter['Elevasi'].min(), df_terfilter['Elevasi'].max()
                    
                    if elevasi_satelit < (elev_min - 50.0) or elevasi_satelit > (elev_max + 50.0):
                        st.error(f"TIDAK COCOK: Ketinggian melampaui batas wilayah terdekat ({elev_min:.0f} - {elev_max:.0f} mdpl).")
                    else:
                        hitung_suara = df_terfilter['Status'].str.lower().value_counts()
                        
                        if len(hitung_suara) > 1 and hitung_suara.iloc[0] == hitung_suara.iloc[1]:
                            st.warning(f"NETRAL: Karakteristik data acuan seimbang (50:50).")
                        else:
                            suara_dominan = hitung_suara.idxmax()
                            if suara_dominan == 'cocok':
                                st.success(f"COCOK: Mayoritas observasi di sekitar lokasi ini merekomendasikan penanaman.")
                            elif suara_dominan == 'netral':
                                st.warning(f"NETRAL: Zonasi di sekitar lokasi didominasi karakteristik lahan marginal.")
                            else:
                                st.error(f"TIDAK COCOK: Mayoritas observasi historis tidak merekomendasikan.")
            else:
                st.error("Gagal menarik data elevasi dari satelit.")

# ==========================================
# HALAMAN 3: REKOMENDASI PEMUPUKAN
# ==========================================
elif st.session_state.page == 'fitur_pupuk':
    col_judul, col_kembali = st.columns([4, 1])
    with col_judul:
        st.markdown("<h2 style='color: white; margin:0;'>Rekomendasi Pemupukan</h2>", unsafe_allow_html=True)
    with col_kembali:
        if st.button("Kembali ke Beranda", use_container_width=True):
            st.session_state.page = 'beranda'
            st.rerun()
            
    st.markdown("<hr style='border-color: rgba(255,255,255,0.2); margin: 15px 0 25px 0;'>", unsafe_allow_html=True)
    st.info("Modul kalkulasi nutrisi tanah sedang dipersiapkan.")